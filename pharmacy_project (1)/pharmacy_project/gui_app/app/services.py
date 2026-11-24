"""Business operations and report queries (everything the screens need beyond plain CRUD).
Stock handling is NOT re-implemented here: sp_checkout / sp_receive_stock and the triggers in the database do it."""
import json
from datetime import date

REQUIRED = {  # tables/columns the application relies on - verified against the real schema at start-up
    "categories": ["category_id", "category_name"], "suppliers": ["supplier_id", "name", "phone", "address", "is_active"],
    "products": ["product_id", "name", "category_id", "unit_price", "reorder_level", "requires_prescription"],
    "purchase_orders": ["po_id", "supplier_id", "order_date", "status", "total_cost"],
    "stock_batches": ["batch_id", "product_id", "po_id", "batch_no", "received_qty", "quantity", "expiry_date", "cost_price"],
    "customers": ["customer_id", "name", "phone"], "employees": ["employee_id", "name", "role", "phone", "hire_date", "is_active"],
    "pharmacists": ["employee_id", "license_no"], "cashiers": ["employee_id", "shift", "counter_no"],
    "sales": ["sale_id", "customer_id", "employee_id", "sale_date", "payment_method", "total_amount"],
    "sale_items": ["sale_id", "product_id", "quantity", "unit_price"],
    "sale_allocations": ["sale_id", "product_id", "batch_id", "quantity", "cost_price"],
}
REQUIRED_VIEWS = ["v_product_stock", "v_low_stock", "v_expiring_30_days", "v_expired_stock", "v_daily_sales_summary", "v_sale_details"]
REQUIRED_ROUTINES = ["sp_checkout", "sp_receive_stock", "sp_monthly_report", "sp_refresh_stock_alerts"]

REPORTS = {
    "Daily sales summary": "SELECT sale_day AS `Day`, bills AS `Bills`, units_sold AS `Units`, revenue AS `Revenue`, avg_bill AS `Average bill` FROM v_daily_sales_summary ORDER BY sale_day DESC",
    "Monthly sales and profit": ("SELECT DATE_FORMAT(s.sale_date,'%Y-%m') AS `Month`, SUM(a.quantity*si.unit_price) AS `Revenue`, SUM(a.quantity*a.cost_price) AS `Cost`, "
                                 "SUM(a.quantity*(si.unit_price-a.cost_price)) AS `Profit`, ROUND(100*SUM(a.quantity*(si.unit_price-a.cost_price))/SUM(a.quantity*si.unit_price),2) AS `Margin %` "
                                 "FROM sale_allocations a JOIN sales s ON s.sale_id=a.sale_id JOIN sale_items si ON si.sale_id=a.sale_id AND si.product_id=a.product_id "
                                 "GROUP BY DATE_FORMAT(s.sale_date,'%Y-%m') ORDER BY `Month`"),
    "Top 10 best-selling medicines": ("SELECT p.name AS `Medicine`, SUM(si.quantity) AS `Units sold`, SUM(si.quantity*si.unit_price) AS `Revenue` FROM sale_items si "
                                      "JOIN products p ON p.product_id=si.product_id GROUP BY p.product_id, p.name ORDER BY `Units sold` DESC, `Revenue` DESC LIMIT 10"),
    "Profit per medicine": ("SELECT p.name AS `Medicine`, SUM(a.quantity) AS `Units`, SUM(a.quantity*si.unit_price) AS `Revenue`, SUM(a.quantity*a.cost_price) AS `Cost`, "
                            "SUM(a.quantity*(si.unit_price-a.cost_price)) AS `Profit` FROM sale_allocations a JOIN sale_items si ON si.sale_id=a.sale_id AND si.product_id=a.product_id "
                            "JOIN products p ON p.product_id=a.product_id GROUP BY p.product_id, p.name ORDER BY `Profit` DESC"),
    "Revenue by category": ("SELECT c.category_name AS `Category`, SUM(si.quantity) AS `Units`, SUM(si.quantity*si.unit_price) AS `Revenue` FROM sale_items si "
                            "JOIN products p ON p.product_id=si.product_id JOIN categories c ON c.category_id=p.category_id GROUP BY c.category_id, c.category_name ORDER BY `Revenue` DESC"),
    "Supplier-wise purchase cost": ("SELECT s.name AS `Supplier`, COUNT(po.po_id) AS `Received orders`, COALESCE(SUM(po.total_cost),0) AS `Total cost` FROM suppliers s "
                                    "LEFT JOIN purchase_orders po ON po.supplier_id=s.supplier_id AND po.status='Received' GROUP BY s.supplier_id, s.name ORDER BY `Total cost` DESC"),
    "Top customers by spending": ("SELECT c.name AS `Customer`, COUNT(s.sale_id) AS `Bills`, SUM(s.total_amount) AS `Total spent` FROM customers c "
                                  "JOIN sales s ON s.customer_id=c.customer_id GROUP BY c.customer_id, c.name ORDER BY `Total spent` DESC LIMIT 15"),
    "Staff performance": ("SELECT e.name AS `Employee`, e.role AS `Role`, COUNT(s.sale_id) AS `Bills`, COALESCE(SUM(s.total_amount),0) AS `Revenue` FROM employees e "
                          "LEFT JOIN sales s ON s.employee_id=e.employee_id GROUP BY e.employee_id, e.name, e.role ORDER BY `Revenue` DESC"),
    "Stock value by category (at cost)": ("SELECT c.category_name AS `Category`, SUM(b.quantity) AS `Units on shelf`, SUM(b.quantity*b.cost_price) AS `Value at cost` FROM stock_batches b "
                                          "JOIN products p ON p.product_id=b.product_id JOIN categories c ON c.category_id=p.category_id WHERE b.expiry_date>=CURRENT_DATE AND b.quantity>0 "
                                          "GROUP BY c.category_id, c.category_name ORDER BY `Value at cost` DESC"),
    "Medicines never sold": ("SELECT p.product_id AS `ID`, p.name AS `Medicine`, p.unit_price AS `Price` FROM products p "
                             "WHERE NOT EXISTS (SELECT 1 FROM sale_items si WHERE si.product_id=p.product_id) ORDER BY p.name"),
}


