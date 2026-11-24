#!/usr/bin/env python3
"""Exports the relational pharmacy data as MongoDB-style documents (Week 15: SQL vs NoSQL).
   Output: sales.json, products.json, customers.json  (one JSON array each; load with mongoimport --jsonArray)"""
import json, os, decimal, datetime
import mysql.connector

db = mysql.connector.connect(user=os.getenv("PHARMACY_USER", "root"),
                             password=os.getenv("PHARMACY_PASSWORD", ""),
                             unix_socket=os.getenv("PHARMACY_SOCKET"),
                             host=None if os.getenv("PHARMACY_SOCKET") else os.getenv("PHARMACY_HOST", "localhost"),
                             database="pharmacy_db")
cur = db.cursor(dictionary=True)

def num(v):
    return float(v) if isinstance(v, decimal.Decimal) else v

def rows(sql, params=()):
    cur.execute(sql, params)
    return [{k: num(v) for k, v in r.items()} for r in cur.fetchall()]

def iso(d):
    return d.isoformat(sep="T") if isinstance(d, datetime.datetime) else str(d)

sales = []
for s in rows("""SELECT s.sale_id, s.sale_date, s.payment_method, s.total_amount,
                        c.customer_id, c.name AS customer_name,
                        e.employee_id, e.name AS employee_name, e.role
                 FROM sales s JOIN customers c ON c.customer_id = s.customer_id
                              JOIN employees e ON e.employee_id = s.employee_id ORDER BY s.sale_id"""):
    items = []
    for it in rows("""SELECT si.product_id, p.name, g.category_name AS category, si.quantity AS qty,
                             si.unit_price, si.quantity * si.unit_price AS line_total
                      FROM sale_items si JOIN products p ON p.product_id = si.product_id
                                         JOIN categories g ON g.category_id = p.category_id
                      WHERE si.sale_id = %s ORDER BY si.product_id""", (s["sale_id"],)):
        it["batches"] = rows("""SELECT b.batch_no, a.quantity AS qty, a.cost_price
                                FROM sale_allocations a JOIN stock_batches b ON b.batch_id = a.batch_id
                                WHERE a.sale_id = %s AND a.product_id = %s ORDER BY b.expiry_date""",
                             (s["sale_id"], it["product_id"]))
        items.append(it)
    sales.append({"_id": s["sale_id"], "sale_date": iso(s["sale_date"]), "payment_method": s["payment_method"],
                  "customer": {"customer_id": s["customer_id"], "name": s["customer_name"]},
                  "employee": {"employee_id": s["employee_id"], "name": s["employee_name"], "role": s["role"]},
                  "items": items, "total_amount": s["total_amount"]})

products = []
for p in rows("""SELECT p.product_id, p.name, p.generic_name, p.unit_price, p.reorder_level,
                        p.requires_prescription, g.category_id, g.category_name
                 FROM products p JOIN categories g ON g.category_id = p.category_id ORDER BY p.product_id"""):
    batches = rows("""SELECT b.batch_id, b.batch_no, b.po_id, b.received_qty, b.quantity AS qty,
                             b.expiry_date, b.cost_price
                      FROM stock_batches b WHERE b.product_id = %s ORDER BY b.expiry_date""", (p["product_id"],))
    for b in batches:
        b["expiry_date"] = str(b["expiry_date"])
    products.append({"_id": p["product_id"], "name": p["name"], "generic_name": p["generic_name"],
                     "category": {"category_id": p["category_id"], "name": p["category_name"]},
                     "unit_price": p["unit_price"], "reorder_level": p["reorder_level"],
                     "requires_prescription": bool(p["requires_prescription"]), "batches": batches})

customers = [{"_id": c["customer_id"], "name": c["name"], "phone": c["phone"], "registered_on": str(c["registered_on"])}
             for c in rows("SELECT customer_id, name, phone, registered_on FROM customers ORDER BY customer_id")]

here = os.path.dirname(os.path.abspath(__file__))
for name, data in (("sales", sales), ("products", products), ("customers", customers)):
    json.dump(data, open(os.path.join(here, f"{name}.json"), "w"), indent=1, ensure_ascii=False)
print(len(sales), "sales,", len(products), "products,", len(customers), "customers exported")
