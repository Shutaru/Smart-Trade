"""
Pydantic schemas for Agent Runner
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class Candle(BaseModel):
    """OHLCV candle data"""
    ts: int = Field(..., description="Unix timestamp (milliseconds)")
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
    
    @validator('high')
    def high_must_be_highest(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('high must be >= low')
        return v
    
    @validator('low')
    def low_must_be_lowest(cls, v, values):
        if 'high' in values and v > values['high']:
            raise ValueError('low must be <= high')
        return v


class OrderSide(str, Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order(BaseModel):
    """Order representation"""
    id: str = Field(..., description="Unique order ID")
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0, description="Limit price")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop trigger price")
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = Field(0.0, ge=0)
    average_fill_price: Optional[float] = None
    timestamp: int = Field(..., description="Order creation timestamp (ms)")
    fee: float = Field(0.0, ge=0, description="Fee paid in base currency")


class Position(BaseModel):
    """Open position"""
    symbol: str
    side: Literal["long", "short"]
    quantity: float = Field(..., gt=0, description="Position size")
    entry_price: float = Field(..., gt=0, description="Average entry price")
    current_price: float = Field(..., gt=0, description="Current market price")
    unrealized_pnl: float = Field(..., description="Unrealized P&L in quote currency")
    realized_pnl: float = Field(0.0, description="Realized P&L from partial closes")
    leverage: float = Field(1.0, ge=1.0, le=125.0)
    liquidation_price: Optional[float] = Field(None, gt=0)
    opened_at: int = Field(..., description="Position open timestamp (ms)")
    
    @property
    def notional(self) -> float:
        """Position notional value"""
        return self.quantity * self.current_price
    
    @property
    def pnl_pct(self) -> float:
        """P&L percentage"""
        if self.side == "long":
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:  # short
            return ((self.entry_price - self.current_price) / self.entry_price) * 100


class PortfolioState(BaseModel):
    """Current portfolio state"""
    cash: float = Field(..., ge=0, description="Available cash in base currency (USDT)")
    positions: List[Position] = Field(default_factory=list)
    equity: float = Field(..., ge=0, description="Total equity = cash + unrealized PnL")
    unrealized_pnl: float = Field(0.0, description="Sum of all unrealized PnL")
    realized_pnl: float = Field(0.0, description="Cumulative realized PnL")
    total_pnl: float = Field(0.0, description="unrealized + realized")
    timestamp: int = Field(..., description="State snapshot timestamp (ms)")
    
    @property
    def exposure(self) -> float:
        """Total exposure (sum of position notionals)"""
        return sum(pos.notional for pos in self.positions)
    
    @property
    def exposure_pct(self) -> float:
        """Exposure as % of equity"""
        if self.equity == 0:
            return 0.0
        return (self.exposure / self.equity) * 100


class Observation(BaseModel):
    """Agent observation of market and portfolio state"""
    timestamp: int = Field(..., description="Observation timestamp (ms)")
    candles: Dict[str, List[Candle]] = Field(..., description="Recent candles per symbol")
    portfolio: PortfolioState
    volatility: Dict[str, float] = Field(default_factory=dict, description="Volatility per symbol")
    
    @property
    def symbols(self) -> List[str]:
        """List of symbols in observation"""
        return list(self.candles.keys())


class ActionIntent(str, Enum):
    """Agent action intent"""
    HOLD = "hold"
    OPEN_LONG = "open_long"
    OPEN_SHORT = "open_short"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    ADJUST_SL = "adjust_sl"
    ADJUST_TP = "adjust_tp"


class ActionOrder(BaseModel):
    """Order within an Action"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = None
    take_profit: Optional[float] = Field(None, gt=0, description="TP price")
    stop_loss: Optional[float] = Field(None, gt=0, description="SL price")


class Action(BaseModel):
    """Agent action (output of policy)"""
    timestamp: int = Field(..., description="Action timestamp (ms)")
    intent: ActionIntent
    orders: List[ActionOrder] = Field(default_factory=list, description="Orders to execute")
    notes: str = Field("", description="Reasoning or comments")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    
    @validator('orders')
    def validate_orders(cls, v, values):
        """Ensure orders match intent"""
        intent = values.get('intent')
        if intent == ActionIntent.HOLD and len(v) > 0:
            raise ValueError("HOLD intent should have no orders")
        if intent != ActionIntent.HOLD and len(v) == 0:
            raise ValueError(f"{intent} intent requires at least one order")
        return v


class FillReport(BaseModel):
    """Order fill result"""
    order_id: str
    symbol: str
    side: OrderSide
    filled_quantity: float = Field(..., ge=0)
    average_price: float = Field(..., gt=0)
    fee: float = Field(..., ge=0)
    slippage_bps: float = Field(..., description="Slippage in basis points")
    timestamp: int


class Metrics(BaseModel):
    """Performance metrics snapshot"""
    timestamp: int
    equity: float = Field(..., ge=0)
    cash: float = Field(..., ge=0)
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    num_positions: int = Field(..., ge=0)


class RunConfig(BaseModel):
    """Configuration for a single agent run"""
    run_id: str
    exchange: Literal["bitget", "binance"]
    symbols: List[str] = Field(..., min_items=1)
    timeframe: str = Field("5m", regex=r"^\d+[mhd]$")
    paper_mode: bool = Field(True, description="Paper trading mode (no real orders)")
    initial_cash: float = Field(10_000.0, gt=0, description="Starting cash in USDT")
    loop_interval_secs: int = Field(2, ge=1, le=60, description="Loop sleep time")
    data_lookback_bars: int = Field(1000, ge=50, le=5000, description="Historical bars to fetch")
    base_currency: str = Field("USDT")
    
    # Risk limits
    max_exposure_pct: float = Field(95.0, gt=0, le=100, description="Max % of equity exposed")
    max_leverage: float = Field(3.0, ge=1.0, le=125.0)
    max_positions: int = Field(3, ge=1, le=20)
    max_drawdown_intraday_pct: float = Field(5.0, gt=0, le=50, description="Max intraday DD before halt")
    require_sl_tp: bool = Field(False, description="Require SL/TP on all orders (for live mode)")


class TrajectoryEvent(BaseModel):
    """Single event in agent trajectory (for JSONL logging)"""
    timestamp: int
    step: int
    event_type: Literal["observation", "action", "fill", "metrics", "error"]
    data: Dict[str, Any]