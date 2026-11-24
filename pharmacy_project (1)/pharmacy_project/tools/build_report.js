// Builds docs/Pharmacy_DB_Final_Project_Report.docx from the project files and the captured outputs.
const fs = require("fs"), path = require("path");
const L = require("./report_lib.js");
const { D, FONT, W, rich, P, H1, H1n, H2, H3, bullets, numbered, caption, gap, pb, code, table, fit, fmt, resultTable, img } = L;
const { Document, Packer, Paragraph, TextRun, Footer, Header, PageNumber, AlignmentType, LevelFormat, PageOrientation, TabStopType } = D;

const ROOT = path.join(__dirname, ".."), DOCS = path.join(ROOT, "docs");
const J = (f) => JSON.parse(fs.readFileSync(path.join(DOCS, f), "utf8"));
const Q = J("query_results.json"), PGQ = J("pg_query_results.json"), DML = J("dml_ddl_output.json"),
      TST = J("test_output.json"), PGT = J("pg_test_output.json"), DICT = J("data_dictionary.json"), NOS = J("nosql_verification.json");
const read = (f) => fs.readFileSync(path.join(ROOT, f), "utf8");
const SQL02 = read("mysql/02_programmability.sql");
function block(src, startRe, endRe = /^END\$\$/) {
  const lines = src.split("\n"); const s = lines.findIndex((l) => startRe.test(l)); if (s < 0) throw new Error("block not found " + startRe);
  let e = s; while (!endRe.test(lines[e].trim())) e++;
  return lines.slice(s, e + 1).join("\n").replace(/\$\$/g, ";").replace(/^;$/m, ";");
}
const tidyType = (t) => t.replace("int(10) unsigned", "int unsigned").replace("tinyint(1)", "boolean").replace("tinyint(3) unsigned", "tinyint unsigned").replace("int(11)", "int").replace(/^[a-z]+/, (m) => m.toUpperCase());
const rowCount = Object.fromEntries(DICT.map((t) => [t.table, t.rowcount]));
const qsql = (q) => q.sql;

const children = [];
const add = (...x) => x.flat().forEach((e) => children.push(e));

// ------------------------------------------------------------------ COVER
add(gap(1200),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: "NATIONAL UNIVERSITY OF SCIENCES AND TECHNOLOGY", bold: true, size: 26, font: FONT, color: "1F3864" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: "NUST Islamabad", size: 24, font: FONT, color: "1F3864" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: "Pharmacy Inventory & Sales Management System", bold: true, size: 52, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: "Final Project Report", size: 34, font: FONT, color: "2E5E9E" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "CS220 Database Systems  |  BESE 2K25", size: 24, font: FONT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 500 }, children: [new TextRun({ text: "Instructor: Bilal Rizvi", size: 24, font: FONT })] }),
  table(["Name", "CMS ID"], [["MUHAMMAD SAADAIN ZAHID", "540229"], ["HASHIR SALEEM", "549261"], ["ABDUL AHAD", "541845"]], [3, 1.5], { total: 6000 }),
  gap(400),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "November 2026", size: 22, font: FONT, color: "555555" })] }));

// ------------------------------------------------------------------ CONTENTS (static)
add(H1("Contents"));
const toc = ["1  Introduction, objectives and scope", "2  Database concepts and system architecture (Weeks 1-2)", "3  Requirements and business rules",
  "4  Conceptual design: ER and EER model (Weeks 5-6)", "5  Logical design: relational schema and data dictionary", "6  Anomalies, functional dependencies and normalization (Weeks 10-11)",
  "7  Physical implementation: DDL, constraints, indexes (Week 8)", "8  Data manipulation: DML and transactions (Week 12)", "9  Data retrieval: 34 documented queries (Weeks 3, 4, 13)",
  "10  Relational algebra (Week 7)", "11  Views, functions, stored procedures, triggers and events (Week 14)", "12  Testing: transactions, triggers and constraints",
  "13  SQL versus NoSQL (Week 15)", "14  PostgreSQL implementation (Week 16)", "15  Python menu interface", "16  Conclusion, limitations and future work",
  "Appendix A  Topic coverage matrix", "Appendix B  Files, environment and how to run", "Appendix C  Viva preparation"];
add(...toc.map((t) => P(t, { after: 80 })));

// ------------------------------------------------------------------ 1 INTRO
add(H1("1  Introduction, objectives and scope"));
add(H2("1.1 Problem statement"),
  P("Small and medium pharmacies often track stock, purchases and sales on paper or in spreadsheets. This causes stock-outs, expired medicines sitting on shelves, billing mistakes and no clear view of profit. This project designs and implements a relational database that manages a pharmacy's complete workflow - from buying medicines from suppliers to selling them to customers - while keeping stock accurate and expiry-aware."),
  P("The system is implemented in **MySQL** (as promised in the proposal), ported to **PostgreSQL** (Week 16), compared with a **MongoDB** document model (Week 15) and fronted by a small **Python** menu program. Every topic of the 16-week course is used somewhere in the project; Appendix A shows exactly where."));
add(H2("1.2 Objectives and how they were met"),
  table(["Objective (from the proposal)", "How it was achieved", "Evidence"], [
    ["Normalized (3NF) MySQL database for a real pharmacy", "9 core entities + EER subclasses + 3 supporting tables; every table in 3NF (BCNF checked)", "Chapters 5-7, mysql/01_schema.sql"],
    ["Automate stock updates; flag low-stock and near-expiry medicines", "Triggers deduct stock First-Expiry-First-Out; views and a daily event raise alerts", "Chapter 11; tests T1, T10"],
    ["Business reports (sales, profit, top products) with SQL", "34 documented queries and the sp_monthly_report procedure", "Chapter 9; Q4-Q12, Q31"],
    ["Data integrity through constraints, triggers and transactions", "PK/FK/NOT NULL/UNIQUE/CHECK/DEFAULT + 14 triggers + atomic checkout; 25 negative tests all rejected", "Chapters 7, 11, 12"]],
    [3.2, 4.4, 2.4], { size: 17 }), gap());
add(H2("1.3 Scope (as proposed)"),
  ...bullets(["**Inventory:** medicines, categories and batch-wise stock with expiry dates.", "**Purchasing:** supplier records and purchase orders that add new stock batches.",
    "**Sales & billing:** customer purchases with multiple items per bill and automatic totals.", "**Staff & customers:** which employee made each sale and each customer's purchase history."]));
add(H2("1.4 Size of the database"),
  table(["Table", "Rows", "Table", "Rows"], [
    ["categories", rowCount.categories, "sales", rowCount.sales], ["products", rowCount.products, "sale_items", rowCount.sale_items], ["suppliers", rowCount.suppliers, "sale_allocations", rowCount.sale_allocations],
    ["purchase_orders", rowCount.purchase_orders, "pharmacists", rowCount.pharmacists], ["stock_batches", rowCount.stock_batches, "cashiers", rowCount.cashiers], ["customers", rowCount.customers, "employees", rowCount.employees]],
    [3, 1, 3, 1], { size: 18, right: [1, 3] }),
  P("The proposal asked for 30-50 rows per main table. The transactional tables meet or slightly exceed this (products 41, customers 40, stock_batches 52, purchase_orders 30, sales 56, sale_items 137). Small lookup tables (categories 10, suppliers 12, employees 12) are smaller because a real pharmacy has only that many. All names, phone numbers and prices are fictional/illustrative.", { run: { size: 19 } }));

// ------------------------------------------------------------------ 2 CONCEPTS
add(H1("2  Database concepts and system architecture"));
add(H2("2.1 Why a database and not a spreadsheet?"),
  table(["Pharmacy problem", "Spreadsheet / paper", "Database solution in this project"], [
    ["Same medicine typed twice with different spellings", "Nothing prevents it", "UNIQUE name, one row per product, foreign keys everywhere"],
    ["Selling more than is in stock", "Discovered on the shelf", "Trigger rejects the sale before it is saved"],
    ["Expired medicine sold or forgotten", "Manual checking", "Expiry stored per batch; expired stock cannot be sold; views list it"],
    ["Two cashiers editing the same sheet", "Lost updates", "InnoDB row locks and ACID transactions"],
    ["Wrong bill total", "Hand-typed formula", "Total maintained by trigger from the bill lines"],
    ["Which batch was sold, and what profit?", "Unknown", "sale_allocations records batch and cost for every line"]], [3, 2.4, 4.6], { size: 17 }), gap());
