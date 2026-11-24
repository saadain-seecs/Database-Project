#!/usr/bin/env python3
"""Runs a DELIMITER-free .sql script statement by statement and writes a clean
transcript (statement, result table or ERROR) to a text file and a JSON file.
usage: run_script.py script.sql out_prefix"""
import sys, json, decimal, datetime
import pymysql

src, prefix = sys.argv[1], sys.argv[2]

def clean(v):
    if isinstance(v, decimal.Decimal): return float(v) if v % 1 else int(v)
    if isinstance(v, (datetime.datetime, datetime.date)): return str(v)
    if isinstance(v, (bytes, bytearray)): return v.decode()
    return v

def table(cols, rows):
    rows = [["NULL" if v is None else str(v) for v in r] for r in rows]
    w = [max([len(c)] + [len(r[i]) for r in rows]) for i, c in enumerate(cols)]
    line = "+" + "+".join("-" * (x + 2) for x in w) + "+"
    out = [line, "| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(cols)) + " |", line]
    for r in rows:
        out.append("| " + " | ".join(r[i].ljust(w[i]) for i in range(len(cols))) + " |")
    out.append(line)
    return "\n".join(out)

stmts, buf = [], []
for line in open(src, encoding="utf-8"):
    if line.strip().startswith("--") or not line.strip():
        continue
    buf.append(line.rstrip("\n"))
    if line.rstrip().endswith(";"):
        stmts.append("\n".join(buf).rstrip().rstrip(";")); buf = []

conn = pymysql.connect(user="root", unix_socket="/run/mysqld/mysqld.sock", autocommit=True)
cur = conn.cursor()
cur.execute("SET SESSION sql_mode='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
cur.execute("SET SESSION time_zone='+00:00'")
cur.execute("SET SESSION timestamp = UNIX_TIMESTAMP('2026-11-18 10:00:00')")
txt, js = [], []
for s in stmts:
    entry = dict(sql=s, results=[], error=None, info=None)
    txt.append("mysql> " + s.replace("\n", "\n    ") + ";")
    try:
        cur.execute(s)
        affected = cur.rowcount
        sets = []
        while True:
            if cur.description:
                sets.append((cur.description, cur.fetchall()))
            if not cur.nextset():
                break
        for desc, rows in sets:
            cols = [d[0] for d in desc]
            entry["results"].append(dict(columns=cols, rows=[[clean(v) for v in r] for r in rows]))
            txt.append(table(cols, rows)); txt.append(f"{len(rows)} row(s)")
        if not sets:
            entry["info"] = f"OK, {affected if affected and affected > 0 else 0} row(s) affected"
            txt.append(entry["info"])
    except pymysql.MySQLError as e:
        entry["error"] = f"ERROR {e.args[0]}: {e.args[1]}"
        txt.append(entry["error"])
    txt.append("")
    js.append(entry)
open(prefix + ".txt", "w", encoding="utf-8").write("\n".join(txt))
json.dump(js, open(prefix + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(src, "->", len(js), "statements,", sum(1 for e in js if e["error"]), "errors")
