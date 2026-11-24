-- =====================================================================
--  Pharmacy Inventory & Sales Management System
--  File 6 of 6 : TESTS - transactions, triggers and constraints (Week 14)
--  Run with:   mysql --force -t -vvv -u root < 06_tests_transactions.sql
--  Statements marked "EXPECTED ERROR" are SUPPOSED to be rejected.
-- =====================================================================
USE pharmacy_db;

-- ---------- T1 : successful checkout (transaction COMMITs) -----------
SELECT 'T1  sp_checkout: 3 Panadol + 1 Dettol + 2 ORS sold to customer 3 by cashier 6' AS test;
SELECT product_id, on_hand FROM v_product_stock WHERE product_id IN (1, 17, 39) ORDER BY product_id;
CALL sp_checkout(3, 6, 'Cash',
     '[{"product_id":1,"qty":3},{"product_id":39,"qty":1},{"product_id":17,"qty":2}]', @sale);
SELECT @sale AS new_sale_id;
SELECT sale_id, customer, served_by, product, quantity, unit_price, line_total FROM v_sale_details WHERE sale_id = @sale;
SELECT sale_id, total_amount FROM sales WHERE sale_id = @sale;
SELECT sale_id, product_id, batch_id, quantity, cost_price FROM sale_allocations WHERE sale_id = @sale;
SELECT product_id, on_hand FROM v_product_stock WHERE product_id IN (1, 17, 39) ORDER BY product_id;

SELECT 'T1b deleting that bill puts the stock back (trigger trg_sales_bd)' AS test;
DELETE FROM sales WHERE sale_id = @sale;
SELECT product_id, on_hand FROM v_product_stock WHERE product_id IN (1, 17, 39) ORDER BY product_id;

-- ---------- T2 : not enough stock -> whole checkout rolls back -------
SELECT 'T2  EXPECTED ERROR: 100 Augmentin requested but only a few are in stock' AS test;
SELECT COUNT(*) AS sales_before FROM sales;
CALL sp_checkout(3, 6, 'Cash', '[{"product_id":7,"qty":100}]', @s);
SELECT COUNT(*) AS sales_after FROM sales;

SELECT 'T3  EXPECTED ERROR: second line fails, so the first (valid) line is also rolled back' AS test;
SELECT on_hand AS panadol_before FROM v_product_stock WHERE product_id = 1;
CALL sp_checkout(3, 6, 'Cash', '[{"product_id":1,"qty":2},{"product_id":7,"qty":500}]', @s);
SELECT on_hand AS panadol_after FROM v_product_stock WHERE product_id = 1;
SELECT COUNT(*) AS sales_after FROM sales;

SELECT 'T4  EXPECTED ERROR: expired stock cannot be sold (Benylin has 18 units but all expired)' AS test;
SELECT product_name, on_hand, expired_qty FROM v_product_stock WHERE product_id = 23;
CALL sp_checkout(3, 6, 'Cash', '[{"product_id":23,"qty":1}]', @s);

SELECT 'T5  EXPECTED ERROR: empty bill / unknown product / invalid payment method' AS test;
CALL sp_checkout(3, 6, 'Cash', '[]', @s);
CALL sp_checkout(3, 6, 'Cash', '[{"product_id":999,"qty":1}]', @s);
CALL sp_checkout(3, 6, 'Bitcoin', '[{"product_id":1,"qty":1}]', @s);
SELECT COUNT(*) AS sales_still FROM sales;

-- ---------- T6 : who may sell --------------------------------------
SELECT 'T6  EXPECTED ERROR: a Manager cannot make a sale' AS test;
CALL sp_checkout(3, 1, 'Cash', '[{"product_id":1,"qty":1}]', @s);
SELECT 'T6b EXPECTED ERROR: an inactive cashier (employee 9) cannot make a sale' AS test;
CALL sp_checkout(3, 9, 'Cash', '[{"product_id":1,"qty":1}]', @s);

-- ---------- T7 : constraints ---------------------------------------
SELECT 'T7a EXPECTED ERROR: CHECK unit_price >= 0' AS test;
INSERT INTO products (name, category_id, unit_price) VALUES ('Bad Price Medicine', 1, -10);
SELECT 'T7b EXPECTED ERROR: CHECK reorder_level >= 0' AS test;
INSERT INTO products (name, category_id, unit_price, reorder_level) VALUES ('Bad Reorder Medicine', 1, 10, -5);
SELECT 'T7c EXPECTED ERROR: NOT NULL name' AS test;
INSERT INTO products (name, category_id, unit_price) VALUES (NULL, 1, 10);
SELECT 'T7d EXPECTED ERROR: UNIQUE product name' AS test;
INSERT INTO products (name, category_id, unit_price) VALUES ('Panadol 500mg Tablets', 1, 10);
SELECT 'T7e EXPECTED ERROR: FOREIGN KEY - category 999 does not exist' AS test;
INSERT INTO products (name, category_id, unit_price) VALUES ('Orphan Medicine', 999, 10);
SELECT 'T7f EXPECTED ERROR: FOREIGN KEY RESTRICT - category still has products' AS test;
DELETE FROM categories WHERE category_id = 1;
SELECT 'T7g EXPECTED ERROR: CHECK phone format' AS test;
INSERT INTO customers (name, phone) VALUES ('Bad Phone', '12345');
SELECT 'T7h EXPECTED ERROR: UNIQUE phone (customer 2 already owns it)' AS test;
INSERT INTO customers (name, phone) SELECT 'Phone Thief', phone FROM customers WHERE customer_id = 2;

