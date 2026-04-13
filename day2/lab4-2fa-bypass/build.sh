#!/bin/bash
echo "========================================="
echo "  Lab 4 — 2FA Bypass"
echo "  App Port: 5004  |  Mailbox Port: 5014"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for services to start..."
sleep 4

APP_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5004/login)
MAIL_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5014/)

if [ "$APP_OK" = "200" ] && [ "$MAIL_OK" = "200" ]; then
    echo "App is ready at     http://localhost:5004"
    echo "Mailbox is ready at http://localhost:5014"
    echo ""
    echo "Credentials:"
    echo "  user  / password   (your account)"
    echo "  admin / adminpass  (target, has 2FA)"
else
    echo "ERROR: One or more services failed to start."
    [ "$APP_OK" != "200" ] && echo "  App (5004): not responding"
    [ "$MAIL_OK" != "200" ] && echo "  Mailbox (5014): not responding"
    echo "Check logs with: docker compose logs"
fi
