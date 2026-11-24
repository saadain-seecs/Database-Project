-- =====================================================================
--  Pharmacy Inventory & Sales Management System
--  File 4 of 6 : DATA RETRIEVAL (DRL) - 34 queries
--  Weeks 3, 4, 7, 13 : SELECT, multiple clauses, relational algebra, sub-queries
--  Format of every block:  -- Q<n> | <topic> | <title>   (+ optional -- RA: ...)
--  Needs MySQL 8.0.31+ for INTERSECT / EXCEPT (Q18, Q19).  Equivalent
--  EXISTS / NOT EXISTS versions are shown in comments for older servers.
-- =====================================================================
USE pharmacy_db;

-- ---------------------------------------------------------------------
--  PART A : basic retrieval (Weeks 3-4)
-- ---------------------------------------------------------------------

-- Q1 | DRL - JOIN, ORDER BY | Product catalogue with its category
-- RA: π product_id, name, category_name, unit_price, requires_prescription (Products ⋈ Categories)
SELECT p.product_id, p.name, c.category_name, p.unit_price, p.requires_prescription
FROM   products p
JOIN   categories c ON c.category_id = p.category_id
ORDER BY c.category_name, p.name;

-- Q2 | DRL - WHERE, BETWEEN, LIKE, IN | Cheap over-the-counter medicines (Rs 25-150)
-- RA: π product_id, name, generic_name, unit_price (σ requires_prescription=false ∧ unit_price between 25 and 150 ∧ (name like 'P%' ∨ generic_name ∈ {Ibuprofen, Aspirin, Cetirizine}) (Products))
SELECT product_id, name, generic_name, unit_price
FROM   products
WHERE  requires_prescription = FALSE
  AND  unit_price BETWEEN 25 AND 150
  AND  (name LIKE 'P%' OR generic_name IN ('Ibuprofen', 'Aspirin', 'Cetirizine'))
ORDER BY unit_price DESC, name;

-- Q3 | DRL - IN, BETWEEN, ORDER BY | October bills above Rs 1,000 paid by card or mobile wallet
-- RA: σ payment_method ∈ {Card, Mobile Wallet} ∧ total_amount > 1000 ∧ sale_date in Oct-2026 (Sales)
SELECT sale_id, customer_id, sale_date, payment_method, total_amount
FROM   sales
WHERE  payment_method IN ('Card', 'Mobile Wallet')
  AND  total_amount > 1000
  AND  sale_date BETWEEN '2026-10-01 00:00:00' AND '2026-10-31 23:59:59'
ORDER BY total_amount DESC;

-- Q4 | DRL - GROUP BY, VIEW | Total sales per day (proposal report)
-- RA: γ DATE(sale_date); COUNT(sale_id), SUM(quantity*unit_price) (Sales ⋈ Sale_Items)
SELECT sale_day, bills, units_sold, revenue, avg_bill
FROM   v_daily_sales_summary
ORDER BY sale_day;

-- Q5 | DRL - GROUP BY, aggregate functions | Total sales per month (proposal report)
-- RA: γ month(sale_date); COUNT(DISTINCT sale_id), SUM(quantity), SUM(quantity*unit_price) (Sales ⋈ Sale_Items)
SELECT DATE_FORMAT(s.sale_date, '%Y-%m')      AS sale_month,
       COUNT(DISTINCT s.sale_id)              AS bills,
       SUM(si.quantity)                       AS units_sold,
       SUM(si.quantity * si.unit_price)       AS revenue
FROM   sales s
JOIN   sale_items si ON si.sale_id = s.sale_id
GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
ORDER BY sale_month;

-- Q6 | DRL - GROUP BY, ORDER BY, LIMIT | Top 10 best-selling medicines (proposal report)
-- RA: τ units desc (γ product_id, name; SUM(quantity) → units (Sale_Items ⋈ Products))   [top 10]
SELECT p.product_id, p.name, SUM(si.quantity) AS units_sold,
       SUM(si.quantity * si.unit_price)       AS revenue
FROM   sale_items si
JOIN   products p ON p.product_id = si.product_id
GROUP BY p.product_id, p.name
ORDER BY units_sold DESC, revenue DESC
LIMIT 10;

