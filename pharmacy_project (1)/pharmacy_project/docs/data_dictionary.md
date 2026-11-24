# Data dictionary

## categories  (10 rows)
Groups medicines into categories (analgesics, antibiotics ...).

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| category_id | int(10) unsigned | NO | PK | Surrogate key. |
| category_name | varchar(60) | NO | UNIQUE | Unique category name. |
| description | varchar(200) | YES |  | Free-text note. |

## products  (41 rows)
Catalogue of medicines and devices sold by the pharmacy.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| product_id | int(10) unsigned | NO | PK | Surrogate key. |
| name | varchar(100) | NO | UNIQUE | Brand / product name with strength (unique). |
| generic_name | varchar(100) | YES |  | Active ingredient. |
| manufacturer | varchar(80) | YES |  | Added later with ALTER TABLE (DDL demo); optional. |
| category_id | int(10) unsigned | NO | FK -> categories(category_id) | Category the product belongs to. |
| unit_price | decimal(10,2) | NO | CHECK unit_price >= 0 | Selling price per unit in PKR. |
| reorder_level | int(11) | NO | CHECK reorder_level >= 0; DEFAULT 20 | Re-order when sellable stock falls below this. |
| requires_prescription | tinyint(1) | NO | DEFAULT 0 | TRUE for prescription-only medicines. |

## suppliers  (12 rows)
Wholesalers / distributors the pharmacy buys from.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| supplier_id | int(10) unsigned | NO | PK | Surrogate key. |
| name | varchar(100) | NO | UNIQUE | Supplier trade name (unique). |
| phone | varchar(15) | NO | UNIQUE; CHECK phone regexp '^[0-9]{3,4}-[0-9]{7}$' | Contact number, format 051-1234567. |
| address | varchar(250) | NO |  | Postal address. |
| is_active | tinyint(1) | NO | DEFAULT 1 | FALSE = no longer used for orders. |

## purchase_orders  (30 rows)
One delivery / order placed with a supplier.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| po_id | int(10) unsigned | NO | PK | Surrogate key. |
| supplier_id | int(10) unsigned | NO | FK -> suppliers(supplier_id) | Supplier the order was placed with. |
| order_date | date | NO | DEFAULT curdate() | Date of the order / delivery. |
| status | enum('Pending','Received','Cancelled') | NO | DEFAULT Pending | Pending, Received or Cancelled. |
| total_cost | decimal(12,2) | NO | CHECK total_cost >= 0; DEFAULT 0.00 | Sum of received_qty x cost_price of its batches (maintained by trigger). |

## stock_batches  (52 rows)
Stock received in a purchase order, tracked per batch with its own expiry date.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| batch_id | int(10) unsigned | NO | PK | Surrogate key. |
| product_id | int(10) unsigned | NO | FK -> products(product_id); UNIQUE | Medicine in this batch. |
| po_id | int(10) unsigned | NO | FK -> purchase_orders(po_id) | Purchase order that delivered it. |
| batch_no | varchar(30) | NO | UNIQUE | Manufacturer lot number (unique per product). |
| received_qty | int(11) | NO | CHECK received_qty > 0; CHECK quantity >= 0 and quantity <= received_qty | Units delivered. |
| quantity | int(11) | NO | CHECK quantity >= 0 and quantity <= received_qty | Units still on the shelf (falls as sales are made). |
| expiry_date | date | NO |  | Last day the batch may be sold. |
| cost_price | decimal(10,2) | NO | CHECK cost_price >= 0 | Purchase price per unit in PKR. |

## customers  (40 rows)
Customers (includes one 'Walk-in Customer' for anonymous sales).

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| customer_id | int(10) unsigned | NO | PK | Surrogate key. |
| name | varchar(100) | NO |  | Customer name. |
| phone | varchar(15) | YES | UNIQUE; CHECK phone is null or phone regexp '^[0-9]{3,4}-[0-9]{7}$' | Mobile number 03xx-xxxxxxx; NULL for the walk-in customer. |
| email | varchar(100) | YES | UNIQUE | Added later with ALTER TABLE (DDL demo); optional, unique. |
| registered_on | date | NO | DEFAULT curdate() | Date the customer was registered. |

## employees  (12 rows)
All staff - superclass of the EER specialisation.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| employee_id | int(10) unsigned | NO | PK | Surrogate key. |
| name | varchar(100) | NO |  | Employee name. |
| role | enum('Pharmacist','Cashier','Manager','Inventory Clerk') | NO |  | Pharmacist, Cashier, Manager or Inventory Clerk. |
| phone | varchar(15) | NO | UNIQUE; CHECK phone regexp '^[0-9]{3,4}-[0-9]{7}$' | Mobile number (unique). |
| hire_date | date | NO |  | Date joined. |
| is_active | tinyint(1) | NO | DEFAULT 1 | FALSE after the employee leaves. |