START TRANSACTION;
INSERT INTO sales (customer_id, employee_id, payment_method) VALUES (2, 6, 'Cash');
SET @tmp = LAST_INSERT_ID();
SELECT 'T7i EXPECTED ERROR: CHECK quantity > 0 on sale_items' AS test;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (@tmp, 1, 0, 35);
SELECT 'T7j EXPECTED ERROR: CHECK unit_price >= 0 on sale_items' AS test;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (@tmp, 1, 1, -35);
SELECT 'T7k EXPECTED ERROR: composite primary key (same product twice on one bill)' AS test;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (@tmp, 1, 1, 35);
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (@tmp, 1, 1, 35);
SELECT 'T7l EXPECTED ERROR: sale items are immutable (trigger)' AS test;
UPDATE sale_items SET quantity = 5 WHERE sale_id = @tmp AND product_id = 1;
SELECT 'T7m deleting one line returns its stock and lowers the bill total' AS test;
SELECT total_amount AS total_before FROM sales WHERE sale_id = @tmp;
DELETE FROM sale_items WHERE sale_id = @tmp AND product_id = 1;
SELECT total_amount AS total_after FROM sales WHERE sale_id = @tmp;
ROLLBACK;

-- ---------- T8 : EER specialisation and purchase-order triggers ----
SELECT 'T8a EXPECTED ERROR: a Cashier cannot be stored in the pharmacists table' AS test;
INSERT INTO pharmacists (employee_id, license_no) VALUES (6, 'PC-XXX-0001');
SELECT 'T8b EXPECTED ERROR: cannot add a batch to a cancelled purchase order' AS test;
INSERT INTO stock_batches (product_id, po_id, batch_no, received_qty, quantity, expiry_date, cost_price)
SELECT 1, po_id, 'TEST-01', 10, 10, '2028-01-01', 20 FROM purchase_orders WHERE status = 'Cancelled' LIMIT 1;
SELECT 'T8c EXPECTED ERROR: a batch that is already expired on the order date' AS test;
CALL sp_receive_stock(1, '2026-11-18', '[{"product_id":1,"qty":10,"cost_price":20,"expiry_date":"2026-11-01","batch_no":"OLD-01"}]', @po);
SELECT 'T8d EXPECTED ERROR: a Received purchase order cannot go back to Pending' AS test;
UPDATE purchase_orders SET status = 'Pending' WHERE po_id = 1;

-- ---------- T9 : receive stock transaction + total_cost trigger ----
SELECT 'T9  sp_receive_stock: two new batches, PO total_cost is calculated by trigger' AS test;
CALL sp_receive_stock(2, '2026-11-18',
     '[{"product_id":7,"qty":100,"cost_price":340.5,"expiry_date":"2028-06-30","batch_no":"AUG-2611-01"},
       {"product_id":14,"qty":80,"cost_price":295,"expiry_date":"2028-05-31","batch_no":"NEX-2611-01"}]', @po);
SELECT po_id, supplier_id, order_date, status, total_cost FROM purchase_orders WHERE po_id = @po;
SELECT batch_id, product_id, batch_no, received_qty, quantity, expiry_date, cost_price FROM stock_batches WHERE po_id = @po;
SELECT product_id, product_name, on_hand, reorder_level FROM v_product_stock WHERE product_id IN (7, 14);
SELECT 'T9b clean-up: remove the test purchase order again (trigger lowers total_cost first)' AS test;
DELETE FROM stock_batches WHERE po_id = @po;
SELECT total_cost AS total_cost_after_batch_delete FROM purchase_orders WHERE po_id = @po;
DELETE FROM purchase_orders WHERE po_id = @po;

-- ---------- T10 : reports, alerts, event ---------------------------
SELECT 'T10a sp_monthly_report(2026, 10) - three result sets' AS test;
CALL sp_monthly_report(2026, 10);
SELECT 'T10b EXPECTED ERROR: invalid month' AS test;
CALL sp_monthly_report(2026, 13);
SELECT 'T10c sp_refresh_stock_alerts and the stock_alerts table' AS test;
CALL sp_refresh_stock_alerts();
SELECT alert_type, COUNT(*) AS alerts FROM stock_alerts GROUP BY alert_type ORDER BY alert_type;
SELECT alert_type, message FROM stock_alerts ORDER BY alert_type, alert_id;
SELECT 'T10d the scheduled event' AS test;
SELECT event_name, interval_value, interval_field, status FROM information_schema.events WHERE event_schema = 'pharmacy_db';
SELECT 'T10e stored function fn_stock_on_hand' AS test;
SELECT product_id, name, fn_stock_on_hand(product_id, CURRENT_DATE) AS sellable_today
FROM products WHERE product_id IN (1, 7, 23, 38) ORDER BY product_id;
DELETE FROM stock_alerts;

-- ---------- T11 : consistency audit (derived figures vs recomputed figures) ----
SELECT 'T11 consistency audit: every figure kept by a trigger must equal the value recomputed from the detail rows (0 = no mismatch)' AS test;
SELECT COUNT(*) AS sale_total_mismatches FROM sales s
WHERE  s.total_amount <> (SELECT SUM(si.quantity * si.unit_price) FROM sale_items si WHERE si.sale_id = s.sale_id);
SELECT COUNT(*) AS po_total_mismatches FROM purchase_orders p
WHERE  p.total_cost <> COALESCE((SELECT SUM(b.received_qty * b.cost_price) FROM stock_batches b WHERE b.po_id = p.po_id), 0);
SELECT COUNT(*) AS stock_mismatches FROM stock_batches b
WHERE  b.received_qty - b.quantity <> COALESCE((SELECT SUM(a.quantity) FROM sale_allocations a WHERE a.batch_id = b.batch_id), 0);
SELECT COUNT(*) AS allocation_mismatches FROM sale_items si
WHERE  si.quantity <> (SELECT SUM(a.quantity) FROM sale_allocations a WHERE a.sale_id = si.sale_id AND a.product_id = si.product_id);
