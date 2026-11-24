"""Reusable widgets: cards, data table, toast notifications, dialogs and a generated form."""
import tkinter as tk
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from tkinter import ttk

import customtkinter as ctk

from . import theme as T
from .database import DatabaseError


# ---------------------------------------------------------------------------------------------- buttons
def button(master, text, command=None, kind="primary", width=None, height=36, **kw):
    styles = {"primary": dict(fg_color=T.GREEN, hover_color=T.GREEN_DARK, text_color="white"),
              "navy": dict(fg_color=T.NAVY, hover_color=T.NAVY_3, text_color="white"),
              "ghost": dict(fg_color="white", hover_color="#EEF2F7", text_color=T.TEXT, border_width=1, border_color=T.BORDER),
              "danger": dict(fg_color=T.RED, hover_color="#B93A3A", text_color="white"),
              "soft": dict(fg_color=T.GREEN_SOFT, hover_color="#CDECDC", text_color=T.GREEN_DARK)}
    opts = dict(styles[kind]); opts.update(kw)
    if width:
        opts["width"] = width
    return ctk.CTkButton(master, text=text, command=command, height=height, corner_radius=8, font=T.font(13, "bold"), **opts)


def card(master, **kw):
    return ctk.CTkFrame(master, fg_color=T.CARD, corner_radius=12, border_width=1, border_color=T.BORDER, **kw)


class StatCard(ctk.CTkFrame):
    """Dashboard tile: coloured icon, big number, title and a small caption."""

    def __init__(self, master, title, icon, accent=T.GREEN, soft=T.GREEN_SOFT):
        super().__init__(master, fg_color=T.CARD, corner_radius=14, border_width=1, border_color=T.BORDER)
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text=icon, width=46, height=46, corner_radius=23, fg_color=soft, text_color=accent,
                     font=T.font(20, "bold")).grid(row=0, column=0, rowspan=3, padx=(16, 12), pady=16)
        ctk.CTkLabel(self, text=title, font=T.font(12), text_color=T.MUTED, anchor="w").grid(row=0, column=1, sticky="we", pady=(14, 0), padx=(0, 12))
        self.value = ctk.CTkLabel(self, text="-", font=T.font(24, "bold"), text_color=T.TEXT, anchor="w")
        self.value.grid(row=1, column=1, sticky="we", padx=(0, 12))
        self.sub = ctk.CTkLabel(self, text="", font=T.font(11), text_color=T.MUTED, anchor="w")
        self.sub.grid(row=2, column=1, sticky="we", pady=(0, 12), padx=(0, 12))

    def set(self, value, sub=""):
        self.value.configure(text=value)
        self.sub.configure(text=sub)


# ---------------------------------------------------------------------------------------------- toast
_toasts = []


def toast(widget, message, kind="success", ms=3600):
    root = widget.winfo_toplevel()
    colors = {"success": (T.GREEN, "#E7F6EE", "✔"), "error": (T.RED, T.RED_SOFT, "✖"), "info": (T.BLUE, T.BLUE_SOFT, "ℹ"), "warn": (T.ORANGE, T.ORANGE_SOFT, "!")}
    accent, soft, sym = colors[kind]
    f = ctk.CTkFrame(root, fg_color=soft, corner_radius=10, border_width=1, border_color=accent)
    ctk.CTkLabel(f, text=sym, text_color=accent, font=T.font(15, "bold"), width=28).pack(side="left", padx=(10, 0), pady=10)
    ctk.CTkLabel(f, text=message, text_color=T.TEXT, font=T.font(13), wraplength=380, justify="left").pack(side="left", padx=(4, 14), pady=10)
    _toasts.append(f)
    f.place(relx=1.0, rely=1.0, x=-24, y=-24 - 62 * (len(_toasts) - 1), anchor="se")
    f.lift()

    def kill():
        if f in _toasts:
            _toasts.remove(f)
        f.destroy()
    root.after(ms, kill)