## pharmacists  (4 rows)
EER subclass: licensed pharmacists (extra attributes).

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| employee_id | int(10) unsigned | NO | PK; FK -> employees(employee_id) | Same key as the employee (subclass). |
| license_no | varchar(20) | NO | UNIQUE | Pharmacy-council licence number (unique). |
| qualification | varchar(60) | NO | DEFAULT Pharm-D | Degree, default Pharm-D. |

## cashiers  (4 rows)
EER subclass: cashiers (shift and counter).

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| employee_id | int(10) unsigned | NO | PK; FK -> employees(employee_id) | Same key as the employee (subclass). |
| shift | enum('Morning','Evening','Night') | NO | DEFAULT Morning | Morning, Evening or Night. |
| counter_no | tinyint(3) unsigned | NO | CHECK counter_no between 1 and 6 | Billing counter 1-6. |

## sales  (56 rows)
Header of a bill: who bought, who served, when and how paid.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| sale_id | int(10) unsigned | NO | PK | Bill number. |
| customer_id | int(10) unsigned | NO | FK -> customers(customer_id) | Buyer. |
| employee_id | int(10) unsigned | NO | FK -> employees(employee_id) | Pharmacist / cashier who served. |
| sale_date | datetime | NO | DEFAULT current_timestamp() | Date and time of the sale. |
| payment_method | enum('Cash','Card','Mobile Wallet') | NO | DEFAULT Cash | Cash, Card or Mobile Wallet. |
| total_amount | decimal(12,2) | NO | CHECK total_amount >= 0; DEFAULT 0.00 | Bill total, maintained by trigger from the bill lines. |

## sale_items  (137 rows)
Lines of a bill; resolves the Sales M:N Products relationship.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| sale_id | int(10) unsigned | NO | PK; FK -> sales(sale_id) | Bill the line belongs to. |
| product_id | int(10) unsigned | NO | PK; FK -> products(product_id) | Medicine sold. |
| quantity | int(11) | NO | CHECK quantity > 0 | Units sold (> 0). |
| unit_price | decimal(10,2) | NO | CHECK unit_price >= 0 | Price charged on the day of sale. |

## sale_allocations  (138 rows)
Which batch(es) every bill line was taken from (FEFO) with the batch cost - gives exact profit.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| sale_id | int(10) unsigned | NO | PK; FK -> sale_items(sale_id) | Bill number (part of the sale-line key). |
| product_id | int(10) unsigned | NO | PK; FK -> sale_items(product_id) | Medicine (part of the sale-line key). |
| batch_id | int(10) unsigned | NO | PK; FK -> stock_batches(batch_id) | Batch the units were taken from. |
| quantity | int(11) | NO | CHECK quantity > 0 | Units taken from that batch. |
| cost_price | decimal(10,2) | NO | CHECK cost_price >= 0 | Batch cost per unit at the time of sale. |

## stock_alerts  (0 rows)
Low-stock / near-expiry / expired alerts produced by the daily event.

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| alert_id | int(10) unsigned | NO | PK | Surrogate key. |
| alert_type | enum('LOW_STOCK','NEAR_EXPIRY','EXPIRED') | NO |  | LOW_STOCK, NEAR_EXPIRY or EXPIRED. |
| product_id | int(10) unsigned | NO | FK -> products(product_id) | Product concerned. |
| batch_id | int(10) unsigned | YES | FK -> stock_batches(batch_id) | Batch concerned (NULL for low-stock alerts). |
| message | varchar(255) | NO |  | Human-readable alert text. |
| created_at | datetime | NO | DEFAULT current_timestamp() | When the alert was generated. |

## audit_log  (0 rows)
Audit trail written by triggers (price changes).

| Column | Type | Null | Constraints | Description |
|---|---|---|---|---|
| log_id | int(10) unsigned | NO | PK | Surrogate key. |
| table_name | varchar(40) | NO |  | Table that changed. |
| record_id | int(10) unsigned | NO |  | Key of the changed row. |
| action | varchar(20) | NO |  | Kind of change, e.g. PRICE_CHANGE. |
| old_value | varchar(255) | YES |  | Value before. |
| new_value | varchar(255) | YES |  | Value after. |
| changed_at | datetime | NO | DEFAULT current_timestamp() | Time of change. |
| changed_by | varchar(80) | NO | DEFAULT current_user() | Database user who made the change. |
