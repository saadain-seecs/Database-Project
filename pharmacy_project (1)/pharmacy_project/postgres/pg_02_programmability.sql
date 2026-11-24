-- =====================================================================
--  File 2 of 5 : VIEWS, FUNCTIONS, PROCEDURE, TRIGGERS (PL/pgSQL)
--  expiry_date = LAST day a batch may be sold.
-- =====================================================================
\set ON_ERROR_STOP on
\connect pharmacy_db

CREATE OR REPLACE VIEW v_product_stock AS
SELECT p.product_id, p.name AS product_name, c.category_name, p.reorder_level,
       COALESCE(SUM(b.quantity) FILTER (WHERE b.expiry_date >= CURRENT_DATE), 0)::INT AS on_hand,
       COALESCE(SUM(b.quantity) FILTER (WHERE b.expiry_date <  CURRENT_DATE), 0)::INT AS expired_qty
FROM products p
JOIN categories c      ON c.category_id = p.category_id
LEFT JOIN stock_batches b ON b.product_id = p.product_id
GROUP BY p.product_id, p.name, c.category_name, p.reorder_level;

CREATE OR REPLACE VIEW v_low_stock AS
SELECT product_id, product_name, category_name, on_hand, reorder_level,
       (reorder_level - on_hand) AS shortage
FROM v_product_stock WHERE on_hand < reorder_level;

CREATE OR REPLACE VIEW v_expiring_30_days AS
SELECT b.batch_id, p.product_id, p.name AS product_name, b.batch_no, b.quantity, b.expiry_date,
       (b.expiry_date - CURRENT_DATE)  AS days_left,
       (b.quantity * b.cost_price)     AS stock_value_at_cost
FROM stock_batches b JOIN products p ON p.product_id = b.product_id
WHERE b.quantity > 0 AND b.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 30;

CREATE OR REPLACE VIEW v_expired_stock AS
SELECT b.batch_id, p.product_id, p.name AS product_name, b.batch_no, b.quantity, b.expiry_date,
       (CURRENT_DATE - b.expiry_date)  AS days_expired,
       (b.quantity * b.cost_price)     AS loss_at_cost
FROM stock_batches b JOIN products p ON p.product_id = b.product_id
WHERE b.quantity > 0 AND b.expiry_date < CURRENT_DATE;

CREATE OR REPLACE VIEW v_daily_sales_summary AS
SELECT s.sale_date::date AS sale_day,
       COUNT(DISTINCT s.sale_id) AS bills,
       SUM(si.quantity)          AS units_sold,
       SUM(si.line_total)        AS revenue,
       ROUND(SUM(si.line_total) / COUNT(DISTINCT s.sale_id), 2) AS avg_bill
FROM sales s JOIN sale_items si ON si.sale_id = s.sale_id
GROUP BY s.sale_date::date;

CREATE OR REPLACE VIEW v_sale_details AS
SELECT s.sale_id, s.sale_date, cu.name AS customer, e.name AS served_by, p.name AS product,
       si.quantity, si.unit_price, si.line_total, s.payment_method
FROM sales s
JOIN customers cu  ON cu.customer_id = s.customer_id
JOIN employees e   ON e.employee_id  = s.employee_id
JOIN sale_items si ON si.sale_id     = s.sale_id
JOIN products p    ON p.product_id   = si.product_id;

-- Materialized view (PostgreSQL feature): stored result, refreshed on demand
CREATE MATERIALIZED VIEW mv_monthly_sales AS
SELECT to_char(s.sale_date, 'YYYY-MM') AS sale_month,
       COUNT(DISTINCT s.sale_id) AS bills,
       SUM(si.quantity)          AS units_sold,
       SUM(si.line_total)        AS revenue
FROM sales s JOIN sale_items si ON si.sale_id = s.sale_id
GROUP BY to_char(s.sale_date, 'YYYY-MM');

-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_stock_on_hand(p_product_id INT, p_on_date DATE)
RETURNS INT LANGUAGE sql STABLE AS $$
    SELECT COALESCE(SUM(quantity), 0)::INT
    FROM stock_batches WHERE product_id = p_product_id AND expiry_date >= p_on_date;
$$;

