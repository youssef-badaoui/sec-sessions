Write-Host "========================================="
Write-Host "  Lab 4 - 2FA Bypass"
Write-Host "  App Port: 5004  |  Mailbox Port: 5014"
Write-Host "========================================="
Write-Host ""
Write-Host "Building and starting containers..."
docker compose down -v 2>$null
docker compose up --build -d

Write-Host ""
Write-Host "Waiting for services to start..."
Start-Sleep -Seconds 4

function Get-Status($url) {
    try {
        return (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode
    } catch {
        return 0
    }
}

$appOk  = Get-Status "http://localhost:5004/login"
$mailOk = Get-Status "http://localhost:5014/login"

if ($appOk -eq 200 -and $mailOk -eq 200) {
    Write-Host "App is ready at     http://localhost:5004"
    Write-Host "Mailbox is ready at http://localhost:5014"
    Write-Host ""
    Write-Host "Credentials:"
    Write-Host "  user  / password   (your account)"
    Write-Host "  admin / adminpass  (target, has 2FA)"
    Write-Host ""
    Write-Host "Mailbox accounts:"
    Write-Host "  user  / password"
    Write-Host "  admin / adminpass"
} else {
    Write-Host "ERROR: One or more services failed to start."
    if ($appOk  -ne 200) { Write-Host "  App (5004): not responding" }
    if ($mailOk -ne 200) { Write-Host "  Mailbox (5014): not responding" }
    Write-Host "Check logs with: docker compose logs"
}
