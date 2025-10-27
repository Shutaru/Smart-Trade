"""Router for Strategy Lab"""
from fastapi import APIRouter, HTTPException
from typing import List
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
    """Backfill OHLCV data and calculate features"""
    import ccxt
    import pandas as pd
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
                    all_candles = []
                    current_since = request.since
                    
                    while current_since < request.until:
                        candles = ex.fetch_ohlcv(symbol, timeframe=tf, since=current_since, limit=1000)
                        if not candles:
                            break
                        all_candles.extend(candles)
                        current_since = candles[-1][0] + 1
                        if len(candles) < 1000:
                            break
                    
                    all_candles = [c for c in all_candles if request.since <= c[0] < request.until]
                    
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
                        except Exception as e:
                            print(f"Feature calc error: {e}")
                    
                    conn.close()
                    
                    results.append(BackfillResult(symbol=symbol, timeframe=tf, candles_inserted=candles_inserted, features_inserted=features_inserted, db_path=db_path))
                    total_candles += candles_inserted
                    total_features += features_inserted
                
                except Exception as e:
                    results.append(BackfillResult(symbol=symbol, timeframe=tf, candles_inserted=0, features_inserted=0, db_path=f"Error: {e}"))
        
        return BackfillResponse(success=True, message=f"Backfilled {len(request.symbols)} symbols", results=results, total_candles=total_candles, total_features=total_features)
    
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


@router.get("/run/{run_id}/status", response_model=RunStatus)
async def get_run_status_endpoint(run_id: str):
    """Get status of a running or completed backtest"""
    from lab_runner import get_run_status
    
    status = get_run_status(run_id)
    if not status:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    return RunStatus(
        run_id=status['run_id'],
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
        results = get_run_results(run_id, limit, offset)
        trials = [TrialResult(trial_id=r['trial_id'], params=r['params'], metrics=r['metrics'], score=r['score']) for r in results]
        return RunResultsResponse(run_id=run_id, trials=trials, total=len(trials))
    except Exception as e:
        raise HTTPException(500, f"Failed to get results: {str(e)}")


@router.get("/runs", response_model=List[RunStatus])
async def list_runs(limit: int = 100):
    """List all runs"""
    conn = db_sqlite.connect_lab()
    runs = db_sqlite.get_all_runs(conn, limit)
    conn.close()
    
    return [RunStatus(run_id=run["id"], status=run["status"], progress=0.0, started_at=run.get("started_at"), completed_at=run.get("completed_at")) for run in runs]