-- =====================================================================
--  Pharmacy Inventory & Sales Management System
--  File 2 of 6 : VIEWS, FUNCTION, STORED PROCEDURES, TRIGGERS, EVENT
--  (Weeks 13-14 : sub-queries, stored procedures, triggers, DB events)
--  Rule used everywhere:  expiry_date = LAST day the batch may be sold.
-- =====================================================================
USE pharmacy_db;

-- ---------------------------------------------------------------------
-- A. VIEWS
-- ---------------------------------------------------------------------

-- Sellable stock and expired stock per product (LEFT JOIN keeps products with no batches)
CREATE OR REPLACE VIEW v_product_stock AS
SELECT  p.product_id,
        p.name                                   AS product_name,
        c.category_name,
        p.reorder_level,
        COALESCE(SUM(CASE WHEN b.expiry_date >= CURRENT_DATE THEN b.quantity END), 0) AS on_hand,
        COALESCE(SUM(CASE WHEN b.expiry_date <  CURRENT_DATE THEN b.quantity END), 0) AS expired_qty
FROM    products p
JOIN    categories c        ON c.category_id = p.category_id
LEFT JOIN stock_batches b   ON b.product_id  = p.product_id
GROUP BY p.product_id, p.name, c.category_name, p.reorder_level;

-- VIEW 1 (proposal): low-stock medicines  (sellable stock below the reorder level)
CREATE OR REPLACE VIEW v_low_stock AS
SELECT  product_id, product_name, category_name, on_hand, reorder_level,
        (reorder_level - on_hand) AS shortage
FROM    v_product_stock
WHERE   on_hand < reorder_level;

-- VIEW 2 (proposal): batches expiring within the next 30 days
CREATE OR REPLACE VIEW v_expiring_30_days AS
SELECT  b.batch_id, p.product_id, p.name AS product_name, b.batch_no,
        b.quantity, b.expiry_date,
        DATEDIFF(b.expiry_date, CURRENT_DATE)  AS days_left,
        (b.quantity * b.cost_price)            AS stock_value_at_cost
FROM    stock_batches b
JOIN    products p ON p.product_id = b.product_id
WHERE   b.quantity > 0
  AND   b.expiry_date BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY);

-- Extra view: stock that is already expired and must be removed from the shelf
CREATE OR REPLACE VIEW v_expired_stock AS
SELECT  b.batch_id, p.product_id, p.name AS product_name, b.batch_no,
        b.quantity, b.expiry_date,
        DATEDIFF(CURRENT_DATE, b.expiry_date)  AS days_expired,
        (b.quantity * b.cost_price)            AS loss_at_cost
FROM    stock_batches b
JOIN    products p ON p.product_id = b.product_id
WHERE   b.quantity > 0 AND b.expiry_date < CURRENT_DATE;

-- VIEW 3 (proposal): daily sales summary
CREATE OR REPLACE VIEW v_daily_sales_summary AS
SELECT  DATE(s.sale_date)                         AS sale_day,
        COUNT(DISTINCT s.sale_id)                 AS bills,
        SUM(si.quantity)                          AS units_sold,
        SUM(si.quantity * si.unit_price)          AS revenue,
        ROUND(SUM(si.quantity * si.unit_price) / COUNT(DISTINCT s.sale_id), 2) AS avg_bill
FROM    sales s
JOIN    sale_items si ON si.sale_id = s.sale_id
GROUP BY DATE(s.sale_date);

-- Extra view: printable bill lines
CREATE OR REPLACE VIEW v_sale_details AS
SELECT  s.sale_id, s.sale_date, cu.name AS customer, e.name AS served_by,
        p.name AS product, si.quantity, si.unit_price,
        (si.quantity * si.unit_price) AS line_total, s.payment_method
FROM    sales s
JOIN    customers cu  ON cu.customer_id = s.customer_id
JOIN    employees e   ON e.employee_id  = s.employee_id
JOIN    sale_items si ON si.sale_id     = s.sale_id
JOIN    products p    ON p.product_id   = si.product_id;

DELIMITER $$

-- ---------------------------------------------------------------------
-- B. STORED FUNCTION : sellable stock of one product on a given day
-- ---------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_stock_on_hand$$
CREATE FUNCTION fn_stock_on_hand(p_product_id INT UNSIGNED, p_on_date DATE)
RETURNS INT
READS SQL DATA
BEGIN
    RETURN COALESCE((SELECT SUM(quantity)
                     FROM   stock_batches
                     WHERE  product_id  = p_product_id
                       AND  expiry_date >= p_on_date), 0);