add(H2("2.2 DBMS architecture used"),
  P("The project follows the classic **three-schema architecture**, which gives data independence:"),
  table(["Level", "Meaning", "In this project"], [
    ["External (views)", "What each user group sees", "v_low_stock, v_expiring_30_days, v_daily_sales_summary, v_sale_details; the Python menu only uses views and procedures"],
    ["Conceptual (logical)", "Whole database, independent of storage", "14 tables, keys, constraints (Chapters 4-5)"],
    ["Internal (physical)", "Files, pages, indexes", "InnoDB storage engine, B-tree indexes idx_batches_fefo, idx_sales_date ... (Chapter 7)"]], [2, 3, 5], { size: 17 }), gap(),
  P("Physical data independence was demonstrated: indexes were added with CREATE INDEX without changing a single query. Logical data independence: columns email and manufacturer were added with ALTER TABLE and no existing query or view needed to change."),
  P("**Client-server architecture.** Three tiers are used: (1) client programs - MySQL Workbench, the mysql command line and the Python menu; (2) the database server (mysqld) containing the connection handler, SQL parser, optimizer, executor, the trigger/procedure engine and the event scheduler; (3) the storage engine (InnoDB) providing transactions, row-level locking, foreign keys and crash recovery."),
  H2("2.3 Components and languages"),
  table(["SQL sub-language", "Statements", "Used in"], [
    ["DDL - Data Definition", "CREATE, ALTER, DROP, TRUNCATE, RENAME, CREATE INDEX/VIEW", "mysql/01_schema.sql, 05_dml_ddl_demo.sql (Part 2)"],
    ["DML - Data Manipulation", "INSERT, UPDATE, DELETE, INSERT...SELECT, upsert", "03_sample_data.sql, 05_dml_ddl_demo.sql (Part 1)"],
    ["DRL - Data Retrieval", "SELECT with WHERE, JOIN, GROUP BY, HAVING, ORDER BY, LIMIT, sub-queries, set operators, window functions", "04_queries.sql (34 queries)"],
    ["TCL - Transaction control", "START TRANSACTION, COMMIT, ROLLBACK, SAVEPOINT", "sp_checkout, sp_receive_stock, tests"],
    ["DCL - Data control", "CREATE USER, GRANT", "00_app_user.sql (limited account for the Python program)"]], [2.6, 4.2, 3.2], { size: 17 }), gap(),
  P("**Database users:** the database administrator (creates schema, grants), the pharmacy manager (reports), pharmacists and cashiers (billing through the checkout procedure) and the application programmer (Python menu)."));

// ------------------------------------------------------------------ 3 REQUIREMENTS
add(H1("3  Requirements and business rules"));
add(P("Each business rule is enforced **inside the database** by the mechanism shown, so that no application - not even a careless manual INSERT - can break it."));
add(table(["#", "Business rule", "Enforced by"], [
  ["BR1", "Every product belongs to exactly one category", "FK products.category_id NOT NULL"],
  ["BR2", "Product names, supplier names/phones, customer phones, licence numbers are unique", "UNIQUE constraints"],
  ["BR3", "Prices, costs and reorder levels cannot be negative; sale quantity must be greater than 0", "CHECK constraints"],
  ["BR4", "Phone numbers have a valid format", "CHECK with REGEXP"],
  ["BR5", "Stock is kept per batch with its own expiry date; remaining quantity never exceeds what was received", "stock_batches + CHECK (quantity <= received_qty)"],
  ["BR6", "A sale is rejected when sellable (unexpired) stock is not enough", "Trigger trg_sale_items_bi"],
  ["BR7", "Stock is deducted automatically, earliest-expiring batch first (FEFO)", "Trigger trg_sale_items_ai"],
  ["BR8", "Expired batches can never be sold", "FEFO query filters expiry_date >= sale date; fn_stock_on_hand"],
  ["BR9", "Bill total = sum of its lines; purchase-order total = sum of its batches", "Triggers (sale_items, stock_batches)"],
  ["BR10", "Only active pharmacists or cashiers can make a sale", "Trigger trg_sales_bi"],
  ["BR11", "A pharmacist/cashier record must belong to an employee with that role (EER subclass rule)", "Triggers trg_pharmacists_bi, trg_cashiers_bi"],
  ["BR12", "A Received or Cancelled purchase order cannot change status; no stock can be added to a cancelled order", "Triggers trg_po_bu, trg_batches_bi"],
  ["BR13", "A bill line is never edited in place; deleting a line or a bill returns the stock", "Triggers trg_sale_items_bu / _bd, trg_sales_bd"],
  ["BR14", "Checkout (sale + lines + stock update) succeeds completely or not at all", "Procedure sp_checkout with a transaction"],
  ["BR15", "Every price change is audited", "Trigger trg_products_au -> audit_log"],
  ["BR16", "Low-stock, near-expiry and expired items are flagged every morning", "Views + procedure sp_refresh_stock_alerts + EVENT"]],
  [0.8, 5.8, 3.4], { size: 17 }));

// ------------------------------------------------------------------ 4 EER
add(H1("4  Conceptual design: ER and EER model"));
add(P("The design has the nine entities of the proposal. EER concepts used: **specialization** (Employee into Pharmacist and Cashier), an **associative entity** (Sale Item resolving the many-to-many relationship between Sale and Product) and **derived attributes** (total_amount, total_cost)."));
add(img(path.join(DOCS, "eer_diagram.png"), 400, 604), caption("Figure 4.1  EER diagram (crow's foot relationships are shown as 1 / M labels on diamonds)"));
add(H2("4.1 Relationships"),
  table(["Relationship", "Entities", "Cardinality", "Participation"], [
    ["classifies", "Category - Product", "1 : M", "Product total (must have a category); Category partial"],
    ["supplies", "Supplier - Purchase Order", "1 : M", "PO total; Supplier partial"],
    ["contains", "Purchase Order - Stock Batch", "1 : M", "Batch total; PO partial (pending/cancelled orders have no batches yet)"],
    ["stocked as", "Product - Stock Batch", "1 : M", "Batch total; Product partial"],
    ["places", "Customer - Sale", "1 : M", "Sale total; Customer partial (some never bought)"],
    ["makes", "Employee - Sale", "1 : M", "Sale total; Employee partial"],
    ["includes", "Sale - Product (via Sale Item)", "M : N", "Sale Item total on Sale and Product"],
    ["served from", "Sale Item - Stock Batch (sale_allocations)", "M : N", "A line may be served from several batches"]],
    [1.6, 3.2, 1.2, 4], { size: 17 }), gap());
add(H2("4.2 Specialization (EER)"),
  P("EMPLOYEE is the superclass. PHARMACIST (extra attribute licence number, qualification) and CASHIER (shift, counter number) are subclasses. The specialization is **disjoint** (an employee cannot be both) and **partial** (managers and inventory clerks belong to neither subclass). The defining attribute is `role`, and the rule is enforced by two triggers. In the relational model the subclasses share the superclass key (`employee_id` is both PK and FK)."),
  H2("4.3 Design decisions"),
  ...bullets(["**Stock is kept per batch**, not per product. Medicines expire batch by batch, so one quantity column on Products would make expiry tracking impossible.",
    "**sale_allocations** is an extra table (M:N between a bill line and batches). It records which batch each unit came from and at what cost, which makes profit exact and lets the system prove FEFO.",
    "**Derived values** (bill total, purchase-order total, remaining batch quantity) are stored on purpose for speed and are kept correct by triggers; Chapter 6 discusses this controlled redundancy and test T11 proves there are zero mismatches.",
    "**unit_price on Sale Items** stores the price on the day of sale. It is not redundant: product prices change over time, and old bills must not change.",
    "A **Walk-in Customer** row (id 1) lets anonymous sales keep the foreign key NOT NULL instead of allowing NULLs."]));

