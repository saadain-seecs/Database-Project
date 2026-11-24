#!/usr/bin/env python3
"""
Pharmacy Inventory & Sales Management System - menu-based interface (optional deliverable).
All business rules (stock checks, FEFO, totals, transactions) live in the DATABASE;
this program only calls the stored procedures / views, so it stays very small.

Setup :  pip install mysql-connector-python
Config:  environment variables PHARMACY_HOST, PHARMACY_USER, PHARMACY_PASSWORD, PHARMACY_DB
         (defaults: localhost / pharmacy_app / pharmacy123 / pharmacy_db)
Run   :  python pharmacy_cli.py
"""
import json
import warnings
import os
import sys
from datetime import date

import mysql.connector

warnings.filterwarnings("ignore", category=DeprecationWarning)


def connect():
    kwargs = dict(host=os.getenv("PHARMACY_HOST", "localhost"),
                  user=os.getenv("PHARMACY_USER", "pharmacy_app"),
                  password=os.getenv("PHARMACY_PASSWORD", "pharmacy123"),
                  database=os.getenv("PHARMACY_DB", "pharmacy_db"),
                  autocommit=True)
    sock = os.getenv("PHARMACY_SOCKET")
    if sock:
        kwargs["unix_socket"] = sock
    return mysql.connector.connect(**kwargs)


def show(cursor, title=""):
    """Print a cursor's rows as a simple text table."""
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    if title:
        print(f"\n== {title} ==")
    if not rows:
        print("(no rows)")
        return
    data = [[("" if v is None else str(v)) for v in r] for r in rows]
    w = [max(len(c), *(len(r[i]) for r in data)) for i, c in enumerate(cols)]
    print("  ".join(c.ljust(w[i]) for i, c in enumerate(cols)))
    print("  ".join("-" * x for x in w))
    for r in data:
        print("  ".join(r[i].ljust(w[i]) for i in range(len(cols))))
    print(f"({len(rows)} row(s))")


def ask_int(prompt, minimum=1):
    while True:
        text = input(prompt).strip()
        if text.isdigit() and int(text) >= minimum:
            return int(text)
        print(f"  please enter a whole number >= {minimum}")


# ----------------------------------------------------------------- menu actions
def stock_overview(db):
    term = input("Medicine name contains (Enter = all): ").strip()
    cur = db.cursor()
    cur.execute("SELECT product_id, product_name, category_name, on_hand, reorder_level, expired_qty "
                "FROM v_product_stock WHERE product_name LIKE %s ORDER BY product_name", (f"%{term}%",))
    show(cur, "Stock overview")


def low_stock(db):
    cur = db.cursor()
    cur.execute("SELECT product_id, product_name, on_hand, reorder_level, shortage FROM v_low_stock "
                "ORDER BY shortage DESC")
    show(cur, "Medicines below their reorder level")


def expiry_report(db):
    cur = db.cursor()
    cur.execute("SELECT product_name, batch_no, quantity, expiry_date, days_left FROM v_expiring_30_days "
                "ORDER BY days_left")
    show(cur, "Batches expiring within 30 days")
    cur.execute("SELECT product_name, batch_no, quantity, expiry_date, days_expired, loss_at_cost "
                "FROM v_expired_stock ORDER BY loss_at_cost DESC")
    show(cur, "Expired batches still in stock (remove from shelf)")


def new_sale(db):
    cur = db.cursor()
    customer = ask_int("Customer id (1 = walk-in): ")
    employee = ask_int("Employee id serving (pharmacist/cashier): ")
    payment = input("Payment method [Cash/Card/Mobile Wallet] (Enter = Cash): ").strip() or "Cash"
    items = []
    print("Add items (empty product id to finish)")
    while True:
        text = input("  product id: ").strip()
        if not text:
            break
        if not text.isdigit():
            print("  numbers only")
            continue
        items.append({"product_id": int(text), "qty": ask_int("  quantity: ")})
    if not items:
        print("Nothing to sell.")
        return
    try:
        # the whole checkout is ONE database transaction inside the procedure
        result = cur.callproc("sp_checkout", (customer, employee, payment, json.dumps(items), 0))
        sale_id = result[4]
    except mysql.connector.Error as err:
        print(f"\nSale REJECTED and rolled back: {err.msg}")
        return
    cur.execute("SELECT product, quantity, unit_price, line_total FROM v_sale_details WHERE sale_id = %s", (sale_id,))
    show(cur, f"Bill #{sale_id}")
    cur.execute("SELECT total_amount FROM sales WHERE sale_id = %s", (sale_id,))
    print("TOTAL: Rs", cur.fetchone()[0])


