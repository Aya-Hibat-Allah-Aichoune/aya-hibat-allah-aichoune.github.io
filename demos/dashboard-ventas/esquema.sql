CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    region VARCHAR(50),
    product VARCHAR(50),
    quantity INT,
    total_sales FLOAT,
    sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO sales_data (region, product, quantity, total_sales)
VALUES
('Andalucía', 'Hydrating Face Moisturizer', 10, 250.50),
('Cataluña', 'Vitamin C Brightening Serum', 5, 125.75),
('Galicia', 'Matte Liquid Lipstick', 8, 200.00),
('País Vasco', 'Eye Shadow Palette Pro', 3, 75.25);
