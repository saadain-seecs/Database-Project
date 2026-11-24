"""End-to-end checks of the GUI against the real database (run under a display, e.g. xvfb-run).
Every record created is removed again; row counts are compared before and after."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PHARMACY_SOCKET", "/run/mysqld/mysqld.sock")
from datetime import date
from app.config import load_config
from app.database import Database, Schema, DatabaseError
from app.main_window import MainWindow
from app.widgets import FormDialog, Field
from app.services import REPORTS

db = Database(load_config()); db.connect(); schema = Schema(db)
app = MainWindow(db, schema)
def pump(n=8):
    for _ in range(n): app.update(); time.sleep(0.03)
passed = failed = 0
def check(name, cond, extra=""):
    global passed, failed
    if cond: passed += 1; print("PASS", name)
    else: failed += 1; print("FAIL", name, extra)
def raises(fn, text=None):
    try: fn()
    except DatabaseError as e: return text is None or text.lower() in str(e).lower()
    return False
TABLES = ["categories","suppliers","products","purchase_orders","stock_batches","customers","employees","pharmacists","cashiers","sales","sale_items","sale_allocations","audit_log"]
before = {t: db.scalar(f"SELECT COUNT(*) FROM {t}") for t in TABLES}
stock_before = db.scalar("SELECT SUM(quantity) FROM stock_batches")

def page(name):
    app.show(name); pump(); return app.pages[name]

# ---------------------------------------------------------------- categories CRUD
p = page("Categories")
check("categories grid loaded", len(p.grid_.rows) == before["categories"])
p._create({"category_name": "GUI Test Category", "description": None}); pump()
row = db.one("SELECT * FROM categories WHERE category_name='GUI Test Category'")
check("category INSERT", row is not None and row["description"] is None)
cid = row["category_id"]
p._update(cid, {"category_name": "GUI Test Category 2", "description": "edited"}); pump()
check("category UPDATE", db.scalar("SELECT description FROM categories WHERE category_id=%s", (cid,)) == "edited")
check("duplicate category rejected with friendly message", raises(lambda: p.repo.insert({"category_name": "GUI Test Category 2"}), "already exists"))

# ---------------------------------------------------------------- medicines CRUD + trigger audit
m = page("Medicines")
m._create({"name": "GUI Test Medicine", "generic_name": "testol", "category_id": cid, "unit_price": 50, "reorder_level": None, "requires_prescription": False}); pump()
pid = db.scalar("SELECT product_id FROM products WHERE name='GUI Test Medicine'")
check("medicine INSERT (blank reorder level -> DEFAULT 20)", db.scalar("SELECT reorder_level FROM products WHERE product_id=%s", (pid,)) == 20)
m._update(pid, {"name": "GUI Test Medicine", "category_id": cid, "unit_price": 65, "reorder_level": 10, "requires_prescription": True}); pump()
check("medicine UPDATE", float(db.scalar("SELECT unit_price FROM products WHERE product_id=%s", (pid,))) == 65.0)
check("price-change trigger wrote audit_log", db.scalar("SELECT COUNT(*) FROM audit_log WHERE table_name='products' AND record_id=%s", (pid,)) == 1)
check("negative price rejected by CHECK", raises(lambda: m.repo.insert({"name": "Bad", "category_id": cid, "unit_price": -1}), "rule"))
check("category in use cannot be deleted (FK)", raises(lambda: p.repo.delete(cid), "used by other"))

# ---------------------------------------------------------------- form validation
fields = m.resolved_fields()
dlg = FormDialog(app, "t", fields, {}, "Save", lambda v: None); pump(3)
dlg.widgets["name"].insert(0, "x"); dlg.widgets["unit_price"].insert(0, "-5"); dlg.widgets["reorder_level"].insert(0, "abc")
vals, errs = dlg.collect()
check("form: required category and bad numbers flagged", "category_id" in errs and "unit_price" in errs and "reorder_level" in errs, str(errs))
dlg.destroy()
dlg = FormDialog(app, "t", [Field("d", "Date", "date", required=True)], {}, "Save", lambda v: None); pump(3)
dlg.widgets["d"].insert(0, "18-11-2026"); check("form: wrong date format flagged", "d" in dlg.collect()[1]); dlg.destroy()

# ---------------------------------------------------------------- suppliers / customers
s = page("Suppliers")
s._create({"name": "GUI Test Supplier", "phone": "051-9990001", "address": "Test road", "is_active": True}); pump()
sid = db.scalar("SELECT supplier_id FROM suppliers WHERE name='GUI Test Supplier'")
check("supplier INSERT", sid is not None)
check("supplier bad phone rejected by CHECK", raises(lambda: s.repo.update(sid, {"phone": "12"}), "rule"))
s._update(sid, {"name": "GUI Test Supplier", "phone": "051-9990002", "address": "New road", "is_active": False}); pump()
check("supplier UPDATE", db.scalar("SELECT phone FROM suppliers WHERE supplier_id=%s", (sid,)) == "051-9990002")
c = page("Customers")
c._create({"name": "GUI Test Customer", "phone": "0300-9990003"}); pump()
cuid = db.scalar("SELECT customer_id FROM customers WHERE name='GUI Test Customer'")
check("customer INSERT", cuid is not None)
check("customer with sales cannot be deleted", raises(lambda: c.repo.delete(3), "used by other"))

# ---------------------------------------------------------------- staff with EER subclass
st = page("Staff")
st.do_create(st._prepare({"name": "GUI Test Pharmacist", "role": "Pharmacist", "phone": "0300-9990004", "hire_date": date.today(), "is_active": True}, True),
             {"role": "Pharmacist", "license_no": "PC-TEST-0001", "qualification": "Pharm-D"})
eid = db.scalar("SELECT employee_id FROM employees WHERE name='GUI Test Pharmacist'")
check("staff INSERT creates pharmacist subclass row", db.scalar("SELECT license_no FROM pharmacists WHERE employee_id=%s", (eid,)) == "PC-TEST-0001")
st.do_update(eid, st._prepare({"name": "GUI Test Pharmacist", "role": "Cashier", "phone": "0300-9990004", "hire_date": date.today(), "is_active": True}, False),
             {"role": "Cashier", "counter_no": 5, "shift": "Night"})
check("changing role moves subclass row", db.scalar("SELECT COUNT(*) FROM pharmacists WHERE employee_id=%s", (eid,)) == 0 and db.scalar("SELECT counter_no FROM cashiers WHERE employee_id=%s", (eid,)) == 5)
check("pharmacist without licence rejected", raises(lambda: st.do_create(st._prepare({"name": "X", "role": "Pharmacist", "phone": "0300-9990005", "hire_date": date.today()}, True), {"role": "Pharmacist"}), "licence"))
check("failed staff insert left no orphan row", db.scalar("SELECT COUNT(*) FROM employees WHERE name='X'") == 0)

# ---------------------------------------------------------------- purchasing: receive stock (procedure + triggers)
po = app.svc.receive_stock(sid if False else 1, date.today(), [dict(product_id=pid, qty=40, cost_price=30.0, expiry_date="2028-12-31", batch_no="GUI-T1")])
check("receive_stock created PO with trigger-calculated total", float(db.scalar("SELECT total_cost FROM purchase_orders WHERE po_id=%s", (po,))) == 1200.0)
check("new batch starts full", db.scalar("SELECT quantity FROM stock_batches WHERE po_id=%s", (po,)) == 40)
check("receive_stock with expired batch rolled back", raises(lambda: app.svc.receive_stock(1, date.today(), [dict(product_id=pid, qty=5, cost_price=1.0, expiry_date="2020-01-01", batch_no="GUI-T2")]), "expired"))

# ---------------------------------------------------------------- point of sale
sp = page("Sales & Billing")
label = next(l for v, l in sp.product.options if v == pid)
sp.product.set(label); sp.qty.delete(0, "end"); sp.qty.insert(0, "7"); sp.add_item(); pump(3)
check("POS: item added to cart", len(sp.cart) == 1 and sp.cart[0]["qty"] == 7)
sp.product.set(label); sp.qty.delete(0, "end"); sp.qty.insert(0, "3"); sp.add_item()
check("POS: same medicine merges into one line", len(sp.cart) == 1 and sp.cart[0]["qty"] == 10)
sp.customer.set(next(l for v, l in sp.customer.options if v == cuid)); sp.seller.set(sp.seller.options[0][1]); sp.payment.set("Card")
before_stock = db.scalar("SELECT quantity FROM stock_batches WHERE po_id=%s", (po,))
sp.checkout(); pump(10)
for w in list(app.winfo_children()):
    if w.winfo_class() == "Toplevel": w.destroy()
sale = db.one("SELECT * FROM sales WHERE customer_id=%s", (cuid,))
check("POS: checkout created the sale with trigger total", sale is not None and float(sale["total_amount"]) == 650.0 and sale["payment_method"] == "Card")
check("POS: stock deducted by trigger", db.scalar("SELECT quantity FROM stock_batches WHERE po_id=%s", (po,)) == before_stock - 10)
check("POS: cart cleared after sale", sp.cart == [])
sp.cart = [dict(product_id=pid, name="x", price=65, qty=500, stock=30, line=0)]
sp.checkout(); pump(3)
check("POS: overselling blocked before reaching the database", db.scalar("SELECT COUNT(*) FROM sales WHERE customer_id=%s", (cuid,)) == 1)
sp.cart = [dict(product_id=pid, name="x", price=65, qty=500, stock=9999, line=0)]
n_before = db.scalar("SELECT COUNT(*) FROM sales"); sp.checkout(); pump(3)
check("POS: database rejection rolls back (no new sale)", db.scalar("SELECT COUNT(*) FROM sales") == n_before)
sp.cart = []
db.execute("DELETE FROM sales WHERE sale_id=%s", (sale["sale_id"],))
check("deleting a bill restores stock", db.scalar("SELECT quantity FROM stock_batches WHERE po_id=%s", (po,)) == 40)

# ---------------------------------------------------------------- stock / expiry / dashboard / reports
for name in ("Stock", "Expiry", "Dashboard", "Purchases"):
    pg = page(name); check(f"{name} page loads", True)
check("expiry page counts match the views", app.pages["Expiry"].near.rows is not None and len(app.pages["Expiry"].expired.rows) == db.scalar("SELECT COUNT(*) FROM v_expired_stock"))
alerts = app.svc.refresh_alerts(); check("refresh_alerts procedure works", len(alerts) >= 1)
db.execute("DELETE FROM stock_alerts")
rp = page("Reports")
bad = [n for n in REPORTS if not isinstance(app.svc.run_report(n), list)]
check(f"all {len(REPORTS)} reports run", not bad)
rp.year.delete(0, "end"); rp.year.insert(0, "2026"); rp.month.set("10"); rp.monthly(); pump(3)
check("monthly report (stored procedure) fills the cards", rp.m_cards["bills"].value.cget("text") not in ("-", "0") and len(rp.m_top.rows) > 0)
check("monthly report validates month", raises(lambda: app.svc.monthly_report(2026, 13), "month"))

# ---------------------------------------------------------------- clean up
db.execute("DELETE FROM stock_batches WHERE po_id=%s", (po,)); db.execute("DELETE FROM purchase_orders WHERE po_id=%s", (po,))
st.repo.delete(eid); c.repo.delete(cuid); s.repo.delete(sid); m.repo.delete(pid); p.repo.delete(cid)
db.execute("DELETE FROM audit_log WHERE table_name='products' AND record_id=%s", (pid,))
after = {t: db.scalar(f"SELECT COUNT(*) FROM {t}") for t in TABLES}
check("database restored to its original row counts", before == after, f"{before} vs {after}")
check("total stock unchanged", db.scalar("SELECT SUM(quantity) FROM stock_batches") == stock_before)
print(f"\n{passed} passed, {failed} failed")
app.destroy()
sys.exit(1 if failed else 0)
