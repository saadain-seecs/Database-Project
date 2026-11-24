# PharmaCare: Pharmacy Inventory & Sales Management System

A relational database project for a pharmacy, built for **CS220 Database Systems** at NUST Islamabad. It tracks medicines by batch and expiry date, handles billing and purchasing, and comes with a modern Python desktop app.

## Features
- **Batch-wise stock with expiry tracking.** Sales deduct stock from the earliest-expiring batch first (FEFO). Expired stock cannot be sold.
- **Business rules inside the database.** 14 triggers, 4 stored procedures, 1 function, 6 views and 1 scheduled event. Overselling is blocked, bill totals are calculated automatically, and checkout is one transaction that rolls back completely on any error.
- **Normalized schema.** 14 tables in 3NF/BCNF with primary keys, foreign keys, UNIQUE, CHECK and DEFAULT constraints, plus an EER specialization (Pharmacist / Cashier).
- **34 documented SQL queries** covering joins, grouping, sub-queries, set operations, relational-algebra division and window functions.
- **PostgreSQL port** of the same system (PL/pgSQL), with identical query results.
- **MongoDB document model** of the same data, for the SQL vs NoSQL comparison.
- **Desktop GUI (CustomTkinter)** with admin login, dashboard charts, point-of-sale billing, medicines, suppliers, customers, purchases, stock, expiry, staff and reports.

## Project structure
| Folder | Contents |
|---|---|
| `mysql/` | Schema, triggers/procedures, sample data, queries, demos and tests |
| `postgres/` | PostgreSQL version of the schema, functions, data, queries and tests |
| `nosql/` | JSON documents and MongoDB aggregation pipelines |
| `gui_app/` | PharmaCare desktop application |
| `python_app/` | Simple menu-based command-line interface |
| `docs/` | ERD, data dictionary, final report |
| `tools/` | Data generator and build scripts |

## Getting started
1. In MySQL 8.0.31+ (MySQL Workbench works), run the files in `mysql/` in this order:
   `01_schema.sql`, `02_programmability.sql`, `03_sample_data.sql`, `00_app_user.sql`, `07_admin_users.sql`
2. Install and start the GUI:
   ```
   cd gui_app
   pip install -r requirements.txt
   python main.py
   ```
3. On the first start, create the admin account, then sign in.

The sample data is generated and fictional. Run `mysql/04_queries.sql`, `05_dml_ddl_demo.sql` and `06_tests_transactions.sql` to see the queries and tests (the red errors in 06 are intentional).

## Tech stack
MySQL, PostgreSQL, MongoDB (document model), Python, CustomTkinter, Matplotlib

## Testing
- 25 deliberate rule violations are all rejected by the database.
- A consistency audit finds 0 mismatches between stored totals and recomputed values.
- 42 automated GUI checks and 22 login checks pass.
- Developed and tested on MariaDB 10.11 and PostgreSQL 16.

## Screenshots
<img width="959" height="512" alt="Screenshot 2026-11-24 221008" src="https://github.com/user-attachments/assets/19ece952-bf63-4d51-aaf4-d466fd7e8e2a" />
<img width="1918" height="1008" alt="image" src="https://github.com/user-attachments/assets/10721034-9f0e-464d-8021-a3fde3c6b930" />
<img width="1378" height="937" alt="image" src="https://github.com/user-attachments/assets/198f221f-acf7-405b-bec7-2b4354df6686" />




## Team
CS220 Database Systems, BESE 2K25, NUST Islamabad
- Muhammad Saadain Zahid
- Hashir Saleem
- Abdul Ahad


