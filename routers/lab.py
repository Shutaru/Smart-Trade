"""Router for Strategy Lab"""
from fastapi import APIRouter, HTTPException
from typing import List
import db_sqlite
from lab_schemas import ExchangeListResponse, SymbolListResponse, IndicatorCatalogResponse, RunResponse, RunStatus
from lab_indicators import get_indicator_catalog

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
            # Check if it's a perpetual swap
            is_perpetual = market_info.get("type") == "swap"
            
            # Check if it's linear (not inverse)
            is_linear = market_info.get("linear", True)
            
            # Check if it's USDT quoted
            is_usdt = (
                "USDT" in symbol and
                (market_info.get("quote") == "USDT" or "/USDT" in symbol)
            )
            
            # Check if it's active
            is_active = market_info.get("active", True)
            
            if is_perpetual and is_linear and is_usdt and is_active:
                symbols.append(symbol)
        
        # Sort alphabetically
        symbols.sort()
        
        if not symbols:
            raise HTTPException(
                status_code=404,
                detail=f"No USDT perpetual futures found for {exchange}"
            )
        
        return {"symbols": symbols}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error fetching symbols from {exchange}: {str(e)}"
        )


@router.get("/indicators", response_model=IndicatorCatalogResponse)
async def get_indicators():
    """Return indicators catalog"""
    from lab_indicators import get_indicator_catalog
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