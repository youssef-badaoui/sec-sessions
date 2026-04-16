#!/bin/bash
echo "============================================"
echo "  Lab 7 — Weather SSRF"
echo "  App:   http://localhost:5008"
echo "  Files: http://files:7777 (internal only)"
echo "============================================"

docker compose down -v 2>/dev/null
docker compose up --build -d

sleep 3

APP_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5008/)

if [ "$APP_OK" = "200" ]; then
    echo ""
    echo "App is ready at http://localhost:5008"
    echo "The internal file service is on the backend network and is NOT"
    echo "exposed to the host. Reach it through the SSRF in the weather form."
    echo ""
else
    echo "ERROR: App failed to start. Check 'docker compose logs'."
    echo "  App status: $APP_OK"
fi