-- Q7 | DRL - LEFT JOIN, GROUP BY | Supplier-wise purchase cost, received orders only (proposal report)
-- RA: γ supplier; COUNT(po_id), SUM(total_cost) (Suppliers ⟕ σ status='Received' (Purchase_Orders))
SELECT s.supplier_id, s.name AS supplier,
       COUNT(po.po_id)                  AS received_orders,
       COALESCE(SUM(po.total_cost), 0)  AS total_purchase_cost
FROM   suppliers s
LEFT JOIN purchase_orders po ON po.supplier_id = s.supplier_id AND po.status = 'Received'
GROUP BY s.supplier_id, s.name
ORDER BY total_purchase_cost DESC;

-- Q8 | DRL - GROUP BY ... HAVING | Customers with the highest spending (proposal report)
-- RA: σ spent >= 2000 (γ customer; COUNT(sale_id), SUM(total_amount) → spent (Customers ⋈ Sales))
SELECT c.customer_id, c.name, COUNT(s.sale_id) AS bills, SUM(s.total_amount) AS total_spent
FROM   customers c
JOIN   sales s ON s.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(s.total_amount) >= 2000
ORDER BY total_spent DESC
LIMIT 10;

-- Q9 | Sub-query (correlated, scalar) | Products below their reorder level (proposal report)
-- RA: π product_id, name, reorder_level (σ on_hand < reorder_level (Products))   where on_hand = Σ quantity of unexpired batches
SELECT p.product_id, p.name, p.reorder_level,
       (SELECT COALESCE(SUM(b.quantity), 0)
        FROM   stock_batches b
        WHERE  b.product_id = p.product_id AND b.expiry_date >= CURRENT_DATE) AS on_hand
FROM   products p
WHERE  (SELECT COALESCE(SUM(b.quantity), 0)
        FROM   stock_batches b
        WHERE  b.product_id = p.product_id AND b.expiry_date >= CURRENT_DATE) < p.reorder_level
ORDER BY p.name;

-- Q10 | DRL - multi-table JOIN, aggregates | Profit per product (proposal report)
-- RA: γ product; SUM(qty), SUM(qty*price), SUM(qty*cost), SUM(qty*(price-cost)) (Sale_Allocations ⋈ Sale_Items ⋈ Products)
SELECT p.product_id, p.name,
       SUM(a.quantity)                                    AS units_sold,
       SUM(a.quantity * si.unit_price)                    AS revenue,
       SUM(a.quantity * a.cost_price)                     AS cost,
       SUM(a.quantity * (si.unit_price - a.cost_price))   AS profit
FROM   sale_allocations a
JOIN   sale_items si ON si.sale_id = a.sale_id AND si.product_id = a.product_id
JOIN   products p    ON p.product_id = a.product_id
GROUP BY p.product_id, p.name
ORDER BY profit DESC;

-- Q11 | DRL - 4-table JOIN, GROUP BY ... WITH ROLLUP | Revenue per category with a grand total
-- RA: γ category; SUM(quantity), SUM(quantity*unit_price) (Sale_Items ⋈ Products ⋈ Categories)
SELECT COALESCE(c.category_name, '** ALL CATEGORIES **') AS category,
       SUM(si.quantity)                                  AS units_sold,
       SUM(si.quantity * si.unit_price)                  AS revenue
FROM   sale_items si
JOIN   products p    ON p.product_id  = si.product_id
JOIN   categories c  ON c.category_id = p.category_id
GROUP BY c.category_name WITH ROLLUP;

-- Q12 | DRL - LEFT OUTER JOIN | Staff performance (employees with no sales are kept)
-- RA: γ employee; COUNT(sale_id), SUM(total_amount) (Employees ⟕ Sales)
SELECT e.employee_id, e.name, e.role,
       COUNT(s.sale_id)                 AS bills,
       COALESCE(SUM(s.total_amount), 0) AS revenue
FROM   employees e
LEFT JOIN sales s ON s.employee_id = e.employee_id
GROUP BY e.employee_id, e.name, e.role
ORDER BY revenue DESC, e.employee_id;

-- Q13 | RA difference via LEFT JOIN ... IS NULL | Registered customers who never bought anything
-- RA: π customer_id, name (Customers) − π customer_id, name (Customers ⋈ Sales)
SELECT c.customer_id, c.name, c.phone, c.registered_on
FROM   customers c
LEFT JOIN sales s ON s.customer_id = c.customer_id
WHERE  s.sale_id IS NULL
ORDER BY c.customer_id;

