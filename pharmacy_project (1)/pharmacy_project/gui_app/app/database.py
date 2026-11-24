"""Database access layer: connection, schema inspection and generic CRUD.

Nothing here hard-codes the pharmacy schema.  The Schema class reads information_schema, so the
forms can adapt to the real columns (types, NOT NULL, ENUM values, lengths) and the generic
Repository only ever builds SQL from column names that really exist.
"""
import warnings
from contextlib import contextmanager

import mysql.connector

warnings.filterwarnings("ignore", category=DeprecationWarning)


class DatabaseError(Exception):
    """An error whose message is safe to show to the user."""


class SchemaError(Exception):
    pass


def friendly(err):
    """Translate a MySQL error into a short, readable message."""
    no = getattr(err, "errno", None)
    msg = getattr(err, "msg", str(err))
    if no == 1062:
        key = msg.split("for key")[-1].strip(" '\"").split(".")[-1]
        return f"A record with the same value already exists ({key})."
    if no in (1451, 1217):
        return "This record is used by other records, so it cannot be deleted or changed."
    if no in (1452, 1216):
        return "The selected related record does not exist."
    if no in (3819, 4025):
        name = msg.split("constraint")[-1].split()[0].strip("'\"`") if "constraint" in msg.lower() else ""
        return f"A value breaks a rule of the database ({name or 'CHECK constraint'})."
    if no == 1048:
        return "A required field is empty: " + msg.split("'")[1] if "'" in msg else "A required field is empty."
    if no == 1644:
        return msg                                  # message written by our triggers/procedures
    if no in (1265, 1366, 1292):
        return "A value has the wrong type or format."
    if no == 1406:
        return "A value is too long for its field."
    if no == 1142 or no == 1044:
        return "The database account has no permission for this action."
    if no == 1175:
        return "Safe-update mode blocked the statement."
    if no in (2003, 2002, 2006, 2013):
        return "Cannot reach the database server."
    if no == 1045:
        return "Access denied: wrong user name or password."
    return msg


class Database:
    def __init__(self, cfg):
        self.cfg = cfg
        self.conn = None

    # ------------------------------------------------------------------ connection
    def connect(self):
        args = dict(user=self.cfg["user"], password=self.cfg["password"], database=self.cfg["database"],
                    autocommit=True, connection_timeout=8)
        if self.cfg.get("unix_socket"):
            args["unix_socket"] = self.cfg["unix_socket"]
        else:
            args.update(host=self.cfg["host"], port=int(self.cfg["port"]))
        try:
            self.conn = mysql.connector.connect(**args)
        except mysql.connector.Error as err:
            raise DatabaseError(friendly(err)) from err

    def _cursor(self):
        if self.conn is None or not self.conn.is_connected():
            self.connect()
        return self.conn.cursor(dictionary=True, buffered=True)

    def close(self):
        if self.conn is not None:
            self.conn.close()

    # ------------------------------------------------------------------ queries
    def query(self, sql, params=None):
        cur = self._cursor()
        try:
            cur.execute(sql, params or ())
            return cur.fetchall()
        except mysql.connector.Error as err:
            raise DatabaseError(friendly(err)) from err
        finally:
            cur.close()

    def one(self, sql, params=None):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql, params=None):
        row = self.one(sql, params)
        return next(iter(row.values())) if row else None

    def execute(self, sql, params=None):
        """Run INSERT/UPDATE/DELETE. Returns (rows_affected, last_insert_id)."""
        cur = self._cursor()
        try:
            cur.execute(sql, params or ())
            return cur.rowcount, cur.lastrowid
        except mysql.connector.Error as err:
            raise DatabaseError(friendly(err)) from err
        finally:
            cur.close()

    def call(self, proc, args=()):
        """CALL a stored procedure. Returns (arguments incl. OUT values, [result sets as lists of dict rows])."""
        if self.conn is None or not self.conn.is_connected():
            self.connect()
        cur = self.conn.cursor()                       # plain cursor: callproc then returns the argument list
        try:
            result = cur.callproc(proc, list(args))
            sets = [[dict(zip(rs.column_names, row)) for row in rs.fetchall()] for rs in cur.stored_results()]
            return list(result), sets
        except mysql.connector.Error as err:
            raise DatabaseError(friendly(err)) from err
        finally:
            cur.close()

    @contextmanager
    def transaction(self):
        """with db.transaction():  several statements, committed together or rolled back together."""
        cur = self._cursor()
        cur.execute("START TRANSACTION")
        cur.close()
        try:
            yield
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            if isinstance(err, mysql.connector.Error):
                raise DatabaseError(friendly(err)) from err
            raise


