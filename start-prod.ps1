# start-prod.ps1 - Production Mode
# Build frontend and serve via FastAPI

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart-Trade - Production Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ROOT = $PSScriptRoot

# Check if virtual environment exists
$VENV_PATH = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-Not (Test-Path $VENV_PATH)) {
  Write-Host "[ERROR] Virtual environment not found in .venv" -ForegroundColor Red
  Write-Host "Run: python -m venv .venv" -ForegroundColor Yellow
  Write-Host "     .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
  exit 1
}

# Build frontend
Write-Host "[1/3] Building frontend..." -ForegroundColor Green
Push-Location (Join-Path $ROOT "webapp")

# npm ci (clean install) for production
if (Test-Path "package-lock.json") {
  Write-Host "   Running: npm ci" -ForegroundColor Gray
  npm ci --silent
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] npm ci failed" -ForegroundColor Red
    Pop-Location
    exit 1
  }
} else {
  Write-Host "      Running: npm install" -ForegroundColor Gray
  npm install --silent
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] npm install failed" -ForegroundColor Red
    Pop-Location
    exit 1
  }
}

Write-Host " Running: npm run build" -ForegroundColor Gray
npm run build
if ($LASTEXITCODE -ne 0) {
  Write-Host "[ERROR] npm run build failed" -ForegroundColor Red
  Pop-Location
  exit 1
}

Pop-Location
Write-Host "[1/3] ? Frontend build complete" -ForegroundColor Green
Write-Host ""

# Check if build was created
$DIST_PATH = Join-Path $ROOT "webapp\dist"
if (-Not (Test-Path $DIST_PATH)) {
  Write-Host "[ERROR] webapp/dist was not created" -ForegroundColor Red
  exit 1
}

# Count files in dist
$FILE_COUNT = (Get-ChildItem -Path $DIST_PATH -Recurse -File).Count
$DIST_SIZE = [math]::Round((Get-ChildItem -Path $DIST_PATH -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Host "[2/3] Build artifacts: $FILE_COUNT files ($DIST_SIZE MB)" -ForegroundColor Cyan
Write-Host ""

# Start production server
Write-Host "[3/3] Starting production server..." -ForegroundColor Green
Write-Host "      Host: 0.0.0.0" -ForegroundColor Gray
Write-Host "      Port: 8000" -ForegroundColor Gray
Write-Host "      Workers: 1 (FastAPI + SPA)" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Local:   http://localhost:8000" -ForegroundColor White
Write-Host "Network: http://0.0.0.0:8000" -ForegroundColor White
Write-Host "API:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run server (blocks until CTRL+C)
& $VENV_PATH -m uvicorn gui_server:app --host 0.0.0.0 --port 8000
