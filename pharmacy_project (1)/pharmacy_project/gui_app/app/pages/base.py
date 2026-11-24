"""Page base class and a generic CRUD page that adapts itself to the database schema."""
import copy
from datetime import date

import customtkinter as ctk

from .. import theme as T
from ..database import DatabaseError, Repository
from ..widgets import DataTable, Field, FormDialog, button, confirm, search_bar, toast


class Page(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG)
        self.app = app
        self.db, self.schema, self.svc = app.db, app.schema, app.svc
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=28, pady=(22, 6))
        text = ctk.CTkFrame(head, fg_color="transparent")
        text.pack(side="left")
        ctk.CTkLabel(text, text=self.title, font=T.font(24, "bold"), text_color=T.NAVY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(text, text=self.subtitle, font=T.font(13), text_color=T.MUTED, anchor="w").pack(anchor="w")
        self.actions = ctk.CTkFrame(head, fg_color="transparent", width=1, height=1)
        self.actions.pack(side="right")
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=28, pady=(8, 22))

    def on_show(self):
        """Called every time the page is opened - reload data here."""

    def notify(self, message, kind="success"):
        toast(self, message, kind)

    def guard(self, fn, *a, **kw):
        """Run fn; show database errors as a red toast instead of crashing."""
        try:
            return fn(*a, **kw)
        except DatabaseError as e:
            self.notify(str(e), "error")
        return None


class CrudPage(Page):
    """List + search + add/edit/delete for one table.  Subclasses set the class attributes below."""
    table = ""
    select_sql = ""
    columns = []                 # dicts for DataTable
    fields = []                  # Field objects (names must be real columns)
    noun = "record"
    row_tag = None
    search_hint = "Search..."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.schema.require(self.table, [f.name for f in self.fields if f.name in self.schema.columns[self.table]])
        self.repo = Repository(self.db, self.schema, self.table)
        self.pk = self.repo.pk[0]
        self.build_toolbar()
        self.grid_ = DataTable(self.body, self.columns, on_double=lambda r: self.edit(), row_tag=self.row_tag)
        self.grid_.pack(fill="both", expand=True, pady=(10, 0))
        button(self.actions, f"+  Add {self.noun}", self.add, "primary", width=150).pack(side="right")
        button(self.actions, "Delete", self.delete, "ghost", width=90).pack(side="right", padx=8)
        button(self.actions, "Edit", self.edit, "ghost", width=80).pack(side="right")

    def build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        self.toolbar.pack(fill="x")
        self.search = search_bar(self.toolbar, lambda t: self.grid_.filter(t), self.search_hint, 300)
        self.search.pack(side="left")
        button(self.toolbar, "⟳ Refresh", self.on_show, "ghost", width=100).pack(side="left", padx=8)

    # ------------------------------------------------------------------ data
    def fetch(self):
        return self.db.query(self.select_sql)

    def on_show(self):
        rows = self.guard(self.fetch)
        if rows is not None:
            self.grid_.load(self.post_process(rows))

    def post_process(self, rows):
        return rows

    # ------------------------------------------------------------------ fields adapted to the schema
    def resolved_fields(self):
        out = []
        for f in self.fields:
            f = copy.copy(f)
            cols = self.schema.columns[self.table]
            if f.name in cols:
                info = cols[f.name]
                if f.required is None:
                    f.required = self.schema.is_required(self.table, f.name) and f.kind != "bool"
                if f.kind == "text" and not f.max_length:
                    f.max_length = info["max_length"]
                if f.kind == "choice" and f.options is None and info["enum"]:
                    f.options = [(v, v) for v in info["enum"]]
            out.append(f)
        return [f for f in out if f.name in self.schema.columns[self.table] or getattr(f, "virtual", False)]

    # ------------------------------------------------------------------ actions
    def add(self):
        initial = {f.name: f.default for f in self.fields}
        FormDialog(self, f"Add {self.noun}", self.resolved_fields(), initial, "Save", self._create, subtitle=self.form_subtitle())

    def edit(self):
        row = self.grid_.selected()
        if not row:
            return self.notify(f"Select a {self.noun} first.", "warn")
        raw = self.guard(self.repo.get, row[self.pk])
        if raw is None:
            return
        FormDialog(self, f"Edit {self.noun}", self.resolved_fields(), self.initial_for_edit(raw), "Save changes",
                   lambda v: self._update(row[self.pk], v), subtitle=self.form_subtitle())

    def delete(self):
        row = self.grid_.selected()
        if not row:
            return self.notify(f"Select a {self.noun} first.", "warn")
        if confirm(self, f"Delete {self.noun}", f"Delete this {self.noun} permanently?\n\n{self.describe(row)}"):
            if self.guard(self.do_delete, row[self.pk]) is not None:
                self.notify(f"{self.noun.capitalize()} deleted.")
                self.on_show()

    def form_subtitle(self):
        return ""

    def initial_for_edit(self, raw):
        return raw

    def describe(self, row):
        return next((str(v) for k, v in row.items() if k != self.pk and v is not None), str(row[self.pk]))

    def do_delete(self, key):
        return self.repo.delete(key) or True

    # ------------------------------------------------------------------ save
    def _prepare(self, values, creating):
        cols = self.schema.columns[self.table]
        out = {}
        for k, v in values.items():
            if k not in cols:
                continue
            if v is None and not cols[k]["nullable"]:
                continue                                  # let the column DEFAULT apply / keep the old value
            out[k] = v
        return out

    def _create(self, values):
        self.do_create(self._prepare(values, True), values)
        self.notify(f"{self.noun.capitalize()} added.")
        self.on_show()

    def _update(self, key, values):
        self.do_update(key, self._prepare(values, False), values)
        self.notify(f"{self.noun.capitalize()} updated.")
        self.on_show()

    def do_create(self, clean, raw):
        return self.repo.insert(clean)

    def do_update(self, key, clean, raw):
        return self.repo.update(key, clean)
