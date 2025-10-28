# stop-dev.ps1 - Para todos os processos de desenvolvimento

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Parando Smart-Trade..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Parar uvicorn (backend)
Write-Host "[1/2] Parando backend (uvicorn)..." -ForegroundColor Yellow
$uvicorn_procs = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*" }
if ($uvicorn_procs) {
    $uvicorn_procs | ForEach-Object {
        Write-Host "Killing PID: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "[1/2] ? Backend stopped" -ForegroundColor Green
} else {
    Write-Host "[1/2] ? Nenhum processo uvicorn encontrado" -ForegroundColor Gray
}

Write-Host ""

# Parar Vite (frontend)
Write-Host "[2/2] Parando frontend (Vite)..." -ForegroundColor Yellow
$vite_procs = Get-Process | Where-Object { $_.ProcessName -like "*node*" -and $_.CommandLine -like "*vite*" }
if ($vite_procs) {
    $vite_procs | ForEach-Object {
        Write-Host "      Killing PID: $($_.Id)" -ForegroundColor Gray
     Stop-Process -Id $_.Id -Force
    }
    Write-Host "[2/2] ? Frontend stopped" -ForegroundColor Green
} else {
    Write-Host "[2/2] ? Nenhum processo Vite encontrado" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Todos os processos parados!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
