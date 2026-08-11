[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ApiDir = Join-Path $RepoRoot "apps\api"
$WebDir = Join-Path $RepoRoot "apps\web"
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "`nFormora local setup" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot`n"

if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.12 or newer is required. Install it from https://www.python.org/downloads/windows/"
}

$PythonLauncher = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
$PythonVersion = if ($PythonLauncher -eq "py") { & py -3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" } else { & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" }
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 or newer is required. The Python launcher could not select Python 3."
}
if ([version]$PythonVersion -lt [version]"3.12.0") {
    throw "Python 3.12 or newer is required. Found Python $PythonVersion."
}
Write-Host "[ok] Python $PythonVersion" -ForegroundColor Green

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js 20.9 or newer is required. Install the current LTS release from https://nodejs.org/"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Reinstall Node.js with npm enabled."
}
$NodeVersionText = (node --version).TrimStart("v")
if ([version]$NodeVersionText -lt [version]"20.9.0") {
    throw "Node.js 20.9 or newer is required. Found Node $NodeVersionText."
}
Write-Host "[ok] Node $NodeVersionText" -ForegroundColor Green

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python virtual environment..."
    if ($PythonLauncher -eq "py") { & py -3 -m venv $VenvDir } else { & python -m venv $VenvDir }
}

Write-Host "Installing backend dependencies..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "${ApiDir}[dev]"

Write-Host "Installing frontend dependencies..."
Push-Location $WebDir
try { npm install } finally { Pop-Location }

$EnvPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path $EnvPath)) {
    Copy-Item (Join-Path $RepoRoot ".env.example") $EnvPath
    Write-Host "[ok] Created .env with safe mock-mode defaults" -ForegroundColor Green
} else {
    Write-Host "[ok] Existing .env preserved" -ForegroundColor Green
}

$env:PYTHONPATH = $ApiDir
& $VenvPython (Join-Path $RepoRoot "scripts\generate_fixtures.py")
& $VenvPython (Join-Path $RepoRoot "scripts\init_db.py")

Write-Host "`nSetup complete." -ForegroundColor Green
Write-Host "Next: .\scripts\doctor.ps1"
Write-Host "Then: .\scripts\dev.ps1`n"