-- Q14 | VIEW | Batches expiring within 30 days (proposal view)
-- RA: π ... (σ quantity>0 ∧ expiry_date between today and today+30 (Stock_Batches ⋈ Products))
SELECT batch_id, product_name, batch_no, quantity, expiry_date, days_left, stock_value_at_cost
FROM   v_expiring_30_days
ORDER BY days_left;

-- Q15 | VIEW | Expired stock still on the shelf, with the loss at cost
SELECT batch_id, product_name, batch_no, quantity, expiry_date, days_expired, loss_at_cost
FROM   v_expired_stock
ORDER BY loss_at_cost DESC;

-- Q16 | DRL - CASE, AVG | Margin band of every product (selling price vs average purchase cost)
SELECT p.product_id, p.name, p.unit_price,
       ROUND(AVG(b.cost_price), 2)                                            AS avg_cost,
       ROUND(100 * (p.unit_price - AVG(b.cost_price)) / p.unit_price, 1)      AS margin_pct,
       CASE WHEN 100 * (p.unit_price - AVG(b.cost_price)) / p.unit_price >= 30 THEN 'High'
            WHEN 100 * (p.unit_price - AVG(b.cost_price)) / p.unit_price >= 24 THEN 'Medium'
            ELSE 'Low' END                                                    AS margin_band
FROM   products p
JOIN   stock_batches b ON b.product_id = p.product_id
GROUP BY p.product_id, p.name, p.unit_price
ORDER BY margin_pct DESC, p.name;

-- ---------------------------------------------------------------------
--  PART B : relational algebra set operations and division (Week 7)
-- ---------------------------------------------------------------------

-- Q17 | RA union (∪) | Customers who bought an antibiotic OR a vitamin/supplement
-- RA: π cid, name (σ cat='Antibiotics' (Customers ⋈ Sales ⋈ Sale_Items ⋈ Products ⋈ Categories)) ∪ π cid, name (σ cat='Vitamins & Supplements' (...))
SELECT c.customer_id, c.name
FROM   customers c JOIN sales s ON s.customer_id = c.customer_id
       JOIN sale_items si ON si.sale_id = s.sale_id
       JOIN products p ON p.product_id = si.product_id
       JOIN categories g ON g.category_id = p.category_id
WHERE  g.category_name = 'Antibiotics'
UNION
SELECT c.customer_id, c.name
FROM   customers c JOIN sales s ON s.customer_id = c.customer_id
       JOIN sale_items si ON si.sale_id = s.sale_id
       JOIN products p ON p.product_id = si.product_id
       JOIN categories g ON g.category_id = p.category_id
WHERE  g.category_name = 'Vitamins & Supplements'
ORDER BY customer_id;

-- Q18 | RA intersection (∩) | Customers who bought BOTH a pain-killer and an antacid/gastro product
-- RA: π cid, name (σ cat='Analgesics & Antipyretics' (...)) ∩ π cid, name (σ cat='Antacids & Gastro' (...))
-- (older MySQL: replace INTERSECT by  WHERE EXISTS (...) AND EXISTS (...) )
SELECT c.customer_id, c.name
FROM   customers c JOIN sales s ON s.customer_id = c.customer_id
       JOIN sale_items si ON si.sale_id = s.sale_id
       JOIN products p ON p.product_id = si.product_id
       JOIN categories g ON g.category_id = p.category_id
WHERE  g.category_name = 'Analgesics & Antipyretics'
INTERSECT
SELECT c.customer_id, c.name
FROM   customers c JOIN sales s ON s.customer_id = c.customer_id
       JOIN sale_items si ON si.sale_id = s.sale_id
       JOIN products p ON p.product_id = si.product_id
       JOIN categories g ON g.category_id = p.category_id
WHERE  g.category_name = 'Antacids & Gastro'
ORDER BY customer_id;

-- Q19 | RA difference (−) | Products that have never been sold
-- RA: π product_id, name (Products) − π product_id, name (Products ⋈ Sale_Items)
-- (older MySQL: use NOT EXISTS / LEFT JOIN ... IS NULL)
SELECT product_id, name FROM products
EXCEPT
SELECT p.product_id, p.name FROM products p JOIN sale_items si ON si.product_id = p.product_id
ORDER BY product_id;

