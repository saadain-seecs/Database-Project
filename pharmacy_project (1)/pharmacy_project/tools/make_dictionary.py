#!/usr/bin/env python3
"""Builds the data dictionary (docs/data_dictionary.json + docs/data_dictionary.md) from the live database."""
import json, re, os, mysql.connector
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PURPOSE = {
 "categories": "Groups medicines into categories (analgesics, antibiotics ...).",
 "products": "Catalogue of medicines and devices sold by the pharmacy.",
 "suppliers": "Wholesalers / distributors the pharmacy buys from.",
 "purchase_orders": "One delivery / order placed with a supplier.",
 "stock_batches": "Stock received in a purchase order, tracked per batch with its own expiry date.",
 "customers": "Customers (includes one 'Walk-in Customer' for anonymous sales).",
 "employees": "All staff - superclass of the EER specialisation.",
 "pharmacists": "EER subclass: licensed pharmacists (extra attributes).",
 "cashiers": "EER subclass: cashiers (shift and counter).",
 "sales": "Header of a bill: who bought, who served, when and how paid.",
 "sale_items": "Lines of a bill; resolves the Sales M:N Products relationship.",
 "sale_allocations": "Which batch(es) every bill line was taken from (FEFO) with the batch cost - gives exact profit.",
 "stock_alerts": "Low-stock / near-expiry / expired alerts produced by the daily event.",
 "audit_log": "Audit trail written by triggers (price changes).",
}
DESC = {
 ("categories","category_id"):"Surrogate key.", ("categories","category_name"):"Unique category name.", ("categories","description"):"Free-text note.",
 ("suppliers","supplier_id"):"Surrogate key.", ("suppliers","name"):"Supplier trade name (unique).", ("suppliers","phone"):"Contact number, format 051-1234567.",
 ("suppliers","address"):"Postal address.", ("suppliers","is_active"):"FALSE = no longer used for orders.",
 ("products","product_id"):"Surrogate key.", ("products","name"):"Brand / product name with strength (unique).", ("products","generic_name"):"Active ingredient.",
 ("products","manufacturer"):"Added later with ALTER TABLE (DDL demo); optional.", ("products","category_id"):"Category the product belongs to.",
 ("products","unit_price"):"Selling price per unit in PKR.", ("products","reorder_level"):"Re-order when sellable stock falls below this.",
 ("products","requires_prescription"):"TRUE for prescription-only medicines.",
 ("purchase_orders","po_id"):"Surrogate key.", ("purchase_orders","supplier_id"):"Supplier the order was placed with.", ("purchase_orders","order_date"):"Date of the order / delivery.",
 ("purchase_orders","status"):"Pending, Received or Cancelled.", ("purchase_orders","total_cost"):"Sum of received_qty x cost_price of its batches (maintained by trigger).",
 ("stock_batches","batch_id"):"Surrogate key.", ("stock_batches","product_id"):"Medicine in this batch.", ("stock_batches","po_id"):"Purchase order that delivered it.",
 ("stock_batches","batch_no"):"Manufacturer lot number (unique per product).", ("stock_batches","received_qty"):"Units delivered.",
 ("stock_batches","quantity"):"Units still on the shelf (falls as sales are made).", ("stock_batches","expiry_date"):"Last day the batch may be sold.",
 ("stock_batches","cost_price"):"Purchase price per unit in PKR.",
 ("customers","customer_id"):"Surrogate key.", ("customers","name"):"Customer name.", ("customers","phone"):"Mobile number 03xx-xxxxxxx; NULL for the walk-in customer.",
 ("customers","email"):"Added later with ALTER TABLE (DDL demo); optional, unique.", ("customers","registered_on"):"Date the customer was registered.",
 ("employees","employee_id"):"Surrogate key.", ("employees","name"):"Employee name.", ("employees","role"):"Pharmacist, Cashier, Manager or Inventory Clerk.",
 ("employees","phone"):"Mobile number (unique).", ("employees","hire_date"):"Date joined.", ("employees","is_active"):"FALSE after the employee leaves.",
 ("pharmacists","employee_id"):"Same key as the employee (subclass).", ("pharmacists","license_no"):"Pharmacy-council licence number (unique).", ("pharmacists","qualification"):"Degree, default Pharm-D.",
 ("cashiers","employee_id"):"Same key as the employee (subclass).", ("cashiers","shift"):"Morning, Evening or Night.", ("cashiers","counter_no"):"Billing counter 1-6.",
 ("sales","sale_id"):"Bill number.", ("sales","customer_id"):"Buyer.", ("sales","employee_id"):"Pharmacist / cashier who served.", ("sales","sale_date"):"Date and time of the sale.",
 ("sales","payment_method"):"Cash, Card or Mobile Wallet.", ("sales","total_amount"):"Bill total, maintained by trigger from the bill lines.",
 ("sale_items","sale_id"):"Bill the line belongs to.", ("sale_items","product_id"):"Medicine sold.", ("sale_items","quantity"):"Units sold (> 0).", ("sale_items","unit_price"):"Price charged on the day of sale.",
 ("sale_allocations","sale_id"):"Bill number (part of the sale-line key).", ("sale_allocations","product_id"):"Medicine (part of the sale-line key).", ("sale_allocations","batch_id"):"Batch the units were taken from.",
 ("sale_allocations","quantity"):"Units taken from that batch.", ("sale_allocations","cost_price"):"Batch cost per unit at the time of sale.",
 ("stock_alerts","alert_id"):"Surrogate key.", ("stock_alerts","alert_type"):"LOW_STOCK, NEAR_EXPIRY or EXPIRED.", ("stock_alerts","product_id"):"Product concerned.",
 ("stock_alerts","batch_id"):"Batch concerned (NULL for low-stock alerts).", ("stock_alerts","message"):"Human-readable alert text.", ("stock_alerts","created_at"):"When the alert was generated.",
 ("audit_log","log_id"):"Surrogate key.", ("audit_log","table_name"):"Table that changed.", ("audit_log","record_id"):"Key of the changed row.", ("audit_log","action"):"Kind of change, e.g. PRICE_CHANGE.",
 ("audit_log","old_value"):"Value before.", ("audit_log","new_value"):"Value after.", ("audit_log","changed_at"):"Time of change.", ("audit_log","changed_by"):"Database user who made the change.",
}
db = mysql.connector.connect(user="root", unix_socket="/run/mysqld/mysqld.sock", database="pharmacy_db")
cur = db.cursor()
def q(sql): cur.execute(sql); return cur.fetchall()
cols = q("SELECT table_name, column_name, column_type, is_nullable, column_key, column_default FROM information_schema.columns "
         "WHERE table_schema='pharmacy_db' AND table_name NOT LIKE 'v\\_%' ORDER BY table_name, ordinal_position")
