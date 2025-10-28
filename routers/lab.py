"""Router for Strategy Lab"""
from fastapi import APIRouter, HTTPException
from typing import List
import os
import db_sqlite
from lab_schemas import (
    ExchangeListResponse, SymbolListResponse, IndicatorCatalogResponse,
    RunResponse, RunStatus, StrategyConfig, ValidateStrategyResponse,
    BackfillRequest, BackfillResponse, BackfillResult,
    RunResultsResponse, TrialResult
)
from lab_indicators import get_indicator_catalog, get_indicator, validate_indicator_params

router = APIRouter(prefix="/api/lab", tags=["lab"])


@router.get("/exchanges", response_model=ExchangeListResponse)
async def get_exchanges():
    """Return list of supported exchanges"""
    return {"exchanges": ["bitget", "binance"]}


@router.get("/symbols", response_model=SymbolListResponse)
async def get_symbols(exchange: str = "bitget", market: str = "futures"):
    """Return list of USDT perpetual linear futures symbols"""
    import ccxt
    from ccxt.base.errors import RateLimitExceeded, RequestTimeout, ExchangeNotAvailable, NetworkError
    
    try:
        if exchange == "bitget":
            ex = ccxt.bitget({"options": {"defaultType": "swap"}})
        elif exchange == "binance":
            ex = ccxt.binance({"options": {"defaultType": "future"}})
        else:
            raise HTTPException(400, f"Unsupported exchange: {exchange}")
        
        try:
            markets = ex.load_markets()
        except RateLimitExceeded:
            raise HTTPException(429, "Rate limit exceeded")
        except (RequestTimeout, NetworkError) as e:
            raise HTTPException(503, f"Exchange unavailable: {str(e)}")
        
        symbols = []
        for symbol, market_info in markets.items():
            is_perpetual = market_info.get("type") == "swap"
            is_linear = market_info.get("linear", True)
            is_usdt = "USDT" in symbol
            is_active = market_info.get("active", True)
            
            if is_perpetual and is_linear and is_usdt and is_active:
                symbols.append(symbol)
        
        symbols.sort()
        
        if not symbols:
            raise HTTPException(404, "No symbols found")
        
        return {"symbols": symbols}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/indicators", response_model=IndicatorCatalogResponse)
async def get_indicators():
    """Return indicators catalog"""
    from lab_schemas import IndicatorInfo
    
    catalog = get_indicator_catalog()
    indicators = [IndicatorInfo(**ind) for ind in catalog]
    return {"indicators": indicators}


@router.post("/strategy/validate", response_model=ValidateStrategyResponse)
async def validate_strategy(config: StrategyConfig):
    """Validate strategy configuration"""
    from lab_objective import objective_evaluator
    
    errors = []
    features_required = set()
    
    try:
        valid, msg = objective_evaluator.validate(config.objective.expression)
        if not valid:
            errors.append(f"Invalid objective: {msg}")
        
        for cond in config.long.entry_all + config.long.entry_any:
            indicator = get_indicator(cond.indicator)
            if not indicator:
                errors.append(f"Indicator '{cond.indicator}' not found")
                continue
            
            if cond.timeframe not in indicator["supported_timeframes"]:
                errors.append(f"Timeframe '{cond.timeframe}' not supported")
            
            features_required.add(f"{cond.indicator}_{cond.timeframe}")
            
            if cond.rhs_indicator:
                features_required.add(f"{cond.rhs_indicator}_{cond.timeframe}")
        
        for cond in config.short.entry_all + config.short.entry_any:
            indicator = get_indicator(cond.indicator)
            if not indicator:
                errors.append(f"Indicator '{cond.indicator}' not found")
                continue
            
            if cond.timeframe not in indicator["supported_timeframes"]:
                errors.append(f"Timeframe '{cond.timeframe}' not supported")
            
            features_required.add(f"{cond.indicator}_{cond.timeframe}")
            
            if cond.rhs_indicator:
                features_required.add(f"{cond.rhs_indicator}_{cond.timeframe}")
        
        return ValidateStrategyResponse(
            valid=len(errors) == 0,
            features_required=sorted(list(features_required)),
            errors=errors
        )
    
    except Exception as e:
        return ValidateStrategyResponse(valid=False, features_required=[], errors=[str(e)])


