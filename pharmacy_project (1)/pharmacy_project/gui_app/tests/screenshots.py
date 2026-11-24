"""Opens every page under a virtual display and saves screenshots (used for checking the layout)."""
import os, sys, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PHARMACY_SOCKET", "/run/mysqld/mysqld.sock")
import customtkinter as ctk
from app.config import load_config
from app.database import Database, Schema
from app.main_window import MainWindow, NAV

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/shots"
os.makedirs(out, exist_ok=True)
db = Database(load_config()); db.connect(); schema = Schema(db)
app = MainWindow(db, schema)
app.update()
for name, _, _ in NAV:
    app.show(name)
    for _ in range(12):
        app.update(); time.sleep(0.05)
    fn = os.path.join(out, name.replace(" ", "_").replace("&", "and") + ".png")
    subprocess.run(["import", "-window", "root", fn], check=False)
    print("shot", name)
app.destroy()
