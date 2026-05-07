#!/bin/bash
echo "============================================"
echo "  Lab 6 — Bank Race Condition"
echo "  Port: 5006"
echo "============================================"

docker compose down -v 2>/dev/null
docker compose up --build -d

sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5006/ | grep -q "200"; then
    echo ""
    echo "App is ready at http://localhost:5006"
    echo "Create two accounts, each starts with \$100."
    echo ""
else
    echo "ERROR: App failed to start. Check 'docker compose logs'."
fi
