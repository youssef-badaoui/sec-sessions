from flask import Flask, request, render_template
import json
import requests as http_requests

app = Flask(__name__)

# Cities shown to the user. The API URL is built client-side and sent in the request.
CITIES = [
    {'name': 'Paris', 'country': 'France', 'emoji': '🇫🇷'},
    {'name': 'Tokyo', 'country': 'Japan', 'emoji': '🇯🇵'},
    {'name': 'New York', 'country': 'USA', 'emoji': '🇺🇸'},
    {'name': 'London', 'country': 'UK', 'emoji': '🇬🇧'},
    {'name': 'Casablanca', 'country': 'Morocco', 'emoji': '🇲🇦'},
    {'name': 'Sydney', 'country': 'Australia', 'emoji': '🇦🇺'},
    {'name': 'Berlin', 'country': 'Germany', 'emoji': '🇩🇪'},
    {'name': 'Dubai', 'country': 'UAE', 'emoji': '🇦🇪'},
]

WEATHER_API_BASE = 'https://wttr.in'

# wttr.in weather codes grouped to a small set of icons.
# https://github.com/chubin/wttr.in/blob/master/lib/constants.py
WEATHER_ICONS = {
    'sunny':   {'codes': {'113'}, 'icon': '☀️'},
    'partly':  {'codes': {'116'}, 'icon': '⛅'},
    'cloudy':  {'codes': {'119', '122'}, 'icon': '☁️'},
    'fog':     {'codes': {'143', '248', '260'}, 'icon': '🌫️'},
    'rain':    {'codes': {'176', '263', '266', '281', '284', '293', '296', '299',
                          '302', '305', '308', '311', '314', '317', '350', '353',
                          '356', '359', '362', '365', '368'}, 'icon': '🌧️'},
    'snow':    {'codes': {'179', '182', '185', '227', '230', '320', '323', '326',
                          '329', '332', '335', '338', '371', '374', '377'}, 'icon': '❄️'},
    'thunder': {'codes': {'200', '386', '389', '392', '395'}, 'icon': '⛈️'},
}


def weather_icon(code):
    code = str(code)
    for group in WEATHER_ICONS.values():
        if code in group['codes']:
            return group['icon']
    return '🌡️'


def parse_weather(body):
    """Try to parse a wttr.in j1 JSON payload into a display-friendly dict.
    Returns None if the body isn't valid weather JSON — the caller falls back
    to rendering the raw response (which is what the SSRF exploit produces)."""
    try:
        data = json.loads(body)
        cur = data['current_condition'][0]
        area = data['nearest_area'][0]
        forecast = []
        for day in data.get('weather', [])[:3]:
            mid_hour = day['hourly'][4] if len(day['hourly']) > 4 else day['hourly'][0]
            forecast.append({
                'date': day['date'],
                'max_c': day['maxtempC'],
                'min_c': day['mintempC'],
                'icon': weather_icon(mid_hour['weatherCode']),
                'desc': mid_hour['weatherDesc'][0]['value'],
            })
        return {
            'temp_c': cur['temp_C'],
            'temp_f': cur['temp_F'],
            'feels_c': cur['FeelsLikeC'],
            'desc': cur['weatherDesc'][0]['value'],
            'icon': weather_icon(cur['weatherCode']),
            'humidity': cur['humidity'],
            'wind_kmph': cur['windspeedKmph'],
            'wind_dir': cur['winddir16Point'],
            'pressure': cur['pressure'],
            'visibility': cur['visibility'],
            'cloudcover': cur['cloudcover'],
            'uv_index': cur['uvIndex'],
            'area': area['areaName'][0]['value'],
            'region': area['region'][0]['value'],
            'country': area['country'][0]['value'],
            'forecast': forecast,
            'observed_at': cur.get('observation_time', ''),
        }
    except (ValueError, KeyError, IndexError, TypeError):
        return None


@app.route('/')
def index():
    return render_template('index.html', cities=CITIES, api_base=WEATHER_API_BASE)


@app.route('/check', methods=['POST'])
def check():
    api_url = request.form.get('api_url', '').strip()
    city = request.form.get('city', 'Unknown')

    if not api_url:
        return render_template('index.html', cities=CITIES, api_base=WEATHER_API_BASE,
                               error='No API URL provided')

    try:
        response = http_requests.get(api_url, timeout=5)
        body = response.text
        content_type = response.headers.get('Content-Type', 'text/plain')
        weather = parse_weather(body)
        return render_template('result.html',
                               city=city,
                               api_url=api_url,
                               status=response.status_code,
                               content_type=content_type,
                               body=body[:8000],
                               weather=weather)
    except Exception as exc:
        return render_template('index.html', cities=CITIES, api_base=WEATHER_API_BASE,
                               error=f'Weather fetch failed: {exc}')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=False)
