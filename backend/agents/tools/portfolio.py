"""
Portfolio management tool (paper trading)
"""

from typing import Dict, Optional
from ..schemas import PortfolioState, Position
from ..config import AgentConfig
import time


class PortfolioTool:
    """Manage portfolio state in paper mode"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
    self.cash = config.initial_cash
        self.positions: Dict[str, Position] = {}
        self.realized_pnl = 0.0
     self.session_start_equity = config.initial_cash
    
    def mark_to_market(self, prices: Dict[str, float]):
      """Update unrealized PnL based on current prices"""
 
        for symbol, position in self.positions.items():
if symbol not in prices:
         continue
     
            current_price = prices[symbol]
            
   if position.side == "LONG":
   pnl = (current_price - position.entry_price) * position.quantity
            else:  # SHORT
           pnl = (position.entry_price - current_price) * position.quantity
 
  position.unrealized_pnl = pnl
    
    def snapshot(self, timestamp: Optional[int] = None) -> PortfolioState:
  """Get current portfolio state"""
        
if timestamp is None:
       timestamp = int(time.time() * 1000)
        
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        equity = self.cash + unrealized_pnl
  
        # Calculate margin used (simplified)
        margin_used = sum(
     p.quantity * p.entry_price / self.config.max_leverage
   for p in self.positions.values()
)
        
        return PortfolioState(
            timestamp=timestamp,
        cash=self.cash,
   positions=list(self.positions.values()),
       equity=equity,
        realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized_pnl,
            margin_used=margin_used
        )
    
  def add_position(self, position: Position):
        """Add new position"""
 self.positions[position.symbol] = position
    
    def remove_position(self, symbol: str) -> Optional[Position]:
        """Remove and return position"""
        return self.positions.pop(symbol, None)
    
    def update_cash(self, amount: float):
        """Update cash balance"""
     self.cash += amount
    
    def update_realized_pnl(self, amount: float):
   """Update realized PnL"""
        self.realized_pnl += amount