fks = {(t, c): f"{rt}({rc})" for t, c, rt, rc in q("SELECT table_name, column_name, referenced_table_name, referenced_column_name FROM information_schema.key_column_usage WHERE table_schema='pharmacy_db' AND referenced_table_name IS NOT NULL")}
uniq = {}
for t, c, cn in q("SELECT table_name, column_name, constraint_name FROM information_schema.key_column_usage WHERE table_schema='pharmacy_db' AND constraint_name LIKE 'uq\\_%'"):
    uniq.setdefault((t, c), []).append(cn)
checks = q("SELECT table_name, constraint_name, check_clause FROM information_schema.check_constraints WHERE constraint_schema='pharmacy_db'")
order = ["categories","products","suppliers","purchase_orders","stock_batches","customers","employees","pharmacists","cashiers","sales","sale_items","sale_allocations","stock_alerts","audit_log"]
out = []
for t in order:
    rowcount = q(f"SELECT COUNT(*) FROM {t}")[0][0]
    rows = []
    for tt, c, ty, nul, key, dflt in cols:
        if tt != t: continue
        cons = []
        if key == "PRI": cons.append("PK")
        if (t, c) in fks: cons.append("FK -> " + fks[(t, c)])
        if (t, c) in uniq: cons.append("UNIQUE")
        for ct, cn, clause in checks:
            if ct == t and re.search(r"`?%s`?" % c, clause) and not (c == "quantity" and t == "stock_batches" and cn != "ck_batch_quantity"):
                cons.append("CHECK " + clause.replace("`", "")[:60])
        if dflt not in (None, "NULL"): cons.append("DEFAULT " + str(dflt).strip("'"))
        rows.append(dict(column=c, type=ty.replace(" unsigned", " unsigned"), nullable=nul, constraints="; ".join(dict.fromkeys(cons)),
                         description=DESC.get((t, c), "")))
    out.append(dict(table=t, purpose=PURPOSE[t], rowcount=rowcount, columns=rows))
json.dump(out, open(os.path.join(ROOT, "docs", "data_dictionary.json"), "w"), indent=1)
md = ["# Data dictionary\n"]
for t in out:
    md.append(f"## {t['table']}  ({t['rowcount']} rows)\n{t['purpose']}\n\n| Column | Type | Null | Constraints | Description |\n|---|---|---|---|---|")
    for r in t["columns"]:
        md.append(f"| {r['column']} | {r['type']} | {r['nullable']} | {r['constraints']} | {r['description']} |")
    md.append("")
open(os.path.join(ROOT, "docs", "data_dictionary.md"), "w").write("\n".join(md))
print("dictionary:", len(out), "tables")

stats = {}
stats["tables"] = q("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='pharmacy_db' AND table_type='BASE TABLE'")[0][0]
for typ in ("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK"):
    stats[typ] = q(f"SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema='pharmacy_db' AND constraint_type='{typ}'")[0][0]
stats["triggers"] = q("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='pharmacy_db'")[0][0]
stats["procedures"] = q("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='pharmacy_db' AND routine_type='PROCEDURE'")[0][0]
stats["functions"] = q("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='pharmacy_db' AND routine_type='FUNCTION'")[0][0]
stats["views"] = q("SELECT COUNT(*) FROM information_schema.views WHERE table_schema='pharmacy_db'")[0][0]
stats["events"] = q("SELECT COUNT(*) FROM information_schema.events WHERE event_schema='pharmacy_db'")[0][0]
stats["indexes"] = q("SELECT COUNT(DISTINCT table_name, index_name) FROM information_schema.statistics WHERE table_schema='pharmacy_db' AND index_name LIKE 'idx\\_%'")[0][0]
json.dump(stats, open(os.path.join(ROOT, "docs", "stats.json"), "w"), indent=1)
print(stats)