// ------------------------------------------------------------------ 5 LOGICAL
add(H1("5  Logical design: relational schema and data dictionary"));
add(H2("5.1 Mapping rules applied"),
  table(["ER/EER construct", "Rule", "Result"], [
    ["Strong entity", "Table; key attribute becomes PRIMARY KEY", "9 core tables"],
    ["1 : M relationship", "Foreign key on the 'many' side", "products.category_id, purchase_orders.supplier_id, stock_batches.po_id / product_id, sales.customer_id / employee_id"],
    ["M : N relationship", "New table with the two keys as composite PK", "sale_items (sale_id, product_id); sale_allocations (sale_id, product_id, batch_id)"],
    ["Specialization (disjoint, partial)", "One table per subclass; PK = FK to superclass", "pharmacists, cashiers"],
    ["Multi-valued / composite attributes", "None present (address kept atomic)", "-"],
    ["Derived attribute", "Stored column maintained by trigger", "sales.total_amount, purchase_orders.total_cost"]], [2.4, 3.8, 3.8], { size: 17 }), gap());
add(H2("5.2 Relational schema"),
  ...code(`CATEGORIES(category_id PK, category_name U, description)
SUPPLIERS(supplier_id PK, name U, phone U, address, is_active)
PRODUCTS(product_id PK, name U, generic_name, manufacturer, category_id FK->CATEGORIES, unit_price, reorder_level, requires_prescription)
PURCHASE_ORDERS(po_id PK, supplier_id FK->SUPPLIERS, order_date, status, total_cost)
STOCK_BATCHES(batch_id PK, product_id FK->PRODUCTS, po_id FK->PURCHASE_ORDERS, batch_no, received_qty, quantity, expiry_date, cost_price)   U(product_id, batch_no)
CUSTOMERS(customer_id PK, name, phone U, email U, registered_on)
EMPLOYEES(employee_id PK, name, role, phone U, hire_date, is_active)
PHARMACISTS(employee_id PK FK->EMPLOYEES, license_no U, qualification)
CASHIERS(employee_id PK FK->EMPLOYEES, shift, counter_no)
SALES(sale_id PK, customer_id FK->CUSTOMERS, employee_id FK->EMPLOYEES, sale_date, payment_method, total_amount)
SALE_ITEMS(sale_id FK->SALES, product_id FK->PRODUCTS, quantity, unit_price)   PK(sale_id, product_id)
SALE_ALLOCATIONS(sale_id, product_id FK->SALE_ITEMS, batch_id FK->STOCK_BATCHES, quantity, cost_price)   PK(sale_id, product_id, batch_id)
STOCK_ALERTS(alert_id PK, alert_type, product_id FK->PRODUCTS, batch_id FK->STOCK_BATCHES, message, created_at)
AUDIT_LOG(log_id PK, table_name, record_id, action, old_value, new_value, changed_at, changed_by)`, 14));
add({ landscapeFigure: true });
add(H2("5.3 Data dictionary"),
  P("Generated from the live database (information_schema). Types shown as stored in MariaDB 10.11; MySQL 8 shows the same types without display widths."));
for (const t of DICT) {
  add(H3(`${t.table}  (${t.rowcount} rows)`), P(t.purpose, { run: { size: 19 }, after: 60 }),
    table(["Column", "Type", "Null", "Constraints", "Description"],
      t.columns.map((c) => [c.column, tidyType(c.type), c.nullable === "YES" ? "yes" : "no", c.constraints.replace(/CHECK /g, "CHECK ").replace(/ -> /g, " > "), c.description]),
      [1.7, 1.5, 0.5, 3.0, 3.3], { size: 15 }), gap(100));
}

// ------------------------------------------------------------------ 6 NORMALIZATION
add(H1("6  Anomalies, functional dependencies and normalization"));
add(H2("6.1 Starting point: the pharmacy's spreadsheet"),
  P("Before the database, sales were recorded in one big sheet (illustrative rows below). It repeats customer, cashier, product, category and supplier information on every row."),
  table(["SaleID", "Date", "Customer", "Cust. phone", "Cashier", "Product", "Category", "Price", "Qty", "Supplier", "Supplier phone"], [
    ["S101", "2026-10-03", "Amna Mirza", "0301-1112223", "Hina Farooq", "Dettol Antiseptic 250ml", "First Aid & Devices", "330", "1", "Capital Medico Distributors", "051-2271101"],
    ["S101", "2026-10-03", "Amna Mirza", "0301-1112223", "Hina Farooq", "Digital Thermometer", "First Aid & Devices", "450", "1", "Rawal Pharma Traders", "051-5566202"],
    ["S102", "2026-10-05", "Amna Mirza", "0301-1112223", "Kamran Ali", "Dettol Antiseptic 250ml", "First Aid & Devices", "330", "2", "Capital Medico Distributors", "051-2271101"],
    ["S103", "2026-10-09", "Noor Chaudhry", "0302-2223334", "Hina Farooq", "Panadol 500mg Tablets", "Analgesics", "35", "10", "Margalla Healthcare Supplies", "051-2822303"]],
    [0.7, 1, 1.1, 1.1, 1, 1.5, 1.2, 0.5, 0.4, 1.4, 1.1], { size: 13 }), gap());
add(H2("6.2 Anomalies"),
  table(["Anomaly", "Example in the sheet", "Consequence"], [
    ["**Update** anomaly", "Dettol's price or Capital Medico's phone number changes", "Every row containing it must be edited; missing one leaves contradictory data"],
    ["**Insertion** anomaly", "A new medicine arrives but nobody has bought it yet; a new customer registers before buying", "There is no row to put them in without inventing a fake sale"],
    ["**Deletion** anomaly", "Noor Chaudhry's only sale (S103) is deleted", "The product Panadol, its category and its supplier vanish from the data as well"]], [1.6, 4, 4.4], { size: 17 }), gap());
add(H2("6.3 Functional dependencies"),
  table(["#", "Functional dependency", "Meaning"], [
    ["FD1", "sale_id -> sale_date, customer_id, employee_id, payment_method, total_amount", "A bill has one date, buyer, seller, payment type and total"],
    ["FD2", "customer_id -> name, phone, registered_on      (phone -> customer_id: candidate key)", "A customer is identified by id or by phone"],
    ["FD3", "employee_id -> name, role, phone, hire_date, is_active", "Employee facts"],
    ["FD4", "product_id -> name, generic_name, category_id, reorder_level, requires_prescription", "Product facts"],
    ["FD5", "category_id -> category_name, description", "Category facts (transitive: product_id -> category_id -> category_name)"],
    ["FD6", "(sale_id, product_id) -> quantity, unit_price", "A bill line: how many, at what price that day"],
    ["FD7", "batch_id -> product_id, po_id, batch_no, received_qty, quantity, expiry_date, cost_price;   (product_id, batch_no) -> batch_id", "Batch facts; the lot number is unique within a product"],
    ["FD8", "po_id -> supplier_id, order_date, status, total_cost", "Purchase-order facts"],
    ["FD9", "supplier_id -> name, phone, address", "Supplier facts (transitive: po_id -> supplier_id -> phone)"],
    ["FD10", "(sale_id, product_id, batch_id) -> quantity, cost_price", "Which batch served which line"]], [0.7, 6, 3.3], { size: 16, mono: [1] }), gap());