END$$

-- ---------------------------------------------------------------------
-- C. TRIGGERS  (data integrity + automatic stock management)
-- ---------------------------------------------------------------------

-- C1. EER specialisation: a pharmacist row must belong to a 'Pharmacist' employee
DROP TRIGGER IF EXISTS trg_pharmacists_bi$$
CREATE TRIGGER trg_pharmacists_bi BEFORE INSERT ON pharmacists
FOR EACH ROW
BEGIN
    IF (SELECT role FROM employees WHERE employee_id = NEW.employee_id) <> 'Pharmacist' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only employees with role Pharmacist can be stored in pharmacists';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_cashiers_bi$$
CREATE TRIGGER trg_cashiers_bi BEFORE INSERT ON cashiers
FOR EACH ROW
BEGIN
    IF (SELECT role FROM employees WHERE employee_id = NEW.employee_id) <> 'Cashier' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only employees with role Cashier can be stored in cashiers';
    END IF;
END$$

-- C2. Price-change audit
DROP TRIGGER IF EXISTS trg_products_au$$
CREATE TRIGGER trg_products_au AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    IF OLD.unit_price <> NEW.unit_price THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value)
        VALUES ('products', NEW.product_id, 'PRICE_CHANGE',
                CAST(OLD.unit_price AS CHAR), CAST(NEW.unit_price AS CHAR));
    END IF;
END$$

-- C3. Purchase-order rules
DROP TRIGGER IF EXISTS trg_po_bu$$
CREATE TRIGGER trg_po_bu BEFORE UPDATE ON purchase_orders
FOR EACH ROW
BEGIN
    IF OLD.status IN ('Received','Cancelled') AND NEW.status <> OLD.status THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A Received or Cancelled purchase order cannot change status';
    END IF;
END$$

-- C4. Stock batches : validate, then keep purchase_orders.total_cost in step
DROP TRIGGER IF EXISTS trg_batches_bi$$
CREATE TRIGGER trg_batches_bi BEFORE INSERT ON stock_batches
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_odate  DATE;
    SET v_status = (SELECT status     FROM purchase_orders WHERE po_id = NEW.po_id);
    SET v_odate  = (SELECT order_date FROM purchase_orders WHERE po_id = NEW.po_id);
    IF v_status = 'Cancelled' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot add stock to a cancelled purchase order';
    END IF;
    IF NEW.expiry_date <= v_odate THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Batch is already expired on the purchase-order date';
    END IF;
    SET NEW.quantity = NEW.received_qty;      -- a new batch starts full
END$$

DROP TRIGGER IF EXISTS trg_batches_ai$$
CREATE TRIGGER trg_batches_ai AFTER INSERT ON stock_batches
FOR EACH ROW
BEGIN
    UPDATE purchase_orders
    SET    total_cost = total_cost + NEW.received_qty * NEW.cost_price
    WHERE  po_id = NEW.po_id;
END$$

DROP TRIGGER IF EXISTS trg_batches_au$$
CREATE TRIGGER trg_batches_au AFTER UPDATE ON stock_batches
FOR EACH ROW
BEGIN
    IF NEW.received_qty <> OLD.received_qty OR NEW.cost_price <> OLD.cost_price THEN
        UPDATE purchase_orders
        SET    total_cost = total_cost - OLD.received_qty * OLD.cost_price
                                       + NEW.received_qty * NEW.cost_price
        WHERE  po_id = NEW.po_id;
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_batches_ad$$
CREATE TRIGGER trg_batches_ad AFTER DELETE ON stock_batches
FOR EACH ROW
BEGIN
    UPDATE purchase_orders
    SET    total_cost = total_cost - OLD.received_qty * OLD.cost_price
    WHERE  po_id = OLD.po_id;
END$$

-- C5. Sales : only active pharmacists / cashiers may make a sale; total starts at 0
DROP TRIGGER IF EXISTS trg_sales_bi$$
CREATE TRIGGER trg_sales_bi BEFORE INSERT ON sales
FOR EACH ROW
BEGIN
    DECLARE v_role   VARCHAR(30);
    DECLARE v_active BOOLEAN;
    SET v_role   = (SELECT role      FROM employees WHERE employee_id = NEW.employee_id);
    SET v_active = (SELECT is_active FROM employees WHERE employee_id = NEW.employee_id);
    IF v_role NOT IN ('Pharmacist','Cashier') OR v_active = FALSE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only active pharmacists or cashiers can make a sale';
    END IF;
    SET NEW.total_amount = 0;
