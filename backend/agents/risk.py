"""
Risk management and validation
"""

from typing import Tuple, List
from .schemas import Action, PortfolioState, Order
from .config import AgentConfig


class RiskGuard:
    """Validates actions against risk limits"""
    
    def __init__(self, config: AgentConfig):
     self.config = config
    
    def validate_action(self, action: Action, portfolio: PortfolioState) -> Tuple[bool, str]:
        """
        Validate action against risk limits
        
        Returns:
  (is_valid, error_message)
        """
        
      # Check number of concurrent positions
     if len(portfolio.positions) >= self.config.max_concurrent_positions:
            return False, f"Maximum {self.config.max_concurrent_positions} concurrent positions reached"
     
        # Validate each order
        for order in action.orders:
     # Check if adding position exceeds limits
 if order.side == "BUY":
    is_valid, msg = self._validate_new_position(order, portfolio)
                if not is_valid:
             return False, msg
            
        # Require SL/TP in live mode
         if not self.config.paper_mode and self.config.require_stop_loss:
  # Check if order creates position without SL
             existing_pos = next((p for p in portfolio.positions if p.symbol == order.symbol), None)
        if not existing_pos or not existing_pos.stop_loss:
            return False, f"Stop loss required for {order.symbol}"
        
        return True, "OK"
    
    def _validate_new_position(self, order: Order, portfolio: PortfolioState) -> Tuple[bool, str]:
        """Validate new position doesn't exceed exposure limits"""
        
        # Calculate position notional value
      notional = order.quantity * (order.price or 0.0)
        
        # Check against max exposure
    max_notional = portfolio.equity * (self.config.max_exposure_pct / 100.0)
        if notional > max_notional:
     return False, f"Position notional ${notional:.2f} exceeds max ${max_notional:.2f}"
        
    return True, "OK"
    
    def check_drawdown(self, portfolio: PortfolioState, session_start_equity: float) -> Tuple[bool, str]:
        """Check if intraday drawdown limit exceeded"""
        
        dd_pct = ((portfolio.equity - session_start_equity) / session_start_equity) * 100.0
        
 if dd_pct < -self.config.max_drawdown_intraday_pct:
        return False, f"Intraday drawdown {dd_pct:.2f}% exceeds limit {self.config.max_drawdown_intraday_pct}%"
        
        return True, "OK"