@router.post("/backfill", response_model=BackfillResponse)
async def backfill_data(request: BackfillRequest):
    """Backfill OHLCV data and calculate features - with progress logging"""
    import ccxt
    import pandas as pd
    import time
    from lab_features import calculate_features, features_to_rows
    
    try:
        ex = ccxt.bitget({"options": {"defaultType": "swap"}}) if request.exchange == "bitget" else ccxt.binance({"options": {"defaultType": "future"}})
        
        all_timeframes = [request.timeframe] + request.higher_tf
        results = []
        total_candles = 0
        total_features = 0
        
        for symbol in request.symbols:
            for tf in all_timeframes:
                try:
                    print(f"[Backfill] Starting {symbol} @ {tf}...")
                    start_time = time.time()
                    api_calls = 0
                    
                    all_candles = []
                    current_since = request.since
                    
                    while current_since < request.until:
                        candles = ex.fetch_ohlcv(symbol, timeframe=tf, since=current_since, limit=1000)
                        api_calls += 1
                        
                        if not candles:
                            break
                        all_candles.extend(candles)
                        current_since = candles[-1][0] + 1
                        if len(candles) < 1000:
                            break
                    
                    all_candles = [c for c in all_candles if request.since <= c[0] < request.until]
                    
                    elapsed = time.time() - start_time
                    print(f"[Backfill] {symbol} @ {tf}: {len(all_candles)} candles in {elapsed:.1f}s ({api_calls} API calls)")
                    
                    if not all_candles:
                        results.append(BackfillResult(symbol=symbol, timeframe=tf, candles_inserted=0, features_inserted=0, db_path="N/A"))
                        continue
                    
                    db_path = db_sqlite.get_db_path(request.exchange, symbol, tf)
                    conn = db_sqlite.connect(db_path, tf)
                    
                    candle_rows = [(int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])) for c in all_candles]
                    db_sqlite.insert_candles_bulk(conn, tf, candle_rows)
                    candles_inserted = len(candle_rows)
                    
                    features_inserted = 0
                    if len(candle_rows) >= 200:
                        try:
                            df = pd.DataFrame(all_candles, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                            features_df = calculate_features(df)
                            feature_rows = features_to_rows(features_df)
                            db_sqlite.insert_features_bulk(conn, tf, feature_rows)
                            features_inserted = len(feature_rows)
                            print(f"[Backfill] Calculated {features_inserted} features")
                        except Exception as e:
                            print(f"[Backfill] Feature calc error: {e}")
                    
                    conn.close()
                    
                    results.append(BackfillResult(symbol=symbol, timeframe=tf, candles_inserted=candles_inserted, features_inserted=features_inserted, db_path=db_path))
                    total_candles += candles_inserted
                    total_features += features_inserted
                
                except Exception as e:
                    import traceback
                    print(f"[Backfill] ERROR for {symbol} @ {tf}: {e}")
                    traceback.print_exc()
                    results.append(BackfillResult(symbol=symbol, timeframe=tf, candles_inserted=0, features_inserted=0, db_path=f"Error: {e}"))
        
        success_count = sum(1 for r in results if r.candles_inserted > 0)
        message = f"Backfilled {success_count}/{len(results)} combinations"
        print(f"[Backfill] Complete: {total_candles} candles, {total_features} features")
        
        return BackfillResponse(success=True, message=message, results=results, total_candles=total_candles, total_features=total_features)
    
    except Exception as e:
        raise HTTPException(500, f"Backfill error: {str(e)}")


@router.post("/run/backtest", response_model=RunResponse)
async def run_backtest(config: StrategyConfig):
    """Start a backtest run asynchronously"""
    from lab_runner import start_backtest_run
    
    try:
        run_id = start_backtest_run(config)
        return RunResponse(run_id=run_id, status="pending")
    except Exception as e:
        raise HTTPException(500, f"Failed to start backtest: {str(e)}")


@router.post("/run/grid", response_model=RunResponse)
async def run_grid_search(config: StrategyConfig):
    """Start a grid search optimization run asynchronously"""
    from lab_runner import start_grid_search_run
    
    try:
        if not config.param_space or len(config.param_space) == 0:
            raise HTTPException(400, "Grid search requires param_space to be defined")
        
        run_id = start_grid_search_run(config)
        return RunResponse(run_id=run_id, status="pending")
    except Exception as e:
        raise HTTPException(500, f"Failed to start grid search: {str(e)}")


@router.post("/run/optuna", response_model=RunResponse)
async def run_optuna_optimization(config: StrategyConfig, n_trials: int = 100):
    """Start an Optuna Bayesian optimization run asynchronously"""
    from lab_runner import start_optuna_run
    
    try:
        if not config.param_space or len(config.param_space) == 0:
            raise HTTPException(400, "Optuna requires param_space to be defined")
 
        run_id = start_optuna_run(config, n_trials=n_trials)
        return RunResponse(run_id=run_id, status="pending")
    except Exception as e:
        raise HTTPException(500, f"Failed to start Optuna: {str(e)}")


@router.get("/run/{run_id}/status", response_model=RunStatus)
async def get_run_status_endpoint(run_id: str):
    """Get status of a running or completed backtest"""
    from lab_runner import get_run_status
    
    status = get_run_status(run_id)
    if not status:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    return RunStatus(        run_id=status['run_id'],
        status=status['status'],
        progress=status['progress'],
        current_trial=status.get('current_trial'),
        total_trials=status.get('total_trials'),
        best_score=status.get('best_score'),
        started_at=status.get('started_at'),
        completed_at=status.get('completed_at')
    )


@router.get("/run/{run_id}/results")
async def get_run_results_endpoint(run_id: str, limit: int = 100, offset: int = 0):
    """Get results (trials) for a completed run"""
    from lab_runner import get_run_results
    
    try:
        # get_run_results j� retorna dicts parsed
        results = get_run_results(run_id, limit, offset)
        
        # Criar TrialResult objects diretamente dos results
        trials = []
        for r in results:
            try:
                # Remove _stats from metrics (nested dict n�o � compat�vel com Pydantic)
                metrics = r['metrics'].copy()
                if '_stats' in metrics:
                    del metrics['_stats']
                
                trials.append(TrialResult(
                    trial_id=r['trial_id'],
                    params=r['params'],
                    metrics=metrics,  # Agora sem _stats
                    score=r['score']
                ))
            except Exception as e:
                print(f"[get_run_results_endpoint] Error creating TrialResult: {e}")
                # Skip malformed trial
                continue
        
        return RunResultsResponse(run_id=run_id, trials=trials, total=len(trials))
    
    except Exception as e:
        import traceback
        print(f"[get_run_results_endpoint] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Failed to get results: {str(e)}")


@router.get("/run/{run_id}/candles")
async def get_run_candles(run_id: str):
    """Get OHLCV candles for the backtest period"""
    import sqlite3
    import json
    
    conn_lab = db_sqlite.connect_lab()
    run = db_sqlite.get_run(conn_lab, run_id)
    conn_lab.close()

    if not run:
        raise HTTPException(404, "Run not found")
    
    config = json.loads(run['config_json'])
    data_spec = config.get('data', {})
    exchange = data_spec.get('exchange', 'bitget')
    symbols = data_spec.get('symbols', ['BTC/USDT:USDT'])  # Default to BTC
    timeframe = data_spec.get('timeframe', '5m')
    since = data_spec.get('since')
    until = data_spec.get('until')
    
    if not symbols:
        symbols = ['BTC/USDT:USDT']  # Fallback
    
    symbol = symbols[0]
    db_path = db_sqlite.get_db_path(exchange, symbol, timeframe)
    
    if not os.path.exists(db_path):
        # Return mock data se DB n�o existe
        import time
        now = int(time.time())
        mock_candles = []
        for i in range(100):
            ts = (now - (100-i) * 300) * 1000  # 5min bars
            price = 42000 + (i * 10) + (i % 10) * 5
            mock_candles.append({
                'time': int(ts / 1000),
                'open': price,
                'high': price + 50,
                'low': price - 50,
                'close': price + 10,
                'volume': 100 + i
            })
        return {'symbol': symbol, 'timeframe': timeframe, 'candles': mock_candles}
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    table = db_sqlite.get_candles_table(timeframe)
    
    if since and until:
        cur.execute(f"SELECT ts, open, high, low, close, volume FROM {table} WHERE ts >= ? AND ts < ? ORDER BY ts ASC", (since, until))
    else:
        cur.execute(f"SELECT ts, open, high, low, close, volume FROM {table} ORDER BY ts ASC LIMIT 5000")
    
    rows = cur.fetchall()
    conn.close()
    
    candles = [{'time': int(r[0] / 1000), 'open': float(r[1]), 'high': float(r[2]), 'low': float(r[3]), 'close': float(r[4]), 'volume': float(r[5])} for r in rows]
    return {'symbol': symbol, 'timeframe': timeframe, 'candles': candles}


@router.get("/run/{run_id}/equity")
async def get_run_equity(run_id: str):
    """Get equity curve data"""
    import csv
    import glob
    import json
    from datetime import datetime
    
    pattern = os.path.join("artifacts", run_id, "*", "equity.csv")
    equity_files = glob.glob(pattern)
    
    if not equity_files:
        trades_pattern = os.path.join("artifacts", run_id, "*", "trades.csv")
        trades_files = glob.glob(trades_pattern)
        
        if not trades_files:
            raise HTTPException(404, "No equity or trades data found")
        
        trades = []
        with open(trades_files[0], 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append({'exit_time': row['exit_time'], 'pnl': float(row['pnl'])})
        
        trades.sort(key=lambda x: datetime.fromisoformat(x['exit_time'])),
  
        equity_data = []
        cumulative = 0.0
        max_equity = 0.0
        
        for trade in trades:
            cumulative += trade['pnl']
            max_equity = max(max_equity, cumulative)
            drawdown = ((cumulative - max_equity) / max(abs(max_equity), 1)) * 100 if max_equity > 0 else 0
            timestamp = int(datetime.fromisoformat(trade['exit_time']).timestamp())
            equity_data.append({'time': timestamp, 'equity': cumulative, 'drawdown': drawdown})
        
        return {'equity': equity_data}
    
    equity_path = equity_files[0]
    equity_data = []
    
    try:
        with open(equity_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = int(datetime.fromisoformat(row['timestamp']).timestamp())
                equity_data.append({'time': timestamp, 'equity': float(row['equity']), 'drawdown': float(row.get('drawdown', 0))})
    except Exception as e:
        raise HTTPException(500, f"Error reading equity: {str(e)}")
    
    return {'equity': equity_data}


@router.get("/run/{run_id}/artifacts/trades")
async def get_run_trades(run_id: str):
    """Get trades from artifacts for a run"""
    import csv
    import glob
    from datetime import datetime
    
    pattern = os.path.join("artifacts", run_id, "*", "trades.csv")
    trades_files = glob.glob(pattern)
    
    if not trades_files:
        return {"trades": []}
    
    trades_path = trades_files[0]
    trades = []
    
    try:
        with open(trades_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Process broker format: group actions by position
            position_map = {}
            
            for row in reader:
                try:
                    action = row.get('action', '')
                    side = row.get('side', 'UNKNOWN')
                    ts_ms = int(row.get('ts_utc', 0))
                    ts_iso = datetime.fromtimestamp(ts_ms / 1000).isoformat() if ts_ms else ''
                    price = float(row.get('price', 0))
                    pnl = float(row.get('pnl', 0))
                    
                    # Handle OPEN actions
                    if 'OPEN' in action:
                        position_map[side] = {
                            'entry_time': ts_iso,
                            'entry_price': price,
                            'side': side,
                            'exit_time': None,
                            'exit_price': None,
                            'pnl': 0.0,
                            'pnl_pct': 0.0
                        }
                    
                    # Handle CLOSE actions (TP, STOP, etc)
                    elif side in position_map and ('TP' in action or 'STOP' in action or 'EXIT' in action):
                        pos = position_map[side]
                        pos['exit_time'] = ts_iso
                        pos['exit_price'] = price
                        pos['pnl'] += pnl
                        
                        # Calculate pnl_pct
                        if pos['entry_price'] and pos['entry_price'] > 0:
                            if side == 'LONG':
                                pos['pnl_pct'] = ((price - pos['entry_price']) / pos['entry_price']) * 100
                            else:
                                pos['pnl_pct'] = ((pos['entry_price'] - price) / pos['entry_price']) * 100
                        
                        # Add completed trade
                        if 'FULL' in action or 'STOP' in action or 'TIME_STOP' in action or 'MANUAL' in action:
                            trades.append(pos.copy())
                            del position_map[side]
                
                except (ValueError, KeyError) as e:
                    print(f"[get_run_trades] Skipping malformed row: {e}")
                    continue
        
        return {"trades": trades}
    
    except FileNotFoundError:
        return {"trades": []}
    except Exception as e:
        import traceback
        print(f"[get_run_trades] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Error reading trades: {str(e)}")
    
    return {"trades": trades}


@router.get("/runs", response_model=List[RunStatus])
async def list_runs(limit: int = 100):
    """List all runs"""
    conn = db_sqlite.connect_lab()
    runs = db_sqlite.get_all_runs(conn, limit)
    conn.close()
    
    return [RunStatus(run_id=run["id"], status=run["status"], progress=0.0, started_at=run.get("started_at"), completed_at=run.get("completed_at")) for run in runs]


@router.get("/run/{run_id}/download")
async def download_artifacts(run_id: str):
    """Download all artifacts as a ZIP file"""
    import glob
    import zipfile
    import tempfile
    from fastapi.responses import FileResponse
    
    artifacts_pattern = os.path.join("artifacts", run_id, "*", "*")
    artifact_files = glob.glob(artifacts_pattern)
    
    if not artifact_files:
        raise HTTPException(404, "No artifacts found for this run")
    
    # Create temporary ZIP file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        zip_path = tmp_file.name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in artifact_files:
                # Add file to ZIP with relative path
                arcname = os.path.relpath(file_path, os.path.join("artifacts", run_id))
                zipf.write(file_path, arcname)
  
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f'artifacts_{run_id[:8]}.zip',
            headers={"Content-Disposition": f"attachment; filename=artifacts_{run_id[:8]}.zip"}
        )


@router.post("/compare")
async def compare_runs(run_ids: List[str]):
    """Compare multiple runs - returns equity curves for overlay"""
    import csv
    import glob
    from datetime import datetime
    
    if len(run_ids) > 10:
        raise HTTPException(400, "Maximum 10 runs can be compared at once")
    
    comparison_data = []
    
    for run_id in run_ids:
        # Get run info
        conn_lab = db_sqlite.connect_lab()
        run = db_sqlite.get_run(conn_lab, run_id)
        conn_lab.close()
        
        if not run:
            continue
        
        # Get equity data
        pattern = os.path.join("artifacts", run_id, "*", "equity.csv")
        equity_files = glob.glob(pattern)
      
        if not equity_files:
            # Try to generate from trades
            trades_pattern = os.path.join("artifacts", run_id, "*", "trades.csv")
            trades_files = glob.glob(trades_pattern)
         
            if not trades_files:
                continue
  
            trades = []
            with open(trades_files[0], 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trades.append({'exit_time': row['exit_time'], 'pnl': float(row['pnl'])})
     
            trades.sort(key=lambda x: datetime.fromisoformat(x['exit_time']))
           
            equity_data = []
            cumulative = 0.0
     
            for trade in trades:
                cumulative += trade['pnl']
                timestamp = int(datetime.fromisoformat(trade['exit_time']).timestamp())
                equity_data.append({'time': timestamp, 'equity': cumulative})
        else:
            equity_path = equity_files[0]
            equity_data = []
 
            try:
                with open(equity_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        timestamp = int(datetime.fromisoformat(row['timestamp']).timestamp())
                        equity_data.append({'time': timestamp, 'equity': float(row['equity'])})
            except Exception:
                continue
        
        # Get final metrics
        trials = db_sqlite.get_run_trials(conn_lab, run_id, limit=1)
        final_metrics = trials[0]['metrics_json'] if trials else {}
        
        comparison_data.append({
            'run_id': run_id,
            'name': run['name'],
            'equity': equity_data,
            'metrics': final_metrics,
            'status': run['status']
        })
    
    return {'runs': comparison_data}