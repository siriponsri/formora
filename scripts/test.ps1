[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ApiDir = Join-Path $RepoRoot "apps\api"
$WebDir = Join-Path $RepoRoot "apps\web"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    throw "Run .\scripts\setup_windows.ps1 before testing."
}

Write-Host "`n[1/5] Backend quality check" -ForegroundColor Cyan
& $PythonPath -m ruff check (Join-Path $RepoRoot "apps\api") (Join-Path $RepoRoot "scripts")

Write-Host "`n[2/5] Backend tests" -ForegroundColor Cyan
Push-Location $ApiDir
try { & $PythonPath -m pytest } finally { Pop-Location }

Write-Host "`n[3/5] Frontend lint" -ForegroundColor Cyan
Push-Location $WebDir
try {
    npm run lint
    Write-Host "`n[4/5] Frontend type check" -ForegroundColor Cyan
    npm run typecheck
    Write-Host "`n[5/5] Production build" -ForegroundColor Cyan
    npm run build
} finally { Pop-Location }

Write-Host "`nAll Formora checks passed.`n" -ForegroundColor Green
