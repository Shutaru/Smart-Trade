"""
Lab Runner - Asynchronous backtest execution system with WebSocket support
"""

import os
import time
import uuid
import json
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Any, Set
from datetime import datetime
from threading import Thread

import db_sqlite
from lab_objective import evaluate_objective
from lab_schemas import StrategyConfig

# Global thread pool for async execution
_executor: Optional[ThreadPoolExecutor] = None
_active_runs: Dict[str, Future] = {}

# WebSocket subscribers: run_id -> set of websocket connections
_ws_subscribers: Dict[str, Set[Any]] = {}

# Main event loop reference (set by gui_server on startup)
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def set_main_loop(loop: asyncio.AbstractEventLoop):
    """Set the main event loop for WebSocket broadcasting"""
    global _main_loop
    _main_loop = loop


def get_executor() -> ThreadPoolExecutor:
    """Get or create global thread pool executor"""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="lab_runner")
    return _executor


def shutdown_executor():
    """Shutdown the executor and wait for all tasks to complete"""
    global _executor
    if _executor is not None:
        print("Shutting down lab runner executor...")
        _executor.shutdown(wait=True)
        _executor = None
        print("Lab runner executor shutdown complete")


def generate_run_id() -> str:
    """Generate unique run ID"""
    return str(uuid.uuid4())


def get_artifact_dir(run_id: str, trial_id: Optional[int] = None) -> str:
    """Get artifact directory path"""
    if trial_id is not None:
        path = os.path.join("artifacts", run_id, str(trial_id))
    else:
        path = os.path.join("artifacts", run_id)
    os.makedirs(path, exist_ok=True)
    return path


def subscribe_ws(run_id: str, websocket: Any):
    """Subscribe a WebSocket to run updates"""
    if run_id not in _ws_subscribers:
        _ws_subscribers[run_id] = set()
    _ws_subscribers[run_id].add(websocket)
    print(f"[WS] Subscribed to run {run_id[:8]}... ({len(_ws_subscribers[run_id])} subscribers)")


def unsubscribe_ws(run_id: str, websocket: Any):
    """Unsubscribe a WebSocket from run updates"""
    if run_id in _ws_subscribers:
        _ws_subscribers[run_id].discard(websocket)
        if not _ws_subscribers[run_id]:
            del _ws_subscribers[run_id]
        print(f"[WS] Unsubscribed from run {run_id[:8]}...")


async def broadcast_update(run_id: str, message: Dict[str, Any]):
    """Broadcast update to all WebSocket subscribers"""
    if run_id not in _ws_subscribers:
        return
    
    dead_sockets = set()
    for ws in list(_ws_subscribers[run_id]):
        try:
            await ws.send_json(message)
        except Exception as e:
            print(f"[WS] Failed to send to subscriber: {e}")
            dead_sockets.add(ws)
    
    for ws in dead_sockets:
        unsubscribe_ws(run_id, ws)


def log_run(run_id: str, level: str, message: str, progress: float = None, best_score: float = None):
    """Log message for a run and broadcast to WebSocket subscribers"""
    conn = db_sqlite.connect_lab()
    db_sqlite.insert_log(conn, run_id, level, message)
    conn.close()
    
    print(f"[{run_id[:8]}] {level}: {message}")
    
    if run_id in _ws_subscribers and _main_loop is not None:
        ws_message = {
            'ts': int(time.time() * 1000),
            'level': level,
            'msg': message,
            'progress': progress,
            'best_score': best_score
        }
        
        try:
            # Use call_soon_threadsafe to schedule from worker thread
            _main_loop.call_soon_threadsafe(
                asyncio.create_task,
                broadcast_update(run_id, ws_message)
            )
        except Exception as e:
            print(f"[WS] Failed to schedule broadcast: {e}")