add(H2("6.4 Normalization step by step"),
  table(["Form", "Problem removed", "Result"], [
    ["**UNF -> 1NF**", "Repeating groups (several products in one cell) and non-atomic values", "One row per bill line; atomic columns. Key = (sale_id, product_id)."],
    ["**1NF -> 2NF**", "Partial dependencies on part of the composite key: sale_id alone determines date, customer, cashier, payment (FD1); product_id alone determines name, category, price (FD4)", "SALES(sale_id ...), PRODUCTS(product_id ...), SALE_ITEMS(sale_id, product_id, quantity, unit_price)"],
    ["**2NF -> 3NF**", "Transitive dependencies: sale_id -> customer_id -> name/phone (FD2); sale_id -> employee_id -> name (FD3); product_id -> category_id -> category_name (FD5); batch -> po -> supplier -> phone (FD8, FD9)", "CUSTOMERS, EMPLOYEES, CATEGORIES, PURCHASE_ORDERS, SUPPLIERS; batches split into STOCK_BATCHES"],
    ["**3NF -> BCNF**", "Every determinant must be a candidate key", "Checked in 6.5: no table has a determinant that is not a key"]], [1.6, 5, 3.4], { size: 17 }), gap());
add(H2("6.5 BCNF check of the final schema"),
  table(["Relation", "Non-trivial determinants", "Are they (candidate) keys?", "BCNF"], [
    ["categories", "category_id; category_name", "Yes (PK; UNIQUE)", "Yes"],
    ["suppliers", "supplier_id; name; phone", "Yes (PK; UNIQUE)", "Yes"],
    ["products", "product_id; name", "Yes (PK; UNIQUE)", "Yes"],
    ["purchase_orders", "po_id", "Yes (PK)", "Yes"],
    ["stock_batches", "batch_id; (product_id, batch_no)", "Yes (PK; UNIQUE)", "Yes"],
    ["customers", "customer_id; phone; email", "Yes (PK; UNIQUE)", "Yes"],
    ["employees / pharmacists / cashiers", "employee_id; phone; license_no", "Yes", "Yes"],
    ["sales", "sale_id", "Yes (PK)", "Yes"],
    ["sale_items", "(sale_id, product_id)", "Yes (composite PK)", "Yes"],
    ["sale_allocations", "(sale_id, product_id, batch_id)", "Yes (composite PK)", "Yes"]], [2.4, 3.2, 3, 0.9], { size: 17 }), gap());
add(H2("6.6 Controlled denormalization (deliberate exceptions)"),
  P("Three stored columns can be recomputed from other tables, so strictly they are redundant: **sales.total_amount**, **purchase_orders.total_cost** and **stock_batches.quantity** (= received_qty minus allocated units). They were kept on purpose because totals and stock levels are read thousands of times more often than they change, and the redundancy is protected by triggers rather than by hope. Test T11 recomputes all three from the detail rows and finds **0 mismatches**. By contrast, `sale_items.unit_price` is *not* redundant: it is the historical price on the day of sale, which differs from the current `products.unit_price`."));

// ------------------------------------------------------------------ 7 DDL
const ST = J("stats.json");
add(H1("7  Physical implementation: DDL, constraints, indexes"));
add(P(`The script \`mysql/01_schema.sql\` creates the database \`pharmacy_db\` and **${ST.tables} tables** (InnoDB, utf8mb4). It contains **${ST["PRIMARY KEY"]} primary keys, ${ST["FOREIGN KEY"]} foreign keys, ${ST.UNIQUE} unique constraints and ${ST.CHECK} CHECK constraints**, plus NOT NULL and DEFAULT clauses and ${ST.indexes} secondary indexes.`));
add(H2("7.1 Constraints used"),
  table(["Constraint", "Where (examples)", "Purpose"], [
    ["PRIMARY KEY", "every table; composite in sale_items and sale_allocations", "Row identity"],
    ["FOREIGN KEY", "products.category_id, stock_batches.po_id, sales.customer_id ... ON UPDATE CASCADE; ON DELETE RESTRICT (CASCADE for subclass rows, sale lines and allocations; SET NULL for alert batch)", "Referential integrity; protects history"],
    ["NOT NULL", "names, prices, quantities, dates", "Mandatory data"],
    ["UNIQUE", "product name, supplier phone, customer phone/email, licence no, (product_id, batch_no)", "No duplicates"],
    ["CHECK", "unit_price >= 0, quantity > 0, quantity <= received_qty, counter_no BETWEEN 1 AND 6, phone REGEXP '^[0-9]{3,4}-[0-9]{7}$'", "Domain rules"],
    ["DEFAULT", "reorder_level 20, status 'Pending', payment_method 'Cash', order_date CURRENT_DATE, sale_date CURRENT_TIMESTAMP", "Sensible values"],
    ["ENUM", "status, role, shift, payment_method, alert_type", "Closed value lists"]], [1.7, 5.3, 3], { size: 16 }), gap());
add(H2("7.2 Indexes"),
  table(["Index", "Columns", "Used by"], [
    ["idx_batches_fefo", "stock_batches (product_id, expiry_date)", "FEFO allocation in the sale trigger; stock views"],
    ["idx_batches_expiry", "stock_batches (expiry_date)", "Near-expiry and expired views"],
    ["idx_sales_date", "sales (sale_date)", "Daily/monthly reports (range scans)"],
    ["idx_sales_customer / _employee", "sales (customer_id) / (employee_id)", "Customer history, staff performance"],
    ["idx_items_product", "sale_items (product_id)", "Top sellers, profit per product"],
    ["idx_products_category / idx_po_supplier", "FK columns", "Join speed"]], [2.6, 3.8, 3.6], { size: 17 }), gap());
