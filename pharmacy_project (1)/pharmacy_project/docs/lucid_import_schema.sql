-- Pharmacy database: tables, keys and foreign keys only (for Lucidchart ERD import)

CREATE TABLE `categories` (
  `category_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category_name` varchar(60) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `uq_category_name` (`category_name`)
);

CREATE TABLE `suppliers` (
  `supplier_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `address` varchar(250) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`supplier_id`),
  UNIQUE KEY `uq_supplier_name` (`name`),
  UNIQUE KEY `uq_supplier_phone` (`phone`)
);

CREATE TABLE `products` (
  `product_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `generic_name` varchar(100) DEFAULT NULL,
  `manufacturer` varchar(80) DEFAULT NULL,
  `category_id` int(10) unsigned NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `reorder_level` int(11) NOT NULL DEFAULT 20,
  `requires_prescription` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`product_id`),
  UNIQUE KEY `uq_product_name` (`name`),
  KEY `idx_products_category` (`category_id`),
  CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON UPDATE CASCADE
);

CREATE TABLE `purchase_orders` (
  `po_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` int(10) unsigned NOT NULL,
  `order_date` date NOT NULL DEFAULT curdate(),
  `status` enum('Pending','Received','Cancelled') NOT NULL DEFAULT 'Pending',
  `total_cost` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`po_id`),
  KEY `idx_po_supplier` (`supplier_id`),
  CONSTRAINT `fk_po_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`supplier_id`) ON UPDATE CASCADE
);

CREATE TABLE `stock_batches` (
  `batch_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `po_id` int(10) unsigned NOT NULL,
  `batch_no` varchar(30) NOT NULL,
  `received_qty` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `expiry_date` date NOT NULL,
  `cost_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`batch_id`),
  UNIQUE KEY `uq_batch_lot` (`product_id`,`batch_no`),
  KEY `fk_batch_po` (`po_id`),
  KEY `idx_batches_fefo` (`product_id`,`expiry_date`),
  KEY `idx_batches_expiry` (`expiry_date`),
  CONSTRAINT `fk_batch_po` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`po_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_batch_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON UPDATE CASCADE
);

CREATE TABLE `customers` (
  `customer_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `registered_on` date NOT NULL DEFAULT curdate(),
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `uq_customer_phone` (`phone`),
  UNIQUE KEY `uq_customer_email` (`email`)
);

CREATE TABLE `employees` (
  `employee_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `role` enum('Pharmacist','Cashier','Manager','Inventory Clerk') NOT NULL,
  `phone` varchar(15) NOT NULL,
  `hire_date` date NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `uq_employee_phone` (`phone`)
);

CREATE TABLE `pharmacists` (
  `employee_id` int(10) unsigned NOT NULL,
  `license_no` varchar(20) NOT NULL,
  `qualification` varchar(60) NOT NULL DEFAULT 'Pharm-D',
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `uq_pharmacist_lic` (`license_no`),
  CONSTRAINT `fk_pharmacist_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `cashiers` (
  `employee_id` int(10) unsigned NOT NULL,
  `shift` enum('Morning','Evening','Night') NOT NULL DEFAULT 'Morning',
  `counter_no` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`employee_id`),
  CONSTRAINT `fk_cashier_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `sales` (
  `sale_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `customer_id` int(10) unsigned NOT NULL,
  `employee_id` int(10) unsigned NOT NULL,
  `sale_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `payment_method` enum('Cash','Card','Mobile Wallet') NOT NULL DEFAULT 'Cash',
  `total_amount` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`sale_id`),
  KEY `idx_sales_date` (`sale_date`),
  KEY `idx_sales_customer` (`customer_id`),
  KEY `idx_sales_employee` (`employee_id`),
  CONSTRAINT `fk_sales_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_sales_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`) ON UPDATE CASCADE
);

CREATE TABLE `sale_items` (
  `sale_id` int(10) unsigned NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`sale_id`,`product_id`),
  KEY `idx_items_product` (`product_id`),
  CONSTRAINT `fk_item_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_item_sale` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`sale_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `sale_allocations` (
  `sale_id` int(10) unsigned NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `batch_id` int(10) unsigned NOT NULL,
  `quantity` int(11) NOT NULL,
  `cost_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`sale_id`,`product_id`,`batch_id`),
  KEY `fk_alloc_batch` (`batch_id`),
  CONSTRAINT `fk_alloc_batch` FOREIGN KEY (`batch_id`) REFERENCES `stock_batches` (`batch_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_alloc_item` FOREIGN KEY (`sale_id`, `product_id`) REFERENCES `sale_items` (`sale_id`, `product_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `stock_alerts` (
  `alert_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `alert_type` enum('LOW_STOCK','NEAR_EXPIRY','EXPIRED') NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `batch_id` int(10) unsigned DEFAULT NULL,
  `message` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`alert_id`),
  KEY `fk_alert_product` (`product_id`),
  KEY `fk_alert_batch` (`batch_id`),
  CONSTRAINT `fk_alert_batch` FOREIGN KEY (`batch_id`) REFERENCES `stock_batches` (`batch_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_alert_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE
);

CREATE TABLE `audit_log` (
  `log_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `table_name` varchar(40) NOT NULL,
  `record_id` int(10) unsigned NOT NULL,
  `action` varchar(20) NOT NULL,
  `old_value` varchar(255) DEFAULT NULL,
  `new_value` varchar(255) DEFAULT NULL,
  `changed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `changed_by` varchar(80) NOT NULL,
  PRIMARY KEY (`log_id`)
);
