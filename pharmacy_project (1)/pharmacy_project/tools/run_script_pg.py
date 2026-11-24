#!/usr/bin/env python3
"""PostgreSQL twin of run_script.py (statement-by-statement transcript)."""
import sys, json, decimal, datetime, psycopg2
src, prefix = sys.argv[1], sys.argv[2]
def clean(v):
    if isinstance(v, decimal.Decimal): return float(v) if v % 1 else int(v)
    if isinstance(v, (datetime.datetime, datetime.date)): return str(v)
    return v
def table(cols, rows):
    rows = [["NULL" if v is None else str(v) for v in r] for r in rows]
    w = [max([len(c)] + [len(r[i]) for r in rows]) for i, c in enumerate(cols)]
    line = "+" + "+".join("-" * (x + 2) for x in w) + "+"
    out = [line, "| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(cols)) + " |", line]
    out += ["| " + " | ".join(r[i].ljust(w[i]) for i in range(len(cols))) + " |" for r in rows]
    return "\n".join(out + [line])
stmts, buf = [], []
for line in open(src, encoding="utf-8"):
    if line.strip().startswith("--") or not line.strip() or line.startswith("\\"): continue
    buf.append(line.rstrip("\n"))
    if line.rstrip().endswith(";"): stmts.append("\n".join(buf).rstrip().rstrip(";")); buf = []
conn = psycopg2.connect(dbname="pharmacy_db", user="root", host="/var/run/postgresql"); conn.autocommit = True
cur = conn.cursor(); txt, js = [], []
for s in stmts:
    e = dict(sql=s, results=[], error=None, info=None)
    txt.append("pharmacy_db=> " + s.replace("\n", "\n    ") + ";")
    try:
        cur.execute(s)
        if cur.description:
            rows = cur.fetchall(); cols = [d[0] for d in cur.description]
            e["results"].append(dict(columns=cols, rows=[[clean(v) for v in r] for r in rows]))
            txt += [table(cols, rows), f"({len(rows)} rows)"]
        else:
            e["info"] = cur.statusmessage; txt.append(e["info"])
    except psycopg2.Error as ex:
        e["error"] = "ERROR: " + (ex.diag.message_primary or str(ex)).strip(); txt.append(e["error"])
    txt.append(""); js.append(e)
open(prefix + ".txt", "w").write("\n".join(txt)); json.dump(js, open(prefix + ".json", "w"), indent=1)
print(src, "->", len(js), "statements,", sum(1 for x in js if x["error"]), "errors")