const dml = DML.filter((e) => !/^USE /.test(e.sql));
function groupEntries(prefixRe) {
  const groups = []; let cur = null;
  for (const e of dml) {
    const m = e.sql.match(/^SELECT '((?:D|DDL)\d+)\s+(.*)' AS step/s);
    if (m) { cur = { id: m[1], title: m[2].replace(/''/g, "'"), entries: [] }; groups.push(cur); continue; }
    if (/^SELECT '(trigger|ROLLBACK|DDL demo)/.test(e.sql) || /AS note$/.test(e.sql)) { if (cur && /ROLLBACK done/.test(e.sql)) cur.entries.push({ ...e, sql: "-- (rolled back)" }); continue; }
    if (cur) cur.entries.push(e);
  }
  return groups.filter((g) => prefixRe.test(g.id));
}
function showEntries(entries, rows = 6) {
  const out = [];
  for (const e of entries) {
    if (e.sql === "-- (rolled back)") continue;
    out.push(...code(e.sql, 15));
    if (e.error) out.push(new Paragraph({ children: [new TextRun({ text: e.error, color: "C00000", size: 17, font: FONT })], spacing: { after: 120 } }));
    else if (e.results.length) e.results.forEach((r) => out.push(...resultTable(r, rows)));
    else if (e.info && !/^OK, 0 row/.test(e.info) || /DELETE|UPDATE|INSERT/.test(e.sql)) out.push(new Paragraph({ children: [new TextRun({ text: e.info, italics: true, size: 16, color: "666666", font: FONT })], spacing: { after: 100 } }));
  }
  return out;
}
add(H2("7.3 DDL in action (Week 8 and sub-queries in DDL, Week 13)"),
  P("Besides CREATE TABLE, the demo script exercises ALTER TABLE (ADD/MODIFY/RENAME COLUMN, ADD/DROP CONSTRAINT), CREATE INDEX / DROP INDEX, CREATE TABLE ... AS SELECT, CREATE VIEW over a sub-query, RENAME TABLE, TRUNCATE and DROP. All temporary objects are dropped at the end."));
for (const g of groupEntries(/^DDL/)) add(H3(`${g.id}  ${g.title}`), ...showEntries(g.entries, 5));

// ------------------------------------------------------------------ 8 DML
add(H1("8  Data manipulation: DML and transactions"));
add(P("The sample data (file 03) is loaded with ordinary INSERT statements in **date order**: purchase orders and sales are interleaved exactly as they would happen. The sale rows are inserted into `sales` and `sale_items` only - the triggers create the allocations, reduce the stock and calculate the totals, so loading the data is itself a test of the triggers (zero rejected rows). The generator (`tools/generate_data.py`) uses a fixed random seed, so everybody gets the same 30 purchase orders, 52 batches and 56 sales."));
add(P("`mysql/05_dml_ddl_demo.sql` (Part 1) runs inside one transaction and ends with ROLLBACK, so the sample data stays untouched. Output of the real run:"));
for (const g of groupEntries(/^D\d/)) add(H3(`${g.id}  ${g.title}`), ...showEntries(g.entries, 5));

// ------------------------------------------------------------------ 9 QUERIES
add(H1("9  Data retrieval: 34 documented queries"));
add(P("All queries are in `mysql/04_queries.sql`; each block carries its Week/topic tag and, where useful, its relational-algebra expression. They were executed under MySQL-8-style settings (ONLY_FULL_GROUP_BY and strict mode) and the output below is the real result. Long outputs are cut after 8 rows."));
const parts = [["Part A - basic retrieval and multiple clauses (Weeks 3-4)", 1, 16], ["Part B - set operations and division (Week 7)", 17, 20], ["Part C - sub-queries, CTE and window functions (Week 13)", 21, 28], ["Part D - EER, FEFO and business reports", 29, 34]];
for (const [title, a, b] of parts) {
  add(H2(title));
  for (const q of Q.filter((x) => x.id >= a && x.id <= b)) {
    add(H3(`Q${q.id}  ${q.title}`), P(`Topic: ${q.topic}`, { run: { size: 17, color: "666666" }, after: 40, keepNext: true }), ...code(qsql(q), 14));
    if (q.ra) add(P("**Relational algebra:** " + q.ra, { run: { size: 17 }, after: 60 }));
    if (q.error) add(P("ERROR: " + q.error)); else add(...resultTable({ columns: q.columns, rows: q.rows }, 8));
  }
}

// ------------------------------------------------------------------ 10 RA
add(H1("10  Relational algebra"));
add(P("Relational algebra is the theoretical foundation of SQL. The table maps every operator to its SQL form and to the query in this project that uses it."));
add(table(["Operator", "Symbol", "SQL form", "Used in"], [
  ["Selection", "σ", "WHERE / HAVING", "Q2, Q3, Q8"], ["Projection", "π", "SELECT column list, DISTINCT", "Q1, Q17"], ["Natural / theta join", "⋈", "JOIN ... ON", "Q1, Q10, Q11"],
  ["Left outer join", "⟕", "LEFT JOIN", "Q7, Q12, Q13"], ["Grouping / aggregation", "γ", "GROUP BY with SUM, COUNT, AVG", "Q5, Q6, Q10"], ["Sorting", "τ", "ORDER BY", "Q6"],
  ["Union", "∪", "UNION", "Q17"], ["Intersection", "∩", "INTERSECT", "Q18"], ["Difference", "−", "EXCEPT / LEFT JOIN ... IS NULL / NOT EXISTS", "Q13, Q19"],
  ["Division", "÷", "double NOT EXISTS", "Q20"], ["Rename", "ρ", "AS (aliases)", "all"]], [2.4, 0.9, 4.2, 2], { size: 17 }), gap());
add(H2("10.1 Worked example - division (Q20)"),
  P("**Question:** which customers bought *every* product of the category First Aid & Devices (Dettol, Band-Aid, Thermometer)?"),
  ...code("BOUGHT   = π customer_id, product_id (Sales ⋈ Sale_Items)\nREQUIRED = π product_id (σ category_name='First Aid & Devices' (Products ⋈ Categories))\nANSWER   = BOUGHT ÷ REQUIRED   then   ⋈ Customers to get the names", 15),
  P("A customer qualifies when no required product exists that the customer did not buy - the double NOT EXISTS in Q20. The result contains the customers 5 and 9, whose bills were planted in the sample data for this demonstration, plus one customer who qualified by chance."),
  H2("10.2 Worked example - difference (Q13) and an equivalent tree"),
  ...code("π customer_id,name (Customers)  −  π customer_id,name (Customers ⋈ Sales)\n\nOptimised form chosen by MySQL:  Customers ⟕ Sales  followed by  σ sale_id IS NULL", 15));

// ------------------------------------------------------------------ 11 PROGRAMMABILITY
add(H1("11  Views, functions, stored procedures, triggers and events"));
add(P(`The database contains **${ST.views} views, ${ST.functions} stored function, ${ST.procedures} stored procedures, ${ST.triggers} triggers and ${ST.events} event** (file mysql/02_programmability.sql). Together they move the business rules out of the application and into the database.`));
add(H2("11.1 Views (external schema)"),
  table(["View", "Purpose"], [["v_product_stock", "Sellable and expired quantity per product (LEFT JOIN keeps products with no batches)"], ["v_low_stock", "Proposal view 1: sellable stock below the reorder level"],
    ["v_expiring_30_days", "Proposal view 2: batches expiring within 30 days, days left, value at cost"], ["v_daily_sales_summary", "Proposal view 3: bills, units, revenue and average bill per day"],
    ["v_expired_stock", "Expired batches still on the shelf and the loss at cost"], ["v_sale_details", "Printable bill lines (5-table join)"]], [2.6, 7.4], { size: 17 }), gap());
add(H2("11.2 Triggers (14)"),
  table(["Trigger", "Timing", "What it does"], [
    ["trg_sale_items_bi", "BEFORE INSERT sale_items", "Rejects the line when sellable stock < quantity (BR6)"],
    ["trg_sale_items_ai", "AFTER INSERT sale_items", "FEFO cursor loop: reduces batches, writes sale_allocations, adds to the bill total (BR7, BR9)"],
    ["trg_sale_items_bu / _bd", "BEFORE UPDATE / DELETE", "Blocks edits; on delete returns stock and lowers the total (BR13)"],
    ["trg_sales_bi / trg_sales_bd", "BEFORE INSERT / DELETE sales", "Only active pharmacists/cashiers sell, total starts at 0 (BR10); deleting a bill restores stock"],
    ["trg_batches_bi / _ai / _au / _ad", "stock_batches", "Validate the batch, keep purchase_orders.total_cost correct (BR9, BR12)"],
    ["trg_po_bu", "BEFORE UPDATE purchase_orders", "Received/Cancelled orders cannot change status (BR12)"],
    ["trg_pharmacists_bi / trg_cashiers_bi", "BEFORE INSERT", "EER subclass must match the employee's role (BR11)"],
    ["trg_products_au", "AFTER UPDATE products", "Writes price changes to audit_log (BR15)"]], [3, 2.4, 4.6], { size: 17 }), gap());
add(P("The two central triggers, as implemented:"));
add(...code(block(SQL02, /^CREATE TRIGGER trg_sale_items_bi/), 14), ...code(block(SQL02, /^CREATE TRIGGER trg_sale_items_ai/), 14));
add(H2("11.3 Stored procedures and function"),
  table(["Object", "Purpose"], [
    ["sp_checkout(customer, employee, payment, items JSON, OUT sale_id)", "The checkout TRANSACTION: inserts the bill and lines; the triggers check and deduct stock; any error triggers ROLLBACK + RESIGNAL (BR14)"],
    ["sp_receive_stock(supplier, date, items JSON, OUT po_id)", "Creates a Received purchase order and its batches in one transaction"],
    ["sp_monthly_report(year, month)", "Proposal report: three result sets - summary with profit and margin, top-5 products by profit, revenue by category"],
    ["sp_refresh_stock_alerts()", "Rebuilds today's rows of stock_alerts from the three alert views"],
    ["fn_stock_on_hand(product, date)", "Stored function: sellable quantity of a product on a given day"],
    ["ev_daily_stock_alerts (EVENT)", "Database event: runs sp_refresh_stock_alerts every day at 06:00 (scheduler must be ON)"]], [4, 6], { size: 17 }), gap());
add(...code(block(SQL02, /^CREATE PROCEDURE sp_checkout/), 14));

// ------------------------------------------------------------------ 12 TESTING
add(H1("12  Testing: transactions, triggers and constraints"));
const tests = []; let cur = null;
for (const e of TST) {
  const m = e.sql.match(/^SELECT '(T\w+)\s+(.*)' AS test$/s);
  if (m) { cur = { id: m[1], title: m[2], errors: [], entries: [e] }; tests.push(cur); continue; }
  if (cur) { cur.entries.push(e); if (e.error) cur.errors.push(e.error.replace(/^ERROR \d+: /, "")); }
}
const clean = (s) => s.replace(/`/g, "").replace(/\(conn=\d+\)/, "").slice(0, 150);
const rows = tests.map((t) => {
  const exp = /EXPECTED ERROR/.test(t.title);
  const pass = exp ? t.errors.length > 0 : t.errors.length === 0;
  return [t.id, t.title.replace(/EXPECTED ERRORS?: ?/, ""), exp ? "Rejected" : "Accepted", t.errors.length ? [...new Set(t.errors)].map(clean).join("\n") : "-", pass ? "PASS" : "FAIL"];
});
add(P(`File \`mysql/06_tests_transactions.sql\` contains ${tests.length} test groups. Statements marked EXPECTED ERROR are supposed to fail; the table shows the message the database returned. **Result: ${rows.filter((r) => r[4] === "PASS").length} of ${rows.length} test groups behave as required; ${TST.filter((e) => e.error).length} deliberate violations were all rejected.**`));
add(table(["Test", "Scenario", "Expected", "Database response", "Result"], rows, [0.7, 3.4, 0.9, 4.4, 0.7], { size: 14 }), gap());
const T = (id) => tests.find((t) => t.id === id);
add(H2("12.1 Successful checkout and stock return (T1, T1b)"));
for (const e of T("T1").entries.slice(1)) { if (e.results.length) e.results.forEach((r) => add(...resultTable(r, 6))); }
add(H2("12.2 Atomic rollback (T2, T3)"),
  P("T2 asks for 100 Augmentin although only 3 are sellable; the sale is rejected and the number of bills is unchanged. T3 is stricter: the first line (2 Panadol) is valid but the second fails, and the Panadol stock afterwards is identical to the stock before - proof that the whole transaction was rolled back."));