END$$

-- Deleting a whole sale: put the stock back (MySQL does not fire row triggers on cascades)
DROP TRIGGER IF EXISTS trg_sales_bd$$
CREATE TRIGGER trg_sales_bd BEFORE DELETE ON sales
FOR EACH ROW
BEGIN
    UPDATE stock_batches b
    JOIN   sale_allocations a ON a.batch_id = b.batch_id
    SET    b.quantity = b.quantity + a.quantity
    WHERE  a.sale_id = OLD.sale_id;
END$$

-- C6. SALE ITEMS (the heart of the system)
--   BEFORE INSERT : block the sale when sellable stock is not enough   (proposal)
--   AFTER  INSERT : reduce stock batch by batch, First-Expiry-First-Out (proposal)
DROP TRIGGER IF EXISTS trg_sale_items_bi$$
CREATE TRIGGER trg_sale_items_bi BEFORE INSERT ON sale_items
FOR EACH ROW
BEGIN
    DECLARE v_day   DATE;
    DECLARE v_avail INT;
    SET v_day   = (SELECT DATE(sale_date) FROM sales WHERE sale_id = NEW.sale_id);
    SET v_avail = fn_stock_on_hand(NEW.product_id, v_day);
    IF v_avail < NEW.quantity THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient stock: requested quantity exceeds sellable (unexpired) stock';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_sale_items_ai$$
CREATE TRIGGER trg_sale_items_ai AFTER INSERT ON sale_items
FOR EACH ROW
BEGIN
    DECLARE v_day        DATE;
    DECLARE v_remaining  INT;
    DECLARE v_batch      INT UNSIGNED;
    DECLARE v_bqty       INT;
    DECLARE v_cost       DECIMAL(10,2);
    DECLARE v_take       INT;
    DECLARE v_done       BOOLEAN DEFAULT FALSE;

    -- earliest-expiring sellable batches first
    DECLARE cur_batches CURSOR FOR
        SELECT batch_id, quantity, cost_price
        FROM   stock_batches
        WHERE  product_id = NEW.product_id AND quantity > 0 AND expiry_date >= v_day
        ORDER BY expiry_date, batch_id
        FOR UPDATE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;

    SET v_day       = (SELECT DATE(sale_date) FROM sales WHERE sale_id = NEW.sale_id);
    SET v_remaining = NEW.quantity;

    OPEN cur_batches;
    alloc_loop: LOOP
        FETCH cur_batches INTO v_batch, v_bqty, v_cost;
        IF v_done THEN LEAVE alloc_loop; END IF;

        SET v_take = LEAST(v_remaining, v_bqty);
        UPDATE stock_batches SET quantity = quantity - v_take WHERE batch_id = v_batch;
        INSERT INTO sale_allocations (sale_id, product_id, batch_id, quantity, cost_price)
        VALUES (NEW.sale_id, NEW.product_id, v_batch, v_take, v_cost);

        SET v_remaining = v_remaining - v_take;
        IF v_remaining = 0 THEN LEAVE alloc_loop; END IF;
    END LOOP;
    CLOSE cur_batches;

    IF v_remaining > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock allocation failed (concurrent sale?)';
    END IF;

    UPDATE sales
    SET    total_amount = total_amount + NEW.quantity * NEW.unit_price
    WHERE  sale_id = NEW.sale_id;
END$$

-- A sale line is never edited in place: delete it and add it again.
DROP TRIGGER IF EXISTS trg_sale_items_bu$$
CREATE TRIGGER trg_sale_items_bu BEFORE UPDATE ON sale_items
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Sale items cannot be updated; delete the line and add it again';
END$$

-- Deleting one line: return its stock and reduce the bill total
DROP TRIGGER IF EXISTS trg_sale_items_bd$$
CREATE TRIGGER trg_sale_items_bd BEFORE DELETE ON sale_items
FOR EACH ROW
BEGIN
    UPDATE stock_batches b
    JOIN   sale_allocations a ON a.batch_id = b.batch_id
    SET    b.quantity = b.quantity + a.quantity
    WHERE  a.sale_id = OLD.sale_id AND a.product_id = OLD.product_id;

    UPDATE sales
    SET    total_amount = total_amount - OLD.quantity * OLD.unit_price
    WHERE  sale_id = OLD.sale_id;
END$$

