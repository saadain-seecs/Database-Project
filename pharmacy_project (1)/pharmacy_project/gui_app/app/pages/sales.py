"""Sales & billing: point-of-sale screen and sales history."""
import customtkinter as ctk

from .. import theme as T
from ..database import DatabaseError
from ..widgets import DataTable, SearchCombo, BaseDialog, button, card, confirm, info_dialog, search_bar
from .base import Page
from .crud_pages import C


class BillDialog(BaseDialog):
    def __init__(self, master, header, lines):
        super().__init__(master, f"Bill #{header['sale_id']}", 520, 560)
        ctk.CTkLabel(self, text="PHARMACY BILL", font=T.font(11, "bold"), text_color=T.GREEN).pack(pady=(22, 0))
        ctk.CTkLabel(self, text=f"Bill #{header['sale_id']}", font=T.font(22, "bold"), text_color=T.NAVY).pack()
        meta = (f"{T.display(header['sale_date'])}\nCustomer: {header['customer']}    Served by: {header['served_by']}\nPayment: {header['payment_method']}")
        ctk.CTkLabel(self, text=meta, font=T.font(12), text_color=T.MUTED, justify="center").pack(pady=(4, 10))
        t = DataTable(self, [C("product", "Medicine", 220), C("quantity", "Qty", 50, "e"), C("unit_price", "Price", 80, "e", T.money), C("line_total", "Amount", 90, "e", T.money)], height=8)
        t.pack(fill="both", expand=True, padx=26)
        t.load(lines)
        ctk.CTkLabel(self, text=f"TOTAL   {T.money(header['total_amount'])}", font=T.font(20, "bold"), text_color=T.NAVY).pack(pady=12)
        button(self, "Close", self.destroy, "navy", width=120).pack(pady=(0, 18))


