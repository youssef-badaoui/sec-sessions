Write-Host "============================================"
Write-Host "  Lab 5 - Store Price Manipulation"
Write-Host "  Port: 5005"
Write-Host "============================================"

docker compose down -v 2>$null
docker compose up --build -d

Start-Sleep -Seconds 3

try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5005/login" -UseBasicParsing -TimeoutSec 5
    $code = $resp.StatusCode
} catch {
    $code = 0
}

if ($code -eq 200) {
    Write-Host ""
    Write-Host "App is ready at http://localhost:5005"
    Write-Host "Create an account - you start with `$200 store credit."
    Write-Host ""
} else {
    Write-Host "ERROR: App failed to start. Check 'docker compose logs'."
}