def receive_stock(db):
    cur = db.cursor()
    supplier = ask_int("Supplier id: ")
    lines = []
    print("Add delivery lines (empty product id to finish)")
    while True:
        text = input("  product id: ").strip()
        if not text:
            break
        if not text.isdigit():
            print("  numbers only")
            continue
        lines.append({"product_id": int(text),
                      "qty": ask_int("  quantity: "),
                      "cost_price": float(input("  cost price per unit: ")),
                      "expiry_date": input("  expiry date (YYYY-MM-DD): ").strip(),
                      "batch_no": input("  batch number: ").strip()})
    if not lines:
        print("Nothing received.")
        return
    try:
        result = cur.callproc("sp_receive_stock", (supplier, date.today().isoformat(), json.dumps(lines), 0))
    except mysql.connector.Error as err:
        print(f"\nDelivery REJECTED and rolled back: {err.msg}")
        return
    cur.execute("SELECT po_id, supplier_id, order_date, status, total_cost FROM purchase_orders WHERE po_id = %s",
                (result[3],))
    show(cur, "Purchase order created")


def daily_sales(db):
    cur = db.cursor()
    cur.execute("SELECT sale_day, bills, units_sold, revenue, avg_bill FROM v_daily_sales_summary "
                "ORDER BY sale_day DESC LIMIT 10")
    show(cur, "Last 10 trading days")


def monthly_report(db):
    year = ask_int("Year (e.g. 2026): ", 2000)
    month = ask_int("Month (1-12): ")
    cur = db.cursor()
    try:
        cur.callproc("sp_monthly_report", (year, month))
        titles = ["Summary", "Top 5 products by profit", "Revenue by category"]
        for title, result in zip(titles, cur.stored_results()):
            rows, cols = result.fetchall(), [d[0] for d in result.description]
            print(f"\n== {title} ==")
            print("  ".join(cols))
            for r in rows:
                print("  ".join(str(v) for v in r))
    except mysql.connector.Error as err:
        print(f"Report failed: {err.msg}")


def top_sellers(db):
    cur = db.cursor()
    cur.execute("SELECT p.name, SUM(si.quantity) AS units_sold, SUM(si.quantity * si.unit_price) AS revenue "
                "FROM sale_items si JOIN products p ON p.product_id = si.product_id "
                "GROUP BY p.product_id, p.name ORDER BY units_sold DESC, revenue DESC LIMIT 10")
    show(cur, "Top 10 best-selling medicines")


def customer_history(db):
    cid = ask_int("Customer id: ")
    cur = db.cursor()
    cur.execute("SELECT s.sale_id, s.sale_date, s.payment_method, s.total_amount FROM sales s "
                "WHERE s.customer_id = %s ORDER BY s.sale_date DESC", (cid,))
    show(cur, f"Purchase history of customer {cid}")


MENU = [("Stock overview / search", stock_overview), ("Low-stock medicines", low_stock),
        ("Expiry report", expiry_report), ("New sale (checkout)", new_sale),
        ("Receive stock from a supplier", receive_stock), ("Daily sales summary", daily_sales),
        ("Monthly sales & profit report", monthly_report), ("Top 10 best sellers", top_sellers),
        ("Customer purchase history", customer_history)]


def main():
    try:
        db = connect()
    except mysql.connector.Error as err:
        sys.exit(f"Cannot connect to the database: {err}")
    while True:
        print("\n===== PHARMACY MANAGEMENT SYSTEM =====")
        for i, (name, _) in enumerate(MENU, 1):
            print(f" {i}. {name}")
        print(" 0. Exit")
        try:
            choice = input("Choose: ").strip()
        except EOFError:
            break
        if choice == "0":
            break
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            try:
                MENU[int(choice) - 1][1](db)
            except mysql.connector.Error as err:
                print(f"Database error: {err.msg}")
        else:
            print("Invalid choice.")
    db.close()
    print("Goodbye.")


if __name__ == "__main__":
    main()
