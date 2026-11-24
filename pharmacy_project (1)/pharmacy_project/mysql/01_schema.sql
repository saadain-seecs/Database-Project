-- =====================================================================
--  Pharmacy Inventory & Sales Management System
--  CS220 Database Systems  |  BESE 2K25  |  NUST Islamabad
--  File 1 of 6 : DATABASE + TABLES (Data Definition Language, Week 8)
--  Target      : MySQL 8.0.31+ / MySQL Workbench  (also tested on MariaDB 10.11)
--  Run order   : 01_schema -> 02_programmability -> 03_sample_data
-- =====================================================================

DROP DATABASE IF EXISTS pharmacy_db;
CREATE DATABASE pharmacy_db
    CHARACTER SET utf8mb4;
USE pharmacy_db;

-- ---------------------------------------------------------------------
-- 1. CATEGORIES  (1 category -> M products)
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    category_id    INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    category_name  VARCHAR(60)   NOT NULL,
    description    VARCHAR(200)  NULL,
    CONSTRAINT pk_categories      PRIMARY KEY (category_id),
    CONSTRAINT uq_category_name   UNIQUE (category_name)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 2. SUPPLIERS  (1 supplier -> M purchase orders)
-- ---------------------------------------------------------------------
CREATE TABLE suppliers (
    supplier_id  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100)  NOT NULL,
    phone        VARCHAR(15)   NOT NULL,
    address      VARCHAR(200)  NOT NULL,
    is_active    BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_suppliers       PRIMARY KEY (supplier_id),
    CONSTRAINT uq_supplier_name   UNIQUE (name),
    CONSTRAINT uq_supplier_phone  UNIQUE (phone),
    CONSTRAINT ck_supplier_phone  CHECK (phone REGEXP '^[0-9]{3,4}-[0-9]{7}$')
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 3. PRODUCTS  (1 category -> M products)
-- ---------------------------------------------------------------------
CREATE TABLE products (
    product_id             INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    name                   VARCHAR(100)   NOT NULL,
    generic_name           VARCHAR(100)   NULL,
    category_id            INT UNSIGNED   NOT NULL,
    unit_price             DECIMAL(10,2)  NOT NULL,          -- selling price per unit (PKR)
    reorder_level          INT            NOT NULL DEFAULT 20,
    requires_prescription  BOOLEAN        NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_products          PRIMARY KEY (product_id),
    CONSTRAINT uq_product_name      UNIQUE (name),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id)
        REFERENCES categories (category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_product_price     CHECK (unit_price >= 0),
    CONSTRAINT ck_product_reorder   CHECK (reorder_level >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 4. PURCHASE_ORDERS  (1 supplier -> M purchase orders)
-- ---------------------------------------------------------------------
CREATE TABLE purchase_orders (
    po_id        INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    supplier_id  INT UNSIGNED   NOT NULL,
    order_date   DATE           NOT NULL DEFAULT (CURRENT_DATE),
    status       ENUM('Pending','Received','Cancelled') NOT NULL DEFAULT 'Pending',
    total_cost   DECIMAL(12,2)  NOT NULL DEFAULT 0,          -- maintained by trigger
    CONSTRAINT pk_purchase_orders  PRIMARY KEY (po_id),
    CONSTRAINT fk_po_supplier      FOREIGN KEY (supplier_id)
        REFERENCES suppliers (supplier_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_po_total         CHECK (total_cost >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 5. STOCK_BATCHES  (1 PO -> M batches ; 1 product -> M batches)
--    quantity       = units still on the shelf (falls as sales are made)
--    received_qty   = units that arrived with the purchase order
-- ---------------------------------------------------------------------
CREATE TABLE stock_batches (
    batch_id      INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    product_id    INT UNSIGNED   NOT NULL,
    po_id         INT UNSIGNED   NOT NULL,
    batch_no      VARCHAR(30)    NOT NULL,                   -- manufacturer's batch / lot number
    received_qty  INT            NOT NULL,
    quantity      INT            NOT NULL,
    expiry_date   DATE           NOT NULL,
    cost_price    DECIMAL(10,2)  NOT NULL,                   -- purchase price per unit (PKR)
    CONSTRAINT pk_stock_batches     PRIMARY KEY (batch_id),
    CONSTRAINT uq_batch_lot         UNIQUE (product_id, batch_no),
    CONSTRAINT fk_batch_product     FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_batch_po          FOREIGN KEY (po_id)
        REFERENCES purchase_orders (po_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_batch_received    CHECK (received_qty > 0),
    CONSTRAINT ck_batch_quantity    CHECK (quantity >= 0 AND quantity <= received_qty),
    CONSTRAINT ck_batch_cost        CHECK (cost_price >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 6. CUSTOMERS  (1 customer -> M sales)
-- ---------------------------------------------------------------------
CREATE TABLE customers (
    customer_id    INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name           VARCHAR(100)  NOT NULL,
    phone          VARCHAR(15)   NULL,                       -- NULL allowed for the walk-in customer
    registered_on  DATE          NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT pk_customers      PRIMARY KEY (customer_id),
    CONSTRAINT uq_customer_phone UNIQUE (phone),
    CONSTRAINT ck_customer_phone CHECK (phone IS NULL OR phone REGEXP '^[0-9]{3,4}-[0-9]{7}$')
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 7. EMPLOYEES  (superclass of the EER specialisation)
-- ---------------------------------------------------------------------
CREATE TABLE employees (
    employee_id  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100)  NOT NULL,
    role         ENUM('Pharmacist','Cashier','Manager','Inventory Clerk') NOT NULL,
    phone        VARCHAR(15)   NOT NULL,
    hire_date    DATE          NOT NULL,
    is_active    BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_employees      PRIMARY KEY (employee_id),
    CONSTRAINT uq_employee_phone UNIQUE (phone),
    CONSTRAINT ck_employee_phone CHECK (phone REGEXP '^[0-9]{3,4}-[0-9]{7}$')
) ENGINE = InnoDB;

-- EER subclass 1 : PHARMACIST  (disjoint, partial specialisation of EMPLOYEE)
CREATE TABLE pharmacists (
    employee_id   INT UNSIGNED  NOT NULL,
    license_no    VARCHAR(20)   NOT NULL,                    -- DRAP / provincial pharmacy-council licence
    qualification VARCHAR(60)   NOT NULL DEFAULT 'Pharm-D',
    CONSTRAINT pk_pharmacists      PRIMARY KEY (employee_id),
    CONSTRAINT uq_pharmacist_lic   UNIQUE (license_no),
    CONSTRAINT fk_pharmacist_emp   FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB;

-- EER subclass 2 : CASHIER
CREATE TABLE cashiers (
    employee_id  INT UNSIGNED  NOT NULL,
    shift        ENUM('Morning','Evening','Night') NOT NULL DEFAULT 'Morning',
    counter_no   TINYINT UNSIGNED NOT NULL,
    CONSTRAINT pk_cashiers        PRIMARY KEY (employee_id),
    CONSTRAINT fk_cashier_emp     FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT ck_cashier_counter CHECK (counter_no BETWEEN 1 AND 6)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 8. SALES  (1 customer -> M sales ; 1 employee -> M sales)
-- ---------------------------------------------------------------------
CREATE TABLE sales (
    sale_id         INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    customer_id     INT UNSIGNED   NOT NULL,
    employee_id     INT UNSIGNED   NOT NULL,
    sale_date       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_method  ENUM('Cash','Card','Mobile Wallet') NOT NULL DEFAULT 'Cash',
    total_amount    DECIMAL(12,2)  NOT NULL DEFAULT 0,       -- maintained by trigger
    CONSTRAINT pk_sales          PRIMARY KEY (sale_id),
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_sales_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_sales_total    CHECK (total_amount >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- 9. SALE_ITEMS  (resolves SALES  M--M  PRODUCTS ; composite PK)
-- ---------------------------------------------------------------------
CREATE TABLE sale_items (
    sale_id     INT UNSIGNED   NOT NULL,
    product_id  INT UNSIGNED   NOT NULL,
    quantity    INT            NOT NULL,
    unit_price  DECIMAL(10,2)  NOT NULL,                     -- price charged on the day of sale
    CONSTRAINT pk_sale_items      PRIMARY KEY (sale_id, product_id),
    CONSTRAINT fk_item_sale       FOREIGN KEY (sale_id)
        REFERENCES sales (sale_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_item_product    FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_item_quantity   CHECK (quantity > 0),
    CONSTRAINT ck_item_price      CHECK (unit_price >= 0)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- SUPPORTING TABLES (not in the 9 core entities; they make the core
-- design correct and auditable)
-- ---------------------------------------------------------------------

-- Which batch(es) each sale item was taken from (FEFO). Gives exact profit.
CREATE TABLE sale_allocations (
    sale_id     INT UNSIGNED   NOT NULL,
    product_id  INT UNSIGNED   NOT NULL,
    batch_id    INT UNSIGNED   NOT NULL,
    quantity    INT            NOT NULL,
    cost_price  DECIMAL(10,2)  NOT NULL,                     -- cost of that batch at the time of sale
    CONSTRAINT pk_sale_alloc     PRIMARY KEY (sale_id, product_id, batch_id),
    CONSTRAINT fk_alloc_item     FOREIGN KEY (sale_id, product_id)
        REFERENCES sale_items (sale_id, product_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_alloc_batch    FOREIGN KEY (batch_id)
        REFERENCES stock_batches (batch_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_alloc_qty      CHECK (quantity > 0),
    CONSTRAINT ck_alloc_cost     CHECK (cost_price >= 0)
) ENGINE = InnoDB;

-- Alerts produced by the daily event / stored procedure
CREATE TABLE stock_alerts (
    alert_id     INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    alert_type   ENUM('LOW_STOCK','NEAR_EXPIRY','EXPIRED') NOT NULL,
    product_id   INT UNSIGNED  NOT NULL,
    batch_id     INT UNSIGNED  NULL,
    message      VARCHAR(255)  NOT NULL,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_stock_alerts   PRIMARY KEY (alert_id),
    CONSTRAINT fk_alert_product  FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE CASCADE,
    CONSTRAINT fk_alert_batch    FOREIGN KEY (batch_id)
        REFERENCES stock_batches (batch_id) ON DELETE SET NULL
) ENGINE = InnoDB;

-- Generic audit trail (price changes, etc.)
CREATE TABLE audit_log (
    log_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    table_name  VARCHAR(40)   NOT NULL,
    record_id   INT UNSIGNED  NOT NULL,
    action      VARCHAR(20)   NOT NULL,
    old_value   VARCHAR(255)  NULL,
    new_value   VARCHAR(255)  NULL,
    changed_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by  VARCHAR(80)   NOT NULL DEFAULT (CURRENT_USER()),
    CONSTRAINT pk_audit_log PRIMARY KEY (log_id)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- INDEXES  (speed up the joins / filters used by the reports)
-- ---------------------------------------------------------------------
CREATE INDEX idx_products_category  ON products (category_id);
CREATE INDEX idx_batches_fefo       ON stock_batches (product_id, expiry_date);
CREATE INDEX idx_batches_expiry     ON stock_batches (expiry_date);
CREATE INDEX idx_sales_date         ON sales (sale_date);
CREATE INDEX idx_sales_customer     ON sales (customer_id);
CREATE INDEX idx_sales_employee     ON sales (employee_id);
CREATE INDEX idx_items_product      ON sale_items (product_id);
CREATE INDEX idx_po_supplier        ON purchase_orders (supplier_id);

-- ---------------------------------------------------------------------
-- DDL DEMONSTRATION : ALTER TABLE (add / modify / constrain)
-- ---------------------------------------------------------------------
ALTER TABLE customers
    ADD COLUMN email VARCHAR(100) NULL AFTER phone,
    ADD CONSTRAINT uq_customer_email UNIQUE (email);

ALTER TABLE suppliers
    MODIFY COLUMN address VARCHAR(250) NOT NULL;

ALTER TABLE products
    ADD COLUMN manufacturer VARCHAR(80) NULL AFTER generic_name;

SHOW TABLES;
