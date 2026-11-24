"""Administrator sign-in window and the first-run 'create admin account' window."""
import customtkinter as ctk

from . import theme as T
from .auth import AuthError, AuthService, validate_password, validate_username
from .widgets import button


class _AuthWindow(ctk.CTk):
    TITLE, SUBTITLE, BUTTON = "", "", ""

    def __init__(self, auth: AuthService, db_label=""):
        super().__init__(fg_color="white")
        self.auth, self.result = auth, None
        self.title("PharmaCare - " + self.TITLE)
        w, h = 920, 600
        self.geometry(f"{w}x{h}+{max((self.winfo_screenwidth() - w) // 2, 0)}+{max((self.winfo_screenheight() - h) // 3, 0)}")
        self.resizable(False, False)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._left(db_label)
        self.right = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.fields = {}
        self.build_form()
        self.bind("<Return>", lambda e: self.submit())

    def _left(self, db_label):
        left = ctk.CTkFrame(self, fg_color=T.NAVY, corner_radius=0, width=380)
        left.grid(row=0, column=0, sticky="nsw")
        left.grid_propagate(False)
        ctk.CTkLabel(left, text="✚", width=64, height=64, corner_radius=18, fg_color=T.GREEN, text_color="white", font=T.font(32, "bold")).pack(anchor="w", padx=44, pady=(70, 18))
        ctk.CTkLabel(left, text="PharmaCare", font=T.font(32, "bold"), text_color="white", anchor="w").pack(anchor="w", padx=44)
        ctk.CTkLabel(left, text="Pharmacy Inventory &\nSales Management System", font=T.font(14), text_color="#9FB3CF", justify="left", anchor="w").pack(anchor="w", padx=44, pady=(4, 36))
        for line in ("Live stock and expiry tracking", "Fast, accurate billing", "Purchasing and supplier records", "Sales, profit and stock reports"):
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(anchor="w", padx=44, pady=5)
            ctk.CTkLabel(row, text="✔", text_color="#5BE0A3", font=T.font(13, "bold"), width=22).pack(side="left")
            ctk.CTkLabel(row, text=line, text_color="#D4DFEE", font=T.font(13)).pack(side="left")
        ctk.CTkLabel(left, text=f"CS220 Database Systems\n{db_label}", font=T.font(11), text_color="#6E86A8", justify="left", anchor="w").pack(side="bottom", anchor="w", padx=44, pady=26)

    # ------------------------------------------------------------------ form helpers
    def heading(self):
        ctk.CTkLabel(self.right, text=self.TITLE, font=T.font(28, "bold"), text_color=T.NAVY, anchor="w").pack(fill="x", padx=64, pady=(70, 0))
        ctk.CTkLabel(self.right, text=self.SUBTITLE, font=T.font(13), text_color=T.MUTED, anchor="w", wraplength=400, justify="left").pack(fill="x", padx=64, pady=(2, 18))

    def field(self, key, label, secret=False, placeholder=""):
        ctk.CTkLabel(self.right, text=label, font=T.font(12, "bold"), text_color=T.TEXT, anchor="w").pack(fill="x", padx=64, pady=(8, 2))
        row = ctk.CTkFrame(self.right, fg_color="transparent")
        row.pack(fill="x", padx=64)
        e = ctk.CTkEntry(row, height=42, corner_radius=8, border_color=T.BORDER, fg_color="#F8FAFC", font=T.font(14), text_color=T.TEXT,
                         show="•" if secret else "", placeholder_text=placeholder)
        e.pack(side="left", fill="x", expand=True)
        if secret:
            btn = ctk.CTkButton(row, text="Show", width=58, height=42, corner_radius=8, fg_color="white", hover_color="#EEF2F7", text_color=T.MUTED,
                                border_width=1, border_color=T.BORDER, font=T.font(12))
            btn.configure(command=lambda e=e, b=btn: self._toggle(e, b))
            btn.pack(side="left", padx=(6, 0))
        self.fields[key] = e
        return e

    @staticmethod
    def _toggle(entry, btn):
        hidden = entry.cget("show") == "•"
        entry.configure(show="" if hidden else "•")
        btn.configure(text="Hide" if hidden else "Show")

    def message(self):
        self.msg = ctk.CTkLabel(self.right, text="", font=T.font(12, "bold"), text_color=T.RED, anchor="w", wraplength=400, justify="left")
        self.msg.pack(fill="x", padx=64, pady=(10, 0))

    def error(self, text, ok=False):
        self.msg.configure(text=text, text_color=T.GREEN_DARK if ok else T.RED)

    def build_form(self):
        raise NotImplementedError

    def submit(self):
        raise NotImplementedError


class LoginWindow(_AuthWindow):
    TITLE, SUBTITLE = "Admin sign in", "Enter your administrator account to open the pharmacy system."

    def build_form(self):
        self.heading()
        self.field("username", "Username", placeholder="admin").focus_set()
        self.field("password", "Password", secret=True, placeholder="Your password")
        self.message()
        button(self.right, "Sign in", self.submit, "primary", height=46).pack(fill="x", padx=64, pady=(14, 0))
        ctk.CTkLabel(self.right, text="Access is limited to administrators.", font=T.font(11), text_color=T.MUTED).pack(pady=16)

    def submit(self):
        try:
            self.result = self.auth.login(self.fields["username"].get(), self.fields["password"].get())
        except AuthError as e:
            self.error(str(e))
            self.fields["password"].delete(0, "end")
            return
        self.destroy()


class SetupWindow(_AuthWindow):
    TITLE = "Create admin account"
    SUBTITLE = "First start: choose the administrator login for this pharmacy system."

    def build_form(self):
        self.right.pack_propagate(True)
        self.heading()
        self.field("full_name", "Full name", placeholder="e.g. Pharmacy Manager")
        self.field("username", "Username", placeholder="admin")
        self.field("password", "Password", secret=True, placeholder="At least 8 characters, letters and numbers")
        self.field("confirm", "Confirm password", secret=True)
        self.message()
        button(self.right, "Create account and continue", self.submit, "primary", height=46).pack(fill="x", padx=64, pady=(12, 0))

    def submit(self):
        f = {k: e.get().strip() if k != "password" and k != "confirm" else e.get() for k, e in self.fields.items()}
        err = validate_username(f["username"]) or validate_password(f["password"], f["username"])
        if not err and f["password"] != f["confirm"]:
            err = "The two passwords do not match."
        if err:
            return self.error(err)
        try:
            self.auth.create_admin(f["username"], f["password"], f["full_name"])
            self.result = self.auth.login(f["username"], f["password"])
        except AuthError as e:
            return self.error(str(e))
        self.destroy()