def execute_backtest_task(run_id: str, config: StrategyConfig):
    """Execute REAL backtest task using production engine"""
    conn = db_sqlite.connect_lab()
    
    try:
        db_sqlite.update_run_status(conn, run_id, "running", started_at=int(time.time()))
        log_run(run_id, "INFO", f"Starting backtest for strategy: {config.name}", progress=0.0)
        log_run(run_id, "INFO", f"Portfolio size: ${config.risk.starting_equity:,.2f}", progress=0.05)
        
        log_run(run_id, "INFO", "Loading historical data...", progress=0.1)
        
        # Create trial first to get artifact directory
        trial_id = db_sqlite.insert_trial(conn, run_id=run_id, trial_number=1, params={}, metrics={}, score=0.0)
        artifact_dir = get_artifact_dir(run_id, trial_id)
   
        log_run(run_id, "INFO", "Calculating indicators...", progress=0.3)
        
        # ✅ RUN REAL BACKTEST using production adapter
     from lab_backtest_adapter import run_strategy_lab_backtest
        
     log_run(run_id, "INFO", "Simulating trades...", progress=0.5)
  
        metrics = run_strategy_lab_backtest(config, artifact_dir)
        
      log_run(run_id, "INFO", "Computing metrics...", progress=0.7)
        
        # Evaluate objective
 try:
      score = evaluate_objective(metrics, config.objective.expression)
          log_run(run_id, "INFO", f"Objective score: {score:.4f}", progress=0.85, best_score=score)
        except Exception as e:
     log_run(run_id, "ERROR", f"Failed to evaluate objective: {str(e)}", progress=0.85)
            score = 0.0
        
        # Update trial with real metrics
  conn.execute("UPDATE trials SET metrics_json = ?, score = ? WHERE id = ?",
          (json.dumps(metrics), score, trial_id))
conn.commit()
    
        log_run(run_id, "INFO", "Saving artifacts...", progress=0.9, best_score=score)
        
        # Register artifacts in database
        trades_path = os.path.join(artifact_dir, "trades.csv")
        if os.path.exists(trades_path):
            db_sqlite.insert_artifact(conn, run_id, trial_id, "trades", trades_path)
     
   equity_path = os.path.join(artifact_dir, "equity.csv")
        if os.path.exists(equity_path):
     db_sqlite.insert_artifact(conn, run_id, trial_id, "equity_curve", equity_path)
        
        metrics_path = os.path.join(artifact_dir, "metrics.json")
        if os.path.exists(metrics_path):
      db_sqlite.insert_artifact(conn, run_id, trial_id, "metrics", metrics_path)
        
        db_sqlite.update_run_status(conn, run_id, "completed", completed_at=int(time.time()))
        
      # Final log with portfolio summary
        final_equity = config.risk.starting_equity + metrics.get('total_profit', 0)
   log_run(run_id, "INFO", f"Final equity: ${final_equity:,.2f} (PnL: {metrics.get('total_profit', 0):+.2f}%)", progress=1.0, best_score=score)
  log_run(run_id, "INFO", f"Backtest completed successfully", progress=1.0, best_score=score)
    
    except Exception as e:
    db_sqlite.update_run_status(conn, run_id, "failed", completed_at=int(time.time()))
   error_msg = f"Backtest failed: {str(e)}\n{traceback.format_exc()}"
        log_run(run_id, "ERROR", error_msg, progress=1.0)
    
    finally:
        conn.close()
        if run_id in _active_runs:
    del _active_runs[run_id]


def start_backtest_run(config: StrategyConfig) -> str:
    """Start a backtest run asynchronously"""
    run_id = generate_run_id()
    
    conn = db_sqlite.connect_lab()
    config_dict = config.model_dump()
    db_sqlite.create_run(conn, run_id=run_id, name=config.name, mode="backtest", config=config_dict)
    conn.close()
    
    executor = get_executor()
    future = executor.submit(execute_backtest_task, run_id, config)
    _active_runs[run_id] = future
    
    log_run(run_id, "INFO", f"Run created and queued: {config.name}", progress=0.0)
    
    return run_id


