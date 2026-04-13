#!/bin/bash
echo "========================================="
echo "  Lab 6 — SSRF"
echo "  App Port: 5006  |  Internal API: not exposed"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for services to start..."
sleep 4

APP_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5006/)
INTERNAL_BLOCKED=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")

if [ "$APP_OK" = "200" ]; then
    echo "App is ready at http://localhost:5006"
    if [ "$INTERNAL_BLOCKED" = "000" ] || [ "$INTERNAL_BLOCKED" = "007" ]; then
        echo "Internal API is NOT accessible from host (correct)"
    else
        echo "WARNING: Internal API may be accessible from host on port 8080"
    fi
    echo ""
    echo "SSRF target URL (use inside the app):"
    echo "  http://internal-api:8080/admin/credentials"
else
    echo "ERROR: App failed to start. Check logs with: docker compose logs"
fi
