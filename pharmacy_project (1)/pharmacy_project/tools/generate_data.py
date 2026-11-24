#!/usr/bin/env python3
"""
Generates the sample data for the Pharmacy Inventory & Sales Management System.

 * Output: mysql/03_sample_data.sql and postgres/pg_03_sample_data.sql
 * Deterministic (fixed random seed) so everybody gets exactly the same rows.
 * It simulates the First-Expiry-First-Out stock logic of the database triggers,
   so every generated sale is feasible and none is rejected by the triggers.
 * All names, phone numbers and prices are fictional / illustrative.

Usage:  python3 tools/generate_data.py
"""
import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(220)                      # CS220
ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------
# Master data
# ----------------------------------------------------------------------------
CATEGORIES = [
    ("Analgesics & Antipyretics", "Pain and fever relief"),
    ("Antibiotics", "Prescription antibacterial medicines"),
    ("Antacids & Gastro", "Acidity, ulcer and stomach care"),
    ("Antihistamines & Allergy", "Allergy and cold-allergy relief"),
    ("Cough, Cold & Respiratory", "Cough syrups, decongestants, inhalers"),
    ("Vitamins & Supplements", "Vitamins, minerals and tonics"),
    ("Diabetes Care", "Anti-diabetic medicines and testing supplies"),
    ("Cardiovascular", "Blood-pressure and cholesterol medicines"),
    ("Dermatology", "Creams and ointments for the skin"),
    ("First Aid & Devices", "Antiseptics, dressings and small devices"),
]

# key, name, generic, category (1-based), price PKR, reorder level, rx?
PRODUCTS = [
    ("panadol", "Panadol 500mg Tablets", "Paracetamol", 1, 35, 60, False),
    ("calpol", "Calpol 120mg/5ml Syrup", "Paracetamol", 1, 145, 25, False),
    ("brufen", "Brufen 400mg Tablets", "Ibuprofen", 1, 95, 40, False),
    ("ponstan", "Ponstan Forte 500mg", "Mefenamic acid", 1, 120, 35, False),
    ("disprin", "Disprin 300mg", "Aspirin", 1, 28, 40, False),
    ("voltral", "Voltral 50mg Tablets", "Diclofenac sodium", 1, 170, 25, True),
    ("augmentin", "Augmentin 625mg Tablets", "Amoxicillin + Clavulanate", 2, 480, 40, True),
    ("flagyl", "Flagyl 400mg Tablets", "Metronidazole", 2, 90, 30, True),
    ("zithromax", "Zithromax 500mg Tablets", "Azithromycin", 2, 620, 20, True),
    ("cipro", "Cipro 500mg Tablets", "Ciprofloxacin", 2, 260, 25, True),
    ("amoxil", "Amoxil 500mg Capsules", "Amoxicillin", 2, 210, 30, True),
    ("septran", "Septran DS Tablets", "Co-trimoxazole", 2, 130, 25, True),
    ("risek", "Risek 20mg Capsules", "Omeprazole", 3, 180, 40, False),
    ("nexum", "Nexum 40mg Capsules", "Esomeprazole", 3, 420, 40, False),
    ("gaviscon", "Gaviscon Liquid 150ml", "Alginate + Antacid", 3, 450, 15, False),
    ("motilium", "Motilium 10mg Tablets", "Domperidone", 3, 160, 25, False),
    ("ors", "ORS Sachet", "Oral rehydration salts", 3, 25, 80, False),
    ("buscopan", "Buscopan 10mg Tablets", "Hyoscine butylbromide", 3, 140, 25, False),
    ("zyrtec", "Zyrtec 10mg Tablets", "Cetirizine", 4, 110, 40, False),
    ("avil", "Avil 25mg Tablets", "Pheniramine", 4, 40, 30, False),
    ("claritin", "Claritin 10mg Tablets", "Loratadine", 4, 150, 25, False),
    ("telfast", "Telfast 120mg Tablets", "Fexofenadine", 4, 380, 20, False),
    ("benylin", "Benylin Cough Syrup 100ml", "Dextromethorphan", 5, 320, 20, False),
    ("arinac", "Arinac Forte Tablets", "Ibuprofen + Pseudoephedrine", 5, 85, 40, False),
    ("actifed", "Actifed Syrup 90ml", "Triprolidine + Pseudoephedrine", 5, 290, 20, False),
    ("ventolin", "Ventolin Inhaler 100mcg", "Salbutamol", 5, 550, 30, True),
    ("surbex", "Surbex Z Tablets", "Multivitamin + Zinc", 6, 380, 30, False),
    ("calcium", "Calcium + Vitamin D3 Tablets", "Calcium carbonate + Cholecalciferol", 6, 650, 20, False),
    ("vitc", "Vitamin C 500mg Tablets", "Ascorbic acid", 6, 150, 40, False),
    ("neurobion", "Neurobion Tablets", "Vitamin B1 + B6 + B12", 6, 290, 25, False),
    ("glucophage", "Glucophage 500mg Tablets", "Metformin", 7, 120, 40, True),
    ("diamicron", "Diamicron MR 60mg", "Gliclazide", 7, 470, 40, True),
    ("strips", "Glucometer Test Strips (50)", "Blood-glucose test strips", 7, 1650, 15, False),
    ("norvasc", "Norvasc 5mg Tablets", "Amlodipine", 8, 380, 40, True),
    ("concor", "Concor 5mg Tablets", "Bisoprolol", 8, 410, 25, True),
    ("lipiget", "Lipiget 20mg Tablets", "Atorvastatin", 8, 330, 25, True),
    ("betnovate", "Betnovate-N Cream 15g", "Betamethasone + Neomycin", 9, 190, 20, True),
    ("canesten", "Canesten Cream 20g", "Clotrimazole", 9, 360, 20, False),
    ("dettol", "Dettol Antiseptic 250ml", "Chloroxylenol", 10, 330, 25, False),
    ("bandaid", "Band-Aid Strips (20)", "Adhesive dressing", 10, 95, 25, False),
    ("thermo", "Digital Thermometer", "Clinical thermometer", 10, 450, 10, False),
]
KEY2ID = {p[0]: i + 1 for i, p in enumerate(PRODUCTS)}
PINFO = {p[0]: dict(id=i + 1, name=p[1], price=p[4], reorder=p[5], rx=p[6]) for i, p in enumerate(PRODUCTS)}

