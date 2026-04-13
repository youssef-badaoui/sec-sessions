from flask import Flask, request, redirect, url_for, render_template, make_response, jsonify
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__)
DB_PATH = '/data/app.db'

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
            role TEXT DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY,
            username TEXT,
            content TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT,
            role TEXT
        );
        CREATE TABLE IF NOT EXISTS stolen_tokens (
            id INTEGER PRIMARY KEY,
            token TEXT,
            received_at TEXT
        );
    ''')
    # Seed users
    try:
        conn.execute("INSERT INTO users (username, password, role) VALUES ('user', 'password', 'user')")
        conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'adminpass', 'admin')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def get_current_user(req):
    token = req.cookies.get('session_token')
    if not token:
        return None
    conn = get_db()
    session = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
    conn.close()
    if session:
        return {'username': session['username'], 'role': session['role']}
    return None

@app.route('/')
def index():
    user = get_current_user(request)
    if not user:
        return redirect(url_for('login'))
    return redirect(url_for('board'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        u = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if u:
            token = str(uuid.uuid4())
            conn.execute("INSERT INTO sessions (token, username, role) VALUES (?, ?, ?)", (token, u['username'], u['role']))
            conn.commit()
            conn.close()
            resp = make_response(redirect(url_for('board')))
            resp.set_cookie('session_token', token)
            return resp
        conn.close()
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        conn = get_db()
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
        conn.close()
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('session_token')
    return resp

@app.route('/board', methods=['GET', 'POST'])
def board():
    user = get_current_user(request)
    if not user:
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        content = request.form['content']
        conn.execute("INSERT INTO comments (username, content, created_at) VALUES (?, ?, ?)",
                     (user['username'], content, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
    comments = conn.execute("SELECT * FROM comments ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('board.html', user=user, comments=comments)

@app.route('/steal')
def steal():
    token = request.args.get('token', '')
    if token:
        conn = get_db()
        conn.execute("INSERT INTO stolen_tokens (token, received_at) VALUES (?, ?)",
                     (token, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    return 'OK', 200

@app.route('/stolen')
def stolen():
    conn = get_db()
    tokens = conn.execute("SELECT * FROM stolen_tokens ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('stolen.html', tokens=tokens)

@app.route('/admin/dashboard')
def admin_dashboard():
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return render_template('denied.html'), 403
    return render_template('admin_dashboard.html', user=user)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=False)
