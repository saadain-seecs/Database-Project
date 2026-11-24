# Pharmacy Inventory & Sales Management System
CS220 Database Systems - BESE 2K25 - NUST Islamabad

Complete final project: MySQL database (main), PostgreSQL port, MongoDB document model, Python menu app, and the written report.

## Folder map
| Folder | Contents |
|---|---|
| `mysql/` | `01_schema` -> `02_programmability` -> `03_sample_data` -> `04_queries` -> `05_dml_ddl_demo` -> `06_tests_transactions` (+ optional `00_app_user`) |
| `postgres/` | `pg_01_schema` ... `pg_05_tests` (same system in PostgreSQL / PL/pgSQL) |
| `nosql/` | JSON documents, `mongo_queries.js`, export + verification scripts |
| `python_app/` | `pharmacy_cli.py` menu program |
| `docs/` | **`Pharmacy_DB_Final_Project_Report.docx`**, EER and schema diagrams, data dictionary, captured outputs |
| `tools/` | data generator, runners, report builder, `build_all.sh` |

## Run in MySQL Workbench
1. Execute `mysql/01_schema.sql`, then `02_programmability.sql`, then `03_sample_data.sql` (in that order).
2. Run `04_queries.sql` query by query; run `05` and `06` to see DML/DDL demos and the tests (errors in `06` are intentional).
3. Optional daily event: `SET GLOBAL event_scheduler = ON;`

Command line: `mysql -u root -p < mysql/01_schema.sql` and so on.

## PostgreSQL
`psql -U postgres -f postgres/pg_01_schema.sql` then `pg_02`, `pg_03`, `pg_04`, `pg_05`.

## Python menu
`pip install mysql-connector-python`, run `mysql/00_app_user.sql`, then `python python_app/pharmacy_cli.py`.

## Environment note
Outputs in the report were produced on MariaDB 10.11 (MySQL-compatible, MySQL-8-style strict mode) and PostgreSQL 16.
The scripts use MySQL 8 syntax; `INTERSECT`/`EXCEPT` (Q18, Q19) need MySQL 8.0.31+.
MongoDB pipelines were verified on the `mongomock` emulator, not a real server.
