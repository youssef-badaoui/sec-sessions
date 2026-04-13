from flask import Flask, request, render_template, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = '/data/mailbox.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('/data', exist_ok=True)
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY,
            recipient TEXT,
            subject TEXT,
            body TEXT,
            received_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def inbox():
    conn = get_db()
    emails = conn.execute("SELECT * FROM emails ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('inbox.html', emails=emails)

@app.route('/email/<int:email_id>')
def read_email(email_id):
    conn = get_db()
    email = conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
    conn.close()
    if not email:
        return "Email not found", 404
    return render_template('email.html', email=email)

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
