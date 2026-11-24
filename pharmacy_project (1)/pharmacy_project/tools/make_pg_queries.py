#!/usr/bin/env python3
"""Translates mysql/04_queries.sql to PostgreSQL syntax and appends PostgreSQL-only queries."""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
s = (ROOT / "mysql" / "04_queries.sql").read_text()

s = s.replace("USE pharmacy_db;", "\\connect pharmacy_db")
s = re.sub(r"DATE_FORMAT\(([^,()]+),\s*'%Y-%m'\)", r"to_char(\1, 'YYYY-MM')", s)
s = s.replace("SUM(si.quantity * si.unit_price)", "SUM(si.line_total)") if False else s
# Q11: WITH ROLLUP -> ROLLUP()
s = s.replace("GROUP BY c.category_name WITH ROLLUP;", "GROUP BY ROLLUP (c.category_name);")
# Q34: boolean sums -> FILTER
s = s.replace("SUM(status = 'Received')         AS received", "COUNT(*) FILTER (WHERE status = 'Received')  AS received")
s = s.replace("SUM(status = 'Pending')          AS pending", "COUNT(*) FILTER (WHERE status = 'Pending')   AS pending")
s = s.replace("SUM(status = 'Cancelled')        AS cancelled", "COUNT(*) FILTER (WHERE status = 'Cancelled') AS cancelled")
# Q16/Q31 need numeric ROUND (already numeric) ; Q4 uses the view ; nothing else differs
s = s.replace("(Needs MySQL 8.0.31+ for INTERSECT / EXCEPT (Q18, Q19).", "")
s = re.sub(r"-- File 4 of 6.*", "-- File 4 of 5 (PostgreSQL) : DATA RETRIEVAL - the same 34 queries + 9 PostgreSQL-only ones", s, count=1)

s += r'''
-- ---------------------------------------------------------------------
--  PART E : PostgreSQL-only features (Week 16)
-- ---------------------------------------------------------------------

-- Q35 | PG - DISTINCT ON | The most recent bill of every customer
SELECT DISTINCT ON (s.customer_id) s.customer_id, c.name, s.sale_id, s.sale_date, s.total_amount
FROM   sales s JOIN customers c ON c.customer_id = s.customer_id
ORDER BY s.customer_id, s.sale_date DESC;

-- Q36 | PG - aggregate FILTER | Bills per payment method, one column per month
SELECT payment_method,
       COUNT(*) FILTER (WHERE to_char(sale_date, 'YYYY-MM') = '2026-08') AS aug,
       COUNT(*) FILTER (WHERE to_char(sale_date, 'YYYY-MM') = '2026-09') AS sep,
       COUNT(*) FILTER (WHERE to_char(sale_date, 'YYYY-MM') = '2026-10') AS oct,
       COUNT(*) FILTER (WHERE to_char(sale_date, 'YYYY-MM') = '2026-11') AS nov,
       COUNT(*) AS total
FROM   sales
GROUP BY payment_method
ORDER BY total DESC;

-- Q37 | PG - full-text search (GIN index) | Find medicines mentioning "paracetamol" or "ibuprofen"
SELECT product_id, name, generic_name
FROM   products
WHERE  to_tsvector('english', name || ' ' || COALESCE(generic_name, ''))
       @@ to_tsquery('english', 'paracetamol | ibuprofen')
ORDER BY name;

-- Q38 | PG - JSONB | Every bill as one JSON document (this is the NoSQL document model, built inside SQL)
SELECT jsonb_build_object(
         'sale_id', s.sale_id, 'date', s.sale_date, 'customer', c.name, 'payment', s.payment_method,
         'items', (SELECT jsonb_agg(jsonb_build_object('product', p.name, 'qty', si.quantity, 'price', si.unit_price)
                                    ORDER BY p.name)
                   FROM sale_items si JOIN products p ON p.product_id = si.product_id
                   WHERE si.sale_id = s.sale_id),
         'total', s.total_amount) AS bill
FROM   sales s JOIN customers c ON c.customer_id = s.customer_id
WHERE  s.sale_id IN (1, 2, 3)
ORDER BY s.sale_id;

-- Q39 | PG - materialized view | Pre-computed monthly sales (refreshed with REFRESH MATERIALIZED VIEW)
SELECT sale_month, bills, units_sold, revenue FROM mv_monthly_sales ORDER BY sale_month;

-- Q40 | PG - string_agg | Medicines on each of the five biggest bills
SELECT s.sale_id, s.total_amount, string_agg(p.name, ', ' ORDER BY p.name) AS medicines
FROM   sales s
JOIN   sale_items si ON si.sale_id = s.sale_id
JOIN   products p    ON p.product_id = si.product_id
GROUP BY s.sale_id, s.total_amount
ORDER BY s.total_amount DESC, s.sale_id
LIMIT 5;

-- Q41 | PG - generated column | Line totals come from the STORED generated column (no calculation in the query)
SELECT s.sale_id, SUM(si.line_total) AS total_from_generated_column, s.total_amount AS total_kept_by_trigger
FROM   sales s JOIN sale_items si ON si.sale_id = s.sale_id
WHERE  s.sale_id <= 5
GROUP BY s.sale_id, s.total_amount
ORDER BY s.sale_id;

-- Q42 | PG - LATERAL join | The two most recent purchases of each of the first five customers
SELECT c.customer_id, c.name, x.sale_id, x.sale_date, x.total_amount
FROM   customers c
CROSS JOIN LATERAL (SELECT s.sale_id, s.sale_date, s.total_amount
                    FROM   sales s WHERE s.customer_id = c.customer_id
                    ORDER BY s.sale_date DESC LIMIT 2) x
WHERE  c.customer_id <= 5
ORDER BY c.customer_id, x.sale_date DESC;

-- Q43 | PG - recursive-free CTE with window | Each month's revenue and the change against the previous month
WITH m AS (SELECT sale_month, revenue FROM mv_monthly_sales)
SELECT sale_month, revenue,
       revenue - LAG(revenue) OVER (ORDER BY sale_month) AS change_vs_previous
FROM   m
ORDER BY sale_month;
'''
(ROOT / "postgres" / "pg_04_queries.sql").write_text(s)
print("ok")
