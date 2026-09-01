# PowerShell script to stop all project background processes safely by port binding
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " STOPPING CAMPUS RESOURCE BOOKING SYSTEM " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$TargetPorts = @(8000, 50151, 50152, 50153, 50051, 50052, 50053, 5173)

$StoppedAny = $false
foreach ($Port in $TargetPorts) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($Connections) {
        foreach ($Conn in $Connections) {
            $ProcessId = $Conn.OwningProcess
            if ($ProcessId -and $ProcessId -ne 0) {
                try {
                    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
                    Write-Host "[STOPPED] Process ID $ProcessId listening on port $Port" -ForegroundColor Green
                    $StoppedAny = $true
                } catch {}
            }
        }
    }
}

if (-not $StoppedAny) {
    Write-Host "[INFO] No active processes found on project ports." -ForegroundColor Yellow
}

Write-Host "`nAll Campus Resource Booking System services stopped cleanly." -ForegroundColor Green