SUPPLIERS = [
    ("Capital Medico Distributors", "051-2271101", "Plot 14, Blue Area, Islamabad"),
    ("Rawal Pharma Traders", "051-5566202", "Raja Bazaar, Rawalpindi"),
    ("Margalla Healthcare Supplies", "051-2822303", "Street 6, I-9 Industrial Area, Islamabad"),
    ("Potohar Medical Agencies", "051-5120404", "Committee Chowk, Satellite Town, Rawalpindi"),
    ("Islamabad Drug House", "051-2650505", "Shop 3, G-8 Markaz, Islamabad"),
    ("Faisal Medico Corporation", "051-4430606", "Murree Road, Rawalpindi"),
    ("Karakoram Pharma Distribution", "051-2290707", "F-10 Markaz, Islamabad"),
    ("Indus Healthcare Traders", "051-5530808", "Saddar, Rawalpindi"),
    ("Blue Line Pharma Wholesale", "051-2341909", "Sector I-10/3, Islamabad"),
    ("City Care Medical Supplies", "051-4443010", "Adamjee Road, Rawalpindi"),
    ("Pioneer Medico Agencies", "051-2873111", "Sector G-11, Islamabad"),
    ("Green Valley Drug Distributors", "051-5584212", "Chaklala Scheme III, Rawalpindi"),
]

