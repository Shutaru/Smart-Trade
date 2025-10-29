"""
Agent Service - Singleton service for managing agent lifecycle

Features:
- Start/stop agent in background thread
- Status monitoring
- Log tailing
- Thread-safe singleton pattern
"""

import threading
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import time

from .config import AgentConfig
from .runner import AgentRunner


class AgentService:
    """
    Singleton service for managing agent lifecycle
    
    Prevents multiple concurrent agent instances
    Provides status monitoring and log access
    """
    
    _instance: Optional['AgentService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Agent state
        self.runner: Optional[AgentRunner] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.run_id: Optional[str] = None
        self.config: Optional[AgentConfig] = None
        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None
        
        # Error tracking
        self.last_error: Optional[str] = None
        
        print("[AgentService] Initialized")
    
    def start(self, config_path: str = "configs/agent_paper.yaml", 
             overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start agent in background thread
        
        Args:
            config_path: Path to config YAML
            overrides: Optional config overrides
        
        Returns:
            Dict with run_id and status
        
        Raises:
            RuntimeError: If agent already running
        """
        with self._lock:
            if self.running:
                raise RuntimeError(f"Agent already running with run_id: {self.run_id}")
            
            # Load config
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            self.config = AgentConfig.from_yaml(str(config_file))
            
            # Apply overrides
            if overrides:
                for key, value in overrides.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
            
            # Create runner
            self.runner = AgentRunner(self.config)
            self.run_id = self.runner.run_id
            self.started_at = time.time()
            self.stopped_at = None
            self.last_error = None
            
            # Start in background thread
            self.thread = threading.Thread(
                target=self._run_agent,
                name=f"AgentRunner-{self.run_id}",
                daemon=True
            )
            self.running = True
            self.thread.start()
            
            print(f"[AgentService] Started agent: {self.run_id}")
            
            return {
                "run_id": self.run_id,
                "status": "running",
                "started_at": self.started_at,
                "config": {
                    "exchange": self.config.exchange,
                    "symbols": self.config.symbols,
                    "timeframe": self.config.timeframe,
                    "policy": self.config.policy,
                    "initial_cash": self.config.initial_cash
                }
            }
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop running agent
        
        Returns:
            Dict with stopped status and run_id
        
        Raises:
            RuntimeError: If agent not running
        """
        with self._lock:
            if not self.running:
                raise RuntimeError("Agent not running")
            
            print(f"[AgentService] Stopping agent: {self.run_id}")
            
            # Signal runner to stop
            if self.runner:
                self.runner.running = False
            
            # Wait for thread to finish (with timeout)
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5.0)
            
            self.running = False
            self.stopped_at = time.time()
            
            result = {
                "stopped": True,
                "run_id": self.run_id,
                "stopped_at": self.stopped_at,
                "duration_seconds": self.stopped_at - self.started_at if self.started_at else 0
            }
            
            print(f"[AgentService] Agent stopped: {self.run_id}")
            
            return result
    
    def status(self) -> Dict[str, Any]:
        """
        Get current agent status
        
        Returns:
            Dict with running status, metrics, positions, etc
        """
        if not self.running or not self.runner:
            return {
                "running": False,
                "run_id": self.run_id,
                "last_stopped_at": self.stopped_at
            }
        
        # Get current portfolio state
        portfolio = self.runner.portfolio.snapshot()
        
        # Get risk metrics
        risk_metrics = self.runner.risk_guard.get_risk_metrics()
        
        # Get pending orders
        pending_orders = self.runner.execution.get_pending_orders()
        
        return {
            "running": True,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "uptime_seconds": time.time() - self.started_at if self.started_at else 0,
            "iteration": self.runner.iteration,
            "config": {
                "exchange": self.config.exchange,
                "symbols": self.config.symbols,
                "timeframe": self.config.timeframe,
                "policy": self.config.policy
            },
            "portfolio": {
                "equity": portfolio.equity,
                "cash": portfolio.cash,
                "realized_pnl": portfolio.realized_pnl,
                "unrealized_pnl": portfolio.unrealized_pnl,
                "total_pnl": portfolio.total_pnl,
                "num_positions": len(portfolio.positions),
                "exposure_pct": portfolio.exposure_pct
            },
            "positions": [
                {
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "pnl_pct": pos.pnl_pct
                }
                for pos in portfolio.positions
            ],
            "pending_orders": len(pending_orders),
            "risk": {
                "kill_switch_active": risk_metrics['kill_switch_active'],
                "current_drawdown_pct": risk_metrics['current_drawdown_pct'],
                "violations_count": risk_metrics['violations_count']
            },
            "last_error": self.last_error
        }
    
    def tail_logs(self, n: int = 200, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get last N lines from trajectory.jsonl
        
        Args:
            n: Number of lines to return
            kind: Filter by event kind (observation, action, fill, error)
        
        Returns:
            List of events (newest first)
        """
        if not self.run_id:
            return []
        
        trajectory_path = Path("runs") / self.run_id / "trajectory.jsonl"
        
        if not trajectory_path.exists():
            return []
        
        try:
            # Read all lines
            with open(trajectory_path, 'r') as f:
                lines = f.readlines()
            
            # Parse JSON
            events = []
            for line in reversed(lines):  # Newest first
                try:
                    event = json.loads(line.strip())
                    
                    # Filter by kind if specified
                    if kind and event.get('kind') != kind:
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= n:
                        break
                
                except json.JSONDecodeError:
                    continue
            
            return events
        
        except Exception as e:
            print(f"[AgentService] Error reading logs: {e}")
            return []
    
    def get_equity_curve(self) -> List[Dict[str, float]]:
        """
        Get equity curve data
        
        Returns:
            List of equity data points
        """
        if not self.run_id:
            return []
        
        equity_path = Path("runs") / self.run_id / "equity.json"
        
        if not equity_path.exists():
            return []
        
        try:
            with open(equity_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[AgentService] Error reading equity: {e}")
            return []
    
    def _run_agent(self):
        """
        Background thread function to run agent
        
        Catches exceptions and updates error state
        """
        try:
            print(f"[AgentService] Agent thread started: {self.run_id}")
            self.runner.run()
            print(f"[AgentService] Agent thread finished: {self.run_id}")
        except Exception as e:
            self.last_error = str(e)
            print(f"[AgentService] Agent thread error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            self.stopped_at = time.time()


# Global service instance
agent_service = AgentService()