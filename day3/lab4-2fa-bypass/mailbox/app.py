from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'lab4-mailbox-secret'
DB_PATH = '/data/mailbox.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('/data', exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS mailbox_users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY,
            recipient TEXT,
            subject TEXT,
            body TEXT,
            received_at TEXT
        );
    ''')
    try:
        conn.execute("INSERT INTO mailbox_users (username, password, email) VALUES ('user', 'password', 'user@company.com')")
        conn.execute("INSERT INTO mailbox_users (username, password, email) VALUES ('admin', 'adminpass', 'admin@company.com')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

def get_current_mailbox_user():
    username = session.get('mailbox_username')
    if not username:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM mailbox_users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user

@app.route('/')
def inbox():
    user = get_current_mailbox_user()
    if not user:
        return redirect(url_for('login'))
    conn = get_db()
    emails = conn.execute("SELECT * FROM emails WHERE recipient=? ORDER BY id DESC", (user['email'],)).fetchall()
    conn.close()
    return render_template('inbox.html', emails=emails, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM mailbox_users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()
        if user:
            session['mailbox_username'] = user['username']
            return redirect(url_for('inbox'))
        return render_template('login.html', error='Invalid mailbox credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/email/<int:email_id>')
def read_email(email_id):
    user = get_current_mailbox_user()
    if not user:
        return redirect(url_for('login'))
    conn = get_db()
    email = conn.execute(
        "SELECT * FROM emails WHERE id=? AND recipient=?",
        (email_id, user['email'])
    ).fetchone()
    conn.close()
    if not email:
        return "Email not found", 404
    return render_template('email.html', email=email, user=user)

@app.route('/api/send', methods=['POST'])
def send_email():
    data = request.get_json()
    conn = get_db()
    conn.execute("INSERT INTO emails (recipient, subject, body, received_at) VALUES (?, ?, ?, ?)",
                 (data['to'], data['subject'], data['body'], datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'sent'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5014, debug=False)
