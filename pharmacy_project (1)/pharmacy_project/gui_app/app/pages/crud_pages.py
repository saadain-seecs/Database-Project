"""Medicines, categories, suppliers, customers and staff screens."""
import customtkinter as ctk

from .. import theme as T
from ..database import Repository
from ..widgets import DataTable, Field, BaseDialog, button, info_dialog
from .base import CrudPage

YN = lambda v: "Yes" if v else "No"
C = lambda key, label, width=110, anchor="w", fmt=None, stretch=True: dict(key=key, label=label, width=width, anchor=anchor, fmt=fmt, stretch=stretch)


class BatchesDialog(BaseDialog):
    def __init__(self, master, title, rows):
        super().__init__(master, title, 860, 460)
        ctk.CTkLabel(self, text=title, font=T.font(17, "bold"), text_color=T.NAVY, anchor="w").pack(fill="x", padx=26, pady=(20, 8))
        cols = [C("batch_no", "Batch", 120), C("supplier", "Supplier", 190), C("order_date", "Delivered", 100), C("received_qty", "Received", 80, "e"),
                C("quantity", "On shelf", 80, "e"), C("expiry_date", "Expires", 100), C("cost_price", "Cost", 80, "e"), C("state", "Status", 100)]
        t = DataTable(self, cols, row_tag=lambda r: {"Expired": "danger", "Expires soon": "warn", "Empty": None}.get(r["state"]))
        t.pack(fill="both", expand=True, padx=26)
        t.load(rows)
        button(self, "Close", self.destroy, "navy", width=110).pack(pady=14)


BATCH_SQL = """SELECT b.batch_id, p.name AS medicine, b.batch_no, s.name AS supplier, po.order_date, b.received_qty, b.quantity, b.expiry_date, b.cost_price,
       CASE WHEN b.quantity = 0 THEN 'Empty' WHEN b.expiry_date < CURRENT_DATE THEN 'Expired'
            WHEN b.expiry_date <= DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY) THEN 'Expires soon' ELSE 'OK' END AS state
FROM stock_batches b JOIN products p ON p.product_id = b.product_id JOIN purchase_orders po ON po.po_id = b.po_id
JOIN suppliers s ON s.supplier_id = po.supplier_id"""


class MedicinesPage(CrudPage):
    title, subtitle = "Medicines", "Catalogue, prices and live stock levels"
    table, noun, search_hint = "products", "medicine", "Search medicine, generic name, category..."
    pk = "product_id"
    select_sql = """SELECT p.product_id, p.name, p.generic_name, c.category_name, p.unit_price, s.on_hand, p.reorder_level, p.requires_prescription, s.expired_qty
                    FROM products p JOIN categories c ON c.category_id = p.category_id JOIN v_product_stock s ON s.product_id = p.product_id ORDER BY p.name"""
    columns = [C("product_id", "ID", 50, "e", stretch=False), C("name", "Medicine", 210), C("generic_name", "Generic name", 170), C("category_name", "Category", 150),
               C("unit_price", "Price", 80, "e", T.money), C("on_hand", "In stock", 80, "e"), C("reorder_level", "Reorder at", 85, "e"),
               C("requires_prescription", "Rx only", 70, "center", YN), C("status", "Status", 100)]

    def __init__(self, master, app):
        self.fields = [Field("name", "Medicine name", span=2), Field("generic_name", "Generic name"),
                       Field("category_id", "Category", "choice", required=True, options=lambda: app.svc.categories()),
                       Field("unit_price", "Selling price (Rs)", "decimal", minimum=0), Field("reorder_level", "Reorder level", "int", minimum=0, help="Alert when sellable stock falls below this."),
                       Field("requires_prescription", "Prescription required", "bool")]
        if "manufacturer" in app.schema.columns["products"]:
            self.fields.insert(2, Field("manufacturer", "Manufacturer"))
        super().__init__(master, app)

    def build_toolbar(self):
        super().build_toolbar()
        self.cat_filter = ctk.CTkComboBox(self.toolbar, values=["All categories"], width=200, height=36, command=lambda _: self.apply_filters(), state="readonly",
                                          button_color=T.GREEN, border_color=T.BORDER, fg_color="white", text_color=T.TEXT, font=T.font(13))
        self.cat_filter.set("All categories")
        self.cat_filter.pack(side="left", padx=(8, 0))
        self.stat_filter = ctk.CTkComboBox(self.toolbar, values=["All stock levels", "Low stock", "Out of stock", "In stock"], width=170, height=36, command=lambda _: self.apply_filters(),
                                           state="readonly", button_color=T.GREEN, border_color=T.BORDER, fg_color="white", text_color=T.TEXT, font=T.font(13))
        self.stat_filter.pack(side="left", padx=8)
        button(self.toolbar, "Batches", self.show_batches, "soft", width=100).pack(side="right")
        self.stat_filter.set("All stock levels")

    def row_tag(self, r):
        return {"Out of stock": "danger", "Low stock": "warn"}.get(r.get("status"))

    def post_process(self, rows):
        for r in rows:
            r["status"] = "Out of stock" if r["on_hand"] == 0 else ("Low stock" if r["on_hand"] < r["reorder_level"] else "In stock")
        self.cat_filter.configure(values=["All categories"] + [n for _, n in self.svc.categories()])
        return rows

    def apply_filters(self):
        cat, st = self.cat_filter.get(), self.stat_filter.get()
        rows = [r for r in self.grid_.base_rows if (cat == "All categories" or r["category_name"] == cat) and (st == "All stock levels" or r["status"] == st)]
        self.grid_.load(rows)

    def on_show(self):
        rows = self.guard(self.fetch)
        if rows is None:
            return
        self.grid_.base_rows = self.post_process(rows)
        self.apply_filters()

    def show_batches(self):
        row = self.grid_.selected()
        if not row:
            return self.notify("Select a medicine first.", "warn")
        rows = self.guard(self.db.query, BATCH_SQL + " WHERE b.product_id = %s ORDER BY b.expiry_date", (row["product_id"],))
        if rows is not None:
            BatchesDialog(self, f"Batches of {row['name']}", rows)

    def describe(self, row):
        return f"{row['name']}  ({row['category_name']})"


