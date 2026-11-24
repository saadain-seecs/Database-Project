"""Dashboard: key figures, three charts and short "what needs attention" lists - all from live queries."""
import customtkinter as ctk

from .. import theme as T
from ..widgets import DataTable, StatCard, card
from .base import Page
from .crud_pages import C
from .reports import make_chart, style_axes


class DashboardPage(Page):
    title, subtitle = "Dashboard", "Overview of stock, sales and expiry risk"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.scroll = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        g = self.scroll
        grid = ctk.CTkFrame(g, fg_color="transparent")
        grid.pack(fill="x")
        spec = [("medicines", "Total medicines", "✚", T.GREEN, T.GREEN_SOFT), ("units", "Units in stock (sellable)", "▤", T.BLUE, T.BLUE_SOFT),
                ("low_stock", "Low-stock medicines", "!", T.ORANGE, T.ORANGE_SOFT), ("expired", "Expired batches", "✖", T.RED, T.RED_SOFT),
                ("revenue", "Total revenue", "Rs", T.GREEN, T.GREEN_SOFT), ("profit", "Total profit", "↗", T.BLUE, T.BLUE_SOFT),
                ("bills", "Total sales (bills)", "#", T.NAVY_3, "#E3EAF4"), ("suppliers", "Active suppliers", "⇄", T.NAVY_3, "#E3EAF4")]
        self.cards = {}
        for i, (k, title, ic, ac, so) in enumerate(spec):
            grid.grid_columnconfigure(i % 4, weight=1, uniform="s")
            c = StatCard(grid, title, ic, ac, so)
            c.grid(row=i // 4, column=i % 4, sticky="we", padx=6, pady=6)
            self.cards[k] = c
        charts = ctk.CTkFrame(g, fg_color="transparent")
        charts.pack(fill="x", pady=(6, 0))
        charts.grid_columnconfigure((0, 1, 2), weight=1, uniform="ch")
        self.figs = []
        for i in range(3):
            holder = card(charts)
            holder.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
            fig, canvas = make_chart(holder, 4.2, 2.8)
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self.figs.append((fig, canvas))
        lower = ctk.CTkFrame(g, fg_color="transparent")
        lower.pack(fill="both", pady=(6, 0))
        lower.grid_columnconfigure((0, 1, 2), weight=1, uniform="lo")
        self.recent = self.mini(lower, 0, "Recent sales", [C("sale_id", "Bill", 45, "e", stretch=False), C("customer", "Customer", 130), C("total_amount", "Total", 75, "e", T.money)])
        self.low = self.mini(lower, 1, "Needs re-ordering", [C("product_name", "Medicine", 160), C("on_hand", "Left", 50, "e"), C("reorder_level", "Min", 50, "e")], "warn")
        self.exp = self.mini(lower, 2, "Expiring within 30 days", [C("product_name", "Medicine", 150), C("quantity", "Units", 50, "e"), C("days_left", "Days", 50, "e")], "warn")

    def mini(self, parent, col, title, cols, tag=None):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=0, column=col, sticky="nsew", padx=6)
        ctk.CTkLabel(box, text=title, font=T.font(14, "bold"), text_color=T.NAVY, anchor="w").pack(fill="x", pady=(2, 4))
        t = DataTable(box, cols, height=6, row_tag=(lambda r: tag) if tag else None)
        t.pack(fill="both", expand=True)
        return t

    def on_show(self):
        s = self.guard(self.svc.stats)
        if not s:
            return
        c = self.cards
        c["medicines"].set(str(s["medicines"]), f"{s['customers']} customers registered")
        c["units"].set(f"{int(s['units']):,}", "unexpired units on shelves")
        c["low_stock"].set(str(s["low_stock"]), "below their reorder level")
        c["expired"].set(str(s["expired_batches"]), f"{T.money(s['expired_loss'])} lost; {s['near_expiry']} expiring soon")
        c["revenue"].set(T.money(s["revenue"]), f"today: {T.money(s['today_sales'])}")
        c["profit"].set(T.money(s["profit"]), "revenue minus batch cost")
        c["bills"].set(str(s["bills"]), "completed sales")
        c["suppliers"].set(str(s["suppliers"]), "supplying the pharmacy")
        self.chart_monthly(self.svc.monthly_revenue())
        self.chart_categories(self.svc.category_revenue())
        self.chart_top(self.svc.top_products(5))
        self.recent.load(self.svc.recent_sales(6))
        self.low.load(self.svc.low_stock(6))
        self.exp.load(self.svc.expiring(6))

    def _prep(self, idx, title):
        fig, canvas = self.figs[idx]
        fig.clear()
        ax = fig.add_subplot(111)
        style_axes(ax)
        ax.set_title(title, fontsize=10, color=T.NAVY, loc="left", fontweight="bold")
        return fig, canvas, ax

    def chart_monthly(self, rows):
        fig, canvas, ax = self._prep(0, "Revenue per month (Rs)")
        ax.bar([r["m"] for r in rows], [float(r["revenue"]) for r in rows], color=T.GREEN, width=0.55)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v / 1000:.0f}k")
        fig.tight_layout()
        canvas.draw()

    def chart_categories(self, rows):
        fig, canvas, ax = self._prep(1, "Revenue by category (Rs)")
        rows = rows[:7][::-1]
        ax.barh([r["name"][:22] for r in rows], [float(r["revenue"]) for r in rows], color=T.NAVY_3, height=0.6)
        ax.xaxis.set_major_formatter(lambda v, _: f"{v / 1000:.0f}k")
        fig.tight_layout()
        canvas.draw()

    def chart_top(self, rows):
        fig, canvas, ax = self._prep(2, "Top 5 medicines (units)")
        rows = rows[::-1]
        ax.barh([r["name"][:22] for r in rows], [int(r["units"]) for r in rows], color=T.BLUE, height=0.6)
        fig.tight_layout()
        canvas.draw()