-- ---------------------------------------------------------------------
-- TRIGGER FUNCTIONS
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION tf_pharmacists_bi() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (SELECT role FROM employees WHERE employee_id = NEW.employee_id) <> 'Pharmacist' THEN
        RAISE EXCEPTION 'Only employees with role Pharmacist can be stored in pharmacists';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_pharmacists_bi BEFORE INSERT ON pharmacists FOR EACH ROW EXECUTE FUNCTION tf_pharmacists_bi();

CREATE OR REPLACE FUNCTION tf_cashiers_bi() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (SELECT role FROM employees WHERE employee_id = NEW.employee_id) <> 'Cashier' THEN
        RAISE EXCEPTION 'Only employees with role Cashier can be stored in cashiers';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_cashiers_bi BEFORE INSERT ON cashiers FOR EACH ROW EXECUTE FUNCTION tf_cashiers_bi();

CREATE OR REPLACE FUNCTION tf_products_au() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.unit_price <> NEW.unit_price THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value)
        VALUES ('products', NEW.product_id, 'PRICE_CHANGE', OLD.unit_price::text, NEW.unit_price::text);
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_products_au AFTER UPDATE ON products FOR EACH ROW EXECUTE FUNCTION tf_products_au();

CREATE OR REPLACE FUNCTION tf_po_bu() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status IN ('Received','Cancelled') AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION 'A Received or Cancelled purchase order cannot change status';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_po_bu BEFORE UPDATE ON purchase_orders FOR EACH ROW EXECUTE FUNCTION tf_po_bu();

CREATE OR REPLACE FUNCTION tf_batches_bi() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_status po_status_t; v_odate DATE;
BEGIN
    SELECT status, order_date INTO v_status, v_odate FROM purchase_orders WHERE po_id = NEW.po_id;
    IF v_status = 'Cancelled' THEN
        RAISE EXCEPTION 'Cannot add stock to a cancelled purchase order';
    END IF;
    IF NEW.expiry_date <= v_odate THEN
        RAISE EXCEPTION 'Batch is already expired on the purchase-order date';
    END IF;
    NEW.quantity := NEW.received_qty;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_batches_bi BEFORE INSERT ON stock_batches FOR EACH ROW EXECUTE FUNCTION tf_batches_bi();

CREATE OR REPLACE FUNCTION tf_batches_total() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE purchase_orders SET total_cost = total_cost + NEW.received_qty * NEW.cost_price WHERE po_id = NEW.po_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.received_qty <> OLD.received_qty OR NEW.cost_price <> OLD.cost_price THEN
            UPDATE purchase_orders
            SET total_cost = total_cost - OLD.received_qty * OLD.cost_price + NEW.received_qty * NEW.cost_price
            WHERE po_id = NEW.po_id;
        END IF;
    ELSE
        UPDATE purchase_orders SET total_cost = total_cost - OLD.received_qty * OLD.cost_price WHERE po_id = OLD.po_id;
    END IF;
    RETURN NULL;
END $$;
CREATE TRIGGER trg_batches_total AFTER INSERT OR UPDATE OR DELETE ON stock_batches
    FOR EACH ROW EXECUTE FUNCTION tf_batches_total();

CREATE OR REPLACE FUNCTION tf_sales_bi() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_role employee_role_t; v_active BOOLEAN;
BEGIN
    SELECT role, is_active INTO v_role, v_active FROM employees WHERE employee_id = NEW.employee_id;
    IF v_role NOT IN ('Pharmacist','Cashier') OR v_active = FALSE THEN
        RAISE EXCEPTION 'Only active pharmacists or cashiers can make a sale';
    END IF;
    NEW.total_amount := 0;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_sales_bi BEFORE INSERT ON sales FOR EACH ROW EXECUTE FUNCTION tf_sales_bi();

-- Before a sale line is added: block when sellable stock is not enough
CREATE OR REPLACE FUNCTION tf_sale_items_bi() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_day DATE;
BEGIN
    SELECT sale_date::date INTO v_day FROM sales WHERE sale_id = NEW.sale_id;
    IF fn_stock_on_hand(NEW.product_id, v_day) < NEW.quantity THEN
        RAISE EXCEPTION 'Insufficient stock: requested quantity exceeds sellable (unexpired) stock';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_sale_items_bi BEFORE INSERT ON sale_items FOR EACH ROW EXECUTE FUNCTION tf_sale_items_bi();

