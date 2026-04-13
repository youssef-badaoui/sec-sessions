#!/bin/bash
echo "========================================="
echo "  Lab 3 — Password Reset Flaw"
echo "  App Port: 5003  |  Mailbox Port: 5013"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for services to start..."
sleep 4

APP_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5003/login)
MAIL_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5013/)

if [ "$APP_OK" = "200" ] && [ "$MAIL_OK" = "200" ]; then
    echo "App is ready at     http://localhost:5003"
    echo "Mailbox is ready at http://localhost:5013"
    echo ""
    echo "Credentials:"
    echo "  user  / password         (your account)"
    echo "  admin / unknownpassword  (target)"
else
    echo "ERROR: One or more services failed to start."
    [ "$APP_OK" != "200" ] && echo "  App (5003): not responding"
    [ "$MAIL_OK" != "200" ] && echo "  Mailbox (5013): not responding"
    echo "Check logs with: docker compose logs"
fi
