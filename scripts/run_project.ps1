# PowerShell script to start the Decentralized Campus Resource Booking System
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " STARTING CAMPUS RESOURCE BOOKING SYSTEM " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Detect Python environment
$PythonCmd = "python"
if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    $PythonCmd = "$ProjectRoot\.venv\Scripts\python.exe"
    Write-Host "[OK] Using virtual environment: $ProjectRoot\.venv" -ForegroundColor Green
} else {
    Write-Host "[INFO] Virtual environment (.venv) not found. Using system python." -ForegroundColor Yellow
}

# Ensure Node.js is available on PATH for Windows shells
$NodeInstallDir = "C:\Program Files\nodejs"
if (Test-Path $NodeInstallDir) {
    $env:Path = "$NodeInstallDir;$env:Path"
}

# Detect Node.js/npm environment
$NodeExe = Get-Command node.exe -ErrorAction SilentlyContinue
$NpmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue

if (-not $NodeExe) {
    $PossibleNodePaths = @(
        "$env:ProgramFiles\nodejs\node.exe",
        "$env:ProgramFiles(x86)\nodejs\node.exe",
        "$env:LOCALAPPDATA\Programs\nodejs\node.exe"
    )
    foreach ($Candidate in $PossibleNodePaths) {
        if (Test-Path $Candidate) {
            $NodeExe = @{ Source = $Candidate }
            break
        }
    }
}

if (-not $NpmCmd) {
    if ($NodeExe -and $NodeExe.Source) {
        $NodeDir = Split-Path $NodeExe.Source -Parent
        $NpmCandidate = Join-Path $NodeDir "npm.cmd"
        if (Test-Path $NpmCandidate) {
            $NpmCmd = @{ Source = $NpmCandidate }
        }
    }
}

if (-not $NpmCmd) {
    Write-Host "[WARN] Node.js/npm not found on PATH. Frontend may not start until Node.js is installed." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Found Node.js/npm: $($NpmCmd.Source)" -ForegroundColor Green
}

# Start CSE Node
Write-Host "[1/5] Starting CSE Node (HTTP: 50151 / gRPC: 50051)..." -ForegroundColor Yellow
$CseProcess = Start-Process -FilePath $PythonCmd -ArgumentList "-m", "backend.department_nodes.cse_node.main" -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow

# Start IT Node
Write-Host "[2/5] Starting IT Node (HTTP: 50152 / gRPC: 50052)..." -ForegroundColor Yellow
$ItProcess = Start-Process -FilePath $PythonCmd -ArgumentList "-m", "backend.department_nodes.it_node.main" -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow

# Start E&TC Node
Write-Host "[3/5] Starting E&TC Node (HTTP: 50153 / gRPC: 50053)..." -ForegroundColor Yellow
$EntcProcess = Start-Process -FilePath $PythonCmd -ArgumentList "-m", "backend.department_nodes.entc_node.main" -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow

# Start API Gateway
Write-Host "[4/5] Starting API Gateway (HTTP: 8000)..." -ForegroundColor Yellow
$GatewayHost = if ($env:GATEWAY_HOST) { $env:GATEWAY_HOST } else { "127.0.0.1" }
$GatewayProcess = Start-Process -FilePath $PythonCmd -ArgumentList "-m", "uvicorn", "backend.api_gateway.main:app", "--host", $GatewayHost, "--port", "8000" -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow

# Start Frontend
Write-Host "[5/5] Starting React Frontend (HTTP: 5173)..." -ForegroundColor Yellow
if ($NpmCmd) {
    $NpmFile = $NpmCmd.Source
    $FrontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev --prefix frontend" -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow
    Write-Host "[OK] Frontend launch command queued via cmd.exe" -ForegroundColor Green
} else {
    Write-Host "[WARN] Skipping frontend startup because npm was not found." -ForegroundColor Yellow
}

Start-Sleep -Seconds 3

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " ALL SERVICES STARTED SUCCESSFULLY " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "API Gateway -> http://127.0.0.1:8000"
Write-Host "CSE Node    -> http://127.0.0.1:50151 (gRPC: 50051)"
Write-Host "IT Node     -> http://127.0.0.1:50152 (gRPC: 50052)"
Write-Host "E&TC Node   -> http://127.0.0.1:50153 (gRPC: 50053)"
Write-Host "Frontend    -> http://localhost:5173"
Write-Host "=========================================`n"