# ---------------------------------------------------------------------------------------------- data table
class DataTable(ctk.CTkFrame):
    """A styled, sortable, filterable table (ttk.Treeview)."""
    _styled = False

    def __init__(self, master, columns, on_select=None, on_double=None, row_tag=None, height=10):
        super().__init__(master, fg_color=T.CARD, corner_radius=12, border_width=1, border_color=T.BORDER)
        DataTable._style(self)
        self.on_select, self.on_double, self.row_tag = on_select, on_double, row_tag
        self.rows, self.view, self.sort_state = [], [], (None, False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(self, style="Pharm.Treeview", show="headings", selectmode="browse", height=height)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        sb = ctk.CTkScrollbar(self, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 4))
        self.tree.configure(yscrollcommand=sb.set)
        xb = ctk.CTkScrollbar(self, command=self.tree.xview, orientation="horizontal")
        xb.grid(row=1, column=0, sticky="we", padx=6)
        self.tree.configure(xscrollcommand=xb.set)
        self.footer = ctk.CTkLabel(self, text="", font=T.font(11), text_color=T.MUTED, anchor="w")
        self.footer.grid(row=2, column=0, columnspan=2, sticky="we", padx=12, pady=(2, 8))
        self.tree.tag_configure("odd", background=T.STRIPE)
        self.tree.tag_configure("warn", background=T.ORANGE_SOFT, foreground="#8A4B08")
        self.tree.tag_configure("danger", background=T.RED_SOFT, foreground="#9B2C2C")
        self.tree.tag_configure("ok", background="#EAF7F0", foreground=T.GREEN_DARK)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select and self.on_select(self.selected()))
        self.tree.bind("<Double-1>", lambda e: self.on_double and self.selected() and self.on_double(self.selected()))
        self.set_columns(columns)

    @staticmethod
    def _style(widget):
        if DataTable._styled:
            return
        st = ttk.Style(widget)
        st.theme_use("clam")
        st.configure("Pharm.Treeview", background="white", fieldbackground="white", foreground=T.TEXT, rowheight=32,
                     borderwidth=0, font=(T.FAMILY, 10))
        st.configure("Pharm.Treeview.Heading", background="#EEF2F7", foreground=T.NAVY, relief="flat", font=(T.FAMILY, 10, "bold"), padding=(8, 8))
        st.map("Pharm.Treeview", background=[("selected", "#CFEBDD")], foreground=[("selected", T.TEXT)])
        st.map("Pharm.Treeview.Heading", background=[("active", "#E3E9F1")])
        DataTable._styled = True

    def set_columns(self, columns):
        """columns: list of dicts  key, label, width, anchor, fmt"""
        self.columns = columns
        self.tree.configure(columns=[c["key"] for c in columns])
        for c in columns:
            self.tree.heading(c["key"], text=c["label"], command=lambda k=c["key"]: self.sort_by(k))
            self.tree.column(c["key"], width=c.get("width", 110), anchor=c.get("anchor", "w"), stretch=c.get("stretch", True), minwidth=50)

    def load(self, rows, keep_filter=None):
        self.rows = list(rows)
        self._filter_text = keep_filter if keep_filter is not None else getattr(self, "_filter_text", "")
        self.refresh_view()

    def refresh_view(self):
        text = (getattr(self, "_filter_text", "") or "").lower().strip()
        self.view = [r for r in self.rows if not text or any(text in T.display(v).lower() for v in r.values())]
        key, desc = self.sort_state
        if key:
            self.view.sort(key=lambda r: self._sortkey(r.get(key)), reverse=desc)
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.view):
            tags = [self.row_tag(r)] if self.row_tag and self.row_tag(r) else (["odd"] if i % 2 else [])
            vals = [(c["fmt"](r.get(c["key"])) if c.get("fmt") else T.display(r.get(c["key"]))) for c in self.columns]
            self.tree.insert("", "end", iid=str(i), values=vals, tags=tags)
        n, total = len(self.view), len(self.rows)
        self.footer.configure(text=f"{n} record{'s' if n != 1 else ''}" + (f" (filtered from {total})" if n != total else ""))

    @staticmethod
    def _sortkey(v):
        if v is None:
            return (0, 0, "")
        if isinstance(v, (int, float, Decimal)):
            return (1, float(v), "")
        return (2, 0, str(v).lower())

    def sort_by(self, key):
        cur, desc = self.sort_state
        self.sort_state = (key, (not desc) if cur == key else False)
        self.refresh_view()

    def filter(self, text):
        self._filter_text = text
        self.refresh_view()

    def selected(self):
        sel = self.tree.selection()
        return self.view[int(sel[0])] if sel else None