def get_run_status(run_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a run"""
    conn = db_sqlite.connect_lab()
    run = db_sqlite.get_run(conn, run_id)
    
    if not run:
        conn.close()
        return None
    
    trials = db_sqlite.get_run_trials(conn, run_id, limit=1)
    best_score = trials[0]['score'] if trials else None
    
    conn.close()
    
    progress = 0.0
    if run['status'] == 'running':
        progress = 0.5
    elif run['status'] == 'completed':
        progress = 1.0
    
    return {
        'run_id': run_id, 'name': run['name'], 'status': run['status'],
        'progress': progress, 'best_score': best_score,
        'current_trial': 1 if run['status'] == 'running' else None,
        'total_trials': 1, 'started_at': run.get('started_at'),
        'completed_at': run.get('completed_at'),
        'created_at': run.get('created_at'),
        'updated_at': run.get('updated_at')
    }


def get_run_results(run_id: str, limit: int = 100, offset: int = 0):
    """Get results (trials) for a run"""
    conn = db_sqlite.connect_lab()
    trials = db_sqlite.get_run_trials(conn, run_id, limit, offset)
    conn.close()
    
    results = []
    for trial in trials:
        try:
            # Safely parse JSON strings
            params = json.loads(trial['params_json']) if trial['params_json'] else {}
            metrics = json.loads(trial['metrics_json']) if trial['metrics_json'] else {}
            
            results.append({
                'trial_id': trial['trial_number'],
                'params': params,
                'metrics': metrics,
                'score': trial['score'],
                'created_at': trial['created_at']
            })
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Log error but continue processing other trials
            print(f"[get_run_results] Error parsing trial {trial.get('id', 'unknown')}: {e}")
            # Add trial with empty data instead of failing completely
            results.append({
                'trial_id': trial.get('trial_number', 0),
                'params': {},
                'metrics': {},
                'score': trial.get('score', 0.0),
                'created_at': trial.get('created_at')
            })
    
    return results


def get_run_logs(run_id: str, limit: int = 100) -> list:
    """Get logs for a run"""
    conn = db_sqlite.connect_lab()
    cur = conn.cursor()
    cur.execute("SELECT ts, level, message FROM logs WHERE run_id = ? ORDER BY ts DESC LIMIT ?", (run_id, limit))
    rows = cur.fetchall()
    conn.close()
    
    return [{'ts': r[0], 'level': r[1], 'message': r[2]} for r in rows]


def cancel_run(run_id: str) -> bool:
    """Cancel a running backtest"""
    if run_id not in _active_runs:
        return False
    
    future = _active_runs[run_id]
    cancelled = future.cancel()
    
    if cancelled:
        conn = db_sqlite.connect_lab()
        db_sqlite.update_run_status(conn, run_id, "cancelled", completed_at=int(time.time()))
        conn.close()
        log_run(run_id, "INFO", "Run cancelled by user", progress=1.0)
        del _active_runs[run_id]
    
    return cancelled


def execute_grid_search_task(run_id: str, config: StrategyConfig):
    """Execute grid search task in background thread"""
    conn = db_sqlite.connect_lab()
    
    try:
        db_sqlite.update_run_status(conn, run_id, "running", started_at=int(time.time()))
        log_run(run_id, "INFO", f"Starting grid search for strategy: {config.name}", progress=0.0)
        
        import itertools
        
        # Generate parameter grid
        param_grid = {}
        for param_range in config.param_space:
            if param_range.step:
                values = []
                val = param_range.low
                while val <= param_range.high:
                    values.append(int(val) if param_range.int_ else val)
                    val += param_range.step
            else:
                values = [param_range.low, param_range.high]
            param_grid[param_range.name] = values
        
        # Generate all combinations
        keys = list(param_grid.keys())
        combinations = list(itertools.product(*[param_grid[k] for k in keys]))
        total_trials = min(len(combinations), 1000)  # Max 1000 trials
        
        log_run(run_id, "INFO", f"Testing {total_trials} parameter combinations...", progress=0.1)
    
        best_score = float('-inf')
        best_params = {}
        
        for trial_num, combination in enumerate(combinations[:total_trials], 1):
            params = dict(zip(keys, combination))
            
            # Mock backtest with params (você implementa a lógica real aqui)
            metrics = {
                'total_profit': 45.3 + trial_num * 0.1,
                'sharpe': 2.1 + (trial_num % 10) * 0.05,
                'sortino': 2.8, 'calmar': 1.9,
                'max_dd': -18.5, 'win_rate': 58.5,
                'profit_factor': 2.4, 'avg_trade': 1.8,
                'trades': 125, 'exposure': 65.0
            }
            
            try:
                score = evaluate_objective(metrics, config.objective.expression)
            except Exception:
                score = 0.0
 
            if score > best_score:
                best_score = score
                best_params = params
             
            progress = trial_num / total_trials
            db_sqlite.insert_trial(conn, run_id=run_id, trial_number=trial_num, params=params, metrics=metrics, score=score)
            
            if trial_num % 10 == 0:
                log_run(run_id, "INFO", f"Completed {trial_num}/{total_trials} trials", progress=progress, best_score=best_score)
        
        log_run(run_id, "INFO", f"Grid search completed. Best score: {best_score:.4f}", progress=1.0, best_score=best_score)
        db_sqlite.update_run_status(conn, run_id, "completed", completed_at=int(time.time()))
    
    except Exception as e:
        db_sqlite.update_run_status(conn, run_id, "failed", completed_at=int(time.time()))
        log_run(run_id, "ERROR", f"Grid search failed: {str(e)}", progress=1.0)
    
    finally:
        conn.close()
        if run_id in _active_runs:
            del _active_runs[run_id]


def start_grid_search_run(config: StrategyConfig) -> str:
    """Start a grid search run asynchronously"""
    run_id = generate_run_id()
    
    conn = db_sqlite.connect_lab()
    config_dict = config.model_dump()
    db_sqlite.create_run(conn, run_id=run_id, name=config.name, mode="grid_search", config=config_dict)
    conn.close()
    
    executor = get_executor()
    future = executor.submit(execute_grid_search_task, run_id, config)
    _active_runs[run_id] = future
    
    log_run(run_id, "INFO", f"Grid search created and queued: {config.name}", progress=0.0)
    
    return run_id


def execute_optuna_task(run_id: str, config: StrategyConfig, n_trials: int):
    """Execute Optuna optimization task in background thread"""
    conn = db_sqlite.connect_lab()
    
    try:
        db_sqlite.update_run_status(conn, run_id, "running", started_at=int(time.time()))
        log_run(run_id, "INFO", f"Starting Optuna optimization for strategy: {config.name}", progress=0.0)
        
        log_run(run_id, "INFO", f"Running {n_trials} Bayesian optimization trials...", progress=0.1)
        
        best_score = float('-inf')
         
        for trial_num in range(1, n_trials + 1):
            # Mock Optuna suggest (você implementa com optuna.create_study() real)
            params = {param.name: param.low + (param.high - param.low) * (trial_num / n_trials) for param in config.param_space}
                
            # Mock backtest
            metrics = {
                'total_profit': 45.3 + trial_num * 0.05,
                'sharpe': 2.1 + (trial_num % 20) * 0.03,
                'sortino': 2.8, 'calmar': 1.9,
                'max_dd': -18.5, 'win_rate': 58.5,
                'profit_factor': 2.4, 'avg_trade': 1.8,
                'trades': 125, 'exposure': 65.0
            }
                
            try:
                score = evaluate_objective(metrics, config.objective.expression)
            except Exception:
                score = 0.0
           
            if score > best_score:
                best_score = score
             
            progress = trial_num / n_trials
            db_sqlite.insert_trial(conn, run_id=run_id, trial_number=trial_num, params=params, metrics=metrics, score=score)
        
            if trial_num % 10 == 0:
                log_run(run_id, "INFO", f"Completed {trial_num}/{n_trials} trials", progress=progress, best_score=best_score)
                
        log_run(run_id, "INFO", f"Optuna optimization completed. Best score: {best_score:.4f}", progress=1.0, best_score=best_score)
        db_sqlite.update_run_status(conn, run_id, "completed", completed_at=int(time.time()))
    
    except Exception as e:
        db_sqlite.update_run_status(conn, run_id, "failed", completed_at=int(time.time()))
        log_run(run_id, "ERROR", f"Optuna failed: {str(e)}", progress=1.0)
    
    finally:
        conn.close()
        if run_id in _active_runs:
            del _active_runs[run_id]


def start_optuna_run(config: StrategyConfig, n_trials: int = 100) -> str:
    """Start an Optuna optimization run asynchronously"""
    run_id = generate_run_id()
    
    conn = db_sqlite.connect_lab()
    config_dict = config.model_dump()
    db_sqlite.create_run(conn, run_id=run_id, name=config.name, mode="optuna", config=config_dict)
    conn.close()
    
    executor = get_executor()
    future = executor.submit(execute_optuna_task, run_id, config, n_trials)
    _active_runs[run_id] = future
    
    log_run(run_id, "INFO", f"Optuna optimization created and queued: {config.name}", progress=0.0)
    
    return run_id


import atexit
atexit.register(shutdown_executor)