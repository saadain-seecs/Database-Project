-- =====================================================================
--  File 5 of 5 (PostgreSQL) : TESTS - transactions, triggers, constraints
--  Statements marked EXPECTED ERROR are supposed to be rejected.
--  In PostgreSQL an error inside BEGIN...COMMIT aborts the whole block,
--  so failing statements run on their own or behind a SAVEPOINT.
-- =====================================================================
\connect pharmacy_db

SELECT 'T1  sp_checkout: 3 Panadol + 1 Dettol + 2 ORS (function = one atomic transaction)' AS test;
SELECT product_id, on_hand FROM v_product_stock WHERE product_id IN (1, 17, 39) ORDER BY product_id;
SELECT sp_checkout(3, 6, 'Cash', '[{"product_id":1,"qty":3},{"product_id":39,"qty":1},{"product_id":17,"qty":2}]') AS new_sale_id;
SELECT sale_id, customer, served_by, product, quantity, unit_price, line_total FROM v_sale_details WHERE sale_id = (SELECT MAX(sale_id) FROM sales);
SELECT sale_id, total_amount FROM sales WHERE sale_id = (SELECT MAX(sale_id) FROM sales);
SELECT product_id, on_hand FROM v_product_stock WHERE product_id IN (1, 17, 39) ORDER BY product_id;
SELECT 'T1b deleting that bill puts the stock back (cascade fires trg_sale_items_bd)' AS test;
DELETE FROM sales WHERE sale_id = (SELECT MAX(sale_id) FROM sales);
SELECT product_id, on_hand FROM v_product_stock WHERE product_id IN (1, 17, 39) ORDER BY product_id;

SELECT 'T2  EXPECTED ERROR: 100 Augmentin requested, only a few in stock' AS test;
SELECT COUNT(*) AS sales_before FROM sales;
SELECT sp_checkout(3, 6, 'Cash', '[{"product_id":7,"qty":100}]');
SELECT COUNT(*) AS sales_after FROM sales;
SELECT 'T3  EXPECTED ERROR: second line fails, first line is rolled back too' AS test;
SELECT on_hand AS panadol_before FROM v_product_stock WHERE product_id = 1;
SELECT sp_checkout(3, 6, 'Cash', '[{"product_id":1,"qty":2},{"product_id":7,"qty":500}]');
SELECT on_hand AS panadol_after FROM v_product_stock WHERE product_id = 1;
SELECT 'T4  EXPECTED ERROR: expired stock cannot be sold (Benylin)' AS test;
SELECT product_name, on_hand, expired_qty FROM v_product_stock WHERE product_id = 23;
SELECT sp_checkout(3, 6, 'Cash', '[{"product_id":23,"qty":1}]');
SELECT 'T5  EXPECTED ERROR: empty bill / unknown product / invalid payment method' AS test;
SELECT sp_checkout(3, 6, 'Cash', '[]');
SELECT sp_checkout(3, 6, 'Cash', '[{"product_id":999,"qty":1}]');
SELECT sp_checkout(3, 6, 'Bitcoin', '[{"product_id":1,"qty":1}]');
SELECT 'T6  EXPECTED ERROR: a Manager / an inactive cashier cannot sell' AS test;
SELECT sp_checkout(3, 1, 'Cash', '[{"product_id":1,"qty":1}]');
SELECT sp_checkout(3, 9, 'Cash', '[{"product_id":1,"qty":1}]');

SELECT 'T7  EXPECTED ERRORS: CHECK / NOT NULL / UNIQUE / FOREIGN KEY' AS test;
INSERT INTO products (name, category_id, unit_price) VALUES ('Bad Price Medicine', 1, -10);
INSERT INTO products (name, category_id, unit_price, reorder_level) VALUES ('Bad Reorder Medicine', 1, 10, -5);
INSERT INTO products (name, category_id, unit_price) VALUES (NULL, 1, 10);
INSERT INTO products (name, category_id, unit_price) VALUES ('Panadol 500mg Tablets', 1, 10);
INSERT INTO products (name, category_id, unit_price) VALUES ('Orphan Medicine', 999, 10);
DELETE FROM categories WHERE category_id = 1;
INSERT INTO customers (name, phone) VALUES ('Bad Phone', '12345');
INSERT INTO customers (name, phone) SELECT 'Phone Thief', phone FROM customers WHERE customer_id = 2;

SELECT 'T7b transaction with SAVEPOINTs: CHECK / PK / immutability errors, then ROLLBACK' AS test;
BEGIN;
INSERT INTO sales (customer_id, employee_id, payment_method) VALUES (2, 6, 'Cash');
SAVEPOINT s1;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) SELECT MAX(sale_id), 1, 0, 35 FROM sales;
ROLLBACK TO SAVEPOINT s1;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) SELECT MAX(sale_id), 1, 1, -35 FROM sales;
ROLLBACK TO SAVEPOINT s1;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) SELECT MAX(sale_id), 1, 1, 35 FROM sales;
SAVEPOINT s2;
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) SELECT MAX(sale_id), 1, 1, 35 FROM sales;
ROLLBACK TO SAVEPOINT s2;
UPDATE sale_items SET quantity = 5 WHERE sale_id = (SELECT MAX(sale_id) FROM sales) AND product_id = 1;
ROLLBACK TO SAVEPOINT s2;
SELECT total_amount AS total_before_delete FROM sales WHERE sale_id = (SELECT MAX(sale_id) FROM sales);
DELETE FROM sale_items WHERE sale_id = (SELECT MAX(sale_id) FROM sales) AND product_id = 1;
SELECT total_amount AS total_after_delete FROM sales WHERE sale_id = (SELECT MAX(sale_id) FROM sales);
ROLLBACK;

