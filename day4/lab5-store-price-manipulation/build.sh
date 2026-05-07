#!/bin/bash
echo "============================================"
echo "  Lab 5 — Store Price Manipulation"
echo "  Port: 5005"
echo "============================================"

docker compose down -v 2>/dev/null
docker compose up --build -d

sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5005/login | grep -q "200"; then
    echo ""
    echo "App is ready at http://localhost:5005"
    echo "Create an account — you start with \$200 store credit."
    echo ""
else
    echo "ERROR: App failed to start. Check 'docker compose logs'."
fi
