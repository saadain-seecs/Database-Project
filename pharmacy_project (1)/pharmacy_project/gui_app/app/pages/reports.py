"""Reports & analytics: ready-made reports, the monthly profit report and a chart."""
import csv
from datetime import date
from tkinter import filedialog

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .. import theme as T
from ..services import REPORTS
from ..widgets import DataTable, StatCard, button, card
from .base import Page
from .stock import tabview


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#C9D3E0")
    ax.tick_params(colors=T.MUTED, labelsize=8)
    ax.set_facecolor("white")


def make_chart(parent, w=5.6, h=2.7):
    fig = Figure(figsize=(w, h), dpi=100, facecolor="white")
    canvas = FigureCanvasTkAgg(fig, master=parent)
    return fig, canvas


class ReportsPage(Page):
    title, subtitle = "Reports & Analytics", "Sales, profit, purchasing and stock reports straight from the database"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.tabs = tabview(self.body)
        self.tabs.pack(fill="both", expand=True)
        a, b = self.tabs.add("Reports"), self.tabs.add("Monthly profit report")
        # ---- generic reports
        bar = ctk.CTkFrame(a, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 8))
        self.choice = ctk.CTkComboBox(bar, values=list(REPORTS), width=330, height=36, state="readonly", command=lambda _: self.run(), button_color=T.GREEN,
                                      border_color=T.BORDER, fg_color="white", text_color=T.TEXT, font=T.font(13))
        self.choice.set(list(REPORTS)[0])
        self.choice.pack(side="left")
        button(bar, "Export CSV", self.export, "ghost", width=110).pack(side="right")
        split = ctk.CTkFrame(a, fg_color="transparent")
        split.pack(fill="both", expand=True)
        split.grid_columnconfigure(0, weight=3)
        split.grid_columnconfigure(1, weight=2)
        split.grid_rowconfigure(0, weight=1)
        self.table = DataTable(split, [{"key": "x", "label": "x"}])
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chart_card = card(split)
        self.chart_card.grid(row=0, column=1, sticky="nsew")
        self.fig, self.canvas = make_chart(self.chart_card, 4.2, 3.6)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        # ---- monthly report (stored procedure with three result sets)
        top = ctk.CTkFrame(b, fg_color="transparent")
        top.pack(fill="x", pady=(4, 8))
        self.year = ctk.CTkEntry(top, width=90, height=36, border_color=T.BORDER, fg_color="white", font=T.font(13))
        self.year.insert(0, str(date.today().year))
        self.year.pack(side="left")
        self.month = ctk.CTkComboBox(top, values=[f"{i:02d}" for i in range(1, 13)], width=90, height=36, state="readonly", button_color=T.GREEN, border_color=T.BORDER, fg_color="white", text_color=T.TEXT)
        self.month.set("10")
        self.month.pack(side="left", padx=8)
        button(top, "Run monthly report", self.monthly, "primary", width=170).pack(side="left")
        ctk.CTkLabel(top, text="year / month   (calls stored procedure sp_monthly_report)", font=T.font(11), text_color=T.MUTED).pack(side="left", padx=10)
        cards = ctk.CTkFrame(b, fg_color="transparent")
        cards.pack(fill="x")
        self.m_cards = {}
        specs = [("revenue", "Revenue", "Rs", T.BLUE, T.BLUE_SOFT), ("cost", "Cost of goods", "▤", T.ORANGE, T.ORANGE_SOFT), ("profit", "Profit", "↗", T.GREEN, T.GREEN_SOFT), ("bills", "Bills", "#", T.NAVY_3, "#E3EAF4")]
        for i, (k, t, ic, ac, so) in enumerate(specs):
            cards.grid_columnconfigure(i, weight=1, uniform="m")
            c = StatCard(cards, t, ic, ac, so)
            c.grid(row=0, column=i, sticky="we", padx=(0 if i == 0 else 6, 0 if i == 3 else 6))
            self.m_cards[k] = c
        lower = ctk.CTkFrame(b, fg_color="transparent")
        lower.pack(fill="both", expand=True, pady=(10, 0))
        lower.grid_columnconfigure((0, 1), weight=1, uniform="l")
        lower.grid_rowconfigure(0, weight=1)
        self.m_top = DataTable(lower, [{"key": "product", "label": "Top 5 products by profit", "width": 200}, {"key": "units", "label": "Units", "width": 60, "anchor": "e"},
                                       {"key": "profit", "label": "Profit", "width": 90, "anchor": "e", "fmt": T.money}], height=6)
        self.m_top.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.m_cat = DataTable(lower, [{"key": "category_name", "label": "Revenue by category", "width": 200}, {"key": "units", "label": "Units", "width": 60, "anchor": "e"},
                                       {"key": "revenue", "label": "Revenue", "width": 90, "anchor": "e", "fmt": T.money}], height=6)
        self.m_cat.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    def on_show(self):
        self.run()

    def run(self):
        rows = self.guard(self.svc.run_report, self.choice.get())
        if rows is None:
            return
        cols = list(rows[0].keys()) if rows else []
        self.table.set_columns([{"key": c, "label": c, "width": 140 if i else 230, "anchor": "w" if i == 0 or isinstance(rows[0][c], str) else "e"} for i, c in enumerate(cols)] or [{"key": "x", "label": "No data"}])
        self.table.load(rows)
        self.draw(rows, cols)

    def draw(self, rows, cols):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        style_axes(ax)
        num_cols = [c for c in cols[1:] if rows and isinstance(rows[0][c], (int, float)) or (rows and hasattr(rows[0][c], "as_tuple"))]
        if rows and cols and num_cols:
            data = rows[:12]
            labels = [str(r[cols[0]])[:18] for r in data]
            vals = [float(r[num_cols[-1] if "Revenue" not in num_cols else "Revenue"]) for r in data]
            ax.barh(labels[::-1], vals[::-1], color=T.GREEN, height=0.6)
            ax.set_title(num_cols[-1] if "Revenue" not in num_cols else "Revenue", fontsize=10, color=T.NAVY, loc="left", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No numeric data to chart", ha="center", va="center", color=T.MUTED)
            ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw()

    def export(self):
        if not self.table.rows:
            return self.notify("Nothing to export.", "warn")
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=self.choice.get().replace(" ", "_").lower() + ".csv", filetypes=[("CSV", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(self.table.rows[0].keys())
                for r in self.table.rows:
                    w.writerow([T.display(v) if v is not None else "" for v in r.values()])
            self.notify(f"Saved {len(self.table.rows)} rows to {path}")

    def monthly(self):
        try:
            y, m = int(self.year.get()), int(self.month.get())
        except ValueError:
            return self.notify("Year must be a number.", "warn")
        sets = self.guard(self.svc.monthly_report, y, m)
        if sets is None:
            return
        s = sets[0][0] if sets and sets[0] else {}
        for k, c in self.m_cards.items():
            v = s.get(k) or 0
            c.set(T.money(v) if k != "bills" else str(int(v)), f"margin {s.get('margin_pct')}%" if k == "profit" and s.get("margin_pct") is not None else "")
        self.m_top.load(sets[1] if len(sets) > 1 else [])
        self.m_cat.load(sets[2] if len(sets) > 2 else [])
        if not s or not s.get("bills"):
            self.notify("No sales in that month.", "info")
