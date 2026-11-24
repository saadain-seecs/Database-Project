-- =====================================================================
--  Pharmacy Inventory & Sales Management System
--  File 5 of 6 : DML (Week 12), sub-queries in DML/DDL (Week 13), DDL (Week 8)
--  Part 1 runs inside a transaction that is ROLLED BACK, so the sample data
--  is untouched.  Part 2 (DDL) creates and drops its own temporary objects.
-- =====================================================================
USE pharmacy_db;

-- ================= PART 1 : DATA MANIPULATION LANGUAGE ===============
START TRANSACTION;

SELECT 'D1  INSERT one row (new customer)' AS step;
INSERT INTO customers (name, phone) VALUES ('Sara Imtiaz', '0300-5550101');
SELECT customer_id, name, phone, registered_on FROM customers WHERE phone = '0300-5550101';

SELECT 'D2  INSERT several rows (two new products in one statement)' AS step;
INSERT INTO products (name, generic_name, category_id, unit_price, reorder_level, requires_prescription)
VALUES ('Panadol Extra Tablets', 'Paracetamol + Caffeine', 1, 55.00, 40, FALSE),
       ('Hydrite Sachet', 'Oral rehydration salts', 3, 30.00, 60, FALSE);
SELECT product_id, name, unit_price FROM products WHERE name IN ('Panadol Extra Tablets', 'Hydrite Sachet');

SELECT 'D3  INSERT ... SELECT (sub-query in DML): copy today''s low-stock list into stock_alerts' AS step;
INSERT INTO stock_alerts (alert_type, product_id, message)
SELECT 'LOW_STOCK', product_id, CONCAT(product_name, ' needs re-ordering (', on_hand, ' left)')
FROM   v_low_stock
WHERE  on_hand = 0;
SELECT alert_id, alert_type, product_id, message FROM stock_alerts;

SELECT 'D4  UPDATE with a sub-query in WHERE: raise every antibiotic price by 5 percent' AS step;
UPDATE products
SET    unit_price = ROUND(unit_price * 1.05, 2)
WHERE  category_id = (SELECT category_id FROM categories WHERE category_name = 'Antibiotics');
SELECT product_id, name, unit_price FROM products WHERE category_id = 2 ORDER BY product_id;
SELECT 'trigger trg_products_au wrote the audit trail:' AS note;
SELECT table_name, record_id, action, old_value, new_value FROM audit_log ORDER BY log_id;

SELECT 'D5  UPDATE with a correlated sub-query: best sellers (30+ units) get reorder level 80' AS step;
UPDATE products p
SET    reorder_level = 80
WHERE  (SELECT COALESCE(SUM(si.quantity), 0) FROM sale_items si WHERE si.product_id = p.product_id) >= 30
  AND  reorder_level < 80;
SELECT product_id, name, reorder_level FROM products WHERE reorder_level = 80 ORDER BY product_id;

SELECT 'D6  DELETE with a sub-query: remove cancelled purchase orders that have no stock batches' AS step;
SELECT COUNT(*) AS cancelled_before FROM purchase_orders WHERE status = 'Cancelled';
DELETE FROM purchase_orders
WHERE  status = 'Cancelled'
  AND  po_id NOT IN (SELECT po_id FROM stock_batches);
SELECT COUNT(*) AS cancelled_after FROM purchase_orders WHERE status = 'Cancelled';

SELECT 'D7  UPSERT: INSERT ... ON DUPLICATE KEY UPDATE (category name is UNIQUE)' AS step;
INSERT INTO categories (category_name, description)
VALUES ('Dermatology', 'Creams, ointments and lotions for the skin')
ON DUPLICATE KEY UPDATE description = VALUES(description);
SELECT category_id, category_name, description FROM categories WHERE category_name = 'Dermatology';

SELECT 'D8  Savepoint: undo only the last of two price changes' AS step;
UPDATE products SET unit_price = unit_price + 5 WHERE product_id = 1;
SAVEPOINT after_panadol;
UPDATE products SET unit_price = unit_price + 5 WHERE product_id = 3;
ROLLBACK TO SAVEPOINT after_panadol;
SELECT product_id, name, unit_price FROM products WHERE product_id IN (1, 3);

ROLLBACK;
SELECT 'ROLLBACK done - nothing above was saved' AS step;
SELECT COUNT(*) AS products_now, (SELECT COUNT(*) FROM customers) AS customers_now,
       (SELECT COUNT(*) FROM audit_log) AS audit_rows FROM products;

-- ================= PART 2 : DATA DEFINITION LANGUAGE =================
SELECT 'DDL1  CREATE TABLE ... AS SELECT (sub-query in DDL): archive of expired stock' AS step;
CREATE TABLE expired_stock_archive AS
SELECT batch_id, product_name, batch_no, quantity, expiry_date, loss_at_cost, CURRENT_DATE AS archived_on
FROM   v_expired_stock;
SELECT * FROM expired_stock_archive;

SELECT 'DDL2  CREATE VIEW over a sub-query: prescription-only medicines that sold in October' AS step;
CREATE OR REPLACE VIEW v_rx_sold_october AS
SELECT p.product_id, p.name,
       (SELECT SUM(si.quantity)
        FROM   sale_items si JOIN sales s ON s.sale_id = si.sale_id
        WHERE  si.product_id = p.product_id
          AND  s.sale_date >= '2026-10-01' AND s.sale_date < '2026-11-01') AS units_sold
FROM   products p
WHERE  p.requires_prescription = TRUE;
SELECT * FROM v_rx_sold_october WHERE units_sold IS NOT NULL ORDER BY units_sold DESC;

SELECT 'DDL3  ALTER TABLE: add, modify, rename a column, add and drop a constraint' AS step;
ALTER TABLE expired_stock_archive ADD COLUMN disposal_method VARCHAR(30) NOT NULL DEFAULT 'Return to supplier';
ALTER TABLE expired_stock_archive MODIFY COLUMN disposal_method VARCHAR(60) NOT NULL DEFAULT 'Return to supplier';
ALTER TABLE expired_stock_archive RENAME COLUMN disposal_method TO disposal;
ALTER TABLE expired_stock_archive ADD CONSTRAINT ck_archive_qty CHECK (quantity >= 0);
ALTER TABLE expired_stock_archive DROP CONSTRAINT ck_archive_qty;
DESCRIBE expired_stock_archive;

SELECT 'DDL4  CREATE INDEX, SHOW INDEX, DROP INDEX' AS step;
CREATE INDEX idx_archive_expiry ON expired_stock_archive (expiry_date);
SHOW INDEX FROM expired_stock_archive;
DROP INDEX idx_archive_expiry ON expired_stock_archive;

SELECT 'DDL5  RENAME TABLE, TRUNCATE TABLE, DROP TABLE / VIEW' AS step;
RENAME TABLE expired_stock_archive TO expired_archive_2026;
TRUNCATE TABLE expired_archive_2026;
SELECT COUNT(*) AS rows_after_truncate FROM expired_archive_2026;
DROP TABLE expired_archive_2026;
DROP VIEW v_rx_sold_october;
SELECT 'DDL demo finished - temporary objects dropped' AS step;