-- After a sale line is added: First-Expiry-First-Out deduction
CREATE OR REPLACE FUNCTION tf_sale_items_ai() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_day DATE; v_remaining INT; v_take INT; r RECORD;
BEGIN
    SELECT sale_date::date INTO v_day FROM sales WHERE sale_id = NEW.sale_id;
    v_remaining := NEW.quantity;
    FOR r IN SELECT batch_id, quantity, cost_price FROM stock_batches
             WHERE product_id = NEW.product_id AND quantity > 0 AND expiry_date >= v_day
             ORDER BY expiry_date, batch_id FOR UPDATE
    LOOP
        v_take := LEAST(v_remaining, r.quantity);
        UPDATE stock_batches SET quantity = quantity - v_take WHERE batch_id = r.batch_id;
        INSERT INTO sale_allocations (sale_id, product_id, batch_id, quantity, cost_price)
        VALUES (NEW.sale_id, NEW.product_id, r.batch_id, v_take, r.cost_price);
        v_remaining := v_remaining - v_take;
        EXIT WHEN v_remaining = 0;
    END LOOP;
    IF v_remaining > 0 THEN
        RAISE EXCEPTION 'Stock allocation failed (concurrent sale?)';
    END IF;
    UPDATE sales SET total_amount = total_amount + NEW.quantity * NEW.unit_price WHERE sale_id = NEW.sale_id;
    RETURN NULL;
END $$;
CREATE TRIGGER trg_sale_items_ai AFTER INSERT ON sale_items FOR EACH ROW EXECUTE FUNCTION tf_sale_items_ai();

CREATE OR REPLACE FUNCTION tf_sale_items_bu() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Sale items cannot be updated; delete the line and add it again';
END $$;
CREATE TRIGGER trg_sale_items_bu BEFORE UPDATE ON sale_items FOR EACH ROW EXECUTE FUNCTION tf_sale_items_bu();

-- Fires for a direct delete AND for the cascade from sales (PostgreSQL fires triggers on cascades)
CREATE OR REPLACE FUNCTION tf_sale_items_bd() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE stock_batches b SET quantity = b.quantity + a.quantity
    FROM sale_allocations a
    WHERE a.batch_id = b.batch_id AND a.sale_id = OLD.sale_id AND a.product_id = OLD.product_id;
    UPDATE sales SET total_amount = total_amount - OLD.quantity * OLD.unit_price WHERE sale_id = OLD.sale_id;
    RETURN OLD;
END $$;
CREATE TRIGGER trg_sale_items_bd BEFORE DELETE ON sale_items FOR EACH ROW EXECUTE FUNCTION tf_sale_items_bd();

-- ---------------------------------------------------------------------
-- "STORED PROCEDURES".  A PL/pgSQL function is one atomic statement:
-- any exception rolls back everything it did (the checkout transaction).
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_checkout(p_customer_id INT, p_employee_id INT, p_payment_method TEXT, p_items JSONB)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE v_sale_id INT; r RECORD;
BEGIN
    IF p_items IS NULL OR jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'A bill must contain at least one item';
    END IF;
    INSERT INTO sales (customer_id, employee_id, sale_date, payment_method)
    VALUES (p_customer_id, p_employee_id, now(), p_payment_method::payment_method_t)
    RETURNING sale_id INTO v_sale_id;

    FOR r IN SELECT x.product_id, SUM(x.qty)::INT AS qty
             FROM jsonb_to_recordset(p_items) AS x(product_id INT, qty INT)
             GROUP BY x.product_id ORDER BY x.product_id
    LOOP
        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
        SELECT v_sale_id, r.product_id, r.qty, unit_price FROM products WHERE product_id = r.product_id;
        IF NOT FOUND THEN RAISE EXCEPTION 'Unknown product in bill'; END IF;
    END LOOP;
    RETURN v_sale_id;
END $$;

CREATE OR REPLACE FUNCTION sp_receive_stock(p_supplier_id INT, p_order_date DATE, p_items JSONB)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE v_po INT;
BEGIN
    IF p_items IS NULL OR jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'A purchase order must contain at least one line';
    END IF;
    INSERT INTO purchase_orders (supplier_id, order_date, status)
    VALUES (p_supplier_id, p_order_date, 'Received') RETURNING po_id INTO v_po;
    INSERT INTO stock_batches (product_id, po_id, batch_no, received_qty, quantity, expiry_date, cost_price)
    SELECT x.product_id, v_po, x.batch_no, x.qty, x.qty, x.expiry_date, x.cost_price
    FROM jsonb_to_recordset(p_items)
         AS x(product_id INT, qty INT, cost_price NUMERIC, expiry_date DATE, batch_no TEXT);
    RETURN v_po;
