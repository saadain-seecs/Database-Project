#!/usr/bin/env python3
import json, sys, re, decimal, datetime
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import psycopg2
HDR = re.compile(r"^--\s*Q(\d+)\s*\|\s*(.*?)\s*\|\s*(.*)$")
def parse(path):
    blocks, cur = [], None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n"); m = HDR.match(line)
        if m:
            if cur: blocks.append(cur)
            cur = dict(id=int(m.group(1)), topic=m.group(2), title=m.group(3), ra="", sql=[]); continue
        if cur is None: continue
        if line.startswith("-- RA:"): cur["ra"] += line[6:].strip() + " "
        elif line.strip().startswith("--") or line.startswith("\\"): continue
        else: cur["sql"].append(line)
    if cur: blocks.append(cur)
    for b in blocks:
        b["sql"] = "\n".join(b["sql"]).strip().rstrip(";").strip(); b["ra"] = b["ra"].strip()
    return blocks
def clean(v):
    if isinstance(v, decimal.Decimal): return float(v) if v % 1 else int(v)
    if isinstance(v, (datetime.datetime, datetime.date)): return str(v)
    if isinstance(v, (dict, list)): return json.dumps(v, ensure_ascii=False, default=str)
    return v
conn = psycopg2.connect(dbname="pharmacy_db", user="root", host="/var/run/postgresql")
conn.autocommit = True
cur = conn.cursor(); out = []
for b in parse(sys.argv[1]):
    try:
        cur.execute(b["sql"]); rows = cur.fetchall()
        b["columns"] = [d[0] for d in cur.description]; b["rows"] = [[clean(x) for x in r] for r in rows]
        b["rowcount"] = len(rows); b["error"] = None
    except Exception as e:
        b["columns"], b["rows"], b["rowcount"], b["error"] = [], [], 0, str(e).strip()
    out.append(b); print(f"Q{b['id']:>2} rows={b['rowcount']:>3} {('ERROR: ' + b['error']) if b['error'] else ''} {b['title'][:55]}")
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