class CategoriesPage(CrudPage):
    title, subtitle = "Categories", "Groups used to organise the medicine catalogue"
    table, noun, search_hint = "categories", "category", "Search categories..."
    select_sql = """SELECT c.category_id, c.category_name, c.description, COUNT(p.product_id) AS products
                    FROM categories c LEFT JOIN products p ON p.category_id = c.category_id GROUP BY c.category_id, c.category_name, c.description ORDER BY c.category_name"""
    columns = [C("category_id", "ID", 50, "e", stretch=False), C("category_name", "Category", 220), C("description", "Description", 380), C("products", "Medicines", 90, "e")]

    def __init__(self, master, app):
        self.fields = [Field("category_name", "Category name", span=2), Field("description", "Description", "textarea", span=2)]
        super().__init__(master, app)


class SuppliersPage(CrudPage):
    title, subtitle = "Suppliers", "Wholesalers the pharmacy buys stock from"
    table, noun, search_hint = "suppliers", "supplier", "Search supplier, phone, address..."
    select_sql = """SELECT s.supplier_id, s.name, s.phone, s.address, s.is_active, COUNT(po.po_id) AS orders, COALESCE(SUM(CASE WHEN po.status='Received' THEN po.total_cost END),0) AS purchased
                    FROM suppliers s LEFT JOIN purchase_orders po ON po.supplier_id = s.supplier_id GROUP BY s.supplier_id, s.name, s.phone, s.address, s.is_active ORDER BY s.name"""
    columns = [C("supplier_id", "ID", 50, "e", stretch=False), C("name", "Supplier", 210), C("phone", "Phone", 110), C("address", "Address", 260),
               C("is_active", "Active", 70, "center", YN), C("orders", "Orders", 70, "e"), C("purchased", "Purchased", 110, "e", T.money)]

    def __init__(self, master, app):
        self.fields = [Field("name", "Supplier name", span=2), Field("phone", "Phone", help="Format: 051-1234567"), Field("is_active", "Active supplier", "bool", default=True),
                       Field("address", "Address", span=2)]
        super().__init__(master, app)

    def row_tag(self, r):
        return None if r["is_active"] else "warn"


class CustomersPage(CrudPage):
    title, subtitle = "Customers", "Registered customers and their purchase history"
    table, noun, search_hint = "customers", "customer", "Search name or phone..."
    select_sql = """SELECT c.customer_id, c.name, c.phone, c.registered_on, COUNT(s.sale_id) AS bills, COALESCE(SUM(s.total_amount),0) AS spent
                    FROM customers c LEFT JOIN sales s ON s.customer_id = c.customer_id GROUP BY c.customer_id, c.name, c.phone, c.registered_on ORDER BY c.customer_id"""
    columns = [C("customer_id", "ID", 50, "e", stretch=False), C("name", "Customer", 220), C("phone", "Phone", 120), C("registered_on", "Registered", 100),
               C("bills", "Bills", 70, "e"), C("spent", "Total spent", 110, "e", T.money)]

    def __init__(self, master, app):
        self.fields = [Field("name", "Full name", span=2), Field("phone", "Mobile number", help="Format: 0300-1234567 (optional)")]
        if "email" in app.schema.columns["customers"]:
            self.fields.append(Field("email", "Email"))
        super().__init__(master, app)

    def build_toolbar(self):
        super().build_toolbar()
        button(self.toolbar, "Purchase history", self.history, "soft", width=140).pack(side="right")

    def history(self):
        row = self.grid_.selected()
        if not row:
            return self.notify("Select a customer first.", "warn")
        sales = self.guard(self.db.query, "SELECT sale_id, sale_date, payment_method, total_amount FROM sales WHERE customer_id=%s ORDER BY sale_date DESC", (row["customer_id"],))
        if sales is None:
            return
        lines = [f"{row['name']}  -  {len(sales)} bill(s)", ""] + [f"#{s['sale_id']:<4} {T.display(s['sale_date']):<17} {s['payment_method']:<14} {T.money(s['total_amount']):>10}" for s in sales]
        info_dialog(self, "Purchase history", lines or ["No purchases yet."], 520, 420)

    def describe(self, row):
        return f"{row['name']}  {row['phone'] or ''}"


