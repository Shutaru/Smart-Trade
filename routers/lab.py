"""Router for Strategy Lab"""
from fastapi import APIRouter, HTTPException
from typing import List
import db_sqlite
from lab_schemas import (
    ExchangeListResponse, SymbolListResponse, IndicatorCatalogResponse,
    RunResponse, RunStatus, StrategyConfig, ValidateStrategyResponse,
    BackfillRequest, BackfillResponse, BackfillResult
)
from lab_indicators import get_indicator_catalog, get_indicator, validate_indicator_params

router = APIRouter(prefix="/api/lab", tags=["lab"])


@router.get("/exchanges", response_model=ExchangeListResponse)
async def get_exchanges():
    """Return list of supported exchanges"""
    return {"exchanges": ["bitget", "binance"]}


@router.get("/symbols", response_model=SymbolListResponse)
async def get_symbols(exchange: str = "bitget", market: str = "futures"):
    """
    Return list of USDT perpetual linear futures symbols
    
    Args:
        exchange: Exchange name (bitget or binance)
        market: Market type (futures)
    
    Returns:
        List of symbols like BTC/USDT:USDT, ETH/USDT:USDT
    
    Raises:
        400: Invalid exchange
        429: Rate limit exceeded
        503: Exchange unavailable or timeout
    """
    import ccxt
    from ccxt.base.errors import RateLimitExceeded, RequestTimeout, ExchangeNotAvailable, NetworkError
    
    try:
        # Initialize exchange
        if exchange == "bitget":
            ex = ccxt.bitget({"options": {"defaultType": "swap"}})
        elif exchange == "binance":
            ex = ccxt.binance({"options": {"defaultType": "future"}})
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported exchange: {exchange}. Supported: bitget, binance"
            )
        
        # Load markets with error handling
        try:
            markets = ex.load_markets()
        except RateLimitExceeded:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {exchange}. Please try again later."
            )
        except (RequestTimeout, NetworkError) as e:
            raise HTTPException(
                status_code=503,
                detail=f"Exchange {exchange} is temporarily unavailable: {str(e)}"
            )
        except ExchangeNotAvailable as e:
            raise HTTPException(
                status_code=503,
                detail=f"Exchange {exchange} is not available: {str(e)}"
            )
        
        # Filter: only USDT perpetual linear futures
        symbols = []
        for symbol, market_info in markets.items():
            is_perpetual = market_info.get("type") == "swap"
            is_linear = market_info.get("linear", True)
            is_usdt = "USDT" in symbol and (market_info.get("quote") == "USDT" or "/USDT" in symbol)
            is_active = market_info.get("active", True)
            
            if is_perpetual and is_linear and is_usdt and is_active:
                symbols.append(symbol)
        
        symbols.sort()
        
        if not symbols:
            raise HTTPException(
                status_code=404,
                detail=f"No USDT perpetual futures found for {exchange}"
            )
        
        return {"symbols": symbols}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error fetching symbols from {exchange}: {str(e)}"
        )


@router.get("/indicators", response_model=IndicatorCatalogResponse)
async def get_indicators():
    """Return indicators catalog"""
    from lab_schemas import IndicatorInfo
    
    catalog = get_indicator_catalog()
    indicators = []
    for ind in catalog:
        indicators.append(IndicatorInfo(
            id=ind["id"],
            name=ind["name"],
            params=ind["params"],
            supported_timeframes=ind["supported_timeframes"],
            description=ind["description"]
        ))
    return {"indicators": indicators}