END $$;

-- Monthly report: PostgreSQL functions return table results (3 functions instead of 3 result sets)
CREATE OR REPLACE FUNCTION fn_monthly_report(p_year INT, p_month INT)
RETURNS TABLE (report_month TEXT, bills BIGINT, units_sold BIGINT, revenue NUMERIC, cost NUMERIC,
               profit NUMERIC, margin_pct NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE v_start DATE; v_end DATE;
BEGIN
    IF p_month NOT BETWEEN 1 AND 12 OR p_year NOT BETWEEN 2000 AND 2100 THEN
        RAISE EXCEPTION 'Month must be 1-12 and year 2000-2100';
    END IF;
    v_start := make_date(p_year, p_month, 1);
    v_end   := v_start + INTERVAL '1 month';
    RETURN QUERY
    SELECT to_char(v_start, 'YYYY-MM'), r.bills, r.units, r.rev, c.cost, r.rev - c.cost,
           ROUND(100 * (r.rev - c.cost) / NULLIF(r.rev, 0), 2)
    FROM (SELECT COUNT(DISTINCT s.sale_id) AS bills, COALESCE(SUM(si.quantity), 0) AS units,
                 COALESCE(SUM(si.line_total), 0) AS rev
          FROM sales s JOIN sale_items si ON si.sale_id = s.sale_id
          WHERE s.sale_date >= v_start AND s.sale_date < v_end) r
    CROSS JOIN (SELECT COALESCE(SUM(a.quantity * a.cost_price), 0) AS cost
                FROM sale_allocations a JOIN sales s ON s.sale_id = a.sale_id
                WHERE s.sale_date >= v_start AND s.sale_date < v_end) c;
END $$;

CREATE OR REPLACE FUNCTION fn_monthly_top_products(p_year INT, p_month INT, p_limit INT DEFAULT 5)
RETURNS TABLE (product TEXT, units BIGINT, revenue NUMERIC, profit NUMERIC)
LANGUAGE sql STABLE AS $$
    SELECT p.name::text, SUM(a.quantity), SUM(a.quantity * si.unit_price),
           SUM(a.quantity * (si.unit_price - a.cost_price))
    FROM sale_allocations a
    JOIN sales s       ON s.sale_id = a.sale_id
    JOIN sale_items si ON si.sale_id = a.sale_id AND si.product_id = a.product_id
    JOIN products p    ON p.product_id = a.product_id
    WHERE s.sale_date >= make_date(p_year, p_month, 1)
      AND s.sale_date <  make_date(p_year, p_month, 1) + INTERVAL '1 month'
    GROUP BY p.product_id, p.name
    ORDER BY 4 DESC
    LIMIT p_limit;
$$;

CREATE OR REPLACE PROCEDURE sp_refresh_stock_alerts() LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM stock_alerts WHERE created_at >= CURRENT_DATE;
    INSERT INTO stock_alerts (alert_type, product_id, batch_id, message)
    SELECT 'LOW_STOCK', product_id, NULL,
           product_name || ': only ' || on_hand || ' left (reorder level ' || reorder_level || ')'
    FROM v_low_stock;
    INSERT INTO stock_alerts (alert_type, product_id, batch_id, message)
    SELECT 'NEAR_EXPIRY', product_id, batch_id,
           product_name || ' batch ' || batch_no || ' expires in ' || days_left || ' day(s)'
    FROM v_expiring_30_days;
    INSERT INTO stock_alerts (alert_type, product_id, batch_id, message)
    SELECT 'EXPIRED', product_id, batch_id,
           product_name || ' batch ' || batch_no || ' expired ' || days_expired || ' day(s) ago - remove from shelf'
    FROM v_expired_stock;
END $$;

-- PostgreSQL has no built-in event scheduler (MySQL EVENT).  Equivalent options:
--   * the pg_cron extension:  SELECT cron.schedule('0 6 * * *', 'CALL sp_refresh_stock_alerts()');
--   * an operating-system cron job running psql -c "CALL sp_refresh_stock_alerts()".
