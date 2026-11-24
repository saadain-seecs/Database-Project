#!/usr/bin/env python3
"""PharmaCare - desktop GUI for the Pharmacy Inventory & Sales Management System (CS220 project).

Run:  python main.py
Database settings: environment variables PHARMACY_HOST / PORT / USER / PASSWORD / DB, or config.json (see README_GUI.md).
"""
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from app.config import load_config, save_config
from app.database import Database, DatabaseError, Schema
from app.auth import AuthService
from app.services import PharmacyService

ctk.set_appearance_mode("light")


def ask_connection(cfg, error):
    """Small login window shown when the connection fails."""
    from app import theme as T
    result = {}
    win = ctk.CTk(fg_color=T.BG)
    win.title("Connect to the pharmacy database")
    win.geometry("440x560")
    win.resizable(False, False)
    ctk.CTkLabel(win, text="✚", width=54, height=54, corner_radius=14, fg_color=T.GREEN, text_color="white", font=T.font(26, "bold")).pack(pady=(28, 6))
    ctk.CTkLabel(win, text="Connect to MySQL", font=T.font(20, "bold"), text_color=T.NAVY).pack()
    ctk.CTkLabel(win, text=error, font=T.font(12), text_color=T.RED, wraplength=380).pack(pady=(6, 10))
    entries = {}
    for key, label in [("host", "Host"), ("port", "Port"), ("user", "User"), ("password", "Password"), ("database", "Database")]:
        ctk.CTkLabel(win, text=label, font=T.font(12, "bold"), text_color=T.TEXT, anchor="w").pack(fill="x", padx=40, pady=(6, 0))
        e = ctk.CTkEntry(win, height=36, show="•" if key == "password" else "", border_color=T.BORDER, fg_color="white")
        e.insert(0, str(cfg[key]))
        e.pack(fill="x", padx=40)
        entries[key] = e

    def go():
        for k, e in entries.items():
            cfg[k] = e.get().strip()
        result["cfg"] = cfg
        win.destroy()
    ctk.CTkButton(win, text="Connect", height=42, fg_color=T.GREEN, hover_color=T.GREEN_DARK, font=T.font(14, "bold"), command=go).pack(fill="x", padx=40, pady=22)
    win.bind("<Return>", lambda e: go())
    win.mainloop()
    return result.get("cfg")


def connect():
    cfg = load_config()
    error = None
    while True:
        db = Database(cfg)
        try:
            db.connect()
            return db, cfg
        except DatabaseError as e:
            error = str(e)
        cfg = ask_connection(cfg, f"{error}\nCheck the settings and try again.")
        if cfg is None:
            sys.exit(1)
        cfg["port"] = int(cfg["port"] or 3306)


def main():
    db, cfg = connect()
    try:
        schema = Schema(db)
        problems = PharmacyService(db, schema).verify_schema()
    except DatabaseError as e:
        problems = [str(e)]
    if problems:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database does not match", "The database is missing parts this application needs:\n\n- " + "\n- ".join(problems[:12]) +
                             "\n\nRun mysql/01_schema.sql, 02_programmability.sql and 03_sample_data.sql first.")
        sys.exit(1)
    if not cfg.get("unix_socket"):
        save_config(cfg)
    from app.login_window import LoginWindow, SetupWindow
    from app.main_window import MainWindow
    auth = AuthService(db)
    if not auth.ensure_table():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Admin table missing", "The table app_users does not exist and this database account may not create it.\n\n"
                             "Run mysql/07_admin_users.sql in MySQL Workbench once, then start the program again.")
        sys.exit(1)
    label = f"{cfg['database']} @ {cfg.get('unix_socket') or cfg['host']}"
    while True:                                           # sign in -> work -> log out -> sign in ...
        window = (LoginWindow if auth.has_users() else SetupWindow)(auth, label)
        window.mainloop()
        if not window.result:
            break                                         # window closed without signing in
        app = MainWindow(db, schema, user=window.result, auth=auth)
        app.mainloop()
        if not app.logged_out:
            break
    db.close()


if __name__ == "__main__":
    main()