SELECT 'T8  EXPECTED ERRORS: EER subclass rule and purchase-order triggers' AS test;
INSERT INTO pharmacists (employee_id, license_no) VALUES (6, 'PC-XXX-0001');
INSERT INTO stock_batches (product_id, po_id, batch_no, received_qty, quantity, expiry_date, cost_price)
SELECT 1, po_id, 'TEST-01', 10, 10, '2028-01-01', 20 FROM purchase_orders WHERE status = 'Cancelled' LIMIT 1;
SELECT sp_receive_stock(1, '2026-11-18', '[{"product_id":1,"qty":10,"cost_price":20,"expiry_date":"2026-11-01","batch_no":"OLD-01"}]');
UPDATE purchase_orders SET status = 'Pending' WHERE po_id = 1;

SELECT 'T9  sp_receive_stock: two batches, total_cost calculated by trigger' AS test;
SELECT sp_receive_stock(2, '2026-11-18', '[{"product_id":7,"qty":100,"cost_price":340.5,"expiry_date":"2028-06-30","batch_no":"AUG-2611-01"},{"product_id":14,"qty":80,"cost_price":295,"expiry_date":"2028-05-31","batch_no":"NEX-2611-01"}]') AS new_po_id;
SELECT po_id, supplier_id, order_date, status, total_cost FROM purchase_orders WHERE po_id = (SELECT MAX(po_id) FROM purchase_orders);
SELECT product_id, product_name, on_hand, reorder_level FROM v_product_stock WHERE product_id IN (7, 14) ORDER BY product_id;
DELETE FROM stock_batches WHERE po_id = (SELECT MAX(po_id) FROM purchase_orders);
SELECT total_cost AS total_cost_after_batch_delete FROM purchase_orders WHERE po_id = (SELECT MAX(po_id) FROM purchase_orders);
DELETE FROM purchase_orders WHERE po_id = (SELECT MAX(po_id) FROM purchase_orders);

SELECT 'T10 monthly report functions (October 2026)' AS test;
SELECT * FROM fn_monthly_report(2026, 10);
SELECT * FROM fn_monthly_top_products(2026, 10, 5);
SELECT * FROM fn_monthly_report(2026, 13);
SELECT 'T10b CALL sp_refresh_stock_alerts()' AS test;
CALL sp_refresh_stock_alerts();
SELECT alert_type, COUNT(*) AS alerts FROM stock_alerts GROUP BY alert_type ORDER BY alert_type;
DELETE FROM stock_alerts;

SELECT 'T11 PostgreSQL extras: RETURNING, partial index plan, writable CTE' AS test;
BEGIN;
UPDATE products SET unit_price = unit_price + 5 WHERE product_id = 1 RETURNING product_id, name, unit_price;
SELECT table_name, record_id, action, old_value, new_value FROM audit_log;
ROLLBACK;
WITH moved AS (DELETE FROM stock_alerts WHERE FALSE RETURNING *) SELECT COUNT(*) AS rows_moved FROM moved;
EXPLAIN (COSTS OFF) SELECT batch_id FROM stock_batches WHERE product_id = 1 AND quantity > 0 ORDER BY expiry_date;
EXPLAIN (COSTS OFF) SELECT product_id FROM products WHERE to_tsvector('english', name || ' ' || COALESCE(generic_name, '')) @@ to_tsquery('english', 'paracetamol');

SELECT 'T12 consistency audit: every figure kept by a trigger must equal the value recomputed from the detail rows (0 = no mismatch)' AS test;
SELECT COUNT(*) AS sale_total_mismatches FROM sales s
WHERE  s.total_amount <> (SELECT SUM(si.line_total) FROM sale_items si WHERE si.sale_id = s.sale_id);
SELECT COUNT(*) AS po_total_mismatches FROM purchase_orders p
WHERE  p.total_cost <> COALESCE((SELECT SUM(b.received_qty * b.cost_price) FROM stock_batches b WHERE b.po_id = p.po_id), 0);
SELECT COUNT(*) AS stock_mismatches FROM stock_batches b
WHERE  b.received_qty - b.quantity <> COALESCE((SELECT SUM(a.quantity) FROM sale_allocations a WHERE a.batch_id = b.batch_id), 0);
SELECT COUNT(*) AS allocation_mismatches FROM sale_items si
WHERE  si.quantity <> (SELECT SUM(a.quantity) FROM sale_allocations a WHERE a.sale_id = si.sale_id AND a.product_id = si.product_id);
