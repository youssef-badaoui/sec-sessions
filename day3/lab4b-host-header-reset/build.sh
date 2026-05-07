#!/bin/bash
echo "========================================="
echo "  Lab 4B — Reset Link Host Header Poisoning"
echo "  App Port: 5007  |  Mailbox Port: 5017"
echo "========================================="
echo ""
echo "Building and starting containers..."
docker compose down -v 2>/dev/null
docker compose up --build -d

echo ""
echo "Waiting for services to start..."
sleep 4

APP_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5007/login)
MAIL_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5017/login)

if [ "$APP_OK" = "200" ] && [ "$MAIL_OK" = "200" ]; then
    echo "App is ready at     http://localhost:5007"
    echo "Mailbox is ready at http://localhost:5017"
    echo ""
    echo "Credentials:"
    echo "  user  / password         (your account)"
    echo "  admin / unknownpassword  (target)"
    echo ""
    echo "Mailbox accounts:"
    echo "  user  / password"
    echo "  admin / unknownpassword"
else
    echo "ERROR: One or more services failed to start."
    [ "$APP_OK" != "200" ] && echo "  App (5007): not responding"
    [ "$MAIL_OK" != "200" ] && echo "  Mailbox (5017): not responding"
    echo "Check logs with: docker compose logs"
fi
