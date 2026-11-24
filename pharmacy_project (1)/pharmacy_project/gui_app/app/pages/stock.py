"""Stock management (levels + batches) and expiry management."""
import customtkinter as ctk

from .. import theme as T
from ..widgets import DataTable, StatCard, button, search_bar
from .base import Page
from .crud_pages import BATCH_SQL, C


def combo(parent, values, command, width=180):
    c = ctk.CTkComboBox(parent, values=values, width=width, height=36, state="readonly", command=lambda _: command(), button_color=T.GREEN,
                        border_color=T.BORDER, fg_color="white", text_color=T.TEXT, font=T.font(13))
    c.set(values[0])
    return c


def tabview(master):
    return ctk.CTkTabview(master, fg_color="transparent", segmented_button_selected_color=T.GREEN, segmented_button_selected_hover_color=T.GREEN_DARK,
                          segmented_button_unselected_color="#E6ECF3", segmented_button_unselected_hover_color="#D8E0EA", text_color=T.TEXT, corner_radius=10)


class StockPage(Page):
    title, subtitle = "Stock Management", "Stock levels per medicine and every batch on the shelf"

    def __init__(self, master, app):
        super().__init__(master, app)
        button(self.actions, "⟳ Refresh", self.on_show, "ghost", width=100).pack(side="right")
        self.tabs = tabview(self.body)
        self.tabs.pack(fill="both", expand=True)
        a, b = self.tabs.add("Stock levels"), self.tabs.add("Batches")
        bar = ctk.CTkFrame(a, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 8))
        search_bar(bar, lambda s: self.levels.filter(s), "Search medicine or category...", 280).pack(side="left")
        self.lvl_filter = combo(bar, ["All medicines", "Low stock", "Out of stock", "Has expired stock"], self.apply_levels)
        self.lvl_filter.pack(side="left", padx=8)
        self.levels = DataTable(a, [C("product_id", "ID", 50, "e", stretch=False), C("product_name", "Medicine", 230), C("category_name", "Category", 170), C("on_hand", "Sellable", 80, "e"),
                                    C("reorder_level", "Reorder at", 90, "e"), C("expired_qty", "Expired units", 100, "e"), C("status", "Status", 110)],
                                row_tag=lambda r: {"Out of stock": "danger", "Low stock": "warn"}.get(r["status"]))
        self.levels.pack(fill="both", expand=True)
        bar2 = ctk.CTkFrame(b, fg_color="transparent")
        bar2.pack(fill="x", pady=(4, 8))
        search_bar(bar2, lambda s: self.batches.filter(s), "Search medicine, batch, supplier...", 280).pack(side="left")
        self.b_filter = combo(bar2, ["All batches", "OK", "Expires soon", "Expired", "Empty"], self.apply_batches)
        self.b_filter.pack(side="left", padx=8)
        self.batches = DataTable(b, [C("batch_id", "ID", 50, "e", stretch=False), C("medicine", "Medicine", 200), C("batch_no", "Batch", 110), C("supplier", "Supplier", 170),
                                     C("received_qty", "Received", 75, "e"), C("quantity", "On shelf", 75, "e"), C("expiry_date", "Expires", 95), C("cost_price", "Cost", 70, "e"), C("state", "Status", 95)],
                                 row_tag=lambda r: {"Expired": "danger", "Expires soon": "warn"}.get(r["state"]))
        self.batches.pack(fill="both", expand=True)

    def on_show(self):
        rows = self.guard(self.db.query, "SELECT product_id, product_name, category_name, on_hand, reorder_level, expired_qty FROM v_product_stock ORDER BY product_name") or []
        for r in rows:
            r["status"] = "Out of stock" if r["on_hand"] == 0 else ("Low stock" if r["on_hand"] < r["reorder_level"] else "In stock")
        self.level_rows = rows
        self.batch_rows = self.guard(self.db.query, BATCH_SQL + " ORDER BY b.expiry_date, p.name") or []
        self.apply_levels()
        self.apply_batches()

    def apply_levels(self):
        f = self.lvl_filter.get()
        self.levels.load([r for r in self.level_rows if f == "All medicines" or r["status"] == f or (f == "Has expired stock" and r["expired_qty"] > 0)])

    def apply_batches(self):
        f = self.b_filter.get()
        self.batches.load([r for r in self.batch_rows if f == "All batches" or r["state"] == f])


