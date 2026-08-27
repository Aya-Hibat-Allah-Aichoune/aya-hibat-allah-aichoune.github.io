import random
import time
from datetime import datetime
from sqlalchemy import create_engine

engine = create_engine('postgresql://usuario:contrasena@localhost:5432/sales_dashboard')

regions = ['Andalucía', 'Cataluña', 'Galicia', 'País Vasco']
products = ['Hydrating Face Moisturizer', 'Vitamin C Brightening Serum', 'Matte Liquid Lipstick', 'Eye Shadow Palette Pro']

print("Sales simulator started... Press Ctrl+C to stop.")

while True:
    region = random.choice(regions)
    product = random.choice(products)
    quantity = random.randint(1, 10)
    total_sales = round(random.uniform(50, 500), 2)

    insert_query = f"""
        INSERT INTO sales_data (region, product, quantity, total_sales, sale_time)
        VALUES ('{region}', '{product}', {quantity}, {total_sales}, '{datetime.now()}');
    """

    with engine.connect() as conn:
        conn.execute(insert_query)
        print(f"Inserted: {region}, {product}, {quantity}, ${total_sales}")

    time.sleep(60)
