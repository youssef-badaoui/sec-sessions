#!/bin/bash
echo "========================================="
echo "  Lab 1 — Broken Access Control (Wallet)"
echo "  Port: 5009"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for app to start..."
sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5009/ | grep -q "200"; then
    echo "App is ready at http://localhost:5009"
    echo ""
    echo "Credentials:"
    echo "  admin / admin123"
    echo "  user  / user123"
    echo ""
    echo "Walkthrough:"
    echo "  walkthrough.html"
else
    echo "ERROR: App failed to start. Check logs with: docker compose logs"
fi
