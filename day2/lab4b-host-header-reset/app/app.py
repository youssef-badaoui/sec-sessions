from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
import os
import uuid
import requests as http_requests

app = Flask(__name__)
app.secret_key = 'lab4b-secret-key'
DB_PATH = '/data/app.db'
MAILBOX_URL = 'http://mailbox:5013'

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
            email TEXT UNIQUE,
            role TEXT DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY,
            token TEXT,
            username TEXT,
            expired INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    try:
        conn.execute("INSERT INTO users (username, password, email, role) VALUES ('user', 'password', 'user@company.com', 'user')")
        conn.execute("INSERT INTO users (username, password, email, role) VALUES ('admin', 'unknownpassword', 'admin@company.com', 'admin')")
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
        conn.close()
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'], role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user:
            token = str(uuid.uuid4())
            conn.execute("INSERT INTO reset_tokens (token, username) VALUES (?, ?)", (token, username))
            conn.commit()
            reset_link = f"http://{request.host}{url_for('reset_password')}?token={token}"
            try:
                http_requests.post(f"{MAILBOX_URL}/api/send", json={
                    'to': user['email'],
                    'subject': 'Password Reset Request',
                    'body': f'Click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.'
                }, timeout=3)
            except Exception:
                pass
        conn.close()
        return render_template('forgot_password.html', success=True)
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        token = request.args.get('token', '')
        return render_template('reset_password.html', token=token)

    token = request.form['token']
    new_password = request.form['new_password']

    conn = get_db()
    # Clean logic: the token identifies the account to reset
    reset = conn.execute("SELECT * FROM reset_tokens WHERE token=? AND expired=0", (token,)).fetchone()
    if reset:
        conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, reset['username']))
        conn.execute("UPDATE reset_tokens SET expired=1 WHERE token=?", (token,))
        conn.commit()
        conn.close()
        return render_template('reset_password.html', success=True)
    conn.close()
    return render_template('reset_password.html', error='Invalid or expired token', token=token)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5003, debug=False)