def search_bar(master, on_change, placeholder="Search...", width=260):
    e = ctk.CTkEntry(master, placeholder_text=placeholder, width=width, height=36, corner_radius=8, border_color=T.BORDER, fg_color="white", font=T.font(13))
    e.bind("<KeyRelease>", lambda ev: on_change(e.get()))
    return e


# ---------------------------------------------------------------------------------------------- dialogs
def _center(win, parent, w, h):
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - h) // 3
    win.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")


class BaseDialog(ctk.CTkToplevel):
    def __init__(self, master, title, w, h):
        super().__init__(master, fg_color=T.BG)
        self.title(title)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        _center(self, master.winfo_toplevel(), w, h)
        self.after(120, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass


def confirm(master, title, message, ok_text="Delete", danger=True):
    result = {"ok": False}
    d = BaseDialog(master, title, 440, 210)
    ctk.CTkLabel(d, text=title, font=T.font(17, "bold"), text_color=T.NAVY, anchor="w").pack(fill="x", padx=26, pady=(24, 4))
    ctk.CTkLabel(d, text=message, font=T.font(13), text_color=T.TEXT, wraplength=390, justify="left", anchor="w").pack(fill="x", padx=26)
    bar = ctk.CTkFrame(d, fg_color="transparent")
    bar.pack(side="bottom", fill="x", padx=26, pady=20)

    def yes():
        result["ok"] = True
        d.destroy()
    button(bar, ok_text, yes, "danger" if danger else "primary", width=110).pack(side="right")
    button(bar, "Cancel", d.destroy, "ghost", width=100).pack(side="right", padx=8)
    d.wait_window()
    return result["ok"]


def info_dialog(master, title, lines, w=480, h=360):
    d = BaseDialog(master, title, w, h)
    ctk.CTkLabel(d, text=title, font=T.font(17, "bold"), text_color=T.NAVY, anchor="w").pack(fill="x", padx=26, pady=(22, 8))
    box = ctk.CTkTextbox(d, fg_color="white", border_width=1, border_color=T.BORDER, font=ctk.CTkFont(family="Courier New", size=12), text_color=T.TEXT)
    box.pack(fill="both", expand=True, padx=26)
    box.insert("1.0", "\n".join(lines))
    box.configure(state="disabled")
    button(d, "Close", d.destroy, "navy", width=110).pack(pady=16)
    return d


# ---------------------------------------------------------------------------------------------- generated form
class Field:
    """Description of one form input.  kind: text, textarea, int, decimal, date, bool, choice"""

    def __init__(self, name, label, kind="text", required=None, options=None, default=None, help=None,
                 max_length=None, optional_choice=False, minimum=None, readonly=False, span=1, secret=False):
        self.name, self.label, self.kind, self.required, self.options = name, label, kind, required, options
        self.default, self.help, self.max_length, self.optional_choice = default, help, max_length, optional_choice
        self.minimum, self.readonly, self.span, self.secret = minimum, readonly, span, secret


class FormDialog(BaseDialog):
    def __init__(self, master, title, fields, initial=None, submit_text="Save", on_submit=None, columns=2, subtitle=""):
        rows = (len(fields) + columns - 1) // columns
        h = min(190 + rows * 92 + (40 if subtitle else 0), 740)
        super().__init__(master, title, 330 * columns + 60, h)
        self.fields, self.on_submit, self.widgets, self.err_labels = fields, on_submit, {}, {}
        self.maps = {}
        ctk.CTkLabel(self, text=title, font=T.font(18, "bold"), text_color=T.NAVY, anchor="w").pack(fill="x", padx=28, pady=(22, 0))
        if subtitle:
            ctk.CTkLabel(self, text=subtitle, font=T.font(12), text_color=T.MUTED, anchor="w", wraplength=330 * columns).pack(fill="x", padx=28, pady=(2, 0))
        self.banner = ctk.CTkLabel(self, text="", font=T.font(12, "bold"), text_color=T.RED, fg_color="transparent", anchor="w", wraplength=330 * columns)
        self.banner.pack(fill="x", padx=28, pady=(6, 0))
        bar = ctk.CTkFrame(self, fg_color="transparent", width=1, height=1)
        bar.pack(side="bottom", fill="x", padx=28, pady=(8, 20))
        button(bar, submit_text, self.submit, "primary", width=130).pack(side="right")
        button(bar, "Cancel", self.destroy, "ghost", width=100).pack(side="right", padx=8)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent") if h >= 740 else ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20)
        for c in range(columns):
            body.grid_columnconfigure(c, weight=1, uniform="f")
        r = c = 0
        for f in fields:
            span = min(f.span, columns)
            if c + span > columns:
                r, c = r + 1, 0
            cell = ctk.CTkFrame(body, fg_color="transparent")
            cell.grid(row=r, column=c, columnspan=span, sticky="we", padx=8, pady=(6, 2))
            lab = f.label + (" *" if f.required else "")
            ctk.CTkLabel(cell, text=lab, font=T.font(12, "bold"), text_color=T.TEXT, anchor="w").pack(fill="x")
            w = self._make(cell, f, (initial or {}).get(f.name, f.default))
            w.pack(fill="x", pady=(3, 0))
            self.widgets[f.name] = w
            el = ctk.CTkLabel(cell, text=f.help or "", font=T.font(10), text_color=T.MUTED, anchor="w", wraplength=300 * span)
            el.pack(fill="x")
            self.err_labels[f.name] = el
            c += span
            if c >= columns:
                r, c = r + 1, 0
        self.bind("<Return>", lambda e: self.submit() if not isinstance(self.focus_get(), tk.Text) else None)
        self.bind("<Escape>", lambda e: self.destroy())

    def _make(self, parent, f, value):
        common = dict(height=36, corner_radius=8, border_color=T.BORDER, fg_color="white", font=T.font(13), text_color=T.TEXT)
        if f.kind == "textarea":
            w = ctk.CTkTextbox(parent, height=72, corner_radius=8, border_width=1, border_color=T.BORDER, fg_color="white", font=T.font(13), text_color=T.TEXT)
            if value is not None:
                w.insert("1.0", str(value))
            return w
        if f.kind == "bool":
            w = ctk.CTkCheckBox(parent, text="Yes", font=T.font(13), fg_color=T.GREEN, hover_color=T.GREEN_DARK, text_color=T.TEXT)
            if value:
                w.select()
            return w
        if f.kind == "choice":
            opts = list(f.options() if callable(f.options) else f.options)          # [(value, label)]
            if f.optional_choice or not f.required:
                opts = [(None, "-- none --")] + opts
            elif value is None:
                opts = [(None, "-- choose --")] + opts
            labels = [l for _, l in opts]
            self.maps[f.name] = dict((l, v) for v, l in opts)
            w = ctk.CTkComboBox(parent, values=labels or [""], state="readonly", height=36, corner_radius=8, border_color=T.BORDER,
                                fg_color="white", button_color=T.GREEN, button_hover_color=T.GREEN_DARK, font=T.font(13),
                                dropdown_font=T.font(13), text_color=T.TEXT)
            cur = next((l for v, l in opts if v == value), None)
            w.set(cur if cur is not None else (labels[0] if labels else ""))
            return w
        w = ctk.CTkEntry(parent, **common, placeholder_text="YYYY-MM-DD" if f.kind == "date" else "", show="•" if f.secret else "")
        if value is not None:
            w.insert(0, str(value))
        if f.readonly:
            w.configure(state="disabled")
        return w

    # ------------------------------------------------------------------
    def _value(self, f):
        w = self.widgets[f.name]
        if f.kind == "textarea":
            raw = w.get("1.0", "end").strip()
        elif f.kind == "bool":
            return bool(w.get())
        elif f.kind == "choice":
            return self.maps[f.name].get(w.get())
        else:
            raw = w.get().strip()
        return raw

    def collect(self):
        values, errors = {}, {}
        for f in self.fields:
            raw = self._value(f)
            if f.kind in ("bool", "choice"):
                if f.kind == "choice" and f.required and raw is None:
                    errors[f.name] = "Please choose a value."
                values[f.name] = raw
                continue
            if raw == "":
                if f.required:
                    errors[f.name] = "This field is required."
                values[f.name] = None
                continue
            try:
                if f.max_length and len(raw) > f.max_length:
                    raise ValueError(f"Maximum {f.max_length} characters.")
                if f.kind == "int":
                    raw = int(raw)
                    if f.minimum is not None and raw < f.minimum:
                        raise ValueError(f"Must be at least {f.minimum}.")
                elif f.kind == "decimal":
                    raw = Decimal(raw.replace(",", ""))
                    if f.minimum is not None and raw < f.minimum:
                        raise ValueError(f"Must be at least {f.minimum}.")
                elif f.kind == "date":
                    raw = datetime.strptime(raw, "%Y-%m-%d").date()
            except (ValueError, InvalidOperation) as e:
                msg = str(e)
                errors[f.name] = msg if "Maximum" in msg or "Must" in msg else {"int": "Enter a whole number.", "decimal": "Enter a number.", "date": "Use the format YYYY-MM-DD."}.get(f.kind, "Invalid value.")
            values[f.name] = raw
        return values, errors

    def submit(self):
        values, errors = self.collect()
        for name, lab in self.err_labels.items():
            f = next(x for x in self.fields if x.name == name)
            lab.configure(text=errors.get(name, f.help or ""), text_color=T.RED if name in errors else T.MUTED)
        if errors:
            self.banner.configure(text="Please correct the highlighted fields.")
            return
        try:
            if self.on_submit:
                self.on_submit(values)
        except DatabaseError as e:
            self.banner.configure(text=str(e))
            return
        self.destroy()


class SearchCombo(ctk.CTkComboBox):
    """Combo box that narrows its list while you type.  options = [(value, label)]"""

    def __init__(self, master, options=(), placeholder="", **kw):
        super().__init__(master, values=[""], height=36, corner_radius=8, border_color=T.BORDER, fg_color="white",
                         button_color=T.GREEN, button_hover_color=T.GREEN_DARK, font=T.font(13), dropdown_font=T.font(13),
                         text_color=T.TEXT, **kw)
        self.set_options(options)
        self._entry.bind("<KeyRelease>", self._typed, add="+")

    def set_options(self, options):
        self.options = list(options)
        self.by_label = {l: v for v, l in self.options}
        self.configure(values=[l for _, l in self.options] or [""])

    def _typed(self, _):
        t = self.get().lower()
        labels = [l for _, l in self.options if t in l.lower()]
        self.configure(values=labels or [l for _, l in self.options])

    def value(self):
        return self.by_label.get(self.get())

    def clear(self):
        self.set("")
        self.configure(values=[l for _, l in self.options] or [""])
