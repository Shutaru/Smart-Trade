"""
Portfolio management tool with mark-to-market and position tracking

Features:
- Position tracking with average entry price
- Mark-to-market unrealized PnL calculation
- Realized PnL tracking
- Equity calculation (cash + unrealized PnL)
- Position averaging for scaling in/out
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
import time

from ..schemas import PortfolioState, Position, OrderSide
from ..config import AgentConfig


@dataclass
class PositionInternal:
    """Internal position representation with detailed tracking"""
    symbol: str
    side: str  # "LONG" or "SHORT"
    quantity: float
    entry_price: float  # Average entry price
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0  # From partial closes
    opened_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def to_schema_position(self) -> Position:
        """Convert to schema Position"""
        return Position(
            symbol=self.symbol,
            side=self.side.lower(),
            quantity=self.quantity,
            entry_price=self.entry_price,
            current_price=self.current_price,
            unrealized_pnl=self.unrealized_pnl,
            realized_pnl=self.realized_pnl,
            leverage=1.0,  # Simplified for paper trading
            opened_at=self.opened_at
        )


class PortfolioTool:
    """
    Manage portfolio state with realistic position tracking
    
    Features:
    - Position averaging when scaling in
    - Partial position closes
    - Mark-to-market for unrealized PnL
    - Realized PnL tracking
    - Cash management with fees
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        # Starting state
        self.initial_cash = config.initial_cash
        self.cash = config.initial_cash
        
        # Positions: {symbol: PositionInternal}
        self.positions: Dict[str, PositionInternal] = {}
        
        # PnL tracking
        self.realized_pnl = 0.0
        self.total_fees_paid = 0.0
        
        # High-water mark for drawdown
        self.high_water_mark = config.initial_cash
        self.max_drawdown_pct = 0.0
    
    def execute_trade(self, symbol: str, side: OrderSide, quantity: float, 
                      price: float, fee: float):
        """
        Execute a trade and update positions/cash
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Trade quantity
            price: Execution price
            fee: Trading fee paid
        """
        self.total_fees_paid += fee
        
        if side == OrderSide.BUY:
            self._handle_buy(symbol, quantity, price, fee)
        elif side == OrderSide.SELL:
            self._handle_sell(symbol, quantity, price, fee)
    
    def _handle_buy(self, symbol: str, quantity: float, price: float, fee: float):
        """Handle BUY order"""
        
        # Cost = notional + fee
        cost = (quantity * price) + fee
        
        # Check if position exists
        if symbol in self.positions:
            pos = self.positions[symbol]
            
            if pos.side == "LONG":
                # Scale into LONG: average entry price
                total_quantity = pos.quantity + quantity
                total_cost = (pos.quantity * pos.entry_price) + (quantity * price) + fee
                new_avg_price = total_cost / total_quantity
                
                pos.quantity = total_quantity
                pos.entry_price = new_avg_price
            
            elif pos.side == "SHORT":
                # Closing SHORT position
                if quantity >= pos.quantity:
                    # Full close
                    pnl = (pos.entry_price - price) * pos.quantity - fee
                    self.realized_pnl += pnl
                    self.cash += (pos.quantity * pos.entry_price) - cost
                    del self.positions[symbol]
                    
                    # If quantity > position, reverse to LONG
                    if quantity > pos.quantity:
                        remaining_qty = quantity - pos.quantity
                        self.positions[symbol] = PositionInternal(
                            symbol=symbol,
                            side="LONG",
                            quantity=remaining_qty,
                            entry_price=price,
                            current_price=price
                        )
                else:
                    # Partial close
                    pnl = (pos.entry_price - price) * quantity - fee
                    self.realized_pnl += pnl
                    pos.quantity -= quantity
                    self.cash -= cost
        else:
            # New LONG position
            self.positions[symbol] = PositionInternal(
                symbol=symbol,
                side="LONG",
                quantity=quantity,
                entry_price=price,
                current_price=price
            )
            self.cash -= cost
    
    def _handle_sell(self, symbol: str, quantity: float, price: float, fee: float):
        """Handle SELL order"""
        
        # Revenue = notional - fee
        revenue = (quantity * price) - fee
        
        # Check if position exists
        if symbol in self.positions:
            pos = self.positions[symbol]
            
            if pos.side == "LONG":
                # Closing LONG position
                if quantity >= pos.quantity:
                    # Full close
                    pnl = (price - pos.entry_price) * pos.quantity - fee
                    self.realized_pnl += pnl
                    self.cash += revenue
                    del self.positions[symbol]
                    
                    # If quantity > position, reverse to SHORT
                    if quantity > pos.quantity:
                        remaining_qty = quantity - pos.quantity
                        self.positions[symbol] = PositionInternal(
                            symbol=symbol,
                            side="SHORT",
                            quantity=remaining_qty,
                            entry_price=price,
                            current_price=price
                        )
                else:
                    # Partial close
                    pnl = (price - pos.entry_price) * quantity - fee
                    self.realized_pnl += pnl
                    pos.quantity -= quantity
                    self.cash += revenue
            
            elif pos.side == "SHORT":
                # Scale into SHORT: average entry price
                total_quantity = pos.quantity + quantity
                total_revenue = (pos.quantity * pos.entry_price) + revenue
                new_avg_price = total_revenue / total_quantity
                
                pos.quantity = total_quantity
                pos.entry_price = new_avg_price
        else:
            # New SHORT position
            self.positions[symbol] = PositionInternal(
                symbol=symbol,
                side="SHORT",
                quantity=quantity,
                entry_price=price,
                current_price=price
            )
            self.cash += revenue
    
    def mark_to_market(self, prices: Dict[str, float]):
        """
        Update positions with current prices and calculate unrealized PnL
        
        Args:
            prices: {symbol: current_price}
        """
        for symbol, pos in self.positions.items():
            if symbol not in prices:
                continue
            
            current_price = prices[symbol]
            pos.current_price = current_price
            
            # Calculate unrealized PnL
            if pos.side == "LONG":
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
            elif pos.side == "SHORT":
                pos.unrealized_pnl = (pos.entry_price - current_price) * pos.quantity
        
        # Update equity high-water mark and drawdown
        equity = self.get_equity()
        if equity > self.high_water_mark:
            self.high_water_mark = equity
        
        drawdown = ((equity - self.high_water_mark) / self.high_water_mark) * 100
        if drawdown < self.max_drawdown_pct:
            self.max_drawdown_pct = drawdown
    
    def snapshot(self, timestamp: Optional[int] = None) -> PortfolioState:
        """
        Get current portfolio state snapshot
        
        Args:
            timestamp: Custom timestamp (defaults to now)
        
        Returns:
            PortfolioState with current cash, positions, PnL, equity
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        # Convert positions to schema format
        position_list = [pos.to_schema_position() for pos in self.positions.values()]
        
        # Calculate totals
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        equity = self.cash + unrealized_pnl
        total_pnl = self.realized_pnl + unrealized_pnl
        
        return PortfolioState(
            timestamp=timestamp,
            cash=self.cash,
            positions=position_list,
            equity=equity,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=self.realized_pnl,
            total_pnl=total_pnl
        )
    
    def get_equity(self) -> float:
        """Get current total equity (cash + unrealized PnL)"""
        unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.cash + unrealized
    
    def get_position(self, symbol: str) -> Optional[PositionInternal]:
        """Get position for a symbol"""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if position exists for symbol"""
        return symbol in self.positions
    
    def get_exposure(self) -> float:
        """Get total notional exposure across all positions"""
        return sum(pos.quantity * pos.current_price for pos in self.positions.values())
    
    def get_exposure_pct(self) -> float:
        """Get exposure as % of equity"""
        equity = self.get_equity()
        if equity == 0:
            return 0.0
        return (self.get_exposure() / equity) * 100
    
    def get_pnl_pct(self) -> float:
        """Get total PnL as % of initial capital"""
        total_pnl = self.realized_pnl + sum(pos.unrealized_pnl for pos in self.positions.values())
        return (total_pnl / self.initial_cash) * 100
    
    def get_position_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)
    
    def close_all_positions(self, prices: Dict[str, float]):
        """
        Close all positions at current prices (emergency exit)
        
        Args:
            prices: {symbol: current_price}
        """
        for symbol in list(self.positions.keys()):
            if symbol not in prices:
                continue
            
            pos = self.positions[symbol]
            price = prices[symbol]
            
            # Close position
            if pos.side == "LONG":
                pnl = (price - pos.entry_price) * pos.quantity
                self.cash += pos.quantity * price
            elif pos.side == "SHORT":
                pnl = (pos.entry_price - price) * pos.quantity
                self.cash -= pos.quantity * price
            
            self.realized_pnl += pnl
            del self.positions[symbol]
    
    def reset(self):
        """Reset portfolio to initial state (for testing)"""
        self.cash = self.initial_cash
        self.positions.clear()
        self.realized_pnl = 0.0
        self.total_fees_paid = 0.0
        self.high_water_mark = self.initial_cash
        self.max_drawdown_pct = 0.0