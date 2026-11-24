#!/usr/bin/env python3
"""Draws (1) the EER diagram and (2) the relational schema (read live from MySQL) with Graphviz."""
import subprocess, mysql.connector, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOCS = os.path.join(ROOT, "docs")

def run(dot, out, dpi=150):
    p = os.path.join(DOCS, out.replace(".png", ".dot")); open(p, "w").write(dot)
    subprocess.run(["dot", "-Tpng", f"-Gdpi={dpi}", p, "-o", os.path.join(DOCS, out)], check=True)

# ------------------------------------------------------------------ EER
def ent(name, attrs, color="#DCE9F8", border="#2F5597"):
    rows = "".join(f'<TR><TD ALIGN="LEFT" PORT="{i}">{a}</TD></TR>' for i, a in enumerate(attrs))
    return (f'{name.replace(" ", "")} [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="{border}">'
            f'<TR><TD BGCOLOR="{color}"><B>{name.upper()}</B></TD></TR>{rows}</TABLE>>];')

def rel(name, extra=""):
    return f'{name} [shape=diamond, style=filled, fillcolor="#FFF2CC", color="#BF9000", fontsize=10, label="{name.replace("_", " ")}"{extra}];'

eer = ['digraph EER { graph [rankdir=TB, nodesep=0.55, ranksep=0.8, fontname="Helvetica", splines=true, pad=0.3];',
       'node [fontname="Helvetica", fontsize=10]; edge [fontname="Helvetica", fontsize=11, color="#444444", arrowhead=none];',
       ent("Category", ["<U>category_id</U>", "category_name (U)", "description"]),
       ent("Product", ["<U>product_id</U>", "name (U)", "generic_name", "unit_price", "reorder_level", "requires_prescription"]),
       ent("Supplier", ["<U>supplier_id</U>", "name (U)", "phone (U)", "address", "is_active"]),
       ent("Purchase Order", ["<U>po_id</U>", "order_date", "status", "total_cost (derived)"]),
       ent("Stock Batch", ["<U>batch_id</U>", "batch_no", "received_qty", "quantity", "expiry_date", "cost_price"]),
       ent("Customer", ["<U>customer_id</U>", "name", "phone (U)", "registered_on"]),
       ent("Employee", ["<U>employee_id</U>", "name", "role", "phone (U)", "hire_date", "is_active"], "#E2F0D9", "#548235"),
       ent("Pharmacist", ["license_no (U)", "qualification"], "#E2F0D9", "#548235"),
       ent("Cashier", ["shift", "counter_no"], "#E2F0D9", "#548235"),
       ent("Sale", ["<U>sale_id</U>", "sale_date", "payment_method", "total_amount (derived)"]),
       ent("Sale Item", ["<U>sale_id, product_id</U>", "quantity", "unit_price"], "#FCE4D6", "#C55A11"),
       rel("classifies"), rel("supplies"), rel("contains"), rel("stocked_as"), rel("places"), rel("makes"), rel("includes"),
       rel("served_from", ', fillcolor="#FCE4D6"'),
       'isa [shape=circle, label="d", width=0.35, fixedsize=true, style=filled, fillcolor="#E2F0D9", color="#548235"];',
       'Category -> classifies [label="1"]; classifies -> Product [label="M"];',
       'Supplier -> supplies [label="1"]; supplies -> PurchaseOrder [label="M"];',
       'PurchaseOrder -> contains [label="1"]; contains -> StockBatch [label="M"];',
       'Product -> stocked_as [label="1"]; stocked_as -> StockBatch [label="M"];',
       'Customer -> places [label="1"]; places -> Sale [label="M"];',
       'Employee -> makes [label="1"]; makes -> Sale [label="M"];',
       'Sale -> includes [label="1"]; includes -> SaleItem [label="M", penwidth=2];',
       'Product -> includes [label="N (M:N via Sale Item)", style=dashed];',
       'SaleItem -> served_from [label="M"]; served_from -> StockBatch [label="N"];',
       'Employee -> isa [penwidth=2]; isa -> Pharmacist [dir=forward, arrowhead=none]; isa -> Cashier;',
       '{rank=same; Category; Supplier; Customer; Employee}',
       '{rank=same; Pharmacist; Cashier}',
       'labelloc=t; label=<<B>EER diagram - Pharmacy Inventory &amp; Sales Management System</B><BR/><FONT POINT-SIZE="10">underlined = primary key, (U) = unique, d = disjoint specialisation of EMPLOYEE (partial)</FONT>>;',
       '}']
run("\n".join(eer), "eer_diagram.png", 130)

# ------------------------------------------------------------------ relational schema (live)
db = mysql.connector.connect(user="root", unix_socket="/run/mysqld/mysqld.sock", database="pharmacy_db")
cur = db.cursor()
cur.execute("SELECT table_name, column_name, column_type, column_key, is_nullable FROM information_schema.columns "
            "WHERE table_schema='pharmacy_db' AND table_name NOT LIKE 'v\\_%' ORDER BY table_name, ordinal_position")
cols = {}
import re
def short(ty):
    ty = ty.replace(" unsigned", "").replace("int(10)", "int").replace("tinyint(1)", "bool").replace("tinyint(3)", "tinyint")
    return "enum" if ty.startswith("enum") else ty.replace("int(11)", "int")
for t, c, ty, key, nul in cur.fetchall():
    ty = short(ty)
    cols.setdefault(t, []).append((c, ty, key, nul))
cur.execute("SELECT table_name, column_name, referenced_table_name, referenced_column_name FROM information_schema.key_column_usage "
            "WHERE table_schema='pharmacy_db' AND referenced_table_name IS NOT NULL")
fks = cur.fetchall()
fkcols = {(t, c) for t, c, _, _ in fks}
core = ["categories", "products", "suppliers", "purchase_orders", "stock_batches", "customers", "employees", "sales", "sale_items"]
rs = ['digraph RS { graph [rankdir=LR, nodesep=0.35, ranksep=0.9, fontname="Helvetica", pad=0.3, splines=true];',
      'node [shape=plain, fontname="Helvetica", fontsize=10]; edge [arrowhead=crow, arrowtail=tee, dir=both, color="#555555"];']
for t, cl in cols.items():
    fill = "#DCE9F8" if t in core else ("#E2F0D9" if t in ("pharmacists", "cashiers") else "#EDEDED")
    rows = ""
    for c, ty, key, nul in cl:
        tag = "PK" if key == "PRI" else ("FK" if (t, c) in fkcols else "")
        if key == "PRI" and (t, c) in fkcols: tag = "PK,FK"
        name = f"<B>{c}</B>" if key == "PRI" else c
        rows += (f'<TR><TD ALIGN="LEFT" PORT="{c}">{name}</TD><TD ALIGN="LEFT"><FONT COLOR="#555555">{ty}</FONT></TD>'
                 f'<TD>' + (f'<FONT COLOR="#C00000">{tag}</FONT>' if tag else ' ') + '</TD></TR>')
    rs.append(f'{t} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2" COLOR="#2F5597">'
              f'<TR><TD COLSPAN="3" BGCOLOR="{fill}"><B>{t}</B></TD></TR>{rows}</TABLE>>];')
seen = set()
for t, c, rt, rc in fks:
    if (t, rt) in seen and t == "sale_allocations": pass
    rs.append(f'{rt}:{rc} -> {t}:{c};')
rs.append('labelloc=t; label=<<B>Relational schema (generated from the live MySQL database)</B>>;')
rs.append('}')
run("\n".join(rs), "relational_schema.png", 110)
print("diagrams written")
