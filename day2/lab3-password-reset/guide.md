# Lab 3 — Password Reset Flaw (Broken Token-to-User Binding)

## Overview

Password reset flows are a common source of vulnerabilities. A properly implemented reset flow must ensure that a reset token can only be used to change the password of the user who requested it. When the server fails to validate this binding, an attacker can use their own valid reset token to change someone else's password.

This is an example of an **Insecure Direct Object Reference (IDOR)** combined with a **broken access control** — the server trusts a user-supplied username field instead of deriving the target user from the token itself.

## Step 1 — Analyze the Code

Open `app/app.py` and look at the `/reset-password` POST handler (lines ~99-120):

```python
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        token = request.args.get('token', '')
        username = request.args.get('username', '')
        return render_template('reset_password.html', token=token, username=username)

    token = request.form['token']
    username = request.form['username']
    new_password = request.form['new_password']

    conn = get_db()
    # VULNERABLE: Only checks token validity, not token-to-user binding
    reset = conn.execute("SELECT * FROM reset_tokens WHERE token=? AND expired=0", (token,)).fetchone()
    if reset:
        conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
        conn.execute("UPDATE reset_tokens SET expired=1 WHERE token=?", (token,))
        conn.commit()
```

**Why this is vulnerable:**
1. The token is generated and stored with a specific `username` in the `reset_tokens` table
2. But the reset endpoint only validates that the token **exists** and is **not expired**
3. It does NOT check that the token **belongs to** the `username` submitted in the form
4. The `username` field in the reset form is editable — it's a regular text input, not a hidden field tied to the token

This means: request a reset for YOUR account, get a valid token, then submit it with the ADMIN's username to reset the admin's password.

Also look at `app/templates/reset_password.html`:
```html
<input type="text" name="username" value="{{ username }}">
```
The username is pre-filled from the URL but is an editable text field.

## Step 2 — Exploit the Vulnerability

### Prerequisites
- Start the lab: `docker compose up --build`
- App is at: `http://localhost:5003`
- Mailbox is at: `http://localhost:5013`

### Step 2.1 — Request a password reset for YOUR account

1. Go to `http://localhost:5003/forgot-password`
2. Enter `user` as the username
3. Click "Send Reset Link"
4. You see: "If the account exists, a reset link has been sent to the associated mailbox."

### Step 2.2 — Get the reset link from the mailbox

1. Open the mailbox at `http://localhost:5013`
2. You'll see an email to `user@company.com` with subject "Password Reset Request"
3. Click "Read" to open it
4. The email contains a reset link like:
   ```
   http://localhost:5003/reset-password?token=<UUID>&username=user
   ```
5. Click the link — it opens the reset password form with `user` pre-filled in the username field

[Screenshot: Mailbox showing the reset email with the clickable link]

### Step 2.3 — Exploit: Change the username to admin

1. On the reset password form, you see:
   - Token: (hidden field, pre-filled)
   - Username: `user` (editable text field)
   - New Password: (empty)

2. **Change the username field from `user` to `admin`**
3. Enter a new password, e.g., `hacked123`
4. Click "Reset Password"
5. You see: "Password has been reset successfully!"

This just changed the **admin's** password using **your** valid token.

### Step 2.4 — Confirm the exploit

1. Go to `http://localhost:5003/login`
2. Login with `admin` / `hacked123`
3. You're logged in as admin!

[Screenshot: Dashboard showing "Welcome, admin!" with admin badge]

### Step 2.5 — Exploit via curl (alternative)

```bash
# Step 1: Request reset for 'user'
curl -X POST http://localhost:5003/forgot-password -d "username=user"

# Step 2: Get the token from the mailbox
TOKEN=$(curl -s http://localhost:5013/ | grep -oP 'token=[^&]+' | head -1 | cut -d= -f2)
# Or manually copy it from http://localhost:5013

# Step 3: Use the token but change username to admin
curl -X POST http://localhost:5003/reset-password \
  -d "token=${TOKEN}&username=admin&new_password=hacked123"

# Step 4: Login as admin with the new password
curl -X POST http://localhost:5003/login \
  -d "username=admin&password=hacked123" \
  -c cookies.txt -L

curl -b cookies.txt http://localhost:5003/dashboard
```

## Step 3 — Discuss & Implement the Fix

### The Problem
The reset endpoint validates the token but does not verify it belongs to the submitted username. The username comes from a user-editable form field.

### The Fix
Bind the token validation to the username — ensure the token was actually issued for the user whose password is being changed.

**Before** (`app/app.py`, line ~112):
```python
reset = conn.execute("SELECT * FROM reset_tokens WHERE token=? AND expired=0", (token,)).fetchone()
if reset:
    conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
```

**After:**
```python
reset = conn.execute("SELECT * FROM reset_tokens WHERE token=? AND username=? AND expired=0", (token, username)).fetchone()
if reset:
    conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
```

### Why This Works
The additional `AND username=?` clause ensures that the token must have been generated for the specific user whose password is being changed. If an attacker submits a token generated for `user` but changes the username to `admin`, the query returns no results because there's no row where `token=<user's token> AND username='admin'`.

**Additional best practices:**
- Don't include the username in the reset form at all — derive it from the token server-side
- Use short expiration times for reset tokens (15-30 minutes)
- Invalidate all tokens for a user when a password is successfully reset
- Rate-limit reset requests to prevent enumeration

## Step 4 — Verify the Fix

1. Apply the fix in `app/app.py`: add `AND username=?` to the query and pass `username` as a parameter
2. Restart: `docker compose down && docker compose up --build`
3. Request a reset for `user` again
4. Get the token from the mailbox
5. Try to use it with `admin` as the username:
   - Result: "Invalid or expired token" error — the token doesn't match `admin`
6. Use it correctly with `user` as the username:
   - Result: Password is reset successfully — normal functionality works

[Screenshot: Reset form showing "Invalid or expired token" when username is changed to admin]

**Remember to revert the fix** so the lab ships in its vulnerable state.