-- Q20 | RA DIVISION (÷) via double NOT EXISTS | Customers who bought EVERY First-Aid & Devices product
-- RA: (π customer_id, product_id (Sales ⋈ Sale_Items)) ÷ (π product_id (σ category_name='First Aid & Devices' (Products ⋈ Categories)))
SELECT c.customer_id, c.name
FROM   customers c
WHERE  NOT EXISTS (
         SELECT 1
         FROM   products p
         JOIN   categories g ON g.category_id = p.category_id
         WHERE  g.category_name = 'First Aid & Devices'
           AND  NOT EXISTS (
                  SELECT 1
                  FROM   sales s
                  JOIN   sale_items si ON si.sale_id = s.sale_id
                  WHERE  s.customer_id = c.customer_id
                    AND  si.product_id = p.product_id))
ORDER BY c.customer_id;

-- ---------------------------------------------------------------------
--  PART C : sub-queries (Week 13) and window functions
-- ---------------------------------------------------------------------

-- Q21 | Sub-query - scalar, uncorrelated | Products priced above the average product price
SELECT product_id, name, unit_price
FROM   products
WHERE  unit_price > (SELECT AVG(unit_price) FROM products)
ORDER BY unit_price DESC;

-- Q22 | Sub-query - correlated | Products dearer than the average of their own category
SELECT p.product_id, p.name, p.unit_price
FROM   products p
WHERE  p.unit_price > (SELECT AVG(p2.unit_price)
                       FROM   products p2
                       WHERE  p2.category_id = p.category_id)
ORDER BY p.category_id, p.unit_price DESC;

-- Q23 | Sub-query - IN | Customers who have bought at least one prescription-only medicine
SELECT customer_id, name
FROM   customers
WHERE  customer_id IN (SELECT s.customer_id
                       FROM   sales s
                       JOIN   sale_items si ON si.sale_id = s.sale_id
                       JOIN   products p    ON p.product_id = si.product_id
                       WHERE  p.requires_prescription = TRUE)
ORDER BY customer_id;

-- Q24 | Sub-query - EXISTS | Suppliers that currently have a Pending purchase order
SELECT s.supplier_id, s.name, s.phone
FROM   suppliers s
WHERE  EXISTS (SELECT 1 FROM purchase_orders po
               WHERE  po.supplier_id = s.supplier_id AND po.status = 'Pending')
ORDER BY s.supplier_id;

-- Q25 | Sub-query - ALL | Products costing more than EVERY antibiotic
SELECT product_id, name, unit_price
FROM   products
WHERE  unit_price > ALL (SELECT p.unit_price
                         FROM   products p JOIN categories c ON c.category_id = p.category_id
                         WHERE  c.category_name = 'Antibiotics')
ORDER BY unit_price DESC;

-- Q26 | Sub-query in HAVING | Staff whose average bill is above the pharmacy-wide average bill
SELECT e.employee_id, e.name, COUNT(*) AS bills, ROUND(AVG(s.total_amount), 2) AS avg_bill
FROM   employees e
JOIN   sales s ON s.employee_id = e.employee_id
GROUP BY e.employee_id, e.name
HAVING AVG(s.total_amount) > (SELECT AVG(total_amount) FROM sales)
ORDER BY avg_bill DESC;

-- Q27 | CTE + window function | Running (cumulative) revenue by day
WITH daily AS (
    SELECT sale_day, revenue FROM v_daily_sales_summary
)
SELECT sale_day, revenue,
       SUM(revenue) OVER (ORDER BY sale_day) AS cumulative_revenue
FROM   daily
ORDER BY sale_day;

-- Q28 | Derived table + RANK() | Best-selling product (by revenue) inside every category
SELECT category_name, product, revenue
FROM  (SELECT c.category_name, p.name AS product,
              SUM(si.quantity * si.unit_price) AS revenue,
              RANK() OVER (PARTITION BY c.category_id
                           ORDER BY SUM(si.quantity * si.unit_price) DESC) AS rnk
       FROM   sale_items si
       JOIN   products p   ON p.product_id  = si.product_id
       JOIN   categories c ON c.category_id = p.category_id
       GROUP BY c.category_id, c.category_name, p.product_id, p.name) ranked
