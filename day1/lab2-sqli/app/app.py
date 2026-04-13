from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'lab2-secret-key'
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
            role TEXT DEFAULT 'employee',
            department TEXT,
            salary TEXT
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary TEXT,
            email TEXT
        );
    ''')
    try:
        conn.execute("INSERT INTO users (username, password, role, department, salary) VALUES ('admin', 'supersecretpassword', 'admin', 'IT', '$145,000')")
        conn.execute("INSERT INTO users (username, password, role, department, salary) VALUES ('employee', 'password123', 'employee', 'Sales', '$65,000')")
        conn.execute("INSERT INTO employees (name, department, salary, email) VALUES ('Alice Johnson', 'Engineering', '$130,000', 'alice@company.com')")
        conn.execute("INSERT INTO employees (name, department, salary, email) VALUES ('Bob Smith', 'Marketing', '$85,000', 'bob@company.com')")
        conn.execute("INSERT INTO employees (name, department, salary, email) VALUES ('Carol White', 'Finance', '$95,000', 'carol@company.com')")
        conn.execute("INSERT INTO employees (name, department, salary, email) VALUES ('David Lee', 'Engineering', '$125,000', 'david@company.com')")
        conn.execute("INSERT INTO employees (name, department, salary, email) VALUES ('Eva Martinez', 'HR', '$78,000', 'eva@company.com')")
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
        # VULNERABLE: String concatenation in SQL query
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        try:
            user = conn.execute(query).fetchone()
        except Exception:
            conn.close()
            return render_template('login.html', error='Invalid credentials')

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            conn.close()
            return redirect(url_for('dashboard'))
        conn.close()
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    employees = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, employees=employees, role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
