"""
Pydantic schemas for Agent Runner
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class Candle(BaseModel):
    """OHLCV candle data"""
    ts: int = Field(..., description="Unix timestamp in milliseconds")
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    class Config:
        frozen = True


class Position(BaseModel):
    """Open position"""
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry_price: float
    quantity: float
    unrealized_pnl: float = 0.0
    entry_ts: int = Field(..., description="Entry timestamp (ms)")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class Order(BaseModel):
    """Order representation"""
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT", "STOP_MARKET"]
    quantity: float
    price: Optional[float] = None  # For LIMIT orders
    stop_price: Optional[float] = None  # For STOP orders
    status: Literal["PENDING", "FILLED", "CANCELLED", "REJECTED"] = "PENDING"
filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    fees: float = 0.0
    timestamp: int = Field(..., description="Order timestamp (ms)")


class PortfolioState(BaseModel):
    """Complete portfolio state snapshot"""
    timestamp: int
    cash: float
    positions: List[Position] = Field(default_factory=list)
    equity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    margin_used: float = 0.0
    
    @property
    def total_pnl(self) -> float:
 return self.realized_pnl + self.unrealized_pnl


class Observation(BaseModel):
    """Market observation for decision making"""
    timestamp: int
    candles: Dict[str, List[Candle]] = Field(..., description="Symbol -> recent candles")
    portfolio: PortfolioState
    volatility: Dict[str, float] = Field(default_factory=dict, description="Recent volatility per symbol")
    
    class Config:
        arbitrary_types_allowed = True


class Action(BaseModel):
    """Agent action with strict validation"""
    timestamp: int
    intent: str = Field(..., description="Human-readable action intent")
    orders: List[Order] = Field(default_factory=list)
    notes: Optional[str] = None
    
    @validator('orders')
    def validate_orders(cls, orders):
"""Validate orders make sense"""
   if len(orders) > 10:
          raise ValueError("Maximum 10 orders per action")
        return orders


class Metrics(BaseModel):
    """Performance metrics snapshot"""
    timestamp: int
    equity: float
    cash: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    num_positions: int
 sharpe_rolling: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    win_rate: Optional[float] = None


class TrajectoryEvent(BaseModel):
    """Single event in agent trajectory log"""
  run_id: str
    timestamp: int
    event_type: Literal["observation", "action", "fill", "metrics", "error"]
    data: Dict[str, Any]
    
    class Config:
     arbitrary_types_allowed = True
