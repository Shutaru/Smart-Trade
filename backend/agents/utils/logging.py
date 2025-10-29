"""
Structured logging for agent trajectories
"""

import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from ..schemas import TrajectoryEvent, Metrics


class AgentLogger:
    """Logger for agent run trajectories"""
    
    def __init__(self, run_dir: Path):
   self.run_dir = run_dir
    self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.trajectory_path = run_dir / "trajectory.jsonl"
        self.metrics_path = run_dir / "metrics.csv"
  
        # Initialize metrics file
    if not self.metrics_path.exists():
   pd.DataFrame(columns=[
        'timestamp', 'equity', 'cash', 'realized_pnl', 
      'unrealized_pnl', 'total_pnl', 'num_positions'
       ]).to_csv(self.metrics_path, index=False)
    
    def append_event(self, event: TrajectoryEvent):
    """Append event to trajectory log"""
        
 with open(self.trajectory_path, 'a') as f:
            f.write(event.json() + '\n')
    
    def append_metrics(self, metrics: Metrics):
  """Append metrics snapshot"""
        
      df = pd.DataFrame([{
        'timestamp': metrics.timestamp,
 'equity': metrics.equity,
        'cash': metrics.cash,
            'realized_pnl': metrics.realized_pnl,
   'unrealized_pnl': metrics.unrealized_pnl,
 'total_pnl': metrics.total_pnl,
            'num_positions': metrics.num_positions
        }])
        
    df.to_csv(self.metrics_path, mode='a', header=False, index=False)
    
  def log_observation(self, run_id: str, observation: Dict[str, Any]):
    """Log observation event"""
  event = TrajectoryEvent(
    run_id=run_id,
         timestamp=observation.get('timestamp', 0),
       event_type="observation",
   data=observation
   )
        self.append_event(event)
    
    def log_action(self, run_id: str, action: Dict[str, Any]):
        """Log action event"""
        event = TrajectoryEvent(
            run_id=run_id,
          timestamp=action.get('timestamp', 0),
            event_type="action",
            data=action
        )
        self.append_event(event)
    
    def log_fill(self, run_id: str, fill_data: Dict[str, Any]):
        """Log order fill event"""
        event = TrajectoryEvent(
            run_id=run_id,
     timestamp=fill_data.get('timestamp', 0),
        event_type="fill",
        data=fill_data
        )
  self.append_event(event)
    
    def log_error(self, run_id: str, error_msg: str, timestamp: int):
        """Log error event"""
    event = TrajectoryEvent(
   run_id=run_id,
            timestamp=timestamp,
            event_type="error",
            data={'error': error_msg}
        )
        self.append_event(event)
