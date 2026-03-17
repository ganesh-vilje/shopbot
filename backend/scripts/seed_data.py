"""
Seed the database with comprehensive dummy data.
Covers every field in Customer, Product, Order, OrderItem models.
Idempotent — safe to run multiple times.
"""
import sys, os, uuid, random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.core.security import hash_password


# ─────────────────────────────────────────────────────────────────────────────
#  STATIC DATA SETS
# ─────────────────────────────────────────────────────────────────────────────

CUSTOMERS_DATA = [
    # (full_name, email, phone, address, city, country)
    ("Alex Johnson",   "alex@example.com",   "+1-212-555-0101", "12 Broadway Ave, Apt 4B",    "New York",      "US"),
    ("Sarah Williams", "sarah@example.com",  "+1-310-555-0192", "88 Sunset Blvd, Suite 3",    "Los Angeles",   "US"),
    ("Mike Brown",     "mike@example.com",   "+1-312-555-0143", "200 Michigan Ave",            "Chicago",       "US"),
    ("Emily Davis",    "emily@example.com",  "+1-713-555-0167", "55 River Oaks Dr",            "Houston",       "US"),
    ("James Wilson",   "james@example.com",  "+44-20-5550-0188","14 Baker Street, Flat 2",     "London",        "GB"),
    ("Priya Sharma",   "priya@example.com",  "+1-415-555-0121", "9 Market Street, Unit 7",    "San Francisco", "US"),
    ("Carlos Mendez",  "carlos@example.com", "+1-305-555-0134", "301 Brickell Key Dr",         "Miami",         "US"),
    ("Yuki Tanaka",    "yuki@example.com",   "+1-206-555-0155", "720 Pike Street, Apt 11",    "Seattle",       "US"),
]

