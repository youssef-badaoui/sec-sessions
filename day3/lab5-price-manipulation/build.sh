#!/bin/bash
echo "========================================="
echo "  Lab 5 — Price Manipulation"
echo "  Port: 5005"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for app to start..."
sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5005/ | grep -q "200"; then
    echo "App is ready at http://localhost:5005"
    echo ""
    echo "Useful URLs:"
    echo "  http://localhost:5005/              — Shop"
    echo "  http://localhost:5005/admin/orders  — All orders (admin view)"
else
    echo "ERROR: App failed to start. Check logs with: docker compose logs"
fi
