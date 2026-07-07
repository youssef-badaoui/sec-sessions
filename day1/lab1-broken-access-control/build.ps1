Write-Host "========================================="
Write-Host "  Lab 1 - Broken Access Control (Wallet)"
Write-Host "  Port: 5009"
Write-Host "========================================="
Write-Host ""
Write-Host "Building and starting containers..."
docker compose down -v 2>$null
docker compose up --build -d

Write-Host ""
Write-Host "Waiting for app to start..."
Start-Sleep -Seconds 3

try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5009/" -UseBasicParsing -TimeoutSec 5
    $code = $resp.StatusCode
} catch {
    $code = 0
}

if ($code -eq 200) {
    Write-Host "App is ready at http://localhost:5009"
    Write-Host ""
    Write-Host "Credentials:"
    Write-Host "  admin / admin123"
    Write-Host "  user  / user123"
    Write-Host ""
    Write-Host "Walkthrough:"
    Write-Host "  walkthrough.html"
} else {
    Write-Host "ERROR: App failed to start. Check logs with: docker compose logs"
}
