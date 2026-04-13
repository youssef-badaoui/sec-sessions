from flask import Flask, request, render_template
import requests as http_requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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

    return render_template('preview.html', content=content, url=url, status_code=status_code, content_type=content_type)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=False)