for (const id of ["T3"]) for (const e of T(id).entries.slice(1)) { if (e.results.length) e.results.forEach((r) => add(...resultTable(r, 6))); else if (e.error) add(P("**" + e.error.replace(/`/g, "") + "**", { run: { size: 17, color: "C00000" } })); }
add(H2("12.3 Purchase order totals by trigger (T9)"));
for (const e of T("T9").entries.slice(1)) { if (e.results.length) e.results.forEach((r) => add(...resultTable(r, 6))); }
add(H2("12.4 Monthly report procedure (T10a)"));
for (const e of T("T10a").entries.slice(1)) { if (e.results.length) e.results.forEach((r) => add(...resultTable(r, 6))); }
add(H2("12.5 Alerts, event and function (T10c-e)"));
for (const id of ["T10c", "T10d", "T10e"]) for (const e of T(id).entries.slice(1)) { if (e.results.length) e.results.forEach((r) => add(...resultTable(r, 8))); }
add(H2("12.6 Consistency audit (T11)"),
  P("Every figure maintained by a trigger is recomputed from the detail rows. All four checks return 0 mismatches:"));
for (const e of T("T11").entries.slice(1)) { if (e.results.length) e.results.forEach((r) => add(...resultTable(r, 2))); }
add(H2("12.7 ACID and concurrency"),
  table(["Property", "How the project provides it"], [
    ["Atomicity", "sp_checkout / sp_receive_stock wrap all changes in START TRANSACTION ... COMMIT with an EXIT HANDLER that ROLLBACKs (T2, T3)"],
    ["Consistency", "Constraints and triggers move the database only between valid states (T7, T8, T11)"],
    ["Isolation", "InnoDB REPEATABLE READ + row locks; the FEFO cursor uses SELECT ... FOR UPDATE so that two cashiers selling the same medicine at once should not both take the last units (reasoned, not load-tested)"],
    ["Durability", "InnoDB redo log; committed bills survive a crash"]], [1.8, 8.2], { size: 17 }), gap());

// ------------------------------------------------------------------ 13 NOSQL
add(H1("13  SQL versus NoSQL"));
add(P("To compare paradigms, the same data was exported (`nosql/export_to_json.py`) as MongoDB-style documents: one **sales** document per bill with the customer, employee, items and the batches used embedded inside it; one **products** document with its batches embedded; and a small **customers** collection. A bill that needed two batches (sale 40) looks like this:"));
const sale40 = JSON.parse(read("nosql/sales.json")).find((s) => s._id === 40);
add(...code(JSON.stringify(sale40, (k, v) => v, 1).split("\n").slice(0, 46).join("\n") + "\n ...", 13));
add(H2("13.1 The same reports as aggregation pipelines"),
  P("`nosql/mongo_queries.js` holds the pipelines (generated from `nosql/build_mongo_queries.py`). Because no MongoDB server was available in the development environment, they were executed on **mongomock**, an in-memory emulator of MongoDB's aggregation engine, and compared with the SQL results:"),
  table(["Report", "SQL query", "Documents vs SQL", "Check"], NOS.map((n) => {
    const id = n.title.match(/^(Q\d+)/)[1];
    return [n.title.replace(/^Q\d+\s+/, "").replace(/\s+\(SQL:.*$/, ""), id, `${n.mongo_rows} rows vs ${n.sql_rows} rows`, n.ok === true ? "identical" : (n.python_logic_matches_sql ? "logic verified in Python; pipeline to run on real MongoDB" : "not verified")];
  }), [3.5, 1, 2, 3.5], { size: 17 }), gap(),
  P("**Honest limitation:** an emulator is not a server. The pipelines use standard operators, but `mongo_queries.js` should be run once on a real MongoDB instance (mongosh) to confirm the output there."));
add(H2("13.2 Comparison"),
  table(["Aspect", "SQL (MySQL / PostgreSQL)", "NoSQL document store (MongoDB)", "Pharmacy verdict"], [
    ["Data model", "Tables, rows, fixed schema", "JSON documents, flexible schema", "Data is highly structured -> SQL"],
    ["Relationships", "Foreign keys + JOIN; each fact stored once", "Embedding (fast reads, duplication) or manual references", "Product/price/customer data is shared by many bills -> SQL"],
    ["Integrity", "PK, FK, CHECK, UNIQUE, triggers enforced by the engine", "Optional JSON-schema validation; no foreign keys", "Stock and expiry rules need hard guarantees -> SQL"],
    ["Transactions", "Full ACID across any tables (checkout)", "Single-document atomicity; multi-document transactions need a replica set", "Sale + stock update must be atomic -> SQL"],
    ["Querying / reporting", "SQL, joins, window functions, ad-hoc analysis", "Aggregation pipeline; cross-collection joins ($lookup) are awkward", "Profit and stock reports -> SQL"],
    ["Reads of one whole bill", "5-table join (v_sale_details)", "One findOne() - no join", "NoSQL wins for printing/archiving a bill"],
    ["Schema change", "ALTER TABLE, migration", "Add a field to new documents", "NoSQL easier; rarely needed here"],
    ["Scaling", "Vertical; replicas; sharding is harder", "Horizontal sharding built in", "One pharmacy does not need it"],
    ["Duplicates / update anomalies", "Avoided by normalization", "Embedded customer names/prices copy data: a rename must touch every bill", "SQL"]], [1.6, 2.8, 2.9, 2.7], { size: 15 }), gap(),
  P("**Conclusion:** the transactional core (stock, batches, billing) belongs in a relational database. A document store would be a reasonable *additional* read-optimised copy - for example an archive of finished bills or a customer-facing receipt service - but not the system of record."));

// ------------------------------------------------------------------ 14 POSTGRES
add(H1("14  PostgreSQL implementation"));
add(P("The complete system was ported to **PostgreSQL 16** (`postgres/pg_01_schema.sql` ... `pg_05_tests.sql`): same 14 tables, same constraints, same views, same business rules, same sample data and the same tests. Both implementations were run and compared automatically."));
const norm = (rs) => rs.map((r) => r.map((x) => typeof x === "number" ? Math.round(x * 100) / 100 : (typeof x === "boolean" ? +x : x)).join("|")).sort();
const same = []; for (let i = 1; i <= 34; i++) { const a = Q.find((q) => q.id === i), b = PGQ.find((q) => q.id === i); if (JSON.stringify(norm(a.rows)) === JSON.stringify(norm(b.rows))) same.push(i); }
const pgErr = PGT.filter((e) => e.error).length;
add(table(["Cross-check", "Result"], [
  ["Queries Q1-Q34 on MySQL (MariaDB) vs PostgreSQL, compared row by row", `${same.length} of 34 return identical results`],
  ["Negative tests (violations that must be rejected)", `MySQL ${TST.filter((e) => e.error).length}, PostgreSQL ${pgErr} rejected - same list of tests`],
  ["Consistency audit after loading and testing", "0 mismatches on both"]], [6, 4], { size: 18 }), gap());
add(H2("14.1 What changes between MySQL and PostgreSQL"),
  table(["Topic", "MySQL", "PostgreSQL"], [
    ["Auto numbering", "AUTO_INCREMENT", "GENERATED BY DEFAULT AS IDENTITY (+ setval after explicit-id loads)"],
    ["Fixed value lists", "ENUM(...) in the column", "CREATE TYPE ... AS ENUM, reusable"],
    ["Types", "DATETIME, TINYINT, UNSIGNED", "TIMESTAMP, SMALLINT, no UNSIGNED"],
    ["Regex check", "phone REGEXP '...'", "phone ~ '...'"],
    ["Triggers", "Body written inline in CREATE TRIGGER", "A trigger function (RETURNS trigger) + CREATE TRIGGER ... EXECUTE FUNCTION"],
    ["Raising errors", "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT", "RAISE EXCEPTION"],
    ["Stored procedure with transaction", "PROCEDURE with OUT parameter; handler does ROLLBACK", "A function is already one atomic statement - any exception undoes all of it; PROCEDURE only for CALL tasks"],
    ["JSON input", "JSON_TABLE(p_items, '$[*]' COLUMNS ...)", "jsonb_to_recordset(p_items) AS x(col type ...)"],
    ["Several result sets", "One procedure returns 3 result sets", "Table-returning functions (fn_monthly_report, fn_monthly_top_products)"],
    ["Scheduled jobs", "CREATE EVENT", "No built-in scheduler: pg_cron extension or an OS cron job"],
    ["Cascades and triggers", "Row triggers do NOT fire on FOREIGN KEY cascades, so a separate trigger on sales restores stock", "Row triggers DO fire on cascades, so the sale_items delete trigger alone is correct (a second one would restore stock twice)"],
    ["Errors inside a transaction", "Statement fails, transaction continues", "Transaction is aborted until ROLLBACK or ROLLBACK TO SAVEPOINT (tests use savepoints)"],
    ["DDL and transactions", "DDL commits implicitly", "DDL is transactional"],
    ["Rollup / counting booleans", "WITH ROLLUP; SUM(status='Received')", "ROLLUP(...); COUNT(*) FILTER (WHERE ...)"],
    ["Date arithmetic", "DATE_ADD, DATEDIFF, DATE_FORMAT", "date + 30, date - date, to_char"]], [2.2, 3.8, 4.2], { size: 15 }), gap());
add(H2("14.2 PostgreSQL-only features used (Week 16)"),
  table(["Feature", "Where", "Benefit"], [
    ["Generated column", "sale_items.line_total = quantity * unit_price", "No calculation in queries; always correct"],
    ["Partial index", "idx_batches_fefo ... WHERE quantity > 0", "Smaller index containing only sellable batches"],
    ["Expression index", "idx_sales_day ON ((sale_date::date))", "Fast per-day reports"],
    ["GIN full-text index", "idx_products_fts, query Q37", "Search medicines by name or ingredient"],
    ["Materialized view", "mv_monthly_sales, Q39 / Q43", "Stored report refreshed on demand"],
    ["JSONB", "Q38 builds each bill as a JSON document", "Bridges the SQL and document models"],
    ["DISTINCT ON, FILTER, LATERAL, string_agg", "Q35, Q36, Q42, Q40", "Compact reports"],
    ["RETURNING, writable CTE", "tests T11", "See changed rows without a second query"]], [2.6, 4, 3.4], { size: 16 }), gap());
for (const id of [35, 36, 37, 39, 40, 41, 43]) {
  const q = PGQ.find((x) => x.id === id);
  add(H3(`Q${q.id}  ${q.title}`), ...code(q.sql, 14), ...resultTable({ columns: q.columns, rows: q.rows }, 5));
}
{ const q = PGQ.find((x) => x.id === 38);
  add(H3(`Q38  ${q.title}`), ...code(q.sql, 13), ...code(JSON.stringify(JSON.parse(q.rows[1][0]), null, 1), 13)); }
add(H2("14.3 PostgreSQL test run"),
  P(`The test file runs the same scenarios (checkout, rollbacks, constraints, triggers, reports) and the consistency audit; ${pgErr} deliberate violations are rejected. A selection of the real messages:`));
const sel = PGT.filter((e) => e.error).slice(0, 12).map((e) => [e.sql.replace(/\s+/g, " ").slice(0, 70), e.error.replace("ERROR: ", "").slice(0, 100)]);
add(table(["Statement", "PostgreSQL response"], sel, [4, 6], { size: 14 }), gap());

// ------------------------------------------------------------------ 15 PYTHON
add(H1("15  Python menu interface"));
add(P("`python_app/pharmacy_cli.py` is a thin text menu (about 200 lines) using mysql-connector-python with a limited database account (SELECT/INSERT/UPDATE/DELETE/EXECUTE only). It contains **no business logic**: sales go through `sp_checkout`, deliveries through `sp_receive_stock`, reports through views and `sp_monthly_report`, so a rejected sale is explained by the database's own message. Menu: stock search, low stock, expiry report, new sale, receive stock, daily sales, monthly report, top sellers, customer history."));
const cli = fs.readFileSync(path.join(DOCS, "cli_session.txt"), "utf8").split("\n").filter((l) => !/^===== PHARMACY|^ [0-9]\. /.test(l) && l.trim() !== "");
add(P("Real session (low-stock list, a successful sale, a rejected sale and the October report):", { keepNext: true }), ...code(cli.slice(0, 58).join("\n").replace(/Choose: /g, "\n> "), 12));

// ------------------------------------------------------------------ 16 CONCLUSION
add(H1("16  Conclusion, limitations and future work"));
add(H2("16.1 What was delivered"),
  ...bullets(["A normalized (3NF/BCNF) 14-table pharmacy database with all constraints promised in the proposal.", "Batch-wise stock with First-Expiry-First-Out deduction, expiry control and exact profit.",
    "34 documented queries, six views, four procedures, one function, 14 triggers and one scheduled event.", "25 negative tests, atomic transactions and a zero-mismatch consistency audit.",
    "A PostgreSQL port, a MongoDB document model and a Python menu application."]));
add(H2("16.2 Limitations"),
  ...bullets(["Purchase orders have no line-item table; a Pending order therefore has no lines and a total of 0 until stock is received. A `purchase_order_items` table would fix this.",
    "No returns/refunds, discounts, taxes or prescriptions table (prescription-only items are flagged but not linked to a doctor/patient record).",
    "Prices are per unit; strips/packs and unit conversion are not modelled.",
    "Concurrency control relies on InnoDB locking and was reasoned about but not load-tested with parallel clients.",
    "The development environment ran MariaDB 10.11 (MySQL-compatible) and PostgreSQL 16; the scripts use MySQL 8 syntax but were not executed on Oracle MySQL itself. INTERSECT/EXCEPT need MySQL 8.0.31+.",
    "The MongoDB pipelines were verified on an emulator only."]));
add(H2("16.3 Future work"),
  ...bullets(["purchase_order_items, returns, discounts and a prescriptions/doctor table.", "Role-based security with GRANT per role (manager, pharmacist, cashier) and database views as the only access path.", "A web front end (for example Flask) calling the same procedures.", "Partitioning of sales by month and a data warehouse for multi-year analysis."]));

// ------------------------------------------------------------------ APPENDICES
add(H1("Appendix A  Topic coverage matrix"));
add(table(["Week", "Topic", "Where it is used in this project"], [
  ["1", "Introduction to databases", "Ch. 1-2: database vs spreadsheet, users, DBMS components"],
  ["2", "Database system concepts and architecture", "Ch. 2: three-schema architecture, client-server, InnoDB; views = external level"],
  ["3", "Data Retrieval Language (DRL)", "Ch. 9 Q1-Q16: SELECT, joins, aggregates"],
  ["4", "Multiple clauses of DRL", "Q2-Q12, Q16: WHERE, BETWEEN, LIKE, IN, GROUP BY, HAVING, ORDER BY, LIMIT, CASE, ROLLUP"],
  ["5", "Database design", "Ch. 3-5: requirements, ER model, mapping to relations (Assignment 1)"],
  ["6", "Enhanced ER modelling", "Ch. 4: specialization (disjoint, partial), associative entity, derived attributes"],
  ["7", "Relational algebra", "Ch. 10, RA lines in Ch. 9; Q13, Q17-Q20 (union, intersection, difference, division) (Assignment 2)"],
  ["8", "Data Definition Language", "mysql/01_schema.sql, Ch. 7: CREATE, ALTER, DROP, TRUNCATE, RENAME, constraints, indexes"],
  ["9", "Mid-term", "-"],
  ["10", "Anomalies and functional dependencies", "Ch. 6.2-6.3"],
  ["11", "Normalization", "Ch. 6.4-6.6: UNF to BCNF, controlled denormalization (Assignment 3)"],
  ["12", "Data Manipulation Language", "03_sample_data.sql, 05_dml_ddl_demo.sql, Ch. 8: INSERT, UPDATE, DELETE, INSERT...SELECT, upsert, transactions, savepoints"],
  ["13", "Sub-queries (DRL, DML and DDL)", "DRL: Q9, Q21-Q26, Q28, Q30; DML: D3-D6; DDL: CREATE TABLE AS SELECT, view over a sub-query"],
  ["14", "Stored procedures and triggers (event management)", "Ch. 11-12: 4 procedures, 1 function, 14 triggers, 1 EVENT, 25 negative tests"],
  ["15", "Comparison of NoSQL and SQL", "Ch. 13, nosql/ folder: document model, pipelines, comparison"],
  ["16", "Utilization of PostgreSQL", "Ch. 14, postgres/ folder: full port, PL/pgSQL, PostgreSQL-only features"]], [0.7, 3.3, 6], { size: 16 }), gap());

add(H1("Appendix B  Files, environment and how to run"));
add(table(["File", "Content"], [
  ["mysql/00_app_user.sql", "Limited account for the Python program (optional)"], ["mysql/01_schema.sql", "Database, 14 tables, constraints, indexes, ALTER demo"],
  ["mysql/02_programmability.sql", "Views, function, procedures, 14 triggers, event"], ["mysql/03_sample_data.sql", "All sample data (generated, deterministic)"],
  ["mysql/04_queries.sql", "34 queries with topic tags and relational algebra"], ["mysql/05_dml_ddl_demo.sql", "DML (rolled back) and DDL demonstrations"],
  ["mysql/06_tests_transactions.sql", "Transaction, trigger and constraint tests"], ["postgres/pg_01 ... pg_05", "PostgreSQL schema, programmability, data, queries (43), tests"],
  ["nosql/", "Exported JSON documents, mongo_queries.js, export and verification scripts"], ["python_app/pharmacy_cli.py", "Menu application"],
  ["tools/", "Data generator, runners, diagram and report builders, build_all.sh"], ["docs/", "Diagrams, data dictionary, captured outputs (query_results.json, test_output.txt ...)"]], [3.4, 6.6], { size: 16, mono: [0] }), gap());
add(H2("How to run (MySQL Workbench or command line)"),
  ...numbered(["Open mysql/01_schema.sql in MySQL Workbench and execute it (creates pharmacy_db).", "Execute 02_programmability.sql (Workbench handles the DELIMITER lines), then 03_sample_data.sql.",
    "Execute 04_queries.sql query by query (Ctrl+Enter), then 05 and 06 to see the demos and tests.", "Command line alternative:  mysql -u root -p < mysql/01_schema.sql   and so on in order.",
    "To enable the daily event:  SET GLOBAL event_scheduler = ON;", "PostgreSQL:  psql -U postgres -f postgres/pg_01_schema.sql  then pg_02, pg_03, pg_04, pg_05.",
    "Python menu:  pip install mysql-connector-python, run mysql/00_app_user.sql, then python python_app/pharmacy_cli.py"], "num2"));
add(P("**Environment used to produce the outputs in this report:** MariaDB 10.11 (MySQL-compatible, run with MySQL 8-style ONLY_FULL_GROUP_BY and strict SQL mode), PostgreSQL 16, Python 3.12, session clock fixed to 18 November 2026 for the date-dependent views. If the scripts are run on another day, the near-expiry and expired lists will change accordingly."));

add(H1("Appendix C  Viva preparation"));
add(table(["Question", "Short answer"], [
  ["Why is stock stored per batch?", "Expiry belongs to a batch, not to a product; FEFO needs batch-level quantities."],
  ["How do you stop overselling?", "BEFORE INSERT trigger on sale_items compares the quantity with fn_stock_on_hand; the whole checkout is one transaction."],
  ["Is total_amount a normalization violation?", "It is derived data kept deliberately for speed; triggers maintain it and test T11 proves zero mismatches."],
  ["Why is unit_price in sale_items?", "It is the historical price on the sale date; products.unit_price may change later."],
  ["Which relational-algebra operator is NOT EXISTS used for?", "Difference/anti-join; the double NOT EXISTS implements division (Q20)."],
  ["Difference between a trigger and a procedure?", "A trigger fires automatically on INSERT/UPDATE/DELETE; a procedure runs only when CALLed."],
  ["Why does PostgreSQL need one trigger fewer?", "PostgreSQL fires row triggers on FK cascades; MySQL does not."],
  ["When would you choose MongoDB?", "For flexible, read-heavy, self-contained documents such as archived receipts - not for stock and billing integrity."]], [4, 6], { size: 17 }));

// ------------------------------------------------------------------ ASSEMBLE
const portrait = { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 } } };
const landscape = { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1000, right: 1000, bottom: 1000, left: 1000 } } };
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Pharmacy Inventory & Sales Management System  |  CS220  |  Page ", size: 16, color: "777777", font: FONT }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777", font: FONT })] })] });
const sections = []; let buf = [];
for (const c of children) {
  if (c && c.landscapeFigure) {
    sections.push({ properties: portrait, footers: { default: footer }, children: buf }); buf = [];
    sections.push({ properties: landscape, footers: { default: footer }, children: [
      new Paragraph({ children: [new TextRun({ text: "Figure 5.1  Relational schema (generated from the live database)", bold: true, size: 22, font: FONT })], spacing: { after: 80 } }),
      img(path.join(DOCS, "relational_schema.png"), 720, 605),
      caption("Blue = core tables, green = EER subclasses, grey = supporting tables; arrows point from the parent key to the foreign key (crow's foot at the 'many' side).")] });
  } else buf.push(c);
}
sections.push({ properties: portrait, footers: { default: footer }, children: buf });
const doc = new Document({
  creator: "CS220 project team", title: "Pharmacy Inventory & Sales Management System - Final Report",
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 34, bold: true, font: FONT, color: "1F3864" }, paragraph: { spacing: { before: 120, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: FONT, color: "2E5E9E" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, font: FONT, color: "404040" }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2, keepNext: true } }] },
  numbering: { config: ["bul", "num", "num2"].map((r) => ({ reference: r, levels: [{ level: 0, format: r === "bul" ? LevelFormat.BULLET : LevelFormat.DECIMAL, text: r === "bul" ? "•" : "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] })) },
  sections });
Packer.toBuffer(doc).then((b) => { const out = path.join(DOCS, "Pharmacy_DB_Final_Project_Report.docx"); fs.writeFileSync(out, b); console.log("report written", (b.length / 1024).toFixed(0) + " KB"); });
