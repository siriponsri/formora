[CmdletBinding()]
param()

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ApiDir = Join-Path $RepoRoot "apps\api"
$WebDir = Join-Path $RepoRoot "apps\web"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HasRequiredFailure = $false

function Required-Check([string]$Name, [bool]$Passed, [string]$Details) {
    if ($Passed) { Write-Host "[required:ok] $Name - $Details" -ForegroundColor Green }
    else {
        Write-Host "[required:fail] $Name - $Details" -ForegroundColor Red
        $script:HasRequiredFailure = $true
    }
}

function Optional-Check([string]$Name, [bool]$Passed, [string]$Details) {
    if ($Passed) { Write-Host "[optional:ok] $Name - $Details" -ForegroundColor Green }
    else { Write-Host "[optional:missing] $Name - $Details" -ForegroundColor Yellow }
}

Write-Host "`nFormora doctor`n" -ForegroundColor Cyan
Required-Check "Python environment" (Test-Path $PythonPath) "Run setup_windows.ps1 if missing"
$NodeAvailable = [bool](Get-Command node -ErrorAction SilentlyContinue)
$NodeSupported = $false
if ($NodeAvailable) {
    $NodeSupported = [version]((node --version).TrimStart("v")) -ge [version]"20.9.0"
}
Required-Check "Node.js" $NodeSupported "Node 20.9+ required"
Required-Check "Frontend dependencies" (Test-Path (Join-Path $WebDir "node_modules")) "npm dependencies"

if (Test-Path $PythonPath) {
    Push-Location $ApiDir
    try {
        $PythonVersionText = & $PythonPath -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
        Required-Check "Python version" ([version]$PythonVersionText -ge [version]"3.12.0") "Python 3.12+ required"
        & $PythonPath -c "import fastapi, docx, openpyxl, sqlalchemy; print('Backend imports succeeded')" *> $null
        Required-Check "Backend imports" ($LASTEXITCODE -eq 0) "FastAPI and Office libraries"
        $env:PYTHONPATH = $ApiDir
        & $PythonPath (Join-Path $RepoRoot "scripts\init_db.py") *> $null
        Required-Check "SQLite" ($LASTEXITCODE -eq 0) "Local metadata database is writable"
    } finally { Pop-Location }
}

$DataDir = Join-Path $RepoRoot "data"
try {
    $Probe = Join-Path $DataDir "doctor-probe.tmp"
    Set-Content -Path $Probe -Value "ok" -Encoding UTF8
    Remove-Item $Probe
    Required-Check "Data directory" $true "Writable local filesystem"
} catch {
    Required-Check "Data directory" $false $_.Exception.Message
}

$LibreOffice = Get-Command soffice -ErrorAction SilentlyContinue
if (-not $LibreOffice) { $LibreOffice = Get-Command libreoffice -ErrorAction SilentlyContinue }
if (-not $LibreOffice) {
    $CommonPath = "C:\Program Files\LibreOffice\program\soffice.exe"
    if (Test-Path $CommonPath) { $LibreOffice = $CommonPath }
}
Optional-Check "LibreOffice" ([bool]$LibreOffice) "Needed only for local PDF previews"

$EnvPath = Join-Path $RepoRoot ".env"
$TyphoonConfigured = $false
if (Test-Path $EnvPath) {
    $TyphoonConfigured = [bool](Select-String -Path $EnvPath -Pattern '^TYPHOON_API_KEY=.+$' -Quiet)
}
Optional-Check "Typhoon API key" $TyphoonConfigured "Not required while AI_PROVIDER=mock"

if ($HasRequiredFailure) {
    Write-Host "`nDoctor found a required setup problem.`n" -ForegroundColor Red
    exit 1
}
Write-Host "`nRequired checks passed. Optional items may remain missing in mock mode.`n" -ForegroundColor Green
