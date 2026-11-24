# PharmaCare - desktop GUI for the Pharmacy Database

A modern CustomTkinter application that works **directly on the existing `pharmacy_db`** (nothing is created, renamed or altered).

## 1. Install (one time)
```
pip install -r requirements.txt
```
(`customtkinter`, `mysql-connector-python`, `matplotlib`, `pillow`; Python 3.9+ with Tk, which is included in the normal Windows installer.)

## 2. Prepare the database (one time)
Run `mysql/01_schema.sql`, `02_programmability.sql`, `03_sample_data.sql` and `00_app_user.sql` (creates the login `pharmacy_app` / `pharmacy123`).

## 3. Admin login (one time)
Run `mysql/07_admin_users.sql` in Workbench once. It adds ONE new table, `app_users` (no existing table is changed).
At the first start the program shows **Create admin account**: choose a name, username and password.
After that every start shows the **Admin sign in** page. Passwords are stored only as salted PBKDF2-SHA256 hashes;
5 wrong attempts lock the account for 30 seconds; the sidebar has **Password** (change) and **Log out** buttons.

## 4. Run
```
cd gui_app
python main.py
```
If the connection fails, a small window asks for host, port, user, password and database; they are saved to `config.json`.
To use another account (for example root) set `PHARMACY_USER` / `PHARMACY_PASSWORD`, or edit `config.json`.

## Screens (all read and write the real database)
| Screen | Database objects used |
|---|---|
| Dashboard | views v_product_stock, v_low_stock, v_expired_stock, v_expiring_30_days; tables sales, sale_items, sale_allocations |
| Sales & Billing | procedure `sp_checkout` (transaction + triggers), view v_sale_details, sales history, delete bill (stock is restored by trigger) |
| Medicines / Categories / Suppliers / Customers | full add / edit / delete / search on products, categories, suppliers, customers (drop-downs filled from the related tables) |
| Purchases | procedure `sp_receive_stock`, purchase_orders (create pending, cancel, delete), batches per order |
| Stock | v_product_stock, stock_batches with status filter |
| Expiry | v_expiring_30_days, v_expired_stock, procedure `sp_refresh_stock_alerts`, stock_alerts |
| Staff | employees plus the pharmacists / cashiers subclass tables |
| Reports | 10 reports + procedure `sp_monthly_report`, CSV export, chart |

## Design notes
* `app/database.py` reads `information_schema` at start-up, so forms know which fields are required, their maximum length and ENUM values; the generic repository only builds SQL from columns that really exist. `app/services.py` checks that the expected tables, views and procedures exist and shows a clear message if not.
* Business rules stay in the database (triggers / procedures). The GUI only displays the database's own error messages in plain language.
* Layers: `database.py` (connection, schema, CRUD) - `services.py` (queries/procedures) - `widgets.py` / `theme.py` (UI parts) - `pages/` (screens).

## Limitations (honest list)
* The original database had no login table, so `07_admin_users.sql` adds `app_users` for the admin login. It is an application-level login: anyone who knows the MySQL account password could still open the database directly. "User Management" for staff records remains the **Staff** screen.
* Purchase orders have no line-item table, so a Pending order has no lines; stock arrives through "Receive stock".
* Tested on MariaDB 10.11 under a virtual display (42 automated checks in `tests/test_gui_flows.py`, screenshots in `tests/screenshots.py`). Not run on Oracle MySQL or on a real Windows desktop; fonts will look slightly different there (Segoe UI is used on Windows).

## Tests
```
python tests/test_gui_flows.py      # needs a display (on Linux: xvfb-run -a python tests/test_gui_flows.py)
```
It adds, edits and deletes records through the GUI code paths, runs a sale and a delivery, then checks the database is back to its original row counts.
