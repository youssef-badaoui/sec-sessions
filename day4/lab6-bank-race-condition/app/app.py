from flask import Flask, request, redirect, url_for, session, render_template
import os
import random
import sqlite3

app = Flask(__name__)
app.secret_key = 'lab6-secret-key'
DB_PATH = '/data/bank.db'


def get_db():
    """
    Each request opens its own connection. WAL mode lets readers run concurrently
    with writers — that's what makes the TOCTOU window wide enough to race.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def init_db():
    os.makedirs('/data', exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            account_id TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL DEFAULT 100
        );
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()


def make_account_id():
    return ''.join(random.choice('0123456789') for _ in range(20))


def current_user():
    username = session.get('username')
    if not username:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


@app.route('/')
def index():
    user = current_user()
    if user:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        conn = get_db()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (request.form['username'], request.form['password']),
            ).fetchone()
        finally:
            conn.close()
        if not user:
            return render_template('login.html', error='Invalid credentials')
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error='Username and password are required')

        conn = get_db()
        try:
            while True:
                account_id = make_account_id()
                exists = conn.execute("SELECT 1 FROM users WHERE account_id = ?", (account_id,)).fetchone()
                if not exists:
                    break

            try:
                conn.execute(
                    "INSERT INTO users (username, password, account_id, balance) VALUES (?, ?, ?, ?)",
                    (username, password, account_id, 100),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                return render_template('register.html', error='Username already exists')
        finally:
            conn.close()
        session['username'] = username
        return redirect(url_for('dashboard', message='Account created with $100'))
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    conn = get_db()
    try:
        accounts = conn.execute("SELECT username, account_id, balance FROM users ORDER BY id").fetchall()
        transfers = conn.execute("SELECT sender, recipient, amount, created_at FROM transfers ORDER BY id DESC").fetchall()
    finally:
        conn.close()
    return render_template('dashboard.html', user=user, accounts=accounts, transfers=transfers,
                           message=request.args.get('message'))


@app.route('/transfer', methods=['POST'])
def transfer():
    user = current_user()
    if not user:
        return redirect(url_for('index'))

    target_account_id = request.form['target_account_id'].strip()
    try:
        amount = float(request.form['amount'])
    except ValueError:
        return redirect(url_for('dashboard', message='Invalid amount'))
    if amount <= 0:
        return redirect(url_for('dashboard', message='Amount must be positive'))

    conn = get_db()
    try:
        # 1. READ current balance (separate SELECT — Time Of Check)
        sender = conn.execute("SELECT * FROM users WHERE username = ?", (user['username'],)).fetchone()

        # 2. Look up recipient — a second query that widens the read window
        recipient = conn.execute("SELECT * FROM users WHERE account_id = ?", (target_account_id,)).fetchone()

        if not recipient:
            return redirect(url_for('dashboard', message='Recipient not found'))
        if recipient['username'] == sender['username']:
            return redirect(url_for('dashboard', message='Cannot send money to yourself'))

        # 3. CHECK against the value we read in step 1. If another concurrent request
        #    has already deducted from the balance but not yet committed, we still see
        #    the original balance here and pass the check.
        if sender['balance'] < amount:
            return redirect(url_for('dashboard', message='Insufficient balance'))

        # 4. Write an audit log entry before applying the update. Another plain,
        #    realistic query — in the real world this would be "additional work"
        #    (logging, notifications, fraud checks) that sits between check and use.
        conn.execute(
            "INSERT INTO audit_log (event, details) VALUES (?, ?)",
            ('transfer_attempt', f"{sender['username']} -> {recipient['username']} amount={amount}"),
        )

        # 5. APPLY the update (Time Of Use). balance = balance - amount uses the
        #    CURRENT row value, so concurrent passes of the check push balance negative.
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE username = ?",
            (amount, sender['username']),
        )
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE username = ?",
            (amount, recipient['username']),
        )
        conn.execute(
            "INSERT INTO transfers (sender, recipient, amount) VALUES (?, ?, ?)",
            (sender['username'], recipient['username'], amount),
        )
        conn.commit()
        return redirect(url_for('dashboard', message=f'Sent ${amount:.2f}'))
    except sqlite3.OperationalError as exc:
        app.logger.warning('transfer failed: %s', exc)
        return redirect(url_for('dashboard', message=f'Transfer failed: {exc}'))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5006, debug=False, threaded=True)
