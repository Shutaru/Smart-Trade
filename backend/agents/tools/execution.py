"""
Execution tool for paper trading
"""

from typing import List, Dict, Tuple
import time
import uuid
from ..schemas import Order, Position
from ..config import AgentConfig
from .portfolio import PortfolioTool


class ExecutionTool:
    """Simulate order execution in paper mode"""
  
    def __init__(self, config: AgentConfig, portfolio: PortfolioTool):
        self.config = config
        self.portfolio = portfolio
    
    def execute_orders(self, orders: List[Order], current_prices: Dict[str, float]) -> List[Order]:
        """
        Execute list of orders
      
        Args:
            orders: Orders to execute
      current_prices: Current market prices per symbol
        
        Returns:
         List of filled orders with execution details
     """
        
        filled_orders = []
   
        for order in orders:
      filled = self._execute_single_order(order, current_prices.get(order.symbol))
        if filled:
         filled_orders.append(filled)
        
   return filled_orders
    
    def _execute_single_order(self, order: Order, current_price: Optional[float]) -> Optional[Order]:
    """Execute single order"""
        
        if current_price is None:
            order.status = "REJECTED"
   return order
      
 # Determine fill price based on order type
        if order.order_type == "MARKET":
            fill_price = self._apply_slippage(current_price, order.side)
        elif order.order_type == "LIMIT":
 if order.price is None:
             order.status = "REJECTED"
   return order
            # Simulate limit order fill if price reached
            if (order.side == "BUY" and current_price <= order.price) or \
      (order.side == "SELL" and current_price >= order.price):
              fill_price = order.price
            else:
           order.status = "PENDING"
            return order
        else:
            order.status = "REJECTED"
       return order
    
        # Calculate fees
        fees = self._calculate_fees(order.quantity, fill_price, is_maker=(order.order_type == "LIMIT"))
        
  # Update order
        order.status = "FILLED"
        order.filled_price = fill_price
   order.filled_quantity = order.quantity
        order.fees = fees
        order.timestamp = int(time.time() * 1000)
        
  # Update portfolio
        self._update_portfolio(order, fill_price, fees)
   
        return order
    
    def _apply_slippage(self, price: float, side: str) -> float:
     """Apply slippage to market order"""
        slippage_factor = self.config.slippage_bps / 10000.0
 
        if side == "BUY":
   return price * (1 + slippage_factor)
     else:  # SELL
  return price * (1 - slippage_factor)
    
    def _calculate_fees(self, quantity: float, price: float, is_maker: bool) -> float:
      """Calculate trading fees"""
        notional = quantity * price
        fee_bps = self.config.maker_fee_bps if is_maker else self.config.taker_fee_bps
     return notional * (fee_bps / 10000.0)
    
    def _update_portfolio(self, order: Order, fill_price: float, fees: float):
    """Update portfolio after order fill"""
        
 symbol = order.symbol
        notional = order.quantity * fill_price
        
        if order.side == "BUY":
            # Opening LONG position
       self.portfolio.update_cash(-(notional + fees))
            
   position = Position(
              symbol=symbol,
        side="LONG",
          entry_price=fill_price,
  quantity=order.quantity,
                entry_ts=order.timestamp
      )
   self.portfolio.add_position(position)
        
        elif order.side == "SELL":
    # Closing LONG position or opening SHORT
            existing_pos = self.portfolio.positions.get(symbol)
            
    if existing_pos and existing_pos.side == "LONG":
     # Close LONG
         pnl = (fill_price - existing_pos.entry_price) * existing_pos.quantity
     self.portfolio.update_cash(notional - fees)
        self.portfolio.update_realized_pnl(pnl - fees)
  self.portfolio.remove_position(symbol)
       else:
         # Open SHORT
self.portfolio.update_cash(notional - fees)
          position = Position(
            symbol=symbol,
     side="SHORT",
         entry_price=fill_price,
          quantity=order.quantity,
              entry_ts=order.timestamp
          )
           self.portfolio.add_position(position)
