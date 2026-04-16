# Lab 7: Weather SSRF

- Pick a city and the app will fetch weather data from a weather API.
- Look at the request — the full API URL (`api_url`) is sent from the browser, not built on the server.
- A second container runs an internal file service at `http://files:7777` on the backend network. It is **not** exposed to the host, so you cannot reach it directly.
- Swap the `api_url` for `http://files:7777/` to make the server fetch the internal service on your behalf.
- Goal: retrieve the fake credentials file from the internal service through the weather form.
