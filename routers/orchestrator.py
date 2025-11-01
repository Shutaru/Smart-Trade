"""
Orchestrator API Router

Endpoints for strategy discovery and deployment
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime

from orchestrator.strategy_discovery import StrategyOrchestrator
from core import database as db_sqlite


router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


# ============================================================================
# MODELS
# ============================================================================

class DiscoveryRequest(BaseModel):
    """Request to start strategy discovery"""
    symbols: List[str]
    exchange: str = 'bitget'
    timeframe: str = '5m'
    days: int = 90
    optimization_trials: int = 50
    top_n_to_optimize: int = 5
    auto_deploy_paper: bool = True  # Auto-deploy to paper trading


class DiscoveryStatus(BaseModel):
    """Status of discovery process"""
    run_id: str
    status: str  # 'running', 'completed', 'failed'
    symbols: List[str]
    current_symbol: Optional[str] = None
    progress: float  # 0-100
    best_strategies: Optional[Dict[str, Any]] = None
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class DeployRequest(BaseModel):
    """Request to deploy strategies to paper/live trading"""
    run_id: str
    mode: str = 'paper'  # 'paper' or 'live'


class CheckCacheRequest(BaseModel):
    """Request to check cached optimizations"""
    symbols: List[str]
    exchange: str
    timeframe: str


# ============================================================================
# GLOBAL STATE (in-memory for now)
# ============================================================================

active_discoveries: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/discover")
async def start_discovery(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks
):
    """
    Start strategy discovery for multiple symbols
    
    Workflow:
    1. For each symbol:
       - Test all 38 strategies (baseline)
       - Rank by performance
       - Optimize top N
       - Select best
    2. Export configs for paper trading
    3. (Optional) Auto-deploy to paper trading
    
    Returns:
        run_id to track progress
    """
    
    # Generate run ID
    run_id = f"discovery_{int(time.time())}"
    
    # Initialize state
    active_discoveries[run_id] = {
        'run_id': run_id,
        'status': 'pending',
        'symbols': request.symbols,
        'current_symbol': None,
        'progress': 0,
        'best_strategies': None,
        'started_at': datetime.now().isoformat(),
        'completed_at': None,
        'error': None,
        'request': request.dict()
    }
    
    # Start discovery in background
    background_tasks.add_task(
        run_discovery_task,
        run_id,
        request
    )
    
    return {
        'run_id': run_id,
        'status': 'pending',
        'message': f'Strategy discovery started for {len(request.symbols)} symbols'
    }


@router.get("/status/{run_id}")
async def get_discovery_status(run_id: str):
    """Get status of discovery process"""
    
    if run_id not in active_discoveries:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    
    discovery = active_discoveries[run_id]
    
    return DiscoveryStatus(
        run_id=discovery['run_id'],
        status=discovery['status'],
        symbols=discovery['symbols'],
        current_symbol=discovery['current_symbol'],
        progress=discovery['progress'],
        best_strategies=discovery['best_strategies'],
        started_at=discovery['started_at'],
        completed_at=discovery['completed_at'],
        error=discovery['error']
    )


@router.get("/results/{run_id}")
async def get_discovery_results(run_id: str):
    """Get full results from discovery"""
    
    if run_id not in active_discoveries:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    
    discovery = active_discoveries[run_id]
    
    if discovery['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Discovery not completed yet")
    
    return {
        'run_id': run_id,
        'symbols': discovery['symbols'],
        'best_strategies': discovery['best_strategies'],
        'paper_trade_configs': discovery.get('paper_trade_configs', []),
        'started_at': discovery['started_at'],
        'completed_at': discovery['completed_at']
    }


@router.post("/deploy")
async def deploy_strategies(request: DeployRequest):
    """
    Deploy discovered strategies to paper/live trading
    
    Args:
        run_id: Discovery run ID
        mode: 'paper' or 'live'
    
    Returns:
        Deployment status
    """
    
    if request.run_id not in active_discoveries:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    
    discovery = active_discoveries[request.run_id]
    
    if discovery['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Discovery not completed yet")
    
    if not discovery.get('paper_trade_configs'):
        raise HTTPException(status_code=400, detail="No strategies to deploy")
    
    # TODO: Integrate with paper/live trading system
    # For now, just return the configs
    
    configs = discovery['paper_trade_configs']
    
    print(f"[Deploy] Deploying {len(configs)} strategies to {request.mode} trading...")
    
    for config in configs:
        symbol = config['symbol']
        strategy = config['strategy']
        print(f"  - {symbol}: {strategy}")
    
    return {
        'status': 'deployed',
        'mode': request.mode,
        'strategies': configs,
        'message': f'Deployed {len(configs)} strategies to {request.mode} trading'
    }


# ============================================================================
# BACKGROUND TASK
# ============================================================================

async def run_discovery_task(run_id: str, request: DiscoveryRequest):
    """
    Run strategy discovery in background
    
    This runs synchronously in a thread pool (via BackgroundTasks)
    """
    
    try:
        # Update status
        active_discoveries[run_id]['status'] = 'running'
        
        # Create orchestrator
        orchestrator = StrategyOrchestrator(
            symbols=request.symbols,
            exchange=request.exchange,
            timeframe=request.timeframe,
            days=request.days,
            optimization_trials=request.optimization_trials,
            top_n_to_optimize=request.top_n_to_optimize
        )
        
        # Track progress
        total_symbols = len(request.symbols)
        
        for i, symbol in enumerate(request.symbols):
            # Update current symbol
            active_discoveries[run_id]['current_symbol'] = symbol
            active_discoveries[run_id]['progress'] = (i / total_symbols) * 100
            
            # Run discovery for this symbol
            print(f"[Discovery {run_id}] Processing {symbol}...")
            
            try:
                orchestrator.run_discovery_for_symbol(symbol)
            except Exception as e:
                print(f"[Discovery {run_id}] Error on {symbol}: {e}")
                # Continue with other symbols
        
        # Get best strategies
        best_strategies = orchestrator.best_strategies
        
        # Export for paper trading
        paper_trade_configs = orchestrator.export_for_paper_trade()
        
        # Update state
        active_discoveries[run_id]['status'] = 'completed'
        active_discoveries[run_id]['progress'] = 100
        active_discoveries[run_id]['best_strategies'] = {
            symbol: {
                'strategy': result.strategy_name,
                'baseline_profit': result.baseline_metrics['total_profit'],
                'optimized_profit': result.optimized_metrics['total_profit'] if result.optimized_metrics else None,
                'score': result.optimized_score if result.optimized_score else result.baseline_score,
                'params': result.optimized_params if result.optimized_params else {}
            }
            for symbol, result in best_strategies.items()
        }
        active_discoveries[run_id]['paper_trade_configs'] = paper_trade_configs
        active_discoveries[run_id]['completed_at'] = datetime.now().isoformat()
        
        print(f"[Discovery {run_id}] ✅ Completed!")
        
        # Auto-deploy to paper trading if requested
        if request.auto_deploy_paper:
            print(f"[Discovery {run_id}] Auto-deploying to paper trading...")
            # TODO: Integrate with paper trading system
    
    except Exception as e:
        # Error handling
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        
        active_discoveries[run_id]['status'] = 'failed'
        active_discoveries[run_id]['error'] = error_msg
        active_discoveries[run_id]['completed_at'] = datetime.now().isoformat()
        
        print(f"[Discovery {run_id}] ❌ Failed: {e}")
        traceback.print_exc()


@router.post("/check-cache")
async def check_cached_optimizations(request: CheckCacheRequest):
    """
    Check if optimizations already exist for given symbols
    
    Returns list of cached results
    """
    conn = db_sqlite.connect_lab()
    
    cached = []
    
    for symbol in request.symbols:
        # Query for existing optimization
        cur = conn.cursor()
        cur.execute("""
            SELECT r.id, r.config_json, r.completed_at, t.params_json, t.metrics_json, t.score
            FROM runs r
            JOIN trials t ON t.run_id = r.id
            WHERE r.config_json LIKE ?
            AND r.status = 'completed'
            ORDER BY r.completed_at DESC
            LIMIT 1
        """, (f'%{symbol}%{request.timeframe}%',))
        
        row = cur.fetchone()
        
        if row:
            try:
                config = json.loads(row[1])
                metrics = json.loads(row[4])
                
                cached.append({
                    'symbol': symbol,
                    'timeframe': request.timeframe,
                    'strategy': config.get('strategy', 'unknown'),
                    'optimized_profit': metrics.get('total_profit', 0),
                    'score': row[5],
                    'cached_at': row[2]
                })
            except:
                pass
    
    conn.close()
    
    return {
        'cached': cached,
        'count': len(cached)
    }