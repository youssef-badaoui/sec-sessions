Write-Host "========================================="
Write-Host "  Lab 1 - Stored XSS"
Write-Host "  Port: 5001"
Write-Host "========================================="
Write-Host ""
Write-Host "Building and starting containers..."
docker compose down -v 2>$null
docker compose up --build -d

Write-Host ""
Write-Host "Waiting for app to start..."
Start-Sleep -Seconds 3

try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5001/login" -UseBasicParsing -TimeoutSec 5
    $code = $resp.StatusCode
} catch {
    $code = 0
}

if ($code -eq 200) {
    Write-Host "App is ready at http://localhost:5001"
    Write-Host ""
    Write-Host "Credentials:"
    Write-Host "  user  / password"
    Write-Host "  admin / adminpass"
    Write-Host ""
    Write-Host "Useful URLs:"
    Write-Host "  http://localhost:5001/board     - Comment board"
    Write-Host "  http://localhost:5001/admin/dashboard - Admin-only page"
    Write-Host "  walkthrough.html                - Standalone lab walkthrough"
} else {
    Write-Host "ERROR: App failed to start. Check logs with: docker compose logs"
}
