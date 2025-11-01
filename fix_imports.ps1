# Mass Import Update Script - Smart-Trade
# Updates all Python imports to reflect new modular structure

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " MASS IMPORT UPDATE - Smart-Trade" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# COMPLETE mapping of old -> new imports
$mappings = @{
    'from strategy_registry import' = 'from strategies.registry import'
    'from strategy import' = 'from strategies.core import'
    'from strategy_regime import' = 'from strategies.regime import'
    'from indicator_adapter import' = 'from strategies.adapter import'
    'from strategies_trend_following import' = 'from strategies.trend_following import'
    'from strategies_mean_reversion import' = 'from strategies.mean_reversion import'
    'from strategies_breakout import' = 'from strategies.breakout import'
    'from strategies_volume import' = 'from strategies.volume import'
    'from strategies_hybrid import' = 'from strategies.hybrid import'
    'from strategies_advanced import' = 'from strategies.advanced import'
    'from strategies_refinements import' = 'from strategies.refinements import'
    'from strategies_final import' = 'from strategies.final import'
    'from broker_futures_paper_v2 import' = 'from broker.paper_v2 import'
    'from broker_futures_paper import' = 'from broker.paper_v1 import'
    'from executor_bitget import' = 'from broker.bitget import'
 'from db_sqlite import' = 'from core.database import'
    'from features import' = 'from core.features import'
    'from indicators import' = 'from core.indicators import'
    'from sizing import' = 'from core.sizing import'
    'from metrics import' = 'from core.metrics import'
    'from strategy_optimizer import' = 'from optimization.optimizer import'
    'from portfolio_manager import' = 'from optimization.portfolio import'
    'from walkforward_validator import' = 'from optimization.walkforward import'
    'from lab_runner import' = 'from lab.runner import'
    'from lab_schemas import' = 'from lab.schemas import'
    'from lab_features import' = 'from lab.features import'
    'from lab_indicators import' = 'from lab.indicators import'
    'from lab_objective import' = 'from lab.objective import'
    'from lab_backtest_adapter import' = 'from lab.adapter import'
}

# Get Python files
$folders = @('strategies', 'backtesting', 'optimization', 'broker', 'core', 'ml', 'lab', 'discovery', 'server', 'backend')
$files = @()

foreach ($folder in $folders) {
    if (Test-Path $folder) {
        $files += Get-ChildItem -Path $folder -Filter *.py -Recurse
    }
}

Write-Host "Processing $($files.Count) files...`n" -ForegroundColor Yellow

$modified = 0
$total_changes = 0

foreach ($file in $files) {
    $content = Get-Content -Path $file.FullName -Raw
    $original = $content
    $changes = 0
    
    foreach ($old in $mappings.Keys) {
        if ($content -match [regex]::Escape($old)) {
        $content = $content -replace [regex]::Escape($old), $mappings[$old]
            $changes++
        }
    }
    
    if ($content -ne $original) {
 Set-Content -Path $file.FullName -Value $content -NoNewline
    $modified++
        $total_changes += $changes
     Write-Host "[OK] $($file.Name) - $changes changes" -ForegroundColor Green
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DONE: $modified files modified, $total_changes total changes" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
