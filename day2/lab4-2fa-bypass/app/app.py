from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
import os
import random
import requests as http_requests

app = Flask(__name__)
app.secret_key = 'lab4-secret-key'
DB_PATH = '/data/app.db'
MAILBOX_URL = 'http://mailbox:5014'

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
            email TEXT,
            role TEXT DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS tfa_codes (
            id INTEGER PRIMARY KEY,
            username TEXT,
            code TEXT,
            expired INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    try:
        conn.execute("INSERT INTO users (username, password, email, role) VALUES ('user', 'password', 'user@company.com', 'user')")
        conn.execute("INSERT INTO users (username, password, email, role) VALUES ('admin', 'adminpass', 'admin@company.com', 'admin')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            code = str(random.randint(100000, 999999))
            conn.execute("INSERT INTO tfa_codes (username, code) VALUES (?, ?)", (username, code))
            conn.commit()
            try:
                http_requests.post(f"{MAILBOX_URL}/api/send", json={
                    'to': user['email'],
                    'subject': 'Your 2FA Code',
                    'body': f'Your two-factor authentication code is: {code}\n\nThis code will expire shortly.'
                }, timeout=3)
            except Exception:
                pass
            conn.close()
            return render_template('verify_2fa.html', username=username, password=password)
        conn.close()
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/login2', methods=['POST'])
def login2():
    username = request.form['username']
    password = request.form['password']
    code = request.form['2fa_code']

    conn = get_db()
    code_valid = conn.execute("SELECT * FROM tfa_codes WHERE code=? AND expired=0", (code,)).fetchone()
    user_valid = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()

    if code_valid and user_valid:
        conn.execute("UPDATE tfa_codes SET expired=1 WHERE code=?", (code,))
        conn.commit()
        conn.close()
        session['username'] = username
        session['role'] = user_valid['role']
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('verify_2fa.html', username=username, password=password, error='Invalid 2FA code')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'], role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5004, debug=False)