class SalesPage(Page):
    title, subtitle = "Sales & Billing", "Create a bill and review previous sales"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.cart = []                                   # dicts: product_id, name, price, qty, stock
        self.tabs = ctk.CTkTabview(self.body, fg_color="transparent", segmented_button_selected_color=T.GREEN, segmented_button_selected_hover_color=T.GREEN_DARK,
                                   segmented_button_unselected_color="#E6ECF3", segmented_button_unselected_hover_color="#D8E0EA", text_color=T.TEXT, corner_radius=10)
        self.tabs.pack(fill="both", expand=True)
        self.pos_tab, self.hist_tab = self.tabs.add("New sale"), self.tabs.add("Sales history")
        self.build_pos()
        self.build_history()

    # =================================================================== POS
    def build_pos(self):
        t = self.pos_tab
        t.grid_columnconfigure(0, weight=3)
        t.grid_columnconfigure(1, weight=1, minsize=330)
        t.grid_rowconfigure(0, weight=1)
        left = card(t)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=4)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(left, text="Add medicines to the bill", font=T.font(15, "bold"), text_color=T.NAVY).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))
        row = ctk.CTkFrame(left, fg_color="transparent")
        row.grid(row=1, column=0, sticky="we", padx=18)
        row.grid_columnconfigure(0, weight=1)
        self.product = SearchCombo(row)
        self.product.grid(row=0, column=0, sticky="we")
        self.qty = ctk.CTkEntry(row, width=70, height=36, justify="center", border_color=T.BORDER, fg_color="white", font=T.font(13))
        self.qty.insert(0, "1")
        self.qty.grid(row=0, column=1, padx=8)
        button(row, "+ Add", self.add_item, "primary", width=90).grid(row=0, column=2)
        self.cart_table = DataTable(left, [C("name", "Medicine", 230), C("price", "Price", 80, "e", T.money), C("qty", "Qty", 60, "e"),
                                           C("line", "Amount", 90, "e", T.money), C("stock", "In stock", 80, "e")], row_tag=lambda r: "danger" if r["qty"] > r["stock"] else None, height=9)
        self.cart_table.grid(row=2, column=0, sticky="nsew", padx=14, pady=10)
        bar = ctk.CTkFrame(left, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="we", padx=18, pady=(0, 16))
        button(bar, "Remove selected", self.remove_item, "ghost", width=140).pack(side="left")
        button(bar, "Clear bill", self.clear_cart, "ghost", width=100).pack(side="left", padx=8)

        right = card(t)
        right.grid(row=0, column=1, sticky="nsew", pady=4)
        ctk.CTkLabel(right, text="Bill details", font=T.font(15, "bold"), text_color=T.NAVY).pack(anchor="w", padx=18, pady=(16, 6))

        def label(txt):
            ctk.CTkLabel(right, text=txt, font=T.font(12, "bold"), text_color=T.TEXT).pack(anchor="w", padx=18, pady=(8, 2))
        label("Customer")
        self.customer = SearchCombo(right)
        self.customer.pack(fill="x", padx=18)
        label("Served by")
        self.seller = SearchCombo(right)
        self.seller.pack(fill="x", padx=18)
        label("Payment method")
        self.payment = ctk.CTkComboBox(right, values=self.schema.col("sales", "payment_method")["enum"], state="readonly", height=36, border_color=T.BORDER,
                                       button_color=T.GREEN, fg_color="white", text_color=T.TEXT, font=T.font(13))
        self.payment.pack(fill="x", padx=18)
        self.summary = ctk.CTkFrame(right, fg_color=T.GREEN_SOFT, corner_radius=12)
        self.summary.pack(fill="x", padx=18, pady=(22, 8))
        self.lines_lbl = ctk.CTkLabel(self.summary, text="0 items", font=T.font(12), text_color=T.GREEN_DARK)
        self.lines_lbl.pack(anchor="w", padx=16, pady=(12, 0))
        self.total_lbl = ctk.CTkLabel(self.summary, text="Rs 0", font=T.font(30, "bold"), text_color=T.NAVY)
        self.total_lbl.pack(anchor="w", padx=16, pady=(0, 12))
        button(right, "Complete sale", self.checkout, "primary", height=46).pack(fill="x", padx=18, pady=(6, 0))
        ctk.CTkLabel(right, text="Stock is deducted automatically\n(earliest expiry first).", font=T.font(11), text_color=T.MUTED, justify="left").pack(anchor="w", padx=18, pady=8)

    def load_pos_lookups(self):
        self.products = {p["product_id"]: p for p in self.svc.sellable_products()}
        self.product.set_options([(p["product_id"], f"{p['name']}   -   {T.money(p['unit_price'])}   ({p['on_hand']} in stock)" + ("   Rx" if p["requires_prescription"] else ""))
                                  for p in self.products.values()])
        self.customer.set_options(self.svc.customers())
        self.seller.set_options(self.svc.sellers())
        if not self.customer.get():
            self.customer.set(next((l for v, l in self.customer.options if v == 1), ""))
        if not self.seller.get() and self.seller.options:
            self.seller.set(self.seller.options[0][1])
        if not self.payment.get():
            self.payment.set("Cash")
        for item in self.cart:                                    # refresh stock figures
            if item["product_id"] in self.products:
                item["stock"] = self.products[item["product_id"]]["on_hand"]
        self.refresh_cart()

    def add_item(self):
        pid = self.product.value()
        if pid is None:
            return self.notify("Choose a medicine from the list.", "warn")
        try:
            q = int(self.qty.get())
            if q <= 0:
                raise ValueError
        except ValueError:
            return self.notify("Quantity must be a whole number greater than 0.", "warn")
        p = self.products[pid]
        existing = next((i for i in self.cart if i["product_id"] == pid), None)
        if existing:
            existing["qty"] += q
        else:
            self.cart.append(dict(product_id=pid, name=p["name"], price=p["unit_price"], qty=q, stock=p["on_hand"]))
        if p["requires_prescription"]:
            self.notify(f"{p['name']} is prescription-only - check the prescription.", "info")
        self.product.clear()
        self.qty.delete(0, "end")
        self.qty.insert(0, "1")
        self.refresh_cart()

    def remove_item(self):
        sel = self.cart_table.selected()
        if not sel:
            return self.notify("Select a line to remove.", "warn")
        self.cart = [i for i in self.cart if i["product_id"] != sel["product_id"]]
        self.refresh_cart()

    def clear_cart(self):
        self.cart = []
        self.refresh_cart()

    def refresh_cart(self):
        for i in self.cart:
            i["line"] = i["price"] * i["qty"]
        self.cart_table.load(self.cart)
        total = sum(i["line"] for i in self.cart)
        self.lines_lbl.configure(text=f"{len(self.cart)} line(s), {sum(i['qty'] for i in self.cart)} unit(s)")
        self.total_lbl.configure(text=T.money(total))

    def checkout(self):
        if not self.cart:
            return self.notify("The bill is empty.", "warn")
        cust, emp = self.customer.value(), self.seller.value()
        if cust is None or emp is None:
            return self.notify("Choose the customer and the employee serving.", "warn")
        short = [i["name"] for i in self.cart if i["qty"] > i["stock"]]
        if short:
            return self.notify("Not enough stock for: " + ", ".join(short), "error")
        try:
            sale_id = self.svc.checkout(cust, emp, self.payment.get(), [(i["product_id"], i["qty"]) for i in self.cart])
        except DatabaseError as e:
            return self.notify(f"Sale rejected and rolled back: {e}", "error")
        self.notify(f"Sale #{sale_id} completed.")
        self.cart = []
        self.load_pos_lookups()
        self.load_history()
        BillDialog(self, self.svc.sale_header(sale_id), self.svc.sale_lines(sale_id))

    # =================================================================== history
    def build_history(self):
        t = self.hist_tab
        bar = ctk.CTkFrame(t, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 8))
        self.h_search = search_bar(bar, lambda s: self.h_table.filter(s), "Search bill, customer, staff...", 280)
        self.h_search.pack(side="left")
        self.h_pay = ctk.CTkComboBox(bar, values=["All payments"] + self.schema.col("sales", "payment_method")["enum"], width=170, height=36, state="readonly",
                                     command=lambda _: self.apply_hist_filter(), button_color=T.GREEN, border_color=T.BORDER, fg_color="white", text_color=T.TEXT, font=T.font(13))
        self.h_pay.set("All payments")
        self.h_pay.pack(side="left", padx=8)
        button(bar, "Delete bill", self.delete_sale, "ghost", width=100).pack(side="right")
        button(bar, "View bill", self.view_sale, "soft", width=100).pack(side="right", padx=8)
        self.h_table = DataTable(t, [C("sale_id", "Bill #", 60, "e", stretch=False), C("sale_date", "Date", 130), C("customer", "Customer", 170), C("served_by", "Served by", 150),
                                     C("payment_method", "Payment", 110), C("items", "Items", 60, "e"), C("total_amount", "Total", 100, "e", T.money)], on_double=lambda r: self.view_sale())
        self.h_table.pack(fill="both", expand=True)

    def load_history(self):
        self.hist_rows = self.guard(self.db.query,
            "SELECT s.sale_id, s.sale_date, c.name AS customer, e.name AS served_by, s.payment_method, COUNT(si.product_id) AS items, s.total_amount "
            "FROM sales s JOIN customers c ON c.customer_id=s.customer_id JOIN employees e ON e.employee_id=s.employee_id "
            "LEFT JOIN sale_items si ON si.sale_id=s.sale_id GROUP BY s.sale_id, s.sale_date, c.name, e.name, s.payment_method, s.total_amount ORDER BY s.sale_date DESC, s.sale_id DESC") or []
        self.apply_hist_filter()

    def apply_hist_filter(self):
        p = self.h_pay.get()
        self.h_table.load([r for r in self.hist_rows if p == "All payments" or r["payment_method"] == p])

    def view_sale(self):
        r = self.h_table.selected()
        if not r:
            return self.notify("Select a bill first.", "warn")
        BillDialog(self, self.svc.sale_header(r["sale_id"]), self.svc.sale_lines(r["sale_id"]))

    def delete_sale(self):
        r = self.h_table.selected()
        if not r:
            return self.notify("Select a bill first.", "warn")
        if confirm(self, "Delete bill", f"Delete bill #{r['sale_id']} ({T.money(r['total_amount'])})?\nThe medicines are returned to stock."):
            if self.guard(self.db.execute, "DELETE FROM sales WHERE sale_id=%s", (r["sale_id"],)) is not None:
                self.notify(f"Bill #{r['sale_id']} deleted and stock restored.")
                self.on_show()

    def on_show(self):
        self.guard(self.load_pos_lookups)
        self.load_history()
