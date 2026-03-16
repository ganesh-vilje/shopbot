"""Seed the database with realistic e-commerce data. Idempotent."""
import sys, os, uuid, random
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.core.security import hash_password

def seed():
    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            print("Already seeded — skipping."); return

        products_data = [
            ("Apple iPhone 15 Pro","electronics","Apple",1199.99,0,85,4.8,3241,"SKU-APL-001"),
            ("Samsung Galaxy S24 Ultra","electronics","Samsung",1099.99,5,62,4.7,2876,"SKU-SAM-001"),
            ("Sony WH-1000XM5 Headphones","electronics","Sony",349.99,10,142,4.9,5832,"SKU-SNY-001"),
            ("Apple MacBook Pro 14-inch M3","laptops","Apple",1999.99,0,34,4.9,1423,"SKU-APL-002"),
            ("Dell XPS 15 Laptop","laptops","Dell",1599.99,8,27,4.6,987,"SKU-DEL-001"),
            ("iPad Pro 12.9-inch","electronics","Apple",1099.99,0,58,4.8,2134,"SKU-APL-003"),
            ("Sony PlayStation 5","gaming","Sony",499.99,0,23,4.9,8765,"SKU-SNY-002"),
            ("Nintendo Switch OLED","gaming","Nintendo",349.99,0,47,4.7,6543,"SKU-NIN-001"),
            ("Bose QuietComfort 45","electronics","Bose",279.99,15,93,4.7,3210,"SKU-BSE-001"),
            ("LG OLED 55-inch TV","electronics","LG",1299.99,12,18,4.8,765,"SKU-LG-001"),
            ("Nike Air Max 270","shoes","Nike",150.00,20,234,4.5,4521,"SKU-NKE-001"),
            ("Adidas Ultraboost 22","shoes","Adidas",180.00,10,178,4.6,3876,"SKU-ADI-001"),
            ("Levi's 501 Original Jeans","clothing","Levi's",79.99,0,312,4.4,7865,"SKU-LVS-001"),
            ("The North Face Puffer Jacket","clothing","The North Face",229.99,25,67,4.7,2341,"SKU-TNF-001"),
            ("Ray-Ban Wayfarer Sunglasses","accessories","Ray-Ban",154.00,0,189,4.6,5432,"SKU-RBN-001"),
            ("Dyson V15 Vacuum","home","Dyson",749.99,0,45,4.8,4321,"SKU-DYS-001"),
            ("Instant Pot Duo 7-in-1","kitchen","Instant Pot",99.99,5,287,4.7,12456,"SKU-INP-001"),
            ("Nespresso Vertuo Coffee Machine","kitchen","Nespresso",199.99,10,134,4.6,8765,"SKU-NSP-001"),
            ("KitchenAid Stand Mixer","kitchen","KitchenAid",449.99,0,56,4.9,5678,"SKU-KAD-001"),
            ("Philips Hue Starter Kit","smart home","Philips",199.99,8,98,4.5,3210,"SKU-PHL-001"),
            ("Peloton Bike+","fitness","Peloton",2495.00,0,12,4.5,1234,"SKU-PEL-001"),
            ("Garmin Forerunner 255","fitness","Garmin",349.99,5,78,4.7,2876,"SKU-GMN-001"),
            ("Yoga Mat Premium","fitness","Manduka",88.00,0,456,4.8,9876,"SKU-MNK-001"),
            ("Resistance Band Set","fitness","TheraBand",29.99,0,0,4.3,6543,"SKU-TBD-001"),
            ("Hydro Flask 32oz","fitness","Hydro Flask",49.99,0,567,4.8,15432,"SKU-HDF-001"),
        ]
        products = []
        for (name,cat,brand,price,disc,stock,rating,reviews,sku) in products_data:
            p = Product(id=str(uuid.uuid4()),sku=sku,name=name,category=cat,brand=brand,
                        price=price,discount_pct=disc,stock_qty=stock,rating=rating,
                        review_count=reviews,is_active=True,
                        description=f"Premium {name} — top rated in {cat}.",
                        image_url=f"https://picsum.photos/seed/{sku}/400/400")
            db.add(p); products.append(p)
        db.flush()

        customers_data = [
            ("Alex Johnson","alex@example.com","New York","US"),
            ("Sarah Williams","sarah@example.com","Los Angeles","US"),
            ("Mike Brown","mike@example.com","Chicago","US"),
            ("Emily Davis","emily@example.com","Houston","US"),
            ("James Wilson","james@example.com","London","GB"),
        ]
        demo_pwd = hash_password("Demo@12345")
        customers = []
        for (name,email,city,country) in customers_data:
            c = Customer(id=str(uuid.uuid4()),full_name=name,email=email,city=city,
                         country=country,loyalty_points=random.randint(100,2500),
                         is_verified=True,hashed_password=demo_pwd)
            db.add(c); customers.append(c)
        db.flush()

        statuses = list(OrderStatus)
        order_counter = 1
        for customer in customers:
            for _ in range(random.randint(2,5)):
                selected = random.sample(products, random.randint(1,4))
                subtotal = 0.0; items = []
                for prod in selected:
                    qty = random.randint(1,3)
                    disc = float(prod.discount_pct); unit = float(prod.price)
                    line = round(qty*unit*(1-disc/100),2); subtotal += line
                    items.append((prod,qty,unit,disc,line))
                tax = round(subtotal*0.08,2)
                discount = round(subtotal*random.choice([0,0,0.05,0.10]),2)
                total = round(subtotal-discount+tax,2)
                days_ago = random.randint(1,180)
                created = datetime.now(timezone.utc)-timedelta(days=days_ago)
                status = random.choice(statuses)
                order = Order(id=str(uuid.uuid4()),customer_id=customer.id,
                    order_number=f"ORD-{2025000+order_counter:07d}",
                    status=status,subtotal=subtotal,discount_amount=discount,
                    tax_amount=tax,total_amount=total,
                    payment_method=random.choice(["card","paypal","wallet"]),
                    shipping_address=f"{random.randint(1,999)} Main St, {customer.city}",
                    tracking_number=f"TRK{random.randint(100000,999999)}" if status in [OrderStatus.shipped,OrderStatus.delivered] else None,
                    shipped_at=created+timedelta(days=2) if status in [OrderStatus.shipped,OrderStatus.delivered] else None,
                    delivered_at=created+timedelta(days=6) if status==OrderStatus.delivered else None,
                    created_at=created)
                db.add(order); db.flush()
                for (prod,qty,unit,disc,line) in items:
                    db.add(OrderItem(id=str(uuid.uuid4()),order_id=order.id,
                        product_id=prod.id,quantity=qty,unit_price=unit,
                        discount_pct=disc,line_total=line))
                order_counter += 1

        db.commit()
        print(f"Seeded {len(products)} products, {len(customers)} customers, {order_counter-1} orders.")
        print("Demo login — Email: alex@example.com  Password: Demo@12345")
    except Exception as e:
        db.rollback(); raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