@router.post("/strategy/validate", response_model=ValidateStrategyResponse)
async def validate_strategy(config: StrategyConfig):
    """
    Validate strategy configuration and return required features
    
    Checks:
    - Indicators exist and are valid
    - Timeframes are supported
    - Parameters are within valid ranges
    - Objective expression is safe
    - Exit rules are valid
    
    Returns:
    - valid: bool - Whether strategy is valid
    - features_required: List[str] - Required features (e.g., ['rsi_5m', 'ema_1h'])
    - errors: List[str] - Validation errors if any
    """
    from lab_objective import objective_evaluator
    
    errors = []
    features_required = set()
    
    try:
        # Validate objective expression
        valid, msg = objective_evaluator.validate(config.objective.expression)
        if not valid:
            errors.append(f"Invalid objective: {msg}")
        
        # Validate long side conditions
        for cond in config.long.entry_all + config.long.entry_any:
            indicator = get_indicator(cond.indicator)
            if not indicator:
                errors.append(f"Indicator '{cond.indicator}' not found")
                continue
            
            if cond.timeframe not in indicator["supported_timeframes"]:
                errors.append(
                    f"Timeframe '{cond.timeframe}' not supported for indicator '{cond.indicator}'. "
                    f"Supported: {indicator['supported_timeframes']}"
                )
            
            params_dict = {p.name: p.value for p in cond.params}
            valid, msg = validate_indicator_params(cond.indicator, params_dict)
            if not valid:
                errors.append(f"Long side: {msg}")
            
            features_required.add(f"{cond.indicator}_{cond.timeframe}")
            
            if cond.rhs_indicator:
                rhs_indicator = get_indicator(cond.rhs_indicator)
                if not rhs_indicator:
                    errors.append(f"RHS indicator '{cond.rhs_indicator}' not found")
                else:
                    rhs_params_dict = {p.name: p.value for p in cond.rhs_params}
                    valid, msg = validate_indicator_params(cond.rhs_indicator, rhs_params_dict)
                    if not valid:
                        errors.append(f"Long side RHS: {msg}")
                    
                    rhs_feature = f"{cond.rhs_indicator}_{cond.timeframe}"
                    features_required.add(rhs_feature)
        
        # Validate short side conditions
        for cond in config.short.entry_all + config.short.entry_any:
            indicator = get_indicator(cond.indicator)
            if not indicator:
                errors.append(f"Indicator '{cond.indicator}' not found")
                continue
            
            if cond.timeframe not in indicator["supported_timeframes"]:
                errors.append(
                    f"Timeframe '{cond.timeframe}' not supported for indicator '{cond.indicator}'. "
                    f"Supported: {indicator['supported_timeframes']}"
                )
            
            params_dict = {p.name: p.value for p in cond.params}
            valid, msg = validate_indicator_params(cond.indicator, params_dict)
            if not valid:
                errors.append(f"Short side: {msg}")
            
            features_required.add(f"{cond.indicator}_{cond.timeframe}")
            
            if cond.rhs_indicator:
                rhs_indicator = get_indicator(cond.rhs_indicator)
                if not rhs_indicator:
                    errors.append(f"RHS indicator '{cond.rhs_indicator}' not found")
                else:
                    rhs_params_dict = {p.name: p.value for p in cond.rhs_params}
                    valid, msg = validate_indicator_params(cond.rhs_indicator, rhs_params_dict)
                    if not valid:
                        errors.append(f"Short side RHS: {msg}")
                    
                    rhs_feature = f"{cond.rhs_indicator}_{cond.timeframe}"
                    features_required.add(rhs_feature)
        
        # Validate exit rules
        valid_exit_kinds = ["tp_sl_fixed", "atr_trailing", "chandelier", "bb_target", "time_exit"]
        for rule in config.long.exit_rules + config.short.exit_rules:
            if rule.kind not in valid_exit_kinds:
                errors.append(f"Invalid exit rule kind: '{rule.kind}'. Valid: {valid_exit_kinds}")
        
        # Validate risk parameters
        if isinstance(config.risk.leverage, tuple):
            if len(config.risk.leverage) != 2 or config.risk.leverage[0] > config.risk.leverage[1]:
                errors.append("Leverage tuple must be (min, max) with min <= max")
        elif config.risk.leverage <= 0:
            errors.append("Leverage must be positive")
        
        if config.risk.size_value <= 0:
            errors.append("Position size must be positive")
        
        if config.risk.max_concurrent_positions < 1:
            errors.append("Max concurrent positions must be at least 1")
        
        return ValidateStrategyResponse(
            valid=len(errors) == 0,
            features_required=sorted(list(features_required)),
            errors=errors
        )
    
    except Exception as e:
        return ValidateStrategyResponse(
            valid=False,
            features_required=[],
            errors=[f"Validation error: {str(e)}"]
        )


