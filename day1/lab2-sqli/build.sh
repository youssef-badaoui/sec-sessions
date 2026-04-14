#!/bin/bash
echo "========================================="
echo "  Lab 2 — SQL Injection (Auth Bypass)"
echo "  Port: 5002"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for app to start..."
sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/login | grep -q "200"; then
    echo "App is ready at http://localhost:5002"
    echo ""
    echo "Credentials:"
    echo "  admin    / supersecretpassword"
    echo "  employee / password123"
    echo ""
    echo "Walkthrough:"
    echo "  walkthrough.html"
else
    echo "ERROR: App failed to start. Check logs with: docker compose logs"
fi
