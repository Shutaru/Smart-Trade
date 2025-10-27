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
async def get_symbols(exchange: str = "bitget"):
  """Return list of symbols"""
    return {"symbols": ["BTC/USDT:USDT", "ETH/USDT:USDT"]}


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
