[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ApiDir = Join-Path $RepoRoot "apps\api"
$WebDir = Join-Path $RepoRoot "apps\web"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    throw "Local environment is missing. Run .\scripts\setup_windows.ps1 first."
}
if (-not (Test-Path (Join-Path $WebDir "node_modules"))) {
    throw "Frontend dependencies are missing. Run .\scripts\setup_windows.ps1 first."
}

Write-Host "Starting Formora in two terminal windows..." -ForegroundColor Cyan
$ApiCommand = "Set-Location '$ApiDir'; `$env:PYTHONPATH='$ApiDir'; & '$PythonPath' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$WebCommand = "Set-Location '$WebDir'; npm run dev"

Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $ApiCommand)
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $WebCommand)

Write-Host "`nAPI: http://localhost:8000/docs"
Write-Host "App: http://localhost:3000"
Write-Host "Close both terminal windows to stop Formora.`n"

