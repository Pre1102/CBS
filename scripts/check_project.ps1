# PowerShell script to perform health check across all project services
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " CAMPUS RESOURCE BOOKING SYSTEM " -ForegroundColor Cyan
Write-Host " FINAL HEALTH CHECK " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Check-Endpoint($Name, $Url) {
    try {
        $Response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            Write-Host ("{0,-20} {1}" -f $Name, "ONLINE") -ForegroundColor Green
            return $true
        } else {
            Write-Host ("{0,-20} {1}" -f $Name, "OFFLINE") -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host ("{0,-20} {1}" -f $Name, "OFFLINE") -ForegroundColor Red
        return $false
    }
}

$gw   = Check-Endpoint "API Gateway" "http://127.0.0.1:8000/api/health"
$cse  = Check-Endpoint "CSE Node" "http://127.0.0.1:50151/health"
$it   = Check-Endpoint "IT Node" "http://127.0.0.1:50152/health"
$entc = Check-Endpoint "E&TC Node" "http://127.0.0.1:50153/health"
$fe   = Check-Endpoint "Frontend" "http://localhost:5173"

Write-Host "========================================" -ForegroundColor Cyan

if ($gw -and $cse -and $it -and $entc -and $fe) {
    Write-Host "All required services are running." -ForegroundColor Green
} else {
    Write-Host "Some services are offline. Run .\scripts\run_project.ps1 to start." -ForegroundColor Yellow
}
Write-Host "========================================`n"
