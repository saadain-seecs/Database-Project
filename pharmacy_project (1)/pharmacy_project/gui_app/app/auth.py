"""Administrator accounts: salted PBKDF2 password hashes in the table app_users, with a simple lock-out."""
import hashlib
import hmac
import os
import re
import time

from .database import DatabaseError

ITERATIONS = 200_000
MAX_ATTEMPTS, LOCK_SECONDS = 5, 30

TABLE_SQL = """CREATE TABLE IF NOT EXISTS app_users (
    user_id INT UNSIGNED NOT NULL AUTO_INCREMENT, username VARCHAR(50) NOT NULL, password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NULL, is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME NULL, CONSTRAINT pk_app_users PRIMARY KEY (user_id), CONSTRAINT uq_app_username UNIQUE (username)) ENGINE = InnoDB"""


class AuthError(Exception):
    """Message is safe to show on the login screen."""


def hash_password(password, iterations=ITERATIONS):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algo, iters, salt, digest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(test.hex(), digest)
    except (ValueError, AttributeError):
        return False


def validate_username(name):
    if not re.fullmatch(r"[A-Za-z0-9_.]{3,30}", name or ""):
        return "Username: 3-30 characters, letters, numbers, dot or underscore."
    return None


def validate_password(password, username=""):
    if len(password or "") < 8:
        return "Password must be at least 8 characters."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        return "Password must contain letters and numbers."
    if username and password.lower() == username.lower():
        return "Password must not be the same as the username."
    return None


class AuthService:
    _failures = {}                      # username -> (count, locked_until)

    def __init__(self, db):
        self.db = db

    def table_exists(self):
        return bool(self.db.scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name='app_users'", (self.db.cfg["database"],)))

    def ensure_table(self):
        """True when app_users exists (created now if this database account is allowed to)."""
        if self.table_exists():
            return True
        try:
            self.db.execute(TABLE_SQL)
        except DatabaseError:
            return False
        return self.table_exists()

    def has_users(self):
        return self.db.scalar("SELECT COUNT(*) FROM app_users") > 0

    def create_admin(self, username, password, full_name=None):
        err = validate_username(username) or validate_password(password, username)
        if err:
            raise AuthError(err)
        try:
            self.db.execute("INSERT INTO app_users (username, password_hash, full_name) VALUES (%s,%s,%s)", (username, hash_password(password), full_name or None))
        except DatabaseError as e:
            raise AuthError("That username is already taken." if "already exists" in str(e) else str(e))

    def login(self, username, password):
        key = (username or "").strip().lower()
        count, until = self._failures.get(key, (0, 0))
        if until > time.time():
            raise AuthError(f"Too many failed attempts. Try again in {int(until - time.time()) + 1} seconds.")
        user = self.db.one("SELECT user_id, username, password_hash, full_name, is_active FROM app_users WHERE username=%s", (username.strip(),)) if key else None
        stored = user["password_hash"] if user else hash_password("dummy-password", 1000)       # same work for unknown users
        ok = verify_password(password or "", stored) and user is not None and bool(user["is_active"])
        if not ok:
            count += 1
            self._failures[key] = (count, time.time() + LOCK_SECONDS if count >= MAX_ATTEMPTS else 0)
            left = MAX_ATTEMPTS - count
            raise AuthError("Incorrect username or password." + (f" {left} attempt(s) left." if 0 < left <= 2 else ""))
        self._failures.pop(key, None)
        self.db.execute("UPDATE app_users SET last_login=NOW() WHERE user_id=%s", (user["user_id"],))
        return {"user_id": user["user_id"], "username": user["username"], "full_name": user["full_name"] or user["username"]}

    def change_password(self, user_id, current, new):
        row = self.db.one("SELECT username, password_hash FROM app_users WHERE user_id=%s", (user_id,))
        if not row or not verify_password(current or "", row["password_hash"]):
            raise AuthError("Current password is incorrect.")
        err = validate_password(new, row["username"])
        if err:
            raise AuthError(err)
        self.db.execute("UPDATE app_users SET password_hash=%s WHERE user_id=%s", (hash_password(new), user_id))