# id, name, role, phone, hire date            (pharmacist: licence, cashier: shift/counter)
EMPLOYEES = [
    (1, "Tariq Mehmood", "Manager", "0300-1234501", "2018-03-12"),
    (2, "Ayesha Siddiqui", "Pharmacist", "0301-2345602", "2019-07-01"),
    (3, "Usman Ghani", "Pharmacist", "0312-3456703", "2020-01-15"),
    (4, "Sana Rehman", "Pharmacist", "0321-4567804", "2022-05-20"),
    (5, "Bilal Ahmed", "Pharmacist", "0333-5678905", "2024-02-10"),
    (6, "Hina Farooq", "Cashier", "0345-6789006", "2021-09-01"),
    (7, "Kamran Ali", "Cashier", "0302-7890107", "2022-11-14"),
    (8, "Rabia Khan", "Cashier", "0315-8901208", "2023-04-03"),
    (9, "Zeeshan Malik", "Cashier", "0322-9012309", "2025-01-06"),
    (10, "Naveed Akhtar", "Inventory Clerk", "0334-0123410", "2019-10-21"),
    (11, "Farah Naz", "Inventory Clerk", "0346-1234511", "2023-08-07"),
    (12, "Imran Shah", "Inventory Clerk", "0303-2345612", "2025-06-16"),
]
PHARMACISTS = {2: ("PC-ISB-0412", "Pharm-D"), 3: ("PC-ISB-0587", "Pharm-D"),
               4: ("PC-RWP-0733", "Pharm-D"), 5: ("PC-ISB-0921", "B.Pharm")}
CASHIERS = {6: ("Morning", 1), 7: ("Evening", 2), 8: ("Evening", 3), 9: ("Night", 4)}
SELLERS = [2, 3, 4, 5, 6, 7, 8, 9]
SELLER_W = [3, 2, 2, 1, 3, 3, 2, 1]
INACTIVE_AT_END = [9]               # Zeeshan left the pharmacy in November

FIRST = ["Ali", "Ahmed", "Hamza", "Fahad", "Saad", "Omar", "Danish", "Haris", "Junaid", "Adeel",
         "Fatima", "Zainab", "Maryam", "Noor", "Hira", "Sidra", "Amna", "Iqra", "Mehwish", "Laiba",
         "Talha", "Shahzaib", "Waqas", "Asad", "Rizwan", "Nadia", "Sadia", "Rukhsana", "Bushra", "Kiran"]
LAST = ["Khan", "Malik", "Butt", "Chaudhry", "Raza", "Qureshi", "Abbasi", "Mirza", "Siddiqui", "Hashmi",
        "Javed", "Aslam", "Hussain", "Rana", "Sheikh"]

POPULAR = {"panadol": 6, "brufen": 4, "zyrtec": 4, "risek": 4, "surbex": 4, "ors": 5, "dettol": 4,
           "vitc": 4, "augmentin": 4, "ponstan": 3, "arinac": 3, "calpol": 3, "bandaid": 3, "thermo": 2}
SCARCE = {"augmentin": 26, "nexum": 24, "ventolin": 22, "diamicron": 25, "norvasc": 28, "benylin": 30}
SCARCE_REORDER = {"augmentin": 40, "nexum": 40, "ventolin": 30, "diamicron": 40, "norvasc": 40}

# ----------------------------------------------------------------------------
# Stocking plan
# ----------------------------------------------------------------------------
today = date(2026, 11, 18)
SHORT_EXPIRY = {                      # (a) already expired / (b) expiring within 30 days of 18 Nov 2026
    "benylin": date(2026, 11, 5), "canesten": date(2026, 10, 31),
    "motilium": date(2026, 12, 5), "avil": date(2026, 11, 30), "actifed": date(2026, 12, 14),
}