class PharmacyService:
    def __init__(self, db, schema):
        self.db, self.schema = db, schema

    # ------------------------------------------------------------------ start-up check
    def verify_schema(self):
        problems = []
        for table, cols in REQUIRED.items():
            if table not in self.schema.columns:
                problems.append(f"missing table {table}")
                continue
            miss = [c for c in cols if c not in self.schema.columns[table]]
            if miss:
                problems.append(f"table {table} lacks {', '.join(miss)}")
        views = {r["table_name"] for r in self.db.query("SELECT table_name AS table_name FROM information_schema.views WHERE table_schema=%s", (self.db.cfg["database"],))}
        problems += [f"missing view {v}" for v in REQUIRED_VIEWS if v not in views]
        routines = {r["routine_name"] for r in self.db.query("SELECT routine_name AS routine_name FROM information_schema.routines WHERE routine_schema=%s", (self.db.cfg["database"],))}
        problems += [f"missing routine {r}" for r in REQUIRED_ROUTINES if r not in routines]
        return problems

    # ------------------------------------------------------------------ lookups for drop-downs
    def categories(self):
        return [(r["category_id"], r["category_name"]) for r in self.db.query("SELECT category_id, category_name FROM categories ORDER BY category_name")]

    def suppliers(self, active_only=True):
        w = "WHERE is_active=TRUE" if active_only else ""
        return [(r["supplier_id"], r["name"]) for r in self.db.query(f"SELECT supplier_id, name FROM suppliers {w} ORDER BY name")]

    def customers(self):
        return [(r["customer_id"], r["name"] + (f"  ({r['phone']})" if r["phone"] else "")) for r in
                self.db.query("SELECT customer_id, name, phone FROM customers ORDER BY customer_id")]

    def sellers(self):
        return [(r["employee_id"], f"{r['name']}  ({r['role']})") for r in self.db.query(
            "SELECT employee_id, name, role FROM employees WHERE is_active=TRUE AND role IN ('Pharmacist','Cashier') ORDER BY name")]

    def sellable_products(self):
        return self.db.query("SELECT p.product_id, p.name, p.unit_price, s.on_hand, p.requires_prescription "
                             "FROM products p JOIN v_product_stock s ON s.product_id=p.product_id ORDER BY p.name")

    def products_simple(self):
        return [(r["product_id"], r["name"]) for r in self.db.query("SELECT product_id, name FROM products ORDER BY name")]

    # ------------------------------------------------------------------ dashboard
    def stats(self):
        q = self.db.scalar
        d = {
            "medicines": q("SELECT COUNT(*) FROM products"),
            "units": q("SELECT COALESCE(SUM(on_hand),0) FROM v_product_stock"),
            "low_stock": q("SELECT COUNT(*) FROM v_low_stock"),
            "expired_batches": q("SELECT COUNT(*) FROM v_expired_stock"),
            "expired_loss": q("SELECT COALESCE(SUM(loss_at_cost),0) FROM v_expired_stock"),
            "near_expiry": q("SELECT COUNT(*) FROM v_expiring_30_days"),
            "suppliers": q("SELECT COUNT(*) FROM suppliers WHERE is_active=TRUE"),
            "customers": q("SELECT COUNT(*) FROM customers"),
            "bills": q("SELECT COUNT(*) FROM sales"),
            "revenue": q("SELECT COALESCE(SUM(total_amount),0) FROM sales"),
            "profit": q("SELECT COALESCE(SUM(a.quantity*(si.unit_price-a.cost_price)),0) FROM sale_allocations a "
                        "JOIN sale_items si ON si.sale_id=a.sale_id AND si.product_id=a.product_id"),
            "today_sales": q("SELECT COALESCE(SUM(total_amount),0) FROM sales WHERE DATE(sale_date)=CURRENT_DATE"),
        }
        return {k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in d.items()}

    def monthly_revenue(self):
        return self.db.query("SELECT DATE_FORMAT(sale_date,'%Y-%m') AS m, SUM(total_amount) AS revenue FROM sales GROUP BY DATE_FORMAT(sale_date,'%Y-%m') ORDER BY m")

    def category_revenue(self):
        return self.db.query("SELECT c.category_name AS name, SUM(si.quantity*si.unit_price) AS revenue FROM sale_items si JOIN products p ON p.product_id=si.product_id "
                             "JOIN categories c ON c.category_id=p.category_id GROUP BY c.category_id, c.category_name ORDER BY revenue DESC")

    def top_products(self, n=5):
        return self.db.query("SELECT p.name AS name, SUM(si.quantity) AS units FROM sale_items si JOIN products p ON p.product_id=si.product_id "
                             "GROUP BY p.product_id, p.name ORDER BY units DESC LIMIT %s", (n,))

    def recent_sales(self, n=6):
        return self.db.query("SELECT s.sale_id, s.sale_date, c.name AS customer, s.payment_method, s.total_amount FROM sales s "
                             "JOIN customers c ON c.customer_id=s.customer_id ORDER BY s.sale_date DESC, s.sale_id DESC LIMIT %s", (n,))

    def low_stock(self, n=6):
        return self.db.query("SELECT product_name, on_hand, reorder_level FROM v_low_stock ORDER BY shortage DESC LIMIT %s", (n,))

    def expiring(self, n=6):
        return self.db.query("SELECT product_name, batch_no, quantity, expiry_date, days_left FROM v_expiring_30_days ORDER BY days_left LIMIT %s", (n,))

    # ------------------------------------------------------------------ operations (stored procedures)
    def checkout(self, customer_id, employee_id, payment, cart):
        """cart = [(product_id, qty), ...]  ->  new sale_id.  One database transaction inside the procedure."""
        items = json.dumps([{"product_id": p, "qty": q} for p, q in cart])
        out, _ = self.db.call("sp_checkout", (customer_id, employee_id, payment, items, 0))
        return out[4]

    def receive_stock(self, supplier_id, order_date, lines):
        """lines = [dict(product_id, qty, cost_price, expiry_date, batch_no)] -> new po_id."""
        payload = json.dumps([{**l, "expiry_date": str(l["expiry_date"])} for l in lines])
        out, _ = self.db.call("sp_receive_stock", (supplier_id, order_date, payload, 0))
        return out[3]

    def sale_lines(self, sale_id):
        return self.db.query("SELECT product, quantity, unit_price, line_total FROM v_sale_details WHERE sale_id=%s ORDER BY product", (sale_id,))

    def sale_header(self, sale_id):
        return self.db.one("SELECT s.sale_id, s.sale_date, c.name AS customer, e.name AS served_by, s.payment_method, s.total_amount FROM sales s "
                           "JOIN customers c ON c.customer_id=s.customer_id JOIN employees e ON e.employee_id=s.employee_id WHERE s.sale_id=%s", (sale_id,))

    def monthly_report(self, year, month):
        _, sets = self.db.call("sp_monthly_report", (year, month))
        return sets

    def refresh_alerts(self):
        self.db.call("sp_refresh_stock_alerts")
        return self.db.query("SELECT alert_type, message, created_at FROM stock_alerts ORDER BY alert_type, alert_id")

    def run_report(self, name):
        return self.db.query(REPORTS[name])
