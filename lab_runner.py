"""
Lab Runner - Asynchronous backtest execution system

This module provides non-blocking execution of backtests using ThreadPoolExecutor.
Each run is tracked in SQLite and results are stored as artifacts.
"""

import os
import time
import uuid
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Any
from datetime import datetime

import db_sqlite
from lab_objective import evaluate_objective
from lab_schemas import StrategyConfig


# Global thread pool for async execution
_executor: Optional[ThreadPoolExecutor] = None
_active_runs: Dict[str, Future] = {}


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
        _executor.shutdown(wait=True)
        _executor = None


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


def log_run(run_id: str, level: str, message: str):
    """Log message for a run"""
    conn = db_sqlite.connect_lab()
    db_sqlite.insert_log(conn, run_id, level, message)
    conn.close()
    print(f"[{run_id[:8]}] {level}: {message}")


def execute_backtest_task(run_id: str, config: StrategyConfig):
    """
    Execute backtest task in background thread
    
    This function:
    1. Runs the backtest
    2. Calculates metrics
    3. Evaluates objective
    4. Saves artifacts (trades, equity curve)
    5. Updates database
    """
    conn = db_sqlite.connect_lab()
    
    try:
        # Update status to running
        db_sqlite.update_run_status(conn, run_id, "running", started_at=int(time.time()))
        log_run(run_id, "INFO", f"Starting backtest for strategy: {config.name}")
        
        # Simulate backtest execution
        # TODO: Integrate with actual backtest.py
        time.sleep(2)  # Simulate backtest execution
        
        # Generate mock metrics
        metrics = {
            'total_profit': 45.3,
            'sharpe': 2.1,
            'sortino': 2.8,
            'calmar': 1.9,
            'max_dd': -18.5,
            'win_rate': 58.5,
            'profit_factor': 2.4,
            'avg_trade': 1.8,
            'trades': 125,
            'exposure': 65.0,
            'pnl_std': 2.3
        }
        
        # Evaluate objective
        try:
            score = evaluate_objective(metrics, config.objective.expression)
            log_run(run_id, "INFO", f"Objective score: {score:.4f}")
        except Exception as e:
            log_run(run_id, "ERROR", f"Failed to evaluate objective: {str(e)}")
            score = 0.0
        
        # Insert trial
        trial_id = db_sqlite.insert_trial(
            conn,
            run_id=run_id,
            trial_number=1,
            params={},  # No parameter optimization for single backtest
            metrics=metrics,
            score=score
        )
        
        # Create artifact directory
        artifact_dir = get_artifact_dir(run_id, trial_id)
        
        # Save trades CSV (mock)
        trades_path = os.path.join(artifact_dir, "trades.csv")
        with open(trades_path, 'w') as f:
            f.write("entry_time,exit_time,side,pnl,pnl_pct\n")
            f.write("2024-01-01 10:00,2024-01-01 15:00,long,150.50,2.3\n")
        db_sqlite.insert_artifact(conn, run_id, trial_id, "trades", trades_path)
        log_run(run_id, "INFO", f"Saved trades to {trades_path}")
        
        # Save equity curve (mock)
        equity_path = os.path.join(artifact_dir, "equity.png")
        # TODO: Generate actual equity curve plot
        with open(equity_path, 'w') as f:
            f.write("# Mock equity curve\n")
        db_sqlite.insert_artifact(conn, run_id, trial_id, "equity_curve", equity_path)
        log_run(run_id, "INFO", f"Saved equity curve to {equity_path}")
        
        # Save metrics JSON
        metrics_path = os.path.join(artifact_dir, "metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        db_sqlite.insert_artifact(conn, run_id, trial_id, "metrics", metrics_path)
        
        # Update status to completed
        db_sqlite.update_run_status(conn, run_id, "completed", completed_at=int(time.time()))
        log_run(run_id, "INFO", f"Backtest completed successfully")
    
    except Exception as e:
        # Update status to failed
        db_sqlite.update_run_status(conn, run_id, "failed", completed_at=int(time.time()))
        error_msg = f"Backtest failed: {str(e)}\n{traceback.format_exc()}"
        log_run(run_id, "ERROR", error_msg)
    
    finally:
        conn.close()
        # Remove from active runs
        if run_id in _active_runs:
            del _active_runs[run_id]


def start_backtest_run(config: StrategyConfig) -> str:
    """
    Start a backtest run asynchronously
    
    Args:
        config: Strategy configuration
    
    Returns:
        run_id: Unique identifier for the run
    """
    # Generate run ID
    run_id = generate_run_id()
    
    # Create run in database
    conn = db_sqlite.connect_lab()
    config_dict = config.model_dump()
    db_sqlite.create_run(
        conn,
        run_id=run_id,
        name=config.name,
        mode="backtest",
        config=config_dict
    )
    conn.close()
    
    # Submit task to executor
    executor = get_executor()
    future = executor.submit(execute_backtest_task, run_id, config)
    _active_runs[run_id] = future
    
    log_run(run_id, "INFO", f"Run created and queued: {config.name}")
    
    return run_id


def get_run_status(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a run
    
    Args:
        run_id: Run identifier
    
    Returns:
        Dictionary with status information or None if not found
    """
    conn = db_sqlite.connect_lab()
    run = db_sqlite.get_run(conn, run_id)
    
    if not run:
        conn.close()
        return None
    
    # Get best trial if available
    trials = db_sqlite.get_run_trials(conn, run_id, limit=1)
    best_score = trials[0]['score'] if trials else None
    
    conn.close()
    
    # Calculate progress (mock for now)
    progress = 0.0
    if run['status'] == 'running':
        progress = 0.5
    elif run['status'] == 'completed':
        progress = 1.0
    
    return {
        'run_id': run_id,
        'name': run['name'],
        'status': run['status'],
        'progress': progress,
        'best_score': best_score,
        'current_trial': 1 if run['status'] == 'running' else None,
        'total_trials': 1,
        'started_at': run.get('started_at'),
        'completed_at': run.get('completed_at'),
        'created_at': run.get('created_at'),
        'updated_at': run.get('updated_at')
    }


def get_run_results(run_id: str, limit: int = 100, offset: int = 0):
    """
    Get results (trials) for a run
    
    Args:
        run_id: Run identifier
        limit: Maximum number of results
        offset: Offset for pagination
    
    Returns:
        List of trial results
    """
    conn = db_sqlite.connect_lab()
    trials = db_sqlite.get_run_trials(conn, run_id, limit, offset)
    conn.close()
    
    results = []
    for trial in trials:
        results.append({
            'trial_id': trial['trial_number'],
            'params': json.loads(trial['params_json']),
            'metrics': json.loads(trial['metrics_json']),
            'score': trial['score'],
            'created_at': trial['created_at']
        })
    
    return results


def cancel_run(run_id: str) -> bool:
    """
    Cancel a running backtest
    
    Args:
        run_id: Run identifier
    
    Returns:
        True if cancelled successfully, False otherwise
    """
    if run_id not in _active_runs:
        return False
    
    future = _active_runs[run_id]
    cancelled = future.cancel()
    
    if cancelled:
        conn = db_sqlite.connect_lab()
        db_sqlite.update_run_status(conn, run_id, "cancelled", completed_at=int(time.time()))
        conn.close()
        log_run(run_id, "INFO", "Run cancelled by user")
        del _active_runs[run_id]
    
    return cancelled


# Cleanup on module unload
import atexit
atexit.register(shutdown_executor)