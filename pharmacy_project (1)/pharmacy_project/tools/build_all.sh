#!/bin/bash
# Rebuilds both databases from scratch and regenerates every output used in the report.
set -e
cd "$(dirname "$0")/.."
python3 tools/generate_data.py
for f in 01_schema 02_programmability 03_sample_data; do mysql -uroot < mysql/$f.sql; done
mysql -uroot < mysql/00_app_user.sql
python3 tools/run_queries.py mysql/04_queries.sql docs/query_results.json > docs/query_run.log
python3 tools/run_script.py mysql/05_dml_ddl_demo.sql docs/dml_ddl_output 2>/dev/null
python3 tools/run_script.py mysql/06_tests_transactions.sql docs/test_output 2>/dev/null
mysqldump -uroot --no-data --routines --triggers --events pharmacy_db > docs/schema_dump.sql 2>/dev/null || true
(cd nosql && PHARMACY_SOCKET=/run/mysqld/mysqld.sock python3 export_to_json.py && python3 build_mongo_queries.py > ../docs/nosql_run.log)
python3 tools/make_diagrams.py
python3 tools/make_dictionary.py
python3 tools/make_pg_queries.py
for f in pg_01_schema pg_02_programmability pg_03_sample_data; do su postgres -c "psql -q -v ON_ERROR_STOP=1 -f $PWD/postgres/$f.sql" >/dev/null; done
python3 tools/run_queries_pg.py postgres/pg_04_queries.sql docs/pg_query_results.json > docs/pg_query_run.log
python3 tools/run_script_pg.py postgres/pg_05_tests.sql docs/pg_test_output
echo BUILD OK
# scripted session of the Python menu program (then remove the demo bill again)
printf '3\n6\n9\n1\n4\n3\n6\nCash\n1\n2\n39\n1\n\n4\n3\n6\nCash\n7\n500\n\n7\n2026\n10\n9\n3\n0\n' > /tmp/cli_in.txt
(cd python_app && PHARMACY_SOCKET=/run/mysqld/mysqld.sock python3 pharmacy_cli.py < <(printf '2\n3\n4\n3\n6\nCash\n1\n2\n39\n1\n\n4\n3\n6\nCash\n7\n500\n\n7\n2026\n10\n9\n3\n0\n') > ../docs/cli_session.txt 2>&1)
mysql -uroot pharmacy_db -e "DELETE FROM sales WHERE sale_date >= CURRENT_DATE"
echo CLI OK