class ExpiryPage(Page):
    title, subtitle = "Expiry Management", "Medicines that are about to expire or already expired"

    def __init__(self, master, app):
        super().__init__(master, app)
        button(self.actions, "Refresh alerts", self.refresh_alerts, "primary", width=140).pack(side="right")
        cards = ctk.CTkFrame(self.body, fg_color="transparent")
        cards.pack(fill="x")
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="c")
        self.c_near = StatCard(cards, "Expiring within 30 days", "◷", T.ORANGE, T.ORANGE_SOFT)
        self.c_exp = StatCard(cards, "Expired batches on the shelf", "!", T.RED, T.RED_SOFT)
        self.c_loss = StatCard(cards, "Value of expired stock (at cost)", "Rs", T.RED, T.RED_SOFT)
        for i, c in enumerate((self.c_near, self.c_exp, self.c_loss)):
            c.grid(row=0, column=i, sticky="we", padx=(0 if i == 0 else 8, 0 if i == 2 else 8))
        self.tabs = tabview(self.body)
        self.tabs.pack(fill="both", expand=True, pady=(10, 0))
        a, b, c = self.tabs.add("Expiring soon"), self.tabs.add("Expired"), self.tabs.add("Alerts")
        self.near = DataTable(a, [C("product_name", "Medicine", 230), C("batch_no", "Batch", 110), C("quantity", "Units", 70, "e"), C("expiry_date", "Expires", 100),
                                  C("days_left", "Days left", 80, "e"), C("stock_value_at_cost", "Value at cost", 110, "e", T.money)],
                              row_tag=lambda r: "danger" if r["days_left"] <= 10 else "warn")
        self.near.pack(fill="both", expand=True)
        self.expired = DataTable(b, [C("product_name", "Medicine", 230), C("batch_no", "Batch", 110), C("quantity", "Units", 70, "e"), C("expiry_date", "Expired on", 100),
                                     C("days_expired", "Days ago", 80, "e"), C("loss_at_cost", "Loss at cost", 110, "e", T.money)], row_tag=lambda r: "danger")
        self.expired.pack(fill="both", expand=True)
        self.alerts = DataTable(c, [C("alert_type", "Type", 110), C("message", "Message", 560), C("created_at", "Created", 130)],
                                row_tag=lambda r: {"EXPIRED": "danger", "NEAR_EXPIRY": "warn", "LOW_STOCK": "warn"}.get(r["alert_type"]))
        self.alerts.pack(fill="both", expand=True)

    def on_show(self):
        near = self.guard(self.db.query, "SELECT * FROM v_expiring_30_days ORDER BY days_left") or []
        exp = self.guard(self.db.query, "SELECT * FROM v_expired_stock ORDER BY loss_at_cost DESC") or []
        self.near.load(near)
        self.expired.load(exp)
        self.c_near.set(str(len(near)), f"{sum(r['quantity'] for r in near)} units at risk")
        self.c_exp.set(str(len(exp)), f"{sum(r['quantity'] for r in exp)} units to remove")
        self.c_loss.set(T.money(sum(r["loss_at_cost"] for r in exp)), "write-off value")
        self.alerts.load(self.guard(self.db.query, "SELECT alert_type, message, created_at FROM stock_alerts ORDER BY alert_type, alert_id") or [])

    def refresh_alerts(self):
        rows = self.guard(self.svc.refresh_alerts)
        if rows is not None:
            self.alerts.load(rows)
            self.tabs.set("Alerts")
            self.notify(f"Alerts refreshed: {len(rows)} alert(s).", "info")