-- ---------------------------------------------------------------------
-- D. STORED PROCEDURES
-- ---------------------------------------------------------------------

-- D1. TRANSACTION (proposal): checkout = sale + sale items + stock update, all or nothing.
--     p_items example:  '[{"product_id":1,"qty":2},{"product_id":7,"qty":1}]'
DROP PROCEDURE IF EXISTS sp_checkout$$
CREATE PROCEDURE sp_checkout(
    IN  p_customer_id     INT UNSIGNED,
    IN  p_employee_id     INT UNSIGNED,
    IN  p_payment_method  VARCHAR(20),
    IN  p_items           JSON,
    OUT p_sale_id         INT UNSIGNED)
BEGIN
    DECLARE v_pid   INT UNSIGNED;
    DECLARE v_qty   INT;
    DECLARE v_price DECIMAL(10,2);
    DECLARE v_done  BOOLEAN DEFAULT FALSE;

    DECLARE cur_items CURSOR FOR
        SELECT jt.product_id, SUM(jt.qty)
        FROM   JSON_TABLE(p_items, '$[*]'
                   COLUMNS (product_id INT UNSIGNED PATH '$.product_id',
                            qty        INT          PATH '$.qty')) AS jt
        GROUP BY jt.product_id
        ORDER BY jt.product_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;          -- undo the sale, its items and every stock change
        RESIGNAL;          -- tell the caller why it failed
    END;

    IF p_items IS NULL OR JSON_LENGTH(p_items) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A bill must contain at least one item';
    END IF;

    START TRANSACTION;

    INSERT INTO sales (customer_id, employee_id, sale_date, payment_method)
    VALUES (p_customer_id, p_employee_id, NOW(), p_payment_method);
    SET p_sale_id = LAST_INSERT_ID();

    OPEN cur_items;
    item_loop: LOOP
        FETCH cur_items INTO v_pid, v_qty;
        IF v_done THEN LEAVE item_loop; END IF;

        SET v_price = (SELECT unit_price FROM products WHERE product_id = v_pid);
        IF v_price IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unknown product in bill';
        END IF;

        -- the triggers check stock, deduct it (FEFO) and update the bill total
        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
        VALUES (p_sale_id, v_pid, v_qty, v_price);
    END LOOP;
    CLOSE cur_items;

    COMMIT;
END$$

-- D2. Receive a delivery: creates a Received purchase order and one batch per line.
--     p_items example: '[{"product_id":1,"qty":100,"cost_price":8.5,"expiry_date":"2028-03-31","batch_no":"B123"}]'
DROP PROCEDURE IF EXISTS sp_receive_stock$$
CREATE PROCEDURE sp_receive_stock(
    IN  p_supplier_id  INT UNSIGNED,
    IN  p_order_date   DATE,
    IN  p_items        JSON,
    OUT p_po_id        INT UNSIGNED)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_items IS NULL OR JSON_LENGTH(p_items) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A purchase order must contain at least one line';
    END IF;

    START TRANSACTION;

    INSERT INTO purchase_orders (supplier_id, order_date, status)
    VALUES (p_supplier_id, p_order_date, 'Received');
    SET p_po_id = LAST_INSERT_ID();

    INSERT INTO stock_batches (product_id, po_id, batch_no, received_qty, quantity, expiry_date, cost_price)
    SELECT jt.product_id, p_po_id, jt.batch_no, jt.qty, jt.qty, jt.expiry_date, jt.cost_price
    FROM   JSON_TABLE(p_items, '$[*]'
               COLUMNS (product_id  INT UNSIGNED  PATH '$.product_id',
                        qty         INT           PATH '$.qty',
                        cost_price  DECIMAL(10,2) PATH '$.cost_price',
                        expiry_date DATE          PATH '$.expiry_date',
                        batch_no    VARCHAR(30)   PATH '$.batch_no')) AS jt;

    COMMIT;
END$$

