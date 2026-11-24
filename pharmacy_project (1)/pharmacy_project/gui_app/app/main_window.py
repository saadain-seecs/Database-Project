"""Main window: sidebar navigation + page container."""
import customtkinter as ctk

from . import theme as T
from .database import SchemaError
from .pages.crud_pages import CategoriesPage, CustomersPage, MedicinesPage, StaffPage, SuppliersPage
from .pages.dashboard import DashboardPage
from .pages.purchases import PurchasesPage
from .pages.reports import ReportsPage
from .pages.sales import SalesPage
from .pages.stock import ExpiryPage, StockPage
from .services import PharmacyService

NAV = [("Dashboard", "▣", DashboardPage), ("Sales & Billing", "$", SalesPage), ("Medicines", "✚", MedicinesPage), ("Categories", "☰", CategoriesPage),
       ("Suppliers", "⇄", SuppliersPage), ("Purchases", "⇩", PurchasesPage), ("Stock", "▤", StockPage), ("Expiry", "◷", ExpiryPage),
       ("Customers", "☺", CustomersPage), ("Staff", "♞", StaffPage), ("Reports", "▥", ReportsPage)]


class MainWindow(ctk.CTk):
    def __init__(self, db, schema, user=None, auth=None):
        super().__init__(fg_color=T.BG)
        self.db, self.schema, self.user, self.auth = db, schema, user, auth
        self.logged_out = False
        self.svc = PharmacyService(db, schema)
        self.title("Pharmacy Inventory & Sales Management System")
        self.geometry("1440x860")
        self.minsize(1180, 700)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.pages, self.buttons, self.current = {}, {}, None
        self.build_sidebar()
        self.container = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.show("Dashboard")

    def build_sidebar(self):
        bar = ctk.CTkFrame(self, fg_color=T.NAVY, corner_radius=0, width=232)
        bar.grid(row=0, column=0, sticky="nsw")
        bar.grid_propagate(False)
        logo = ctk.CTkFrame(bar, fg_color="transparent")
        logo.pack(fill="x", padx=18, pady=(24, 18))
        ctk.CTkLabel(logo, text="✚", width=42, height=42, corner_radius=12, fg_color=T.GREEN, text_color="white", font=T.font(22, "bold")).pack(side="left")
        names = ctk.CTkFrame(logo, fg_color="transparent")
        names.pack(side="left", padx=10)
        ctk.CTkLabel(names, text="PharmaCare", font=T.font(17, "bold"), text_color="white", anchor="w").pack(anchor="w")
        ctk.CTkLabel(names, text="Inventory & Sales", font=T.font(11), text_color="#9FB3CF", anchor="w").pack(anchor="w")
        for name, icon, _ in NAV:
            b = ctk.CTkButton(bar, text=f"  {icon}    {name}", anchor="w", height=42, corner_radius=10, fg_color="transparent", hover_color=T.NAVY_2,
                              text_color="#D4DFEE", font=T.font(14), command=lambda n=name: self.show(n))
            b.pack(fill="x", padx=14, pady=2)
            self.buttons[name] = b
        foot = ctk.CTkFrame(bar, fg_color=T.NAVY_2, corner_radius=12)
        foot.pack(side="bottom", fill="x", padx=14, pady=16)
        c = self.db.cfg
        where = c["unix_socket"] or f"{c['host']}:{c['port']}"
        if self.user:
            row = ctk.CTkFrame(foot, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(12, 4))
            ctk.CTkLabel(row, text=self.user["full_name"][:1].upper(), width=36, height=36, corner_radius=18, fg_color=T.GREEN, text_color="white", font=T.font(15, "bold")).pack(side="left")
            who = ctk.CTkFrame(row, fg_color="transparent")
            who.pack(side="left", padx=8)
            ctk.CTkLabel(who, text=self.user["full_name"][:18], font=T.font(12, "bold"), text_color="white", anchor="w").pack(anchor="w")
            ctk.CTkLabel(who, text="Administrator", font=T.font(10), text_color="#9FB3CF", anchor="w").pack(anchor="w")
            btns = ctk.CTkFrame(foot, fg_color="transparent")
            btns.pack(fill="x", padx=12, pady=(0, 8))
            for text, cmd in (("Password", self.change_password), ("Log out", self.logout)):
                ctk.CTkButton(btns, text=text, height=28, corner_radius=8, fg_color=T.NAVY_3, hover_color=T.NAVY, text_color="white", font=T.font(11, "bold"), command=cmd).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkLabel(foot, text="●  Connected", font=T.font(11, "bold"), text_color="#5BE0A3", anchor="w").pack(fill="x", padx=14)
        ctk.CTkLabel(foot, text=f"{c['database']}  @  {where}", font=T.font(10), text_color="#9FB3CF", anchor="w", justify="left", wraplength=180).pack(fill="x", padx=14, pady=(0, 10))

    def logout(self):
        from .widgets import confirm
        if confirm(self, "Log out", "Log out of PharmaCare?", "Log out", danger=False):
            self.logged_out = True
            self.destroy()

    def change_password(self):
        from .auth import AuthError
        from .widgets import Field, FormDialog, toast

        def save(v):
            try:
                self.auth.change_password(self.user["user_id"], v["current"], v["new"])
            except AuthError as e:
                from .database import DatabaseError
                raise DatabaseError(str(e))
            toast(self, "Password changed.")
        fields = [Field("current", "Current password", required=True, secret=True), Field("new", "New password", required=True, secret=True, help="At least 8 characters, letters and numbers."),
                  Field("confirm", "Repeat new password", required=True, secret=True)]

        def check(v):
            if v["new"] != v["confirm"]:
                from .database import DatabaseError
                raise DatabaseError("The two new passwords do not match.")
            save(v)
        FormDialog(self, "Change password", fields, {}, "Change password", check, columns=1)

    def show(self, name):
        if name not in self.pages:
            cls = next(c for n, _, c in NAV if n == name)
            try:
                page = cls(self.container, self)
            except SchemaError as e:
                from .widgets import toast
                toast(self, str(e), "error", 8000)
                return
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page
        for n, b in self.buttons.items():
            b.configure(fg_color=T.GREEN if n == name else "transparent", text_color="white" if n == name else "#D4DFEE", hover_color=T.GREEN_DARK if n == name else T.NAVY_2)
        self.pages[name].tkraise()
        self.current = name
        self.after(30, self.pages[name].on_show)
