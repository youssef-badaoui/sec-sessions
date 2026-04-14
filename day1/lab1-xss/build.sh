#!/bin/bash
echo "========================================="
echo "  Lab 1 — Stored XSS"
echo "  Port: 5001"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for app to start..."
sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/login | grep -q "200"; then
    echo "App is ready at http://localhost:5001"
    echo ""
    echo "Credentials:"
    echo "  user  / password"
    echo "  admin / adminpass"
    echo ""
    echo "Useful URLs:"
    echo "  http://localhost:5001/board     — Comment board"
    echo "  http://localhost:5001/admin/dashboard — Admin-only page"
    echo "  walkthrough.html                — Standalone lab walkthrough"
else
    echo "ERROR: App failed to start. Check logs with: docker compose logs"
fi
