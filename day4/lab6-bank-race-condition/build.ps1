Write-Host "============================================"
Write-Host "  Lab 6 - Bank Race Condition"
Write-Host "  Port: 5006"
Write-Host "============================================"

docker compose down -v 2>$null
docker compose up --build -d

Start-Sleep -Seconds 3

try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5006/" -UseBasicParsing -TimeoutSec 5
    $code = $resp.StatusCode
} catch {
    $code = 0
}

if ($code -eq 200) {
    Write-Host ""
    Write-Host "App is ready at http://localhost:5006"
    Write-Host "Create two accounts, each starts with `$100."
    Write-Host ""
} else {
    Write-Host "ERROR: App failed to start. Check 'docker compose logs'."
}
