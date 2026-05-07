from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'lab5-secret-key'
DB_PATH = '/data/store.db'

PRODUCTS = [
    {'id': 1, 'name': 'USB Cable', 'price': 9.99, 'emoji': '🔌'},
    {'id': 2, 'name': 'Wireless Mouse', 'price': 29.99, 'emoji': '🖱️'},
    {'id': 3, 'name': 'Mechanical Keyboard', 'price': 89.99, 'emoji': '⌨️'},
    {'id': 4, 'name': 'Gaming Monitor', 'price': 349.99, 'emoji': '🖥️'},
    {'id': 5, 'name': 'Laptop Pro', 'price': 1299.99, 'emoji': '💻'},
    {'id': 6, 'name': 'Noise-Cancelling Headphones', 'price': 199.99, 'emoji': '🎧'},
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('/data', exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            balance REAL DEFAULT 200
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            username TEXT,
            product_name TEXT,
            price_paid REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('shop'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = user['username']
            return redirect(url_for('shop'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            return render_template('signup.html', error='All fields are required')
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('signup.html', error='Username already taken')
        conn.close()
        session['username'] = username
        return redirect(url_for('shop'))
    return render_template('signup.html')

@app.route('/shop')
def shop():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    conn.close()
    return render_template('shop.html', user=user, products=PRODUCTS)

@app.route('/buy', methods=['POST'])
def buy():
    if 'username' not in session:
        return redirect(url_for('login'))

    product_name = request.form['product_name']
    price = float(request.form['price'])

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()

    if user['balance'] < price:
        conn.close()
        return render_template('shop.html', user=user, products=PRODUCTS, error='Insufficient balance!')

    conn.execute("UPDATE users SET balance = balance - ? WHERE username=?", (price, session['username']))
    conn.execute("INSERT INTO orders (username, product_name, price_paid) VALUES (?, ?, ?)",
                 (session['username'], product_name, price))
    conn.commit()

    user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    conn.close()
    return redirect(url_for('confirmation', product=product_name, paid=f"{price:.2f}"))

@app.route('/confirmation')
def confirmation():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    conn.close()
    return render_template('confirmation.html', user=user,
                           product=request.args.get('product', ''),
                           paid=request.args.get('paid', ''))

@app.route('/orders')
def orders():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    order_list = conn.execute("SELECT * FROM orders WHERE username=? ORDER BY id DESC", (session['username'],)).fetchall()
    conn.close()
    return render_template('orders.html', user=user, orders=order_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5005, debug=False)