# (name, category, brand, price, discount_pct, stock_qty, rating, review_count, sku, status)
PRODUCTS_DATA = [
    # ── Electronics ───────────────────────────────────────────────────────────
    ("Apple iPhone 15 Pro",             "electronics", "Apple",       1199.99,  0,  85, 4.8, 3241, "SKU-APL-001", "available"),
    ("Samsung Galaxy S24 Ultra",        "electronics", "Samsung",     1099.99,  5,  62, 4.7, 2876, "SKU-SAM-001", "available"),
    ("Sony WH-1000XM5 Headphones",      "electronics", "Sony",         349.99, 10, 142, 4.9, 5832, "SKU-SNY-001", "available"),
    ("iPad Pro 12.9-inch M2",           "electronics", "Apple",       1099.99,  0,  58, 4.8, 2134, "SKU-APL-003", "available"),
    ("Bose QuietComfort 45",            "electronics", "Bose",         279.99, 15,  93, 4.7, 3210, "SKU-BSE-001", "available"),
    ("LG OLED 55-inch TV",              "electronics", "LG",          1299.99, 12,  18, 4.8,  765, "SKU-LG-001",  "available"),
    ("Google Pixel 8 Pro",              "electronics", "Google",       999.99,  8,  44, 4.6, 1876, "SKU-GOG-001", "available"),
    ("Apple AirPods Pro 2nd Gen",       "electronics", "Apple",        249.99,  0, 210, 4.8, 8765, "SKU-APL-004", "available"),
    ("Samsung Galaxy Watch 6",          "electronics", "Samsung",      299.99, 10,  67, 4.5, 2341, "SKU-SAM-002", "available"),
    ("Sony Bravia XR 65-inch 4K TV",    "electronics", "Sony",        1799.99,  0,   9, 4.7,  432, "SKU-SNY-003", "available"),
    # ── Laptops ───────────────────────────────────────────────────────────────
    ("Apple MacBook Pro 14-inch M3",    "laptops",     "Apple",       1999.99,  0,  34, 4.9, 1423, "SKU-APL-002", "available"),
    ("Dell XPS 15 Laptop",              "laptops",     "Dell",        1599.99,  8,  27, 4.6,  987, "SKU-DEL-001", "available"),
    ("Microsoft Surface Pro 9",         "laptops",     "Microsoft",   1299.99,  5,  39, 4.5, 1102, "SKU-MSF-001", "available"),
    ("Lenovo ThinkPad X1 Carbon",       "laptops",     "Lenovo",      1449.99, 10,  21, 4.7,  876, "SKU-LEN-001", "available"),
    ("ASUS ROG Zephyrus G14",           "laptops",     "ASUS",        1349.99,  0,  16, 4.6,  654, "SKU-ASS-001", "available"),
    # ── Gaming ────────────────────────────────────────────────────────────────
    ("Sony PlayStation 5",              "gaming",      "Sony",         499.99,  0,  23, 4.9, 8765, "SKU-SNY-002", "available"),
    ("Nintendo Switch OLED",            "gaming",      "Nintendo",     349.99,  0,  47, 4.7, 6543, "SKU-NIN-001", "available"),
    ("Xbox Series X",                   "gaming",      "Microsoft",    499.99,  0,  31, 4.8, 5432, "SKU-MSF-002", "available"),
    ("Razer DeathAdder V3 Mouse",       "gaming",      "Razer",         79.99,  0, 189, 4.6, 3210, "SKU-RZR-001", "available"),
    ("SteelSeries Arctis Nova Pro",     "gaming",      "SteelSeries",  249.99,  5,  74, 4.7, 1987, "SKU-STL-001", "available"),
    # ── Shoes ─────────────────────────────────────────────────────────────────
    ("Nike Air Max 270",                "shoes",       "Nike",         150.00, 20, 234, 4.5, 4521, "SKU-NKE-001", "available"),
    ("Adidas Ultraboost 22",            "shoes",       "Adidas",       180.00, 10, 178, 4.6, 3876, "SKU-ADI-001", "available"),
    ("New Balance 990v5",               "shoes",       "New Balance",  184.99,  0,  92, 4.7, 2654, "SKU-NB-001",  "available"),
    ("Converse Chuck Taylor All Star",  "shoes",       "Converse",      65.00,  0, 412, 4.4, 9876, "SKU-CNV-001", "available"),
    ("Vans Old Skool",                  "shoes",       "Vans",          70.00,  0, 356, 4.5, 8321, "SKU-VNS-001", "available"),
    # ── Clothing ──────────────────────────────────────────────────────────────
    ("Levi's 501 Original Jeans",       "clothing",    "Levi's",        79.99,  0, 312, 4.4, 7865, "SKU-LVS-001", "available"),
    ("The North Face Puffer Jacket",    "clothing",    "The North Face",229.99, 25,  67, 4.7, 2341, "SKU-TNF-001", "available"),
    ("Patagonia Nano Puff Jacket",      "clothing",    "Patagonia",    219.99,  0,  43, 4.8, 1876, "SKU-PTG-001", "available"),
    ("Champion Reverse Weave Hoodie",   "clothing",    "Champion",      65.00, 15, 287, 4.3, 5432, "SKU-CHP-001", "available"),
    ("Uniqlo Ultra Light Down Jacket",  "clothing",    "Uniqlo",        79.99,  0, 198, 4.5, 4321, "SKU-UNQ-001", "available"),
    # ── Accessories ───────────────────────────────────────────────────────────
    ("Ray-Ban Wayfarer Sunglasses",     "accessories", "Ray-Ban",      154.00,  0, 189, 4.6, 5432, "SKU-RBN-001", "available"),
    ("Apple Watch Series 9",            "accessories", "Apple",        399.99,  0, 134, 4.8, 6543, "SKU-APL-005", "available"),
    ("Fossil Gen 6 Smartwatch",         "accessories", "Fossil",       179.99, 20,  56, 4.3, 2109, "SKU-FSL-001", "available"),
    ("Herschel Supply Backpack",        "accessories", "Herschel",      74.99,  0, 267, 4.5, 4321, "SKU-HSC-001", "available"),
    ("Tumi Alpha 3 Briefcase",          "accessories", "Tumi",         695.00,  0,  22, 4.8,  765, "SKU-TMI-001", "available"),
    # ── Home ──────────────────────────────────────────────────────────────────
    ("Dyson V15 Detect Vacuum",         "home",        "Dyson",        749.99,  0,  45, 4.8, 4321, "SKU-DYS-001", "available"),
    ("iRobot Roomba j7+",               "home",        "iRobot",       599.99, 10,  38, 4.6, 2134, "SKU-IRB-001", "available"),
    ("Philips Hue Starter Kit",         "smart home",  "Philips",      199.99,  8,  98, 4.5, 3210, "SKU-PHL-001", "available"),
    # ── Kitchen ───────────────────────────────────────────────────────────────
    ("Instant Pot Duo 7-in-1",          "kitchen",     "Instant Pot",   99.99,  5, 287, 4.7,12456, "SKU-INP-001", "available"),
    ("Nespresso Vertuo Coffee Machine", "kitchen",     "Nespresso",    199.99, 10, 134, 4.6, 8765, "SKU-NSP-001", "available"),
    ("KitchenAid Stand Mixer",          "kitchen",     "KitchenAid",   449.99,  0,  56, 4.9, 5678, "SKU-KAD-001", "available"),
    ("Vitamix 5200 Blender",            "kitchen",     "Vitamix",      449.95,  0,  33, 4.8, 3456, "SKU-VTX-001", "available"),
    ("Cuisinart Air Fryer Toaster",     "kitchen",     "Cuisinart",    149.99, 12,  87, 4.5, 6789, "SKU-CSN-001", "available"),
    # ── Fitness ───────────────────────────────────────────────────────────────
    ("Peloton Bike+",                   "fitness",     "Peloton",     2495.00,  0,  12, 4.5, 1234, "SKU-PEL-001", "available"),
    ("Garmin Forerunner 255",           "fitness",     "Garmin",       349.99,  5,  78, 4.7, 2876, "SKU-GMN-001", "available"),
    ("Manduka PRO Yoga Mat",            "fitness",     "Manduka",       88.00,  0, 456, 4.8, 9876, "SKU-MNK-001", "available"),
    ("Hydro Flask 32oz Water Bottle",   "fitness",     "Hydro Flask",   49.99,  0, 567, 4.8,15432, "SKU-HDF-001", "available"),
    ("Bowflex SelectTech 552 Dumbbells","fitness",     "Bowflex",      399.00,  0,  29, 4.7, 3210, "SKU-BWF-001", "available"),
    ("Theragun Pro Massage Gun",        "fitness",     "Therabody",    499.00,  8,  54, 4.6, 2345, "SKU-TRG-001", "available"),
    # ── Out of stock ──────────────────────────────────────────────────────────
    ("Resistance Band Set",             "fitness",     "TheraBand",     29.99,  0,   0, 4.3, 6543, "SKU-TBD-001", "out_of_stock"),
    ("GoPro Hero 12 Black",             "electronics", "GoPro",        399.99,  0,   0, 4.7, 4321, "SKU-GPR-001", "out_of_stock"),
    # ── Discontinued ──────────────────────────────────────────────────────────
    ("Sony WF-1000XM4 Earbuds",         "electronics", "Sony",         199.99, 30,   0, 4.6, 7654, "SKU-SNY-004", "discontinued"),
]