class StaffPage(CrudPage):
    """Employees with the EER specialisation: pharmacist / cashier details are stored in their own tables."""
    title, subtitle = "Staff", "Employees, roles and licence / counter details"
    table, noun, search_hint = "employees", "employee", "Search name, role, phone..."
    select_sql = """SELECT e.employee_id, e.name, e.role, e.phone, e.hire_date, e.is_active,
                           CASE e.role WHEN 'Pharmacist' THEN CONCAT('Licence ', ph.license_no) WHEN 'Cashier' THEN CONCAT(ca.shift, ' shift, counter ', ca.counter_no) ELSE '' END AS details,
                           COUNT(s.sale_id) AS bills
                    FROM employees e LEFT JOIN pharmacists ph ON ph.employee_id = e.employee_id LEFT JOIN cashiers ca ON ca.employee_id = e.employee_id
                    LEFT JOIN sales s ON s.employee_id = e.employee_id GROUP BY e.employee_id, e.name, e.role, e.phone, e.hire_date, e.is_active, ph.license_no, ca.shift, ca.counter_no ORDER BY e.employee_id"""
    columns = [C("employee_id", "ID", 50, "e", stretch=False), C("name", "Employee", 190), C("role", "Role", 120), C("phone", "Phone", 110), C("hire_date", "Hired", 95),
               C("is_active", "Active", 65, "center", YN), C("details", "Role details", 210), C("bills", "Bills", 60, "e")]

    def __init__(self, master, app):
        self.fields = [Field("name", "Full name", span=2), Field("role", "Role", "choice"), Field("phone", "Mobile number", help="Format: 0300-1234567"),
                       Field("hire_date", "Hire date", "date", required=True), Field("is_active", "Currently employed", "bool", default=True),
                       Field("license_no", "Licence number", help="Pharmacists only", required=False), Field("qualification", "Qualification", help="Pharmacists only", required=False),
                       Field("shift", "Shift", "choice", help="Cashiers only", required=False, options=app.schema.col("cashiers", "shift")["enum"] and [(v, v) for v in app.schema.col("cashiers", "shift")["enum"]]),
                       Field("counter_no", "Counter number", "int", help="Cashiers only (1-6)", required=False, minimum=1)]
        super().__init__(master, app)
        self.pharm, self.cash = Repository(self.db, self.schema, "pharmacists"), Repository(self.db, self.schema, "cashiers")

    def resolved_fields(self):
        fs = []
        for f in self.fields:
            if f.name in ("license_no", "qualification", "shift", "counter_no"):
                import copy
                g = copy.copy(f)
                g.virtual = True
                if g.kind == "choice":
                    g.optional_choice = True
                fs.append(g)
        base = super().resolved_fields()
        names = {f.name for f in base}
        return base + [f for f in fs if f.name not in names]

    def row_tag(self, r):
        return None if r["is_active"] else "warn"

    def initial_for_edit(self, raw):
        data = dict(raw)
        for repo in (self.pharm, self.cash):
            extra = repo.get(raw["employee_id"])
            if extra:
                data.update({k: v for k, v in extra.items() if k != "employee_id"})
        return data

    def _prepare(self, values, creating):
        emp_cols = self.schema.columns["employees"]
        return {k: v for k, v in values.items() if k in emp_cols and not (v is None and not emp_cols[k]["nullable"])}

    def _validate_role(self, raw):
        if raw["role"] == "Pharmacist" and not raw.get("license_no"):
            from ..database import DatabaseError
            raise DatabaseError("A pharmacist needs a licence number.")
        if raw["role"] == "Cashier" and not raw.get("counter_no"):
            from ..database import DatabaseError
            raise DatabaseError("A cashier needs a counter number.")

    def _save_subclass(self, emp_id, raw):
        self.pharm.delete(emp_id)
        self.cash.delete(emp_id)
        if raw["role"] == "Pharmacist":
            d = {"employee_id": emp_id, "license_no": raw["license_no"]}
            if raw.get("qualification"):
                d["qualification"] = raw["qualification"]
            self.pharm.insert(d)
        elif raw["role"] == "Cashier":
            d = {"employee_id": emp_id, "counter_no": raw["counter_no"]}
            if raw.get("shift"):
                d["shift"] = raw["shift"]
            self.cash.insert(d)

    def do_create(self, clean, raw):
        self._validate_role(raw)
        with self.db.transaction():
            emp_id = self.repo.insert(clean)
            self._save_subclass(emp_id, raw)

    def do_update(self, key, clean, raw):
        self._validate_role(raw)
        with self.db.transaction():
            self.repo.update(key, clean)
            self._save_subclass(key, raw)

    def describe(self, row):
        return f"{row['name']}  ({row['role']})"
