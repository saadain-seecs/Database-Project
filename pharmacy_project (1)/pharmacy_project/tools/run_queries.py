#!/usr/bin/env python3
"""Runs every documented query of a .sql file and stores the results as JSON.
   Session settings mimic MySQL 8 defaults (ONLY_FULL_GROUP_BY, strict mode)."""
import json, re, sys, decimal, datetime
import mysql.connector

SQL_FILE = sys.argv[1]
OUT_FILE = sys.argv[2]
HDR = re.compile(r"^--\s*Q(\d+)\s*\|\s*(.*?)\s*\|\s*(.*)$")

def parse(path):
    blocks, cur = [], None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = HDR.match(line)
        if m:
            if cur: blocks.append(cur)
            cur = dict(id=int(m.group(1)), topic=m.group(2), title=m.group(3), ra="", sql=[])
            continue
        if cur is None: continue
        if line.startswith("-- RA:"):
            cur["ra"] += line[6:].strip() + " "
        elif line.strip().startswith("--"):
            continue
        else:
            cur["sql"].append(line)
    if cur: blocks.append(cur)
    for b in blocks:
        b["sql"] = "\n".join(b["sql"]).strip().rstrip(";").strip()
        b["ra"] = b["ra"].strip()
    return blocks

def clean(v):
    if isinstance(v, decimal.Decimal): return float(v) if v % 1 else int(v)
    if isinstance(v, (datetime.datetime, datetime.date)): return str(v)
    if isinstance(v, (bytes, bytearray)): return v.decode()
    return v

conn = mysql.connector.connect(user="root", unix_socket="/run/mysqld/mysqld.sock", database="pharmacy_db")
cur = conn.cursor()
cur.execute("SET SESSION sql_mode='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
cur.execute("SET SESSION time_zone='+00:00'")
cur.execute("SET SESSION timestamp = UNIX_TIMESTAMP('2026-11-18 10:00:00')")
results = []
for b in parse(SQL_FILE):
    try:
        cur.execute(b["sql"])
        rows = cur.fetchall()
        b["columns"] = [d[0] for d in cur.description]
        b["rows"] = [[clean(x) for x in r] for r in rows]
        b["rowcount"] = len(rows)
        b["error"] = None
    except Exception as e:
        b["columns"], b["rows"], b["rowcount"], b["error"] = [], [], 0, str(e)
    results.append(b)
    print(f"Q{b['id']:>2} rows={b['rowcount']:>3} {'ERROR: '+b['error'] if b['error'] else ''}  {b['title'][:60]}")
json.dump(results, open(OUT_FILE, "w"), indent=1, ensure_ascii=False)
