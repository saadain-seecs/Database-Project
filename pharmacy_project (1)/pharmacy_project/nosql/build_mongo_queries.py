#!/usr/bin/env python3
"""Single source of truth for the MongoDB aggregation pipelines.
   * writes mongo_queries.js (for mongosh)
   * runs the same pipelines in mongomock (an in-memory MongoDB emulator) and compares them with the SQL results
   NOTE: mongomock is an emulator - run mongo_queries.js on a real MongoDB server to confirm."""
import json, os, sys
import mongomock

here = os.path.dirname(os.path.abspath(__file__))
sql = {q["id"]: q for q in json.load(open(os.path.join(here, "..", "docs", "query_results.json")))}

PIPES = [
  ("Q5  monthly sales  (SQL: GROUP BY month)", "sales", [
     {"$group": {"_id": {"$substr": ["$sale_date", 0, 7]}, "bills": {"$sum": 1}, "revenue": {"$sum": "$total_amount"}}},
     {"$sort": {"_id": 1}}], 5),
  ("Q6  top 10 best-selling medicines  (SQL: GROUP BY product ... LIMIT 10)", "sales", [
     {"$unwind": "$items"},
     {"$group": {"_id": "$items.name", "units_sold": {"$sum": "$items.qty"}, "revenue": {"$sum": "$items.line_total"}}},
     {"$sort": {"units_sold": -1, "revenue": -1}}, {"$limit": 10}], 6),
  ("Q8  customers with highest spending  (SQL: GROUP BY ... HAVING)", "sales", [
     {"$group": {"_id": {"id": "$customer.customer_id", "name": "$customer.name"}, "bills": {"$sum": 1}, "total_spent": {"$sum": "$total_amount"}}},
     {"$match": {"total_spent": {"$gte": 2000}}},
     {"$sort": {"total_spent": -1}}, {"$limit": 10}], 8),
  ("Q11 revenue per category  (SQL: 4-table JOIN + GROUP BY)", "sales", [
     {"$unwind": "$items"},
     {"$group": {"_id": "$items.category", "units_sold": {"$sum": "$items.qty"}, "revenue": {"$sum": "$items.line_total"}}},
     {"$sort": {"revenue": -1}}], 11),
  ("Q9  products below reorder level  (SQL: correlated sub-query)", "products", [
     {"$project": {"name": 1, "reorder_level": 1,
                   "on_hand": {"$sum": {"$map": {"input": {"$filter": {"input": "$batches", "as": "b",
                               "cond": {"$gte": ["$$b.expiry_date", "2026-11-18"]}}}, "as": "x", "in": "$$x.qty"}}}}},
     {"$project": {"name": 1, "on_hand": 1, "reorder_level": 1, "low": {"$lt": ["$on_hand", "$reorder_level"]}}},
     {"$match": {"low": True}},
     {"$sort": {"name": 1}}], 9),
]

# ---- write mongo_queries.js
js = ["// MongoDB (mongosh) version of the main reports.  Week 15: SQL vs NoSQL",
      "// Load first:  mongoimport --db pharmacy_nosql --collection sales    --jsonArray --file sales.json",
      "//              mongoimport --db pharmacy_nosql --collection products  --jsonArray --file products.json",
      "//              mongoimport --db pharmacy_nosql --collection customers --jsonArray --file customers.json",
      "// Then:        mongosh pharmacy_nosql mongo_queries.js", "",
      "// Indexes that mirror the relational ones",
      "db.sales.createIndex({ sale_date: 1 });", "db.sales.createIndex({ 'customer.customer_id': 1 });",
      "db.products.createIndex({ 'category.category_id': 1 });", "db.products.createIndex({ 'batches.expiry_date': 1 });", "",
      "// A sale is ONE document (bill + items + customer snapshot): no JOIN is needed to print a bill",
      "printjson(db.sales.findOne({ _id: 40 }));", ""]
for title, coll, pipe, _ in PIPES:
    js += [f"// {title}", f"printjson(db.{coll}.aggregate({json.dumps(pipe, indent=2)}).toArray());", ""]
js += ["// Transaction across two collections is possible only on a replica set / sharded cluster:",
       "// const s = db.getMongo().startSession(); s.startTransaction(); /* insert sale + update product batches */ s.commitTransaction();"]
open(os.path.join(here, "mongo_queries.js"), "w").write("\n".join(js) + "\n")

# ---- verify with mongomock
client = mongomock.MongoClient(); d = client.pharmacy_nosql
for c in ("sales", "products", "customers"):
    d[c].insert_many(json.load(open(os.path.join(here, f"{c}.json"))))
report = []
for title, coll, pipe, qid in PIPES:
    if qid == 9:   # mongomock cannot evaluate $$variables inside $filter/$map -> check the same logic in Python
        prods = json.load(open(os.path.join(here, "products.json")))
        py = sorted((p["name"], sum(b["qty"] for b in p["batches"] if b["expiry_date"] >= "2026-11-18")) for p in prods
                    if sum(b["qty"] for b in p["batches"] if b["expiry_date"] >= "2026-11-18") < p["reorder_level"])
        exp = sorted((r[1], r[3]) for r in sql[9]["rows"])
        report.append(dict(title=title, ok=None, python_logic_matches_sql=(py == exp), mongo_rows=len(py), sql_rows=len(exp),
                           note="mongomock cannot evaluate $$variables; same logic checked in Python - run on a real MongoDB to confirm the pipeline"))
        continue
    try:
        got = list(d[coll].aggregate(pipe))
    except Exception as e:
        report.append(dict(title=title, ok=None, note=f"mongomock cannot run this stage: {e}")); continue
    sq = sql[qid]
    def rnd(x): return round(float(x), 2)
    if qid == 5:   a = [(r["_id"], r["bills"], rnd(r["revenue"])) for r in got];             b = [(r[0], r[1], rnd(r[3])) for r in sq["rows"]]
    elif qid == 6: a = [(r["_id"], r["units_sold"], rnd(r["revenue"])) for r in got];        b = [(r[1], r[2], rnd(r[3])) for r in sq["rows"]]
    elif qid == 8: a = [(r["_id"]["id"], r["bills"], rnd(r["total_spent"])) for r in got];  b = [(r[0], r[2], rnd(r[3])) for r in sq["rows"]]
    elif qid == 11:a = sorted((r["_id"], r["units_sold"], rnd(r["revenue"])) for r in got);  b = sorted((r[0], r[1], rnd(r[2])) for r in sq["rows"] if not r[0].startswith("**"))
    elif qid == 9: a = sorted((r["name"], r["on_hand"]) for r in got);                       b = sorted((r[1], r[3]) for r in sq["rows"])
    # equal-score ties may order differently: compare as sorted sets for the top-N queries
    ok = sorted(a, key=str) == sorted(b, key=str)
    report.append(dict(title=title, ok=ok, mongo_rows=len(a), sql_rows=len(b), sample=[list(map(str, x)) for x in a[:3]]))
json.dump(report, open(os.path.join(here, "..", "docs", "nosql_verification.json"), "w"), indent=1)
for r in report: print(r["ok"], "|", r["title"], "|", r.get("mongo_rows"), r.get("sql_rows"), r.get("note", ""))