class Schema:
    """What the database really looks like (read from information_schema)."""

    def __init__(self, db):
        self.db = db
        name = db.cfg["database"]
        self.columns = {}
        for r in db.query("SELECT table_name t, column_name c, data_type dt, column_type ct, is_nullable nl, column_default df, "
                          "column_key ck, extra ex, character_maximum_length ml FROM information_schema.columns "
                          "WHERE table_schema=%s ORDER BY table_name, ordinal_position", (name,)):
            enum = []
            if r["dt"] == "enum":
                enum = [v.strip("'") for v in r["ct"][5:-1].split(",")]
            self.columns.setdefault(r["t"], {})[r["c"]] = dict(
                type=r["dt"], full_type=r["ct"], nullable=r["nl"] == "YES", default=r["df"], key=r["ck"],
                auto=("auto_increment" in (r["ex"] or "")), max_length=r["ml"], enum=enum, unsigned="unsigned" in r["ct"])
        self.foreign_keys = db.query(
            "SELECT table_name t, column_name c, referenced_table_name rt, referenced_column_name rc "
            "FROM information_schema.key_column_usage WHERE table_schema=%s AND referenced_table_name IS NOT NULL", (name,))

    def tables(self):
        return list(self.columns)

    def require(self, table, cols=()):
        if table not in self.columns:
            raise SchemaError(f"Table '{table}' was not found in database '{self.db.cfg['database']}'.")
        missing = [c for c in cols if c not in self.columns[table]]
        if missing:
            raise SchemaError(f"Table '{table}' has no column(s): {', '.join(missing)}")

    def col(self, table, column):
        return self.columns[table][column]

    def is_required(self, table, column):
        c = self.col(table, column)
        return (not c["nullable"]) and c["default"] is None and not c["auto"]

    def pk(self, table):
        return [c for c, i in self.columns[table].items() if i["key"] == "PRI"]


class Repository:
    """Generic INSERT / UPDATE / DELETE / SELECT-by-key for one table, validated against the Schema."""

    def __init__(self, db, schema, table):
        schema.require(table)
        self.db, self.schema, self.table = db, schema, table
        self.pk = schema.pk(table)

    def _check(self, values):
        bad = [k for k in values if k not in self.schema.columns[self.table]]
        if bad:
            raise SchemaError(f"Unknown column(s) for {self.table}: {', '.join(bad)}")

    def get(self, key):
        key = key if isinstance(key, (tuple, list)) else (key,)
        where = " AND ".join(f"`{c}`=%s" for c in self.pk)
        return self.db.one(f"SELECT * FROM `{self.table}` WHERE {where}", key)

    def insert(self, values):
        self._check(values)
        cols = ", ".join(f"`{c}`" for c in values)
        marks = ", ".join(["%s"] * len(values))
        return self.db.execute(f"INSERT INTO `{self.table}` ({cols}) VALUES ({marks})", list(values.values()))[1]

    def update(self, key, values):
        self._check(values)
        key = key if isinstance(key, (tuple, list)) else (key,)
        sets = ", ".join(f"`{c}`=%s" for c in values)
        where = " AND ".join(f"`{c}`=%s" for c in self.pk)
        return self.db.execute(f"UPDATE `{self.table}` SET {sets} WHERE {where}", list(values.values()) + list(key))[0]

    def delete(self, key):
        key = key if isinstance(key, (tuple, list)) else (key,)
        where = " AND ".join(f"`{c}`=%s" for c in self.pk)
        return self.db.execute(f"DELETE FROM `{self.table}` WHERE {where}", key)[0]