@router.post("/backfill", response_model=BackfillResponse)
async def backfill_data(request: BackfillRequest):
    """
    Backfill OHLCV data and calculate features
    
    For each symbol and timeframe:
    1. Fetch OHLCV data from exchange via CCXT
    2. Store in SQLite database
    3. Calculate technical indicators
    4. Store features in database
    
    Args:
        request: BackfillRequest with exchange, symbols, timeframes, date range
    
    Returns:
        BackfillResponse with counts of inserted candles and features per symbol/timeframe
    
    Raises:
        400: Invalid parameters
        429: Rate limit exceeded
        503: Exchange unavailable
    """
    import ccxt
    import pandas as pd
    from ccxt.base.errors import RateLimitExceeded, RequestTimeout, ExchangeNotAvailable, NetworkError
    from lab_features import calculate_features, features_to_rows
    
    try:
        # Initialize exchange
        if request.exchange == "bitget":
            ex = ccxt.bitget({"options": {"defaultType": "swap"}})
        elif request.exchange == "binance":
            ex = ccxt.binance({"options": {"defaultType": "future"}})
        else:
            raise HTTPException(400, f"Unsupported exchange: {request.exchange}")
        
        # Collect all timeframes to process
        all_timeframes = [request.timeframe] + request.higher_tf
        
        results = []
        total_candles = 0
        total_features = 0
        
        # Process each symbol
        for symbol in request.symbols:
            # Process each timeframe for this symbol
            for tf in all_timeframes:
                try:
                    # Fetch OHLCV data
                    all_candles = []
                    current_since = request.since
                    
                    while current_since < request.until:
                        try:
                            candles = ex.fetch_ohlcv(
                                symbol,
                                timeframe=tf,
                                since=current_since,
                                limit=1000
                            )
                        except RateLimitExceeded:
                            raise HTTPException(429, f"Rate limit exceeded for {request.exchange}")
                        except (RequestTimeout, NetworkError) as e:
                            raise HTTPException(503, f"Exchange temporarily unavailable: {str(e)}")
                        except ExchangeNotAvailable as e:
                            raise HTTPException(503, f"Exchange not available: {str(e)}")
                        
                        if not candles:
                            break
                        
                        all_candles.extend(candles)
                        current_since = candles[-1][0] + 1
                        
                        if len(candles) < 1000:
                            break
                    
                    # Filter candles within range
                    all_candles = [c for c in all_candles if request.since <= c[0] < request.until]
                    
                    if not all_candles:
                        results.append(BackfillResult(
                            symbol=symbol,
                            timeframe=tf,
                            candles_inserted=0,
                            features_inserted=0,
                            db_path="N/A"
                        ))
                        continue
                    
                    # Get database path and connection
                    db_path = db_sqlite.get_db_path(request.exchange, symbol, tf)
                    conn = db_sqlite.connect(db_path, tf)
                    
                    # Prepare candles for insertion: (ts, open, high, low, close, volume)
                    candle_rows = [
                        (int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5]))
                        for c in all_candles
                    ]
                    
                    # Insert candles
                    db_sqlite.insert_candles_bulk(conn, tf, candle_rows)
                    candles_inserted = len(candle_rows)
                    
                    # Calculate features
                    features_inserted = 0
                    try:
                        # Create DataFrame for feature calculation
                        df = pd.DataFrame(all_candles, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                        
                        # Calculate features
                        if len(df) >= 200:
                            features_df = calculate_features(df)
                            feature_rows = features_to_rows(features_df)
                            
                            # Insert features
                            db_sqlite.insert_features_bulk(conn, tf, feature_rows)
                            features_inserted = len(feature_rows)
                        else:
                            print(f"Warning: Not enough data for features ({len(df)} < 200 candles) for {symbol} {tf}")
                    
                    except Exception as e:
                        print(f"Warning: Feature calculation failed for {symbol} {tf}: {str(e)}")
                    
                    conn.close()
                    
                    # Add result
                    results.append(BackfillResult(
                        symbol=symbol,
                        timeframe=tf,
                        candles_inserted=candles_inserted,
                        features_inserted=features_inserted,
                        db_path=db_path
                    ))
                    
                    total_candles += candles_inserted
                    total_features += features_inserted
                
                except HTTPException:
                    raise
                except Exception as e:
                    # Continue with other symbols/timeframes on error
                    print(f"Error processing {symbol} {tf}: {str(e)}")
                    results.append(BackfillResult(
                        symbol=symbol,
                        timeframe=tf,
                        candles_inserted=0,
                        features_inserted=0,
                        db_path=f"Error: {str(e)}"
                    ))
        
        return BackfillResponse(
            success=True,
            message=f"Backfilled {len(request.symbols)} symbols across {len(all_timeframes)} timeframes",
            results=results,
            total_candles=total_candles,
            total_features=total_features
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Backfill error: {str(e)}")


@router.get("/runs", response_model=List[RunStatus])
async def list_runs(limit: int = 100):
    """List all runs"""
    conn = db_sqlite.connect_lab()
    runs = db_sqlite.get_all_runs(conn, limit)
    conn.close()
    
    result = []
    for run in runs:
        result.append(RunStatus(
            run_id=run["id"],
            status=run["status"],
            progress=0.0,
            started_at=run.get("started_at"),
            completed_at=run.get("completed_at")
        ))
    return result