def month_end(y, m):
    nm = date(y + (m // 12), m % 12 + 1, 1)
    return nm - timedelta(days=1)


def random_expiry(after, lo=15, hi=30):
    months = random.randint(lo, hi)
    y = after.year + (after.month - 1 + months) // 12
    m = (after.month - 1 + months) % 12 + 1
    return month_end(y, m)


FIXED_EXPIRY = {"panadol": date(2028, 1, 31)}      # first Panadol batch expires before the restock batch
FIXED_QTY = {"panadol": 60}


def base_qty(key):
    if key in FIXED_QTY:
        return FIXED_QTY[key]
    if key in SCARCE:
        return SCARCE[key]
    if key in POPULAR:
        return random.randint(90, 160)
    return random.randint(45, 110)


# initial stocking: 40 products into 16 purchase orders (8 x 3 + 8 x 2)
order = list(PINFO.keys())
random.shuffle(order)
groups, i = [], 0
for n in [3] * 8 + [2] * 8:
    groups.append(order[i:i + n]); i += n
init_dates = [date(2026, 8, 3) + timedelta(days=k) for k in
              [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 9, 10, 11]]

events = []        # (datetime, rank, kind, payload)   rank: PO first, then sales on the same day
po_rows, batch_rows = [], []
batches = {}       # batch_id -> dict  (simulation state)
batch_seq = {}


def new_batch(po_id, key, qty, expiry, cost_factor, odate):
    bid = len(batches) + 1
    n = batch_seq.get(key, 0) + 1
    batch_seq[key] = n
    p = PINFO[key]
    cost = round(p["price"] * random.uniform(*cost_factor), 2)
    no = f"{key[:3].upper()}-{odate:%y%m}-{n:02d}"
    batches[bid] = dict(id=bid, key=key, po=po_id, no=no, recv=qty, qty=qty, exp=expiry, cost=cost)
    return bid


po_id = 0
for g, d in zip(groups, init_dates):
    po_id += 1
    sup = random.randint(1, len(SUPPLIERS))
    lines = []
    for key in g:
        exp = SHORT_EXPIRY.get(key) or FIXED_EXPIRY.get(key) or random_expiry(d)
        lines.append(new_batch(po_id, key, base_qty(key), exp, (0.68, 0.82), d))
    events.append((datetime.combine(d, datetime.min.time()).replace(hour=8), 0, "po",
                   dict(id=po_id, sup=sup, date=d, status="Received", batches=lines)))

# restock deliveries (each is one purchase order)
RESTOCKS = [
    (date(2026, 9, 2), [("panadol", 140), ("ors", 120)]),
    (date(2026, 9, 16), [("zyrtec", 80), ("brufen", 90)]),
    (date(2026, 9, 30), [("surbex", 70), ("vitc", 90)]),
    (date(2026, 10, 7), [("risek", 90)]),
    (date(2026, 10, 14), [("dettol", 60)]),
    (date(2026, 10, 28), [("glucophage", 70)]),
    (date(2026, 11, 3), [("canesten", 40), ("ponstan", 60)]),
    (date(2026, 11, 10), [("calpol", 50)]),
]
for d, items in RESTOCKS:
    po_id += 1
    sup = random.randint(1, len(SUPPLIERS))
    lines = [new_batch(po_id, key, q, random_expiry(d, 20, 30), (0.70, 0.84), d) for key, q in items]
    events.append((datetime.combine(d, datetime.min.time()).replace(hour=8), 0, "po",
                   dict(id=po_id, sup=sup, date=d, status="Received", batches=lines)))

# open / cancelled orders (no stock arrived yet)
for d, st in [(date(2026, 9, 22), "Cancelled"), (date(2026, 10, 19), "Cancelled"), (date(2026, 11, 5), "Cancelled"),
              (date(2026, 11, 12), "Pending"), (date(2026, 11, 14), "Pending"), (date(2026, 11, 16), "Pending")]:
    po_id += 1
    events.append((datetime.combine(d, datetime.min.time()).replace(hour=8), 0, "po",
                   dict(id=po_id, sup=random.randint(1, len(SUPPLIERS)), date=d, status=st, batches=[])))

# ----------------------------------------------------------------------------
# Customers
# ----------------------------------------------------------------------------
CUSTOMERS = [(1, "Walk-in Customer", None, date(2025, 1, 1))]
used_names, used_phones = set(), set()
while len(CUSTOMERS) < 40:
    nm = f"{random.choice(FIRST)} {random.choice(LAST)}"
    ph = f"03{random.randint(0, 4)}{random.randint(0, 9)}-{random.randint(1000000, 9999999)}"
    if nm in used_names or ph in used_phones:
        continue
    used_names.add(nm); used_phones.add(ph)
    reg = date(2025, 1, 1) + timedelta(days=random.randint(0, 570))
    CUSTOMERS.append((len(CUSTOMERS) + 1, nm, ph, reg))
BUYERS = list(range(1, 31))                      # customers 31-40 never buy (for the LEFT JOIN query)
BUYER_W = [6] + [random.choice([1, 1, 2, 3, 5]) for _ in range(29)]
BUYER_W[6] = 9; BUYER_W[13] = 8; BUYER_W[21] = 7  # a few big spenders

# ----------------------------------------------------------------------------
# Sales  (simulated against the stock state so that every sale is feasible)
# ----------------------------------------------------------------------------
PAY = ["Cash", "Card", "Mobile Wallet"]
PAY_W = [5, 3, 2]
QTY = {"ors": [2, 4, 6, 10], "panadol": [2, 3, 5, 10], "disprin": [2, 3, 5], "bandaid": [1, 1, 2],
       "thermo": [1], "strips": [1], "dettol": [1, 1, 2], "gaviscon": [1], "ventolin": [1],
       "betnovate": [1], "canesten": [1], "telfast": [1], "calcium": [1]}
QTY_DEFAULT = [1, 1, 2, 2, 3, 4]


def eligible(key, when):
    d = when.date()
    return sorted([b for b in batches.values() if b["key"] == key and b["qty"] > 0 and b["exp"] >= d
                   and any(e[3]["id"] == b["po"] and e[0] <= when for e in events if e[2] == "po")],
                  key=lambda b: (b["exp"], b["id"]))


def available(key, when):
    return sum(b["qty"] for b in eligible(key, when))


def take(key, qty, when):
    left, alloc = qty, []
    for b in eligible(key, when):
        t = min(left, b["qty"]); b["qty"] -= t; left -= t
        alloc.append((b["id"], t))
        if left == 0:
            break
    return alloc


def rand_time(d):
    return datetime.combine(d, datetime.min.time()) + timedelta(hours=random.randint(9, 21),
                                                                minutes=random.randint(0, 59),
                                                                seconds=random.randint(0, 59))


sale_specs = []          # (datetime, customer, employee, pay, [(key, qty) ...])
days = [date(2026, 8, 7) + timedelta(days=k) for k in range(0, 103)]
wkeys = list(PINFO.keys())
wts = [POPULAR.get(k, 1) + (2 if k in SCARCE else 0) for k in wkeys]
pending_sales = sorted(rand_time(random.choice(days)) for _ in range(300))

# forced scenarios ---------------------------------------------------------------
forced = [
    # relational-division demo: customers 5 and 9 bought EVERY First-Aid product
    (datetime(2026, 9, 12, 11, 20), 5, 6, "Cash", [("dettol", 1), ("bandaid", 2)]),
    (datetime(2026, 10, 3, 17, 5), 5, 7, "Card", [("thermo", 1)]),
    (datetime(2026, 9, 25, 13, 40), 9, 3, "Cash", [("dettol", 1), ("bandaid", 1), ("thermo", 1)]),
    # short-dated stock sold before it expired
    (datetime(2026, 10, 14, 10, 15), 7, 2, "Cash", [("benylin", 3), ("canesten", 2)]),
    (datetime(2026, 10, 22, 19, 30), 12, 8, "Mobile Wallet", [("benylin", 2), ("motilium", 3)]),
    (datetime(2026, 10, 9, 12, 10), 2, 4, "Card", [("avil", 3), ("actifed", 2)]),
]

# every other sale is random ---------------------------------------------------------
chosen = sorted(random.sample(pending_sales, 49))      # spread over the whole Aug-Nov period

specs = []
for f in forced:
    specs.append(f)
for when in chosen:
    cust = random.choices(BUYERS, BUYER_W)[0]
    emp = random.choices(SELLERS, SELLER_W)[0]
    pay = random.choices(PAY, PAY_W)[0]
    nlines = random.choices([1, 2, 3, 4, 5], [20, 30, 25, 15, 10])[0]
    lines, seen = [], set()
    while len(lines) < nlines:
        k = random.choices(wkeys, wts)[0]
        if k in seen:
            continue
        seen.add(k)
        lines.append((k, random.choice(QTY.get(k, QTY_DEFAULT))))
    specs.append((when, cust, emp, pay, lines))

# one bulk Panadol sale that must span two batches (FEFO demo) – added after simulation of the others
specs.sort(key=lambda s: s[0])
# insert PO events and sale events in one chronological list and simulate stock
timeline = [(e[0], 0, "po", e[3]) for e in events] + [(s[0], 1, "sale", s) for s in specs]
timeline.sort(key=lambda t: (t[0], t[1]))

# first pass: simulate to find out how much Panadol is left in the first batch on 25 Oct
# (so that the bulk sale really spans two batches)
import copy
snapshot = copy.deepcopy(batches)
bulk_when = datetime(2026, 10, 25, 15, 45)
pan_first_left = None
events_by_time = []
for when, rank, kind, payload in timeline:
    if kind == "sale" and when <= bulk_when:
        for key, q in payload[4]:
            qq = min(q, available(key, when))
            if qq > 0:
                take(key, qq, when)
for b in sorted([b for b in batches.values() if b["key"] == "panadol" and b["exp"] >= bulk_when.date()],
                key=lambda b: (b["exp"], b["id"])):
    if pan_first_left is None:
        pan_first_left = b["qty"]
batches.clear(); batches.update(snapshot)
bulk_qty = (pan_first_left or 0) + 7
specs.append((bulk_when, 14, 2, "Cash", [("panadol", bulk_qty), ("ors", 6)]))
specs.sort(key=lambda s: s[0])
timeline = [(e[0], 0, "po", e[3]) for e in events] + [(s[0], 1, "sale", s) for s in specs]
timeline.sort(key=lambda t: (t[0], t[1]))

# second pass: the real simulation
sales_out, sale_no = [], 0
final_events = []
for when, rank, kind, payload in timeline:
    if kind == "po":
        final_events.append(("po", payload))
        continue
    _, cust, emp, pay, lines = payload
    ok_lines = []
    for key, q in lines:
        q = min(q, available(key, when))
        if q > 0:
            take(key, q, when)
            ok_lines.append((key, q))
    if not ok_lines:
        continue
    sale_no += 1
    final_events.append(("sale", dict(id=sale_no, when=when, cust=cust, emp=emp, pay=pay, lines=ok_lines)))

# ----------------------------------------------------------------------------
# Writers
# ----------------------------------------------------------------------------

def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (date, datetime)):
        return "'" + str(v) + "'"
    return "'" + str(v).replace("'", "''") + "'"


def rows(table, cols, data):
    out = [f"INSERT INTO {table} ({', '.join(cols)}) VALUES"]
    out.append(",\n".join("    (" + ", ".join(q(x) for x in r) + ")" for r in data) + ";")
    return "\n".join(out)


def build(dialect):
    L = []
    hdr = f"""-- =====================================================================
--  Pharmacy Inventory & Sales Management System
--  File 3 of 6 : SAMPLE DATA ({'MySQL' if dialect == 'mysql' else 'PostgreSQL'})
--  Generated by tools/generate_data.py (fixed seed) - all names/numbers are fictional.
--  Sales are inserted through the real tables, so the TRIGGERS fill in
--  sale totals, stock reductions (FEFO), sale_allocations and PO totals.
-- =====================================================================
"""
    L.append(hdr)
    L.append("USE pharmacy_db;\n" if dialect == "mysql" else "\\connect pharmacy_db\n\\set ON_ERROR_STOP on\n")
    L.append("-- ---- reference data ----------------------------------------------------")
    L.append(rows("categories", ["category_id", "category_name", "description"],
                  [(i + 1, c[0], c[1]) for i, c in enumerate(CATEGORIES)]))
    L.append(rows("suppliers", ["supplier_id", "name", "phone", "address"],
                  [(i + 1,) + s for i, s in enumerate(SUPPLIERS)]))
    L.append(rows("products", ["product_id", "name", "generic_name", "category_id", "unit_price",
                               "reorder_level", "requires_prescription"],
                  [(i + 1, p[1], p[2], p[3], p[4],
                    SCARCE_REORDER.get(p[0], p[5]), p[6]) for i, p in enumerate(PRODUCTS)]))
    L.append(rows("customers", ["customer_id", "name", "phone", "registered_on"], CUSTOMERS))
    L.append(rows("employees", ["employee_id", "name", "role", "phone", "hire_date"], EMPLOYEES))
    L.append(rows("pharmacists", ["employee_id", "license_no", "qualification"],
                  [(k, v[0], v[1]) for k, v in PHARMACISTS.items()]))
    L.append(rows("cashiers", ["employee_id", "shift", "counter_no"],
                  [(k, v[0], v[1]) for k, v in CASHIERS.items()]))
    L.append("\n-- ---- purchases and sales in date order (triggers do the bookkeeping) ------")
    for kind, p in final_events:
        if kind == "po":
            L.append(f"\n-- Purchase order {p['id']} ({p['date']}, {p['status']})")
            L.append(rows("purchase_orders", ["po_id", "supplier_id", "order_date", "status"],
                          [(p["id"], p["sup"], p["date"], p["status"])]))
            if p["batches"]:
                data = []
                for bid in p["batches"]:
                    b = batches[bid]
                    data.append((b["id"], KEY2ID[b["key"]], b["po"], b["no"], b["recv"], b["recv"], b["exp"], b["cost"]))
                L.append(rows("stock_batches", ["batch_id", "product_id", "po_id", "batch_no", "received_qty",
                                                "quantity", "expiry_date", "cost_price"], data))
        else:
            L.append(f"\n-- Sale {p['id']}")
            L.append(rows("sales", ["sale_id", "customer_id", "employee_id", "sale_date", "payment_method"],
                          [(p["id"], p["cust"], p["emp"], p["when"], p["pay"])]))
            L.append(rows("sale_items", ["sale_id", "product_id", "quantity", "unit_price"],
                          [(p["id"], KEY2ID[k], qty, PINFO[k]["price"]) for k, qty in p["lines"]]))
    L.append("\n-- ---- a cashier left the pharmacy in November -----------------------------")
    L.append("UPDATE employees SET is_active = FALSE WHERE employee_id IN (%s);" % ", ".join(map(str, INACTIVE_AT_END)))
    if dialect == "postgres":
        L.append("\n-- ---- re-sync identity sequences after explicit-id inserts ------------------")
        for t, c in [("categories", "category_id"), ("suppliers", "supplier_id"), ("products", "product_id"),
                     ("purchase_orders", "po_id"), ("stock_batches", "batch_id"), ("customers", "customer_id"),
                     ("employees", "employee_id"), ("sales", "sale_id")]:
            L.append(f"SELECT setval(pg_get_serial_sequence('{t}', '{c}'), (SELECT MAX({c}) FROM {t}));")
        L.append("REFRESH MATERIALIZED VIEW mv_monthly_sales;")
    return "\n".join(L) + "\n"


(ROOT / "mysql" / "03_sample_data.sql").write_text(build("mysql"))
(ROOT / "postgres" / "pg_03_sample_data.sql").write_text(build("postgres"))
print("POs:", po_id, "| batches:", len(batches), "| sales:", sale_no,
      "| sale lines:", sum(len(p["lines"]) for k, p in final_events if k == "sale"),
      "| bulk panadol qty:", bulk_qty)
