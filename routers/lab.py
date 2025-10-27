"""Router for Strategy Lab"""
from fastapi import APIRouter, HTTPException
from typing import List
import db_sqlite
from lab_schemas import (
    ExchangeListResponse, SymbolListResponse, IndicatorCatalogResponse,
    RunResponse, RunStatus, StrategyConfig, ValidateStrategyResponse
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