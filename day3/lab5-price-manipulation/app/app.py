from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'lab5-secret-key'
DB_PATH = '/data/app.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('/data', exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price REAL,
            image_emoji TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            product_name TEXT,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total REAL,
            created_at TEXT
        );
    ''')
    try:
        conn.execute("INSERT INTO products (name, description, price, image_emoji) VALUES ('Laptop Pro 15', 'High-performance laptop with 16GB RAM', 999.99, '💻')")
        conn.execute("INSERT INTO products (name, description, price, image_emoji) VALUES ('Smartphone X', 'Latest flagship smartphone', 699.99, '📱')")
        conn.execute("INSERT INTO products (name, description, price, image_emoji) VALUES ('Wireless Headphones', 'Noise-cancelling over-ear headphones', 149.99, '🎧')")
        conn.execute("INSERT INTO products (name, description, price, image_emoji) VALUES ('Smart Watch', 'Fitness tracking smartwatch', 299.99, '⌚')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

@app.route('/')
def shop():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template('shop.html', products=products)

@app.route('/buy', methods=['POST'])
def buy():
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])  # VULNERABLE: trusting client-sent price

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return "Product not found", 404

    total = price * quantity
    conn.execute("INSERT INTO orders (product_name, product_id, quantity, unit_price, total, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (product['name'], product_id, quantity, price, total, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return render_template('confirmation.html', product=product, quantity=quantity, unit_price=price, total=total, order_id=order_id)

@app.route('/admin/orders')
def admin_orders():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5005, debug=False)
