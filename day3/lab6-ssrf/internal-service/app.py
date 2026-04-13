from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"service": "internal-api", "status": "running", "version": "2.1.0"})

@app.route('/admin/credentials')
def credentials():
    return jsonify({
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
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": "47d 12h 33m"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