WHERE  rnk = 1
ORDER BY revenue DESC;

-- ---------------------------------------------------------------------
--  PART D : EER, FEFO and market-basket reports
-- ---------------------------------------------------------------------

-- Q29 | EER - superclass/subclass JOIN | Pharmacists with licence number and their sales
-- RA: γ employee; COUNT(sale_id), SUM(total_amount) ((Employees ⋈ Pharmacists) ⟕ Sales)
SELECT e.employee_id, e.name, ph.license_no, ph.qualification,
       COUNT(s.sale_id) AS bills, COALESCE(SUM(s.total_amount), 0) AS revenue
FROM   employees e
JOIN   pharmacists ph ON ph.employee_id = e.employee_id
LEFT JOIN sales s     ON s.employee_id  = e.employee_id
GROUP BY e.employee_id, e.name, ph.license_no, ph.qualification
ORDER BY revenue DESC;

-- Q30 | FEFO evidence - row-constructor IN sub-query | Sale lines that were served from more than one batch
SELECT a.sale_id, p.name AS product, b.batch_no, b.expiry_date, a.quantity, a.cost_price
FROM   sale_allocations a
JOIN   stock_batches b ON b.batch_id   = a.batch_id
JOIN   products p      ON p.product_id = a.product_id
WHERE  (a.sale_id, a.product_id) IN (SELECT sale_id, product_id
                                     FROM   sale_allocations
                                     GROUP BY sale_id, product_id
                                     HAVING COUNT(*) > 1)
ORDER BY a.sale_id, b.expiry_date;

-- Q31 | DRL - GROUP BY, multi-table JOIN | Monthly profit and margin (the figures sp_monthly_report returns)
SELECT DATE_FORMAT(s.sale_date, '%Y-%m')                              AS sale_month,
       SUM(a.quantity * si.unit_price)                                AS revenue,
       SUM(a.quantity * a.cost_price)                                 AS cost,
       SUM(a.quantity * (si.unit_price - a.cost_price))               AS profit,
       ROUND(100 * SUM(a.quantity * (si.unit_price - a.cost_price))
                 / SUM(a.quantity * si.unit_price), 2)                AS margin_pct
FROM   sale_allocations a
JOIN   sales s       ON s.sale_id = a.sale_id
JOIN   sale_items si ON si.sale_id = a.sale_id AND si.product_id = a.product_id
GROUP BY DATE_FORMAT(s.sale_date, '%Y-%m')
ORDER BY sale_month;

-- Q32 | DRL - stock valuation by category | Value of sellable stock at cost price
SELECT c.category_name,
       SUM(b.quantity)                  AS units_on_shelf,
       SUM(b.quantity * b.cost_price)   AS stock_value_at_cost
FROM   stock_batches b
JOIN   products p   ON p.product_id  = b.product_id
JOIN   categories c ON c.category_id = p.category_id
WHERE  b.expiry_date >= CURRENT_DATE AND b.quantity > 0
GROUP BY c.category_id, c.category_name
ORDER BY stock_value_at_cost DESC;

-- Q33 | DRL - self-join (market-basket) | Pairs of medicines that were bought together at least twice
SELECT p1.name AS product_a, p2.name AS product_b, COUNT(*) AS times_together
FROM   sale_items a
JOIN   sale_items b  ON b.sale_id = a.sale_id AND a.product_id < b.product_id
JOIN   products p1   ON p1.product_id = a.product_id
JOIN   products p2   ON p2.product_id = b.product_id
GROUP BY p1.product_id, p1.name, p2.product_id, p2.name
HAVING COUNT(*) >= 2
ORDER BY times_together DESC, product_a, product_b;

-- Q34 | DRL - date arithmetic | Purchase orders per month with value of the stock received
SELECT DATE_FORMAT(order_date, '%Y-%m') AS order_month,
       COUNT(*)                         AS orders,
       SUM(status = 'Received')         AS received,
       SUM(status = 'Pending')          AS pending,
       SUM(status = 'Cancelled')        AS cancelled,
       SUM(total_cost)                  AS value_received
FROM   purchase_orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month;
