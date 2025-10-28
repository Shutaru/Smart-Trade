# setup.ps1 - Setup inicial do projeto Smart-Trade

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart-Trade - Initial Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ROOT = $PSScriptRoot

# Verificar Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Green
$PYTHON_VERSION = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ? $PYTHON_VERSION" -ForegroundColor Gray
} else {
    Write-Host "   ? Python não encontrado!" -ForegroundColor Red
    Write-Host "      Instale Python 3.10+ de https://python.org" -ForegroundColor Yellow
    exit 1
}

# Verificar Node.js
Write-Host "[2/5] Checking Node.js..." -ForegroundColor Green
$NODE_VERSION = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
  Write-Host "      ? Node $NODE_VERSION" -ForegroundColor Gray
} else {
    Write-Host "      ? Node.js não encontrado!" -ForegroundColor Red
    Write-Host "      Instale Node.js 18+ de https://nodejs.org" -ForegroundColor Yellow
    exit 1
}

# Criar virtual environment
Write-Host "[3/5] Setting up Python virtual environment..." -ForegroundColor Green
$VENV_PATH = Join-Path $ROOT ".venv"
if (-Not (Test-Path $VENV_PATH)) {
    Write-Host "      Creating .venv..." -ForegroundColor Gray
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      ? Failed to create venv" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      ? .venv já existe" -ForegroundColor Gray
}

# Instalar dependências Python
Write-Host "      Installing Python dependencies..." -ForegroundColor Gray
$PIP = Join-Path $VENV_PATH "Scripts\pip.exe"
& $PIP install -r requirements.txt -q
if ($LASTEXITCODE -eq 0) {
 Write-Host "      ? Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "      ? Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}

# Instalar dependências Node
Write-Host "[4/5] Installing Node.js dependencies..." -ForegroundColor Green
Push-Location (Join-Path $ROOT "webapp")
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ? Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "      ? Failed to install Node.js dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# Criar diretórios necessários
Write-Host "[5/5] Creating necessary directories..." -ForegroundColor Green
$DIRS = @("data", "data\db", "data\profiles", "data\config_snapshots", "artifacts")
foreach ($dir in $DIRS) {
    $path = Join-Path $ROOT $dir
    if (-Not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
        Write-Host "      Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "      ? Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor White
Write-Host "  1. Development: .\start-dev.ps1" -ForegroundColor Yellow
Write-Host "  2. Production:  .\start-prod.ps1" -ForegroundColor Yellow
Write-Host "  3. Stop:     .\stop-dev.ps1" -ForegroundColor Yellow
Write-Host ""
