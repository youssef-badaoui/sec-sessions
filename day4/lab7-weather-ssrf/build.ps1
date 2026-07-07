Write-Host "============================================"
Write-Host "  Lab 7 - Weather SSRF"
Write-Host "  App:   http://localhost:5008"
Write-Host "  Files: http://files:7777 (internal only)"
Write-Host "============================================"

docker compose down -v 2>$null
docker compose up --build -d

Start-Sleep -Seconds 3

try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5008/" -UseBasicParsing -TimeoutSec 5
    $appOk = $resp.StatusCode
} catch {
    $appOk = 0
}

if ($appOk -eq 200) {
    Write-Host ""
    Write-Host "App is ready at http://localhost:5008"
    Write-Host "The internal file service is on the backend network and is NOT"
    Write-Host "exposed to the host. Reach it through the SSRF in the weather form."
    Write-Host ""
} else {
    Write-Host "ERROR: App failed to start. Check 'docker compose logs'."
    Write-Host "  App status: $appOk"
}
