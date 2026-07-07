Write-Host "========================================="
Write-Host "  Lab 4B - Reset Link Host Header Poisoning"
Write-Host "  App Port: 5007  |  Mailbox Port: 5017"
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

$appOk  = Get-Status "http://localhost:5007/login"
$mailOk = Get-Status "http://localhost:5017/login"

if ($appOk -eq 200 -and $mailOk -eq 200) {
    Write-Host "App is ready at     http://localhost:5007"
    Write-Host "Mailbox is ready at http://localhost:5017"
    Write-Host ""
    Write-Host "Credentials:"
    Write-Host "  user  / password         (your account)"
    Write-Host "  admin / unknownpassword  (target)"
    Write-Host ""
    Write-Host "Mailbox accounts:"
    Write-Host "  user  / password"
    Write-Host "  admin / unknownpassword"
} else {
    Write-Host "ERROR: One or more services failed to start."
    if ($appOk  -ne 200) { Write-Host "  App (5007): not responding" }
    if ($mailOk -ne 200) { Write-Host "  Mailbox (5017): not responding" }
    Write-Host "Check logs with: docker compose logs"
}
