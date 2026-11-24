"""Checks the admin login: hashing, first-run setup, sign-in, lock-out, change password and the windows themselves."""
import os, sys, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PHARMACY_SOCKET", "/run/mysqld/mysqld.sock")
os.environ["PHARMACY_USER"] = "root"; os.environ["PHARMACY_PASSWORD"] = ""
from app.config import load_config
from app.database import Database, Schema
from app import auth as A
from app.login_window import LoginWindow, SetupWindow
from app.main_window import MainWindow

shots = sys.argv[1] if len(sys.argv) > 1 else None
db = Database(load_config()); db.connect()
db.execute("DROP TABLE IF EXISTS app_users")
svc = A.AuthService(db)
passed = failed = 0
def check(name, cond, extra=""):
    global passed, failed
    if cond: passed += 1; print("PASS", name)
    else: failed += 1; print("FAIL", name, extra)
def raises(fn, text):
    try: fn()
    except A.AuthError as e: return text.lower() in str(e).lower()
    return False
def shot(win, name):
    for _ in range(10): win.update(); time.sleep(0.05)
    if shots: os.makedirs(shots, exist_ok=True); subprocess.run(["import", "-window", "root", f"{shots}/{name}.png"])

h = A.hash_password("Secret123")
check("hash is salted PBKDF2 and not plain text", h.startswith("pbkdf2_sha256$") and "Secret123" not in h and A.hash_password("Secret123") != h)
check("verify accepts right / rejects wrong password", A.verify_password("Secret123", h) and not A.verify_password("secret123", h) and not A.verify_password("x", "garbage"))
check("password rules", A.validate_password("short1") and A.validate_password("onlyletters") and A.validate_password("12345678") and A.validate_password("admin123", "admin123") and not A.validate_password("Admin2026!x"))
check("username rules", A.validate_username("a") and A.validate_username("bad name") and not A.validate_username("admin_1"))
check("table is created on demand", svc.ensure_table() and svc.table_exists())
check("no users at first", not svc.has_users())

# ---- first-run window
setup = SetupWindow(svc, "test"); shot(setup, "setup")
for k, v in {"full_name": "Pharmacy Manager", "username": "admin", "password": "Pharma2026", "confirm": "Different1"}.items(): setup.fields[k].insert(0, v)
setup.submit(); check("setup: mismatching passwords refused", setup.result is None and "match" in setup.msg.cget("text"))
setup.fields["confirm"].delete(0, "end"); setup.fields["confirm"].insert(0, "Pharma2026"); setup.submit()
check("setup: admin created and signed in", setup.result and setup.result["username"] == "admin" and setup.result["full_name"] == "Pharmacy Manager")
check("password stored as hash only", "Pharma2026" not in db.scalar("SELECT password_hash FROM app_users WHERE username='admin'"))
check("duplicate admin username refused", raises(lambda: svc.create_admin("admin", "Another123"), "taken"))

# ---- sign-in
check("login: wrong password refused with generic message", raises(lambda: svc.login("admin", "nope"), "incorrect username or password"))
check("login: unknown user gets the same message", raises(lambda: svc.login("ghost", "Pharma2026"), "incorrect username or password"))
u = svc.login("admin", "Pharma2026"); check("login: correct credentials", u["username"] == "admin")
check("login: last_login recorded", db.scalar("SELECT last_login FROM app_users WHERE username='admin'") is not None)
for _ in range(5):
    try: svc.login("admin", "bad")
    except A.AuthError: pass
check("lock-out after 5 failures (even with the right password)", raises(lambda: svc.login("admin", "Pharma2026"), "too many"))
A.AuthService._failures.clear()

login = LoginWindow(svc, "test"); shot(login, "login")
login.fields["username"].insert(0, "admin"); login.fields["password"].insert(0, "wrong"); login.submit()
check("login window: shows error and keeps window open", login.result is None and "Incorrect" in login.msg.cget("text"))
shot(login, "login_error")
login.fields["password"].insert(0, "Pharma2026"); login.submit()
check("login window: success returns the user", login.result and login.result["username"] == "admin")

# ---- change password and inactive accounts
check("change password: wrong current refused", raises(lambda: svc.change_password(u["user_id"], "x", "NewPass2026"), "current password"))
check("change password: weak new password refused", raises(lambda: svc.change_password(u["user_id"], "Pharma2026", "weak"), "at least 8"))
svc.change_password(u["user_id"], "Pharma2026", "NewPass2026")
check("change password: old fails, new works", raises(lambda: svc.login("admin", "Pharma2026"), "incorrect") and svc.login("admin", "NewPass2026"))
A.AuthService._failures.clear()
db.execute("UPDATE app_users SET is_active=FALSE WHERE username='admin'")
check("deactivated admin cannot sign in", raises(lambda: svc.login("admin", "NewPass2026"), "incorrect"))
db.execute("UPDATE app_users SET is_active=TRUE WHERE username='admin'")

# ---- main window with a signed-in user
app = MainWindow(db, Schema(db), user=u, auth=svc); shot(app, "main_with_user")
def texts(w):
    out = []
    try: out.append(str(w.cget("text")))
    except Exception: pass
    for c in w.winfo_children(): out += texts(c)
    return out
t = texts(app)
check("main window shows the signed-in user, role, Log out and Password buttons", "Administrator" in t and "Log out" in t and "Password" in t and "P" in t and "Pharmacy Manager" in t)
app.destroy()

db.execute("DROP TABLE app_users")
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
