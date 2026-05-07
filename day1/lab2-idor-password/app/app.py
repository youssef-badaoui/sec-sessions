from flask import Flask, request, session, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = "dev-secret"

ADMIN_SECRET = "ID0R_PWN3D_TH3_4DM1N"

users = {
    1: {"id": 1, "username": "admin", "password": "admin123"},
    2: {"id": 2, "username": "user", "password": "user123"},
}


def current_user():
    uid = session.get("uid")
    return users.get(uid)


def is_admin(u):
    return bool(u) and u["id"] == 1


def render_page(title, body, user=None):
    nav = ""
    if user:
        nav_items = ["<a href='/profile'>Profile</a>"]
        if is_admin(user):
            nav_items.append("<a href='/admin/secrets'>Admin Secrets</a>")
        nav_items.append("<a href='/logout'>Logout</a>")
        nav = "<nav>" + "".join(nav_items) + "</nav>"

    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>My Account</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Work+Sans:wght@400;600&display=swap');
    :root {{
      --green: #628e3d;
      --green-dark: #4d6f2f;
      --green-light: #eaf2e2;
      --sand: #f6f4ef;
      --ink: #1e1f1c;
      --muted: #6b6f66;
      --card: #ffffff;
      --shadow: 0 12px 30px rgba(0,0,0,.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: radial-gradient(1200px 600px at 10% -20%, var(--green-light), transparent),
                  radial-gradient(800px 400px at 110% 10%, #f1f5ea, transparent),
                  var(--sand);
      font-family: "Work Sans", "Trebuchet MS", sans-serif;
      min-height: 100vh;
    }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 32px 20px 60px; }}
    .center {{ display: flex; justify-content: center; align-items: center; min-height: 60vh; }}
    header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 26px; }}
    .brand {{ display: flex; align-items: center; gap: 12px; }}
    .mark {{
      width: 44px; height: 44px; border-radius: 10px;
      background: linear-gradient(135deg, var(--green), var(--green-dark));
      box-shadow: inset 0 0 0 2px rgba(255,255,255,.2);
    }}
    h1 {{ margin: 0; font-family: "Libre Baskerville", Georgia, serif; font-weight: 700; letter-spacing: .4px; }}
    nav a {{
      margin-left: 14px; text-decoration: none; color: var(--green-dark);
      font-weight: 600; padding: 6px 10px; border-radius: 20px;
      background: rgba(98,142,61,.1);
    }}
    .card {{
      background: var(--card); border-radius: 14px; padding: 22px;
      box-shadow: var(--shadow); border: 1px solid rgba(0,0,0,.06);
    }}
    .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .muted {{ color: var(--muted); }}
    label {{ font-weight: 600; }}
    input {{
      width: 100%; padding: 10px 12px; margin-top: 6px;
      border-radius: 10px; border: 1px solid #d8ded2;
      background: #fbfcf9; font-size: 14px;
    }}
    button {{
      margin-top: 14px; padding: 10px 14px; border: 0; border-radius: 10px;
      background: var(--green); color: white; font-weight: 600; cursor: pointer;
      box-shadow: 0 8px 16px rgba(98,142,61,.25);
    }}
    .badge {{
      display: inline-block; padding: 4px 10px; border-radius: 999px;
      background: var(--green-light); color: var(--green-dark);
      font-size: 12px; font-weight: 600;
    }}
    code {{ background: #f1f4ee; padding: 2px 6px; border-radius: 6px; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">
        <div class="mark"></div>
        <div><h1>My Account</h1></div>
      </div>
      {nav}
    </header>
    <main>
      <h2>{title}</h2>
      {body}
    </main>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    if current_user():
        return redirect(url_for("profile"))
    body = """
    <div class="center">
      <div class="card" style="max-width:360px;width:100%;">
        <div class="badge">Access Panel</div>
        <h3>Login</h3>
        <form method="post" action="/login">
          <label>Username</label>
          <input name="username" required>
          <label>Password</label>
          <input name="password" type="password" required>
          <button type="submit">Sign in</button>
        </form>
        <p class="muted">Users: admin / user</p>
        <p class="muted">Passwords: admin123 / user123</p>
      </div>
    </div>
    """
    return render_page("Welcome", body)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    for u in users.values():
        if u["username"] == username and u["password"] == password:
            session["uid"] = u["id"]
            return redirect(url_for("profile"))
    body = """
    <div class="card" style="max-width:360px;">
      <div class="badge">Access Denied</div>
      <h3>Invalid credentials</h3>
      <p><a href="/">Back to login</a></p>
    </div>
    """
    return render_page("Login Failed", body), 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/profile")
def profile():
    u = current_user()
    if not u:
        return redirect(url_for("index"))

    body = f"""
    <div class="grid">
      <div class="card">
        <div class="badge">Account</div>
        <p>User: <strong>{u['username']}</strong> (id {u['id']})</p>
      </div>
      <div class="card">
        <h3>Update Password</h3>
        <form method="post" action="/update_password">
          <input name="id" type="hidden" value="{u['id']}">
          <label>Old Password</label>
          <input name="old" type="password" required>
          <label>New Password</label>
          <input name="new" type="password" required>
          <button type="submit">Update Password</button>
        </form>
      </div>
    </div>
    """
    return render_page("Profile", body, u)


@app.route("/update_password", methods=["POST"])
def update_password():
    data = request.get_json(silent=True) or {}
    uid = int(data.get("id", 0) or request.form.get("id", 0))
    old = data.get("old") or request.form.get("old")
    new = data.get("new") or request.form.get("new")
    cu = current_user()
    if cu and cu["password"] == old and uid in users:
        users[uid]["password"] = new
        return jsonify({"status": "ok"}) if request.is_json else redirect(url_for("profile"))
    if request.is_json:
        return jsonify({"status": "fail"}), 400
    body = """
    <div class="card">
      <div class="badge">Failed</div>
      <h3>Password update failed</h3>
    </div>
    """
    return render_page("Profile", body, current_user()), 400


@app.route("/admin/secrets")
def admin_secrets():
    u = current_user()
    if not is_admin(u):
        body = """
        <div class="card">
          <div class="badge">Access Denied</div>
          <h3>Admin only.</h3>
        </div>
        """
        return render_page("Admin Secrets", body, u), 403
    body = f"""
    <div class="card">
      <div class="badge">Confidential</div>
      <h3>Admin secret</h3>
      <p>Flag: <strong>{ADMIN_SECRET}</strong></p>
    </div>
    """
    return render_page("Admin Secrets", body, u)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