-- D3. STORED PROCEDURE (proposal): monthly sales and profit report.
--     Returns three result sets: (1) summary, (2) top-5 products by profit, (3) revenue by category.
DROP PROCEDURE IF EXISTS sp_monthly_report$$
CREATE PROCEDURE sp_monthly_report(IN p_year INT, IN p_month INT)
BEGIN
    DECLARE v_start DATE;
    DECLARE v_end   DATE;

    IF p_month NOT BETWEEN 1 AND 12 OR p_year NOT BETWEEN 2000 AND 2100 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Month must be 1-12 and year 2000-2100';
    END IF;

    SET v_start = STR_TO_DATE(CONCAT(p_year, '-', p_month, '-01'), '%Y-%m-%d');
    SET v_end   = DATE_ADD(v_start, INTERVAL 1 MONTH);

    -- (1) summary
    SELECT  DATE_FORMAT(v_start, '%Y-%m')                       AS report_month,
            r.bills, r.units_sold, r.revenue, c.cost,
            (r.revenue - c.cost)                                AS profit,
            ROUND(100 * (r.revenue - c.cost) / NULLIF(r.revenue, 0), 2) AS margin_pct
    FROM   (SELECT COUNT(DISTINCT s.sale_id)          AS bills,
                   COALESCE(SUM(si.quantity), 0)      AS units_sold,
                   COALESCE(SUM(si.quantity * si.unit_price), 0) AS revenue
            FROM   sales s JOIN sale_items si ON si.sale_id = s.sale_id
            WHERE  s.sale_date >= v_start AND s.sale_date < v_end) AS r
    CROSS JOIN
           (SELECT COALESCE(SUM(a.quantity * a.cost_price), 0) AS cost
            FROM   sale_allocations a JOIN sales s ON s.sale_id = a.sale_id
            WHERE  s.sale_date >= v_start AND s.sale_date < v_end) AS c;

    -- (2) top 5 products by profit
    SELECT  p.name AS product, SUM(si.quantity) AS units,
            SUM(si.quantity * si.unit_price)    AS revenue,
            SUM(si.quantity * si.unit_price) - SUM(x.cost) AS profit
    FROM    sale_items si
    JOIN    sales s    ON s.sale_id    = si.sale_id
    JOIN    products p ON p.product_id = si.product_id
    JOIN   (SELECT sale_id, product_id, SUM(quantity * cost_price) AS cost
            FROM   sale_allocations GROUP BY sale_id, product_id) x
           ON x.sale_id = si.sale_id AND x.product_id = si.product_id
    WHERE   s.sale_date >= v_start AND s.sale_date < v_end
    GROUP BY p.product_id, p.name
    ORDER BY profit DESC
    LIMIT 5;

    -- (3) revenue by category
    SELECT  c.category_name, SUM(si.quantity) AS units,
            SUM(si.quantity * si.unit_price)  AS revenue
    FROM    sale_items si
    JOIN    sales s      ON s.sale_id      = si.sale_id
    JOIN    products p   ON p.product_id   = si.product_id
    JOIN    categories c ON c.category_id  = p.category_id
    WHERE   s.sale_date >= v_start AND s.sale_date < v_end
    GROUP BY c.category_id, c.category_name
    ORDER BY revenue DESC;
END$$

-- D4. Refresh the stock_alerts table (low stock, near expiry, expired)
DROP PROCEDURE IF EXISTS sp_refresh_stock_alerts$$
CREATE PROCEDURE sp_refresh_stock_alerts()
BEGIN
    DELETE FROM stock_alerts WHERE created_at >= CURRENT_DATE;   -- today's alerts are rebuilt

    INSERT INTO stock_alerts (alert_type, product_id, batch_id, message)
    SELECT 'LOW_STOCK', product_id, NULL,
           CONCAT(product_name, ': only ', on_hand, ' left (reorder level ', reorder_level, ')')
    FROM   v_low_stock;

    INSERT INTO stock_alerts (alert_type, product_id, batch_id, message)
    SELECT 'NEAR_EXPIRY', product_id, batch_id,
           CONCAT(product_name, ' batch ', batch_no, ' expires in ', days_left, ' day(s)')
    FROM   v_expiring_30_days;

    INSERT INTO stock_alerts (alert_type, product_id, batch_id, message)
    SELECT 'EXPIRED', product_id, batch_id,
           CONCAT(product_name, ' batch ', batch_no, ' expired ', days_expired, ' day(s) ago - remove from shelf')
    FROM   v_expired_stock;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- E. DATABASE EVENT (DB event management): rebuild alerts every morning.
--    The scheduler is OFF by default:  SET GLOBAL event_scheduler = ON;
-- ---------------------------------------------------------------------
DROP EVENT IF EXISTS ev_daily_stock_alerts;
CREATE EVENT ev_daily_stock_alerts
    ON SCHEDULE EVERY 1 DAY
    STARTS (TIMESTAMP(CURRENT_DATE) + INTERVAL 1 DAY + INTERVAL 6 HOUR)
    DO CALL sp_refresh_stock_alerts();
