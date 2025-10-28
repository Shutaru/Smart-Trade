# start-dev.ps1 - Desenvolvimento com hot-reload
# Inicia backend (FastAPI) e frontend (Vite) em paralelo

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart-Trade - Development Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ROOT = $PSScriptRoot

# Verificar se virtual environment existe
$VENV_PATH = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-Not (Test-Path $VENV_PATH)) {
  Write-Host "[ERROR] Virtual environment não encontrado em .venv" -ForegroundColor Red
    Write-Host "Execute: python -m venv .venv" -ForegroundColor Yellow
    Write-Host "         .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
exit 1
}

# Verificar se node_modules existe
$NODE_MODULES = Join-Path $ROOT "webapp\node_modules"
if (-Not (Test-Path $NODE_MODULES)) {
    Write-Host "[INFO] node_modules não encontrado. Instalando dependências..." -ForegroundColor Yellow
    Push-Location (Join-Path $ROOT "webapp")
    npm install
    Pop-Location
}

Write-Host "[INFO] Iniciando backend (FastAPI com uvicorn --reload)..." -ForegroundColor Green
Write-Host "     URL: http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host ""

# Iniciar backend em nova janela
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ROOT'; & '$VENV_PATH' -m uvicorn gui_server:app --host 127.0.0.1 --port 8000 --reload"
) -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "[INFO] Iniciando frontend (Vite dev server)..." -ForegroundColor Green
Write-Host "    URL: http://localhost:5173" -ForegroundColor Gray
Write-Host ""

# Iniciar frontend em nova janela
Start-Process powershell -ArgumentList @(
  "-NoExit",
    "-Command",
  "cd '$ROOT\webapp'; npm run dev"
) -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Servidores iniciados!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Pressione CTRL+C nas janelas para parar" -ForegroundColor Yellow
Write-Host ""
