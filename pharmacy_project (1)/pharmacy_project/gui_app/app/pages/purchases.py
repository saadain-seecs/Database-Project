"""Purchase management: purchase orders and receiving stock from suppliers."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import customtkinter as ctk

from .. import theme as T
from ..database import DatabaseError
from ..widgets import DataTable, SearchCombo, BaseDialog, button, card, confirm, search_bar
from .base import Page
from .crud_pages import BatchesDialog, C


class ReceiveStockDialog(BaseDialog):
    """Record a delivery: one purchase order with one stock batch per line (procedure sp_receive_stock)."""

    def __init__(self, master, svc, on_done):
        super().__init__(master, "Receive stock", 900, 640)
        self.svc, self.on_done, self.lines = svc, on_done, []
        ctk.CTkLabel(self, text="Receive stock from a supplier", font=T.font(18, "bold"), text_color=T.NAVY).pack(anchor="w", padx=26, pady=(20, 0))
        ctk.CTkLabel(self, text="Creates a Received purchase order and one batch per line. Batches start full; the PO total is calculated by the database.",
                     font=T.font(12), text_color=T.MUTED).pack(anchor="w", padx=26)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=26, pady=(10, 4))
        self.supplier = SearchCombo(top, svc.suppliers(), width=330)
        self.supplier.pack(side="left")
        self.odate = ctk.CTkEntry(top, width=130, height=36, border_color=T.BORDER, fg_color="white", font=T.font(13))
        self.odate.insert(0, date.today().isoformat())
        self.odate.pack(side="left", padx=10)
        ctk.CTkLabel(top, text="Supplier  /  order date (YYYY-MM-DD)", font=T.font(11), text_color=T.MUTED).pack(side="left")
        box = card(self)
        box.pack(fill="x", padx=26, pady=8)
        r = ctk.CTkFrame(box, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=12)
        self.product = SearchCombo(r, svc.products_simple(), width=250)
        self.product.grid(row=0, column=0, padx=(0, 6))
        self.e = {}
        for i, (key, ph, w) in enumerate([("qty", "Quantity", 80), ("cost", "Cost / unit", 90), ("expiry", "Expiry YYYY-MM-DD", 140), ("batch", "Batch no.", 110)], 1):
            en = ctk.CTkEntry(r, width=w, height=36, placeholder_text=ph, border_color=T.BORDER, fg_color="white", font=T.font(13))
            en.grid(row=0, column=i, padx=3)
            self.e[key] = en
        button(r, "+ Add line", self.add_line, "primary", width=100).grid(row=0, column=5, padx=(6, 0))
        self.table = DataTable(self, [C("name", "Medicine", 240), C("qty", "Qty", 60, "e"), C("cost_price", "Cost", 80, "e", T.money), C("expiry_date", "Expiry", 100),
                                      C("batch_no", "Batch", 110), C("total", "Line cost", 100, "e", T.money)], height=7)
        self.table.pack(fill="both", expand=True, padx=26)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=26, pady=14)
        self.total = ctk.CTkLabel(bar, text="Total: Rs 0", font=T.font(16, "bold"), text_color=T.NAVY)
        self.total.pack(side="left")
        button(bar, "Save delivery", self.save, "primary", width=150).pack(side="right")
        button(bar, "Remove line", self.remove, "ghost", width=110).pack(side="right", padx=8)
        button(bar, "Cancel", self.destroy, "ghost", width=90).pack(side="right")
        self.msg = ctk.CTkLabel(self, text="", text_color=T.RED, font=T.font(12, "bold"))
        self.msg.pack(pady=(0, 6))

    def add_line(self):
        try:
            pid = self.product.value()
            if pid is None:
                raise ValueError("Choose a medicine.")
            qty = int(self.e["qty"].get())
            cost = Decimal(self.e["cost"].get())
            exp = datetime.strptime(self.e["expiry"].get().strip(), "%Y-%m-%d").date()
            batch = self.e["batch"].get().strip()
            if qty <= 0 or cost < 0 or not batch:
                raise ValueError("Quantity must be above 0, cost cannot be negative and a batch number is required.")
        except (ValueError, InvalidOperation) as e:
            self.msg.configure(text=str(e) if "Choose" in str(e) or "Quantity" in str(e) else "Check quantity, cost and the date format YYYY-MM-DD.")
            return
        self.msg.configure(text="")
        self.lines.append(dict(product_id=pid, name=self.product.get().split("   ")[0], qty=qty, cost_price=cost, expiry_date=exp, batch_no=batch, total=cost * qty))
        for en in self.e.values():
            en.delete(0, "end")
        self.product.clear()
        self.refresh()

    def remove(self):
        s = self.table.selected()
        if s:
            self.lines.remove(s)
            self.refresh()

    def refresh(self):
        self.table.load(self.lines)
        self.total.configure(text=f"Total: {T.money(sum(l['total'] for l in self.lines))}")

    def save(self):
        sid = self.supplier.value()
        if sid is None or not self.lines:
            return self.msg.configure(text="Choose a supplier and add at least one line.")
        try:
            od = datetime.strptime(self.odate.get().strip(), "%Y-%m-%d").date()
            po = self.svc.receive_stock(sid, od, [{k: l[k] if k != "cost_price" else float(l[k]) for k in ("product_id", "qty", "cost_price", "expiry_date", "batch_no")} for l in self.lines])
        except ValueError:
            return self.msg.configure(text="Order date must be YYYY-MM-DD.")
        except DatabaseError as e:
            return self.msg.configure(text=f"Rejected and rolled back: {e}")
        self.on_done(po)
        self.destroy()


class PurchasesPage(Page):
    title, subtitle = "Purchase Management", "Purchase orders and stock deliveries from suppliers"

    def __init__(self, master, app):
        super().__init__(master, app)
        button(self.actions, "+  Receive stock", self.receive, "primary", width=160).pack(side="right")
        button(self.actions, "New pending order", self.new_pending, "ghost", width=160).pack(side="right", padx=8)
        bar = ctk.CTkFrame(self.body, fg_color="transparent")
        bar.pack(fill="x")
        search_bar(bar, lambda s: self.table.filter(s), "Search supplier, status...", 280).pack(side="left")
        self.status = ctk.CTkComboBox(bar, values=["All statuses"] + self.schema.col("purchase_orders", "status")["enum"], width=170, height=36, state="readonly",
                                      command=lambda _: self.apply(), button_color=T.GREEN, border_color=T.BORDER, fg_color="white", text_color=T.TEXT, font=T.font(13))
        self.status.set("All statuses")
        self.status.pack(side="left", padx=8)
        button(bar, "Delete", self.delete, "ghost", width=90).pack(side="right")
        button(bar, "Cancel order", self.cancel, "ghost", width=120).pack(side="right", padx=8)
        button(bar, "View batches", self.view, "soft", width=130).pack(side="right")
        self.table = DataTable(self.body, [C("po_id", "PO #", 60, "e", stretch=False), C("supplier", "Supplier", 230), C("order_date", "Order date", 100), C("status", "Status", 100),
                                           C("batches", "Batches", 70, "e"), C("units", "Units", 80, "e"), C("total_cost", "Total cost", 110, "e", T.money)],
                               on_double=lambda r: self.view(), row_tag=lambda r: {"Pending": "warn", "Cancelled": "danger"}.get(r["status"]))
        self.table.pack(fill="both", expand=True, pady=(10, 0))

    def on_show(self):
        self.rows = self.guard(self.db.query,
            "SELECT po.po_id, s.name AS supplier, po.order_date, po.status, COUNT(b.batch_id) AS batches, COALESCE(SUM(b.received_qty),0) AS units, po.total_cost "
            "FROM purchase_orders po JOIN suppliers s ON s.supplier_id=po.supplier_id LEFT JOIN stock_batches b ON b.po_id=po.po_id "
            "GROUP BY po.po_id, s.name, po.order_date, po.status, po.total_cost ORDER BY po.order_date DESC, po.po_id DESC") or []
        self.apply()

    def apply(self):
        st = self.status.get()
        self.table.load([r for r in self.rows if st == "All statuses" or r["status"] == st])

    def receive(self):
        ReceiveStockDialog(self, self.svc, lambda po: (self.notify(f"Purchase order #{po} received - stock added."), self.on_show()))

    def new_pending(self):
        from ..widgets import Field, FormDialog
        fields = [Field("supplier_id", "Supplier", "choice", required=True, options=lambda: self.svc.suppliers(), span=2), Field("order_date", "Order date", "date", required=True, default=date.today(), span=2)]

        def save(v):
            self.db.execute("INSERT INTO purchase_orders (supplier_id, order_date, status) VALUES (%s,%s,'Pending')", (v["supplier_id"], v["order_date"]))
            self.notify("Pending purchase order created.")
            self.on_show()
        FormDialog(self, "New pending order", fields, {}, "Create", save, columns=1, subtitle="A pending order has no stock yet. Use 'Receive stock' when the delivery arrives.")

    def view(self):
        r = self.table.selected()
        if not r:
            return self.notify("Select a purchase order first.", "warn")
        from .crud_pages import BATCH_SQL
        rows = self.guard(self.db.query, BATCH_SQL + " WHERE b.po_id=%s ORDER BY p.name", (r["po_id"],))
        if rows is not None:
            BatchesDialog(self, f"Purchase order #{r['po_id']} - {r['supplier']}", rows) if rows else self.notify("This order has no batches yet.", "info")

    def cancel(self):
        r = self.table.selected()
        if not r:
            return self.notify("Select a purchase order first.", "warn")
        if confirm(self, "Cancel order", f"Mark purchase order #{r['po_id']} as Cancelled?", "Cancel order"):
            if self.guard(self.db.execute, "UPDATE purchase_orders SET status='Cancelled' WHERE po_id=%s", (r["po_id"],)) is not None:
                self.notify("Order cancelled.")
                self.on_show()

    def delete(self):
        r = self.table.selected()
        if not r:
            return self.notify("Select a purchase order first.", "warn")
        if confirm(self, "Delete order", f"Delete purchase order #{r['po_id']}?\nOnly orders without stock batches can be deleted."):
            if self.guard(self.db.execute, "DELETE FROM purchase_orders WHERE po_id=%s", (r["po_id"],)) is not None:
                self.notify("Purchase order deleted.")
                self.on_show()
