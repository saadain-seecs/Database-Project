/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.14-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: pharmacy_db
-- ------------------------------------------------------
-- Server version	10.11.14-MariaDB-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit_log`
--

DROP TABLE IF EXISTS `audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_log` (
  `log_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `table_name` varchar(40) NOT NULL,
  `record_id` int(10) unsigned NOT NULL,
  `action` varchar(20) NOT NULL,
  `old_value` varchar(255) DEFAULT NULL,
  `new_value` varchar(255) DEFAULT NULL,
  `changed_at` datetime NOT NULL DEFAULT current_timestamp(),
  `changed_by` varchar(80) NOT NULL DEFAULT current_user(),
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cashiers`
--

DROP TABLE IF EXISTS `cashiers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cashiers` (
  `employee_id` int(10) unsigned NOT NULL,
  `shift` enum('Morning','Evening','Night') NOT NULL DEFAULT 'Morning',
  `counter_no` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`employee_id`),
  CONSTRAINT `fk_cashier_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ck_cashier_counter` CHECK (`counter_no` between 1 and 6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_cashiers_bi BEFORE INSERT ON cashiers
FOR EACH ROW
BEGIN
    IF (SELECT role FROM employees WHERE employee_id = NEW.employee_id) <> 'Cashier' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only employees with role Cashier can be stored in cashiers';
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `category_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category_name` varchar(60) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `uq_category_name` (`category_name`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `customer_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `registered_on` date NOT NULL DEFAULT curdate(),
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `uq_customer_phone` (`phone`),
  UNIQUE KEY `uq_customer_email` (`email`),
  CONSTRAINT `ck_customer_phone` CHECK (`phone` is null or `phone` regexp '^[0-9]{3,4}-[0-9]{7}$')
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `employees` (
  `employee_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `role` enum('Pharmacist','Cashier','Manager','Inventory Clerk') NOT NULL,
  `phone` varchar(15) NOT NULL,
  `hire_date` date NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `uq_employee_phone` (`phone`),
  CONSTRAINT `ck_employee_phone` CHECK (`phone` regexp '^[0-9]{3,4}-[0-9]{7}$')
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pharmacists`
--

DROP TABLE IF EXISTS `pharmacists`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pharmacists` (
  `employee_id` int(10) unsigned NOT NULL,
  `license_no` varchar(20) NOT NULL,
  `qualification` varchar(60) NOT NULL DEFAULT 'Pharm-D',
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `uq_pharmacist_lic` (`license_no`),
  CONSTRAINT `fk_pharmacist_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_pharmacists_bi BEFORE INSERT ON pharmacists
FOR EACH ROW
BEGIN
    IF (SELECT role FROM employees WHERE employee_id = NEW.employee_id) <> 'Pharmacist' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only employees with role Pharmacist can be stored in pharmacists';
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
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
  CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON UPDATE CASCADE,
  CONSTRAINT `ck_product_price` CHECK (`unit_price` >= 0),
  CONSTRAINT `ck_product_reorder` CHECK (`reorder_level` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_products_au AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    IF OLD.unit_price <> NEW.unit_price THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value)
        VALUES ('products', NEW.product_id, 'PRICE_CHANGE',
                CAST(OLD.unit_price AS CHAR), CAST(NEW.unit_price AS CHAR));
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `purchase_orders`
--

DROP TABLE IF EXISTS `purchase_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_orders` (
  `po_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` int(10) unsigned NOT NULL,
  `order_date` date NOT NULL DEFAULT curdate(),
  `status` enum('Pending','Received','Cancelled') NOT NULL DEFAULT 'Pending',
  `total_cost` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`po_id`),
  KEY `idx_po_supplier` (`supplier_id`),
  CONSTRAINT `fk_po_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`supplier_id`) ON UPDATE CASCADE,
  CONSTRAINT `ck_po_total` CHECK (`total_cost` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_po_bu BEFORE UPDATE ON purchase_orders
FOR EACH ROW
BEGIN
    IF OLD.status IN ('Received','Cancelled') AND NEW.status <> OLD.status THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A Received or Cancelled purchase order cannot change status';
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `sale_allocations`
--

DROP TABLE IF EXISTS `sale_allocations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sale_allocations` (
  `sale_id` int(10) unsigned NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `batch_id` int(10) unsigned NOT NULL,
  `quantity` int(11) NOT NULL,
  `cost_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`sale_id`,`product_id`,`batch_id`),
  KEY `fk_alloc_batch` (`batch_id`),
  CONSTRAINT `fk_alloc_batch` FOREIGN KEY (`batch_id`) REFERENCES `stock_batches` (`batch_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_alloc_item` FOREIGN KEY (`sale_id`, `product_id`) REFERENCES `sale_items` (`sale_id`, `product_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ck_alloc_qty` CHECK (`quantity` > 0),
  CONSTRAINT `ck_alloc_cost` CHECK (`cost_price` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sale_items`
--

DROP TABLE IF EXISTS `sale_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sale_items` (
  `sale_id` int(10) unsigned NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`sale_id`,`product_id`),
  KEY `idx_items_product` (`product_id`),
  CONSTRAINT `fk_item_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_item_sale` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`sale_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ck_item_quantity` CHECK (`quantity` > 0),
  CONSTRAINT `ck_item_price` CHECK (`unit_price` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_sale_items_bi BEFORE INSERT ON sale_items
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_sale_items_ai AFTER INSERT ON sale_items
FOR EACH ROW
BEGIN
    DECLARE v_day        DATE;
    DECLARE v_remaining  INT;
    DECLARE v_batch      INT UNSIGNED;
    DECLARE v_bqty       INT;
    DECLARE v_cost       DECIMAL(10,2);
    DECLARE v_take       INT;
    DECLARE v_done       BOOLEAN DEFAULT FALSE;

    
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_sale_items_bu BEFORE UPDATE ON sale_items
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Sale items cannot be updated; delete the line and add it again';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_sale_items_bd BEFORE DELETE ON sale_items
FOR EACH ROW
BEGIN
    UPDATE stock_batches b
    JOIN   sale_allocations a ON a.batch_id = b.batch_id
    SET    b.quantity = b.quantity + a.quantity
    WHERE  a.sale_id = OLD.sale_id AND a.product_id = OLD.product_id;

    UPDATE sales
    SET    total_amount = total_amount - OLD.quantity * OLD.unit_price
    WHERE  sale_id = OLD.sale_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `sales`
--

DROP TABLE IF EXISTS `sales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sales` (
  `sale_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `customer_id` int(10) unsigned NOT NULL,
  `employee_id` int(10) unsigned NOT NULL,
  `sale_date` datetime NOT NULL DEFAULT current_timestamp(),
  `payment_method` enum('Cash','Card','Mobile Wallet') NOT NULL DEFAULT 'Cash',
  `total_amount` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`sale_id`),
  KEY `idx_sales_date` (`sale_date`),
  KEY `idx_sales_customer` (`customer_id`),
  KEY `idx_sales_employee` (`employee_id`),
  CONSTRAINT `fk_sales_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_sales_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`) ON UPDATE CASCADE,
  CONSTRAINT `ck_sales_total` CHECK (`total_amount` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_sales_bi BEFORE INSERT ON sales
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_sales_bd BEFORE DELETE ON sales
FOR EACH ROW
BEGIN
    UPDATE stock_batches b
    JOIN   sale_allocations a ON a.batch_id = b.batch_id
    SET    b.quantity = b.quantity + a.quantity
    WHERE  a.sale_id = OLD.sale_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `stock_alerts`
--

DROP TABLE IF EXISTS `stock_alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_alerts` (
  `alert_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `alert_type` enum('LOW_STOCK','NEAR_EXPIRY','EXPIRED') NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `batch_id` int(10) unsigned DEFAULT NULL,
  `message` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`alert_id`),
  KEY `fk_alert_product` (`product_id`),
  KEY `fk_alert_batch` (`batch_id`),
  CONSTRAINT `fk_alert_batch` FOREIGN KEY (`batch_id`) REFERENCES `stock_batches` (`batch_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_alert_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stock_batches`
--

DROP TABLE IF EXISTS `stock_batches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
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
  CONSTRAINT `fk_batch_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON UPDATE CASCADE,
  CONSTRAINT `ck_batch_received` CHECK (`received_qty` > 0),
  CONSTRAINT `ck_batch_quantity` CHECK (`quantity` >= 0 and `quantity` <= `received_qty`),
  CONSTRAINT `ck_batch_cost` CHECK (`cost_price` >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_batches_bi BEFORE INSERT ON stock_batches
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
    SET NEW.quantity = NEW.received_qty;      
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_batches_ai AFTER INSERT ON stock_batches
FOR EACH ROW
BEGIN
    UPDATE purchase_orders
    SET    total_cost = total_cost + NEW.received_qty * NEW.cost_price
    WHERE  po_id = NEW.po_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_batches_au AFTER UPDATE ON stock_batches
FOR EACH ROW
BEGIN
    IF NEW.received_qty <> OLD.received_qty OR NEW.cost_price <> OLD.cost_price THEN
        UPDATE purchase_orders
        SET    total_cost = total_cost - OLD.received_qty * OLD.cost_price
                                       + NEW.received_qty * NEW.cost_price
        WHERE  po_id = NEW.po_id;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_batches_ad AFTER DELETE ON stock_batches
FOR EACH ROW
BEGIN
    UPDATE purchase_orders
    SET    total_cost = total_cost - OLD.received_qty * OLD.cost_price
    WHERE  po_id = OLD.po_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `supplier_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `address` varchar(250) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`supplier_id`),
  UNIQUE KEY `uq_supplier_name` (`name`),
  UNIQUE KEY `uq_supplier_phone` (`phone`),
  CONSTRAINT `ck_supplier_phone` CHECK (`phone` regexp '^[0-9]{3,4}-[0-9]{7}$')
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `v_daily_sales_summary`
--

DROP TABLE IF EXISTS `v_daily_sales_summary`;
/*!50001 DROP VIEW IF EXISTS `v_daily_sales_summary`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_daily_sales_summary` AS SELECT
 1 AS `sale_day`,
  1 AS `bills`,
  1 AS `units_sold`,
  1 AS `revenue`,
  1 AS `avg_bill` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_expired_stock`
--

DROP TABLE IF EXISTS `v_expired_stock`;
/*!50001 DROP VIEW IF EXISTS `v_expired_stock`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_expired_stock` AS SELECT
 1 AS `batch_id`,
  1 AS `product_id`,
  1 AS `product_name`,
  1 AS `batch_no`,
  1 AS `quantity`,
  1 AS `expiry_date`,
  1 AS `days_expired`,
  1 AS `loss_at_cost` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_expiring_30_days`
--

DROP TABLE IF EXISTS `v_expiring_30_days`;
/*!50001 DROP VIEW IF EXISTS `v_expiring_30_days`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_expiring_30_days` AS SELECT
 1 AS `batch_id`,
  1 AS `product_id`,
  1 AS `product_name`,
  1 AS `batch_no`,
  1 AS `quantity`,
  1 AS `expiry_date`,
  1 AS `days_left`,
  1 AS `stock_value_at_cost` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_low_stock`
--

DROP TABLE IF EXISTS `v_low_stock`;
/*!50001 DROP VIEW IF EXISTS `v_low_stock`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_low_stock` AS SELECT
 1 AS `product_id`,
  1 AS `product_name`,
  1 AS `category_name`,
  1 AS `on_hand`,
  1 AS `reorder_level`,
  1 AS `shortage` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_product_stock`
--

DROP TABLE IF EXISTS `v_product_stock`;
/*!50001 DROP VIEW IF EXISTS `v_product_stock`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_product_stock` AS SELECT
 1 AS `product_id`,
  1 AS `product_name`,
  1 AS `category_name`,
  1 AS `reorder_level`,
  1 AS `on_hand`,
  1 AS `expired_qty` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_sale_details`
--

DROP TABLE IF EXISTS `v_sale_details`;
/*!50001 DROP VIEW IF EXISTS `v_sale_details`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_sale_details` AS SELECT
 1 AS `sale_id`,
  1 AS `sale_date`,
  1 AS `customer`,
  1 AS `served_by`,
  1 AS `product`,
  1 AS `quantity`,
  1 AS `unit_price`,
  1 AS `line_total`,
  1 AS `payment_method` */;
SET character_set_client = @saved_cs_client;

--
-- Dumping events for database 'pharmacy_db'
--
/*!50106 SET @save_time_zone= @@TIME_ZONE */ ;
/*!50106 DROP EVENT IF EXISTS `ev_daily_stock_alerts` */;
DELIMITER ;;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;;
/*!50003 SET character_set_client  = latin1 */ ;;
/*!50003 SET character_set_results = latin1 */ ;;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;;
/*!50003 SET @saved_time_zone      = @@time_zone */ ;;
/*!50003 SET time_zone             = 'SYSTEM' */ ;;
/*!50106 CREATE*/ /*!50117 DEFINER=`root`@`localhost`*/ /*!50106 EVENT `ev_daily_stock_alerts` ON SCHEDULE EVERY 1 DAY STARTS '2026-11-19 06:00:00' ON COMPLETION NOT PRESERVE ENABLE DO CALL sp_refresh_stock_alerts() */ ;;
/*!50003 SET time_zone             = @saved_time_zone */ ;;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;;
/*!50003 SET character_set_client  = @saved_cs_client */ ;;
/*!50003 SET character_set_results = @saved_cs_results */ ;;
/*!50003 SET collation_connection  = @saved_col_connection */ ;;
DELIMITER ;
/*!50106 SET TIME_ZONE= @save_time_zone */ ;

--
-- Dumping routines for database 'pharmacy_db'
--
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_stock_on_hand` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_stock_on_hand`(p_product_id INT UNSIGNED, p_on_date DATE) RETURNS int(11)
    READS SQL DATA
BEGIN
    RETURN COALESCE((SELECT SUM(quantity)
                     FROM   stock_batches
                     WHERE  product_id  = p_product_id
                       AND  expiry_date >= p_on_date), 0);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_checkout` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_checkout`(
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
        ROLLBACK;          
        RESIGNAL;          
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

        
        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
        VALUES (p_sale_id, v_pid, v_qty, v_price);
    END LOOP;
    CLOSE cur_items;

    COMMIT;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_monthly_report` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_monthly_report`(IN p_year INT, IN p_month INT)
BEGIN
    DECLARE v_start DATE;
    DECLARE v_end   DATE;

    IF p_month NOT BETWEEN 1 AND 12 OR p_year NOT BETWEEN 2000 AND 2100 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Month must be 1-12 and year 2000-2100';
    END IF;

    SET v_start = STR_TO_DATE(CONCAT(p_year, '-', p_month, '-01'), '%Y-%m-%d');
    SET v_end   = DATE_ADD(v_start, INTERVAL 1 MONTH);

    
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

    
    SELECT  c.category_name, SUM(si.quantity) AS units,
            SUM(si.quantity * si.unit_price)  AS revenue
    FROM    sale_items si
    JOIN    sales s      ON s.sale_id      = si.sale_id
    JOIN    products p   ON p.product_id   = si.product_id
    JOIN    categories c ON c.category_id  = p.category_id
    WHERE   s.sale_date >= v_start AND s.sale_date < v_end
    GROUP BY c.category_id, c.category_name
    ORDER BY revenue DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_receive_stock` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_receive_stock`(
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
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_refresh_stock_alerts` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = latin1 */ ;
/*!50003 SET character_set_results = latin1 */ ;
/*!50003 SET collation_connection  = latin1_swedish_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_refresh_stock_alerts`()
BEGIN
    DELETE FROM stock_alerts WHERE created_at >= CURRENT_DATE;   

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
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Final view structure for view `v_daily_sales_summary`
--

/*!50001 DROP VIEW IF EXISTS `v_daily_sales_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_daily_sales_summary` AS select cast(`s`.`sale_date` as date) AS `sale_day`,count(distinct `s`.`sale_id`) AS `bills`,sum(`si`.`quantity`) AS `units_sold`,sum(`si`.`quantity` * `si`.`unit_price`) AS `revenue`,round(sum(`si`.`quantity` * `si`.`unit_price`) / count(distinct `s`.`sale_id`),2) AS `avg_bill` from (`sales` `s` join `sale_items` `si` on(`si`.`sale_id` = `s`.`sale_id`)) group by cast(`s`.`sale_date` as date) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_expired_stock`
--

/*!50001 DROP VIEW IF EXISTS `v_expired_stock`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_expired_stock` AS select `b`.`batch_id` AS `batch_id`,`p`.`product_id` AS `product_id`,`p`.`name` AS `product_name`,`b`.`batch_no` AS `batch_no`,`b`.`quantity` AS `quantity`,`b`.`expiry_date` AS `expiry_date`,to_days(curdate()) - to_days(`b`.`expiry_date`) AS `days_expired`,`b`.`quantity` * `b`.`cost_price` AS `loss_at_cost` from (`stock_batches` `b` join `products` `p` on(`p`.`product_id` = `b`.`product_id`)) where `b`.`quantity` > 0 and `b`.`expiry_date` < curdate() */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_expiring_30_days`
--

/*!50001 DROP VIEW IF EXISTS `v_expiring_30_days`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_expiring_30_days` AS select `b`.`batch_id` AS `batch_id`,`p`.`product_id` AS `product_id`,`p`.`name` AS `product_name`,`b`.`batch_no` AS `batch_no`,`b`.`quantity` AS `quantity`,`b`.`expiry_date` AS `expiry_date`,to_days(`b`.`expiry_date`) - to_days(curdate()) AS `days_left`,`b`.`quantity` * `b`.`cost_price` AS `stock_value_at_cost` from (`stock_batches` `b` join `products` `p` on(`p`.`product_id` = `b`.`product_id`)) where `b`.`quantity` > 0 and `b`.`expiry_date` between curdate() and curdate() + interval 30 day */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_low_stock`
--

/*!50001 DROP VIEW IF EXISTS `v_low_stock`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_low_stock` AS select `v_product_stock`.`product_id` AS `product_id`,`v_product_stock`.`product_name` AS `product_name`,`v_product_stock`.`category_name` AS `category_name`,`v_product_stock`.`on_hand` AS `on_hand`,`v_product_stock`.`reorder_level` AS `reorder_level`,`v_product_stock`.`reorder_level` - `v_product_stock`.`on_hand` AS `shortage` from `v_product_stock` where `v_product_stock`.`on_hand` < `v_product_stock`.`reorder_level` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_product_stock`
--

/*!50001 DROP VIEW IF EXISTS `v_product_stock`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_product_stock` AS select `p`.`product_id` AS `product_id`,`p`.`name` AS `product_name`,`c`.`category_name` AS `category_name`,`p`.`reorder_level` AS `reorder_level`,coalesce(sum(case when `b`.`expiry_date` >= curdate() then `b`.`quantity` end),0) AS `on_hand`,coalesce(sum(case when `b`.`expiry_date` < curdate() then `b`.`quantity` end),0) AS `expired_qty` from ((`products` `p` join `categories` `c` on(`c`.`category_id` = `p`.`category_id`)) left join `stock_batches` `b` on(`b`.`product_id` = `p`.`product_id`)) group by `p`.`product_id`,`p`.`name`,`c`.`category_name`,`p`.`reorder_level` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_sale_details`
--

/*!50001 DROP VIEW IF EXISTS `v_sale_details`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_sale_details` AS select `s`.`sale_id` AS `sale_id`,`s`.`sale_date` AS `sale_date`,`cu`.`name` AS `customer`,`e`.`name` AS `served_by`,`p`.`name` AS `product`,`si`.`quantity` AS `quantity`,`si`.`unit_price` AS `unit_price`,`si`.`quantity` * `si`.`unit_price` AS `line_total`,`s`.`payment_method` AS `payment_method` from ((((`sales` `s` join `customers` `cu` on(`cu`.`customer_id` = `s`.`customer_id`)) join `employees` `e` on(`e`.`employee_id` = `s`.`employee_id`)) join `sale_items` `si` on(`si`.`sale_id` = `s`.`sale_id`)) join `products` `p` on(`p`.`product_id` = `si`.`product_id`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-18 12:37:52