PAYMENT_METHODS  = ["card", "paypal", "wallet", "apple_pay", "google_pay"]
TRACKING_PREFIXES = ["TRK", "UPS", "FDX", "DHL"]


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def make_tracking() -> str:
    return f"{random.choice(TRACKING_PREFIXES)}{random.randint(1000000, 9999999)}"

def make_order_number(n: int) -> str:
    return f"ORD-{2025000 + n:07d}"

def line_total(qty: int, unit: float, disc: float) -> float:
    return round(qty * unit * (1 - disc / 100), 2)


# ─────────────────────────────────────────────────────────────────────────────
#  SEED
# ─────────────────────────────────────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            print("Already seeded — skipping. Delete products rows to re-seed.")
            return

        print("Seeding database...\n")

        # ══ 1. PRODUCTS ═══════════════════════════════════════════════════════
        products: list[Product] = []
        for (name, cat, brand, price, disc, stock, rating, reviews, sku, status) in PRODUCTS_DATA:
            p = Product(
                id           = str(uuid.uuid4()),
                sku          = sku,
                name         = name,
                description  = (f"Premium {name} — highly rated in {cat}. "
                                f"Trusted by {reviews:,} customers. "
                                f"Rated {rating}/5 stars."),
                category     = cat,
                brand        = brand,
                price        = price,
                discount_pct = disc,
                stock_qty    = stock,
                rating       = rating,
                review_count = reviews,
                is_active    = (status != "discontinued"),
                status       = status,
                image_url    = f"https://picsum.photos/seed/{sku}/400/400",
            )
            db.add(p)
            products.append(p)

        db.flush()

        available_products = [p for p in products if p.status == "available"]

        # ══ 2. CUSTOMERS ══════════════════════════════════════════════════════
        demo_pwd  = hash_password("Demo@12345")
        customers: list[Customer] = []

        for (full_name, email, phone, address, city, country) in CUSTOMERS_DATA:
            c = Customer(
                id             = str(uuid.uuid4()),
                full_name      = full_name,
                email          = email,
                phone          = phone,
                address        = address,
                city           = city,
                country        = country,
                is_verified    = True,
                hashed_password= demo_pwd,
                oauth_provider = None,
                oauth_id       = None,
            )
            db.add(c)
            customers.append(c)

        db.flush()

        # ══ 3. ORDERS + ORDER ITEMS ═══════════════════════════════════════════
        all_statuses      = list(OrderStatus)
        order_counter     = 1
        total_items       = 0

        for customer in customers:
            for _ in range(random.randint(3, 7)):

                # Pick products for this order
                selected = random.sample(available_products, random.randint(1, 4))

                subtotal   = 0.0
                line_items = []
                for prod in selected:
                    qty  = random.randint(1, 3)
                    unit = float(prod.price)
                    disc = float(prod.discount_pct)
                    lt   = line_total(qty, unit, disc)
                    subtotal += lt
                    line_items.append((prod, qty, unit, disc, lt))

                subtotal      = round(subtotal, 2)
                coupon_pct    = random.choice([0, 0, 0, 0.05, 0.10])
                discount_amt  = round(subtotal * coupon_pct, 2)
                tax_amt       = round((subtotal - discount_amt) * 0.08, 2)
                total_amt     = round(subtotal - discount_amt + tax_amt, 2)

                days_ago      = random.randint(1, 365)
                created       = datetime.now(timezone.utc) - timedelta(days=days_ago)
                status        = random.choice(all_statuses)

                shipped_at    = None
                delivered_at  = None
                tracking      = None

                if status in (OrderStatus.shipped, OrderStatus.delivered):
                    shipped_at = created + timedelta(days=random.randint(1, 3))
                    tracking   = make_tracking()
                if status == OrderStatus.delivered:
                    delivered_at = shipped_at + timedelta(days=random.randint(2, 7))

                order = Order(
                    id               = str(uuid.uuid4()),
                    customer_id      = customer.id,
                    order_number     = make_order_number(order_counter),
                    status           = status,
                    subtotal         = subtotal,
                    discount_amount  = discount_amt,
                    tax_amount       = tax_amt,
                    total_amount     = total_amt,
                    payment_method   = random.choice(PAYMENT_METHODS),
                    shipping_address = f"{customer.address}, {customer.city}, {customer.country}",
                    tracking_number  = tracking,
                    shipped_at       = shipped_at,
                    delivered_at     = delivered_at,
                    created_at       = created,
                )
                db.add(order)
                db.flush()

                for (prod, qty, unit, disc, lt) in line_items:
                    db.add(OrderItem(
                        id           = str(uuid.uuid4()),
                        order_id     = order.id,
                        product_id   = prod.id,
                        quantity     = qty,
                        unit_price   = unit,
                        discount_pct = disc,
                        line_total   = lt,
                    ))
                    total_items += 1

                order_counter += 1

        db.commit()

        # ── Print summary ──────────────────────────────────────────────────────
        avail_count = sum(1 for p in products if p.status == "available")
        oos_count   = sum(1 for p in products if p.status == "out_of_stock")
        disc_count  = sum(1 for p in products if p.status == "discontinued")

        print("=" * 56)
        print("  DATABASE SEEDED SUCCESSFULLY")
        print("=" * 56)
        print(f"  Products      : {len(products)}")
        print(f"    available   : {avail_count}")
        print(f"    out_of_stock: {oos_count}")
        print(f"    discontinued: {disc_count}")
        print(f"  Customers     : {len(customers)}")
        print(f"  Orders        : {order_counter - 1}")
        print(f"  Order items   : {total_items}")
        print("=" * 56)
        print("\n  Demo login credentials (password: Demo@12345)\n")
        for (name, email, *_) in CUSTOMERS_DATA:
            print(f"  {name:<22} {email}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\nERROR during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()