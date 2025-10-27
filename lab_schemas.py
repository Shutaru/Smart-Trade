from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List, Dict, Any
from enum import Enum


class ConditionOperator(str, Enum):
    """Supported comparison operators"""
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    BETWEEN = "between"
    CROSSES_UP = "crosses_up"
    CROSSES_DOWN = "crosses_down"


class ExitRuleKind(str, Enum):
    """Supported exit rule types"""
    TP_SL_FIXED = "tp_sl_fixed"
    ATR_TRAILING = "atr_trailing"
    CHANDELIER = "chandelier"
    BB_TARGET = "bb_target"
    TIME_EXIT = "time_exit"


class IndicatorParam(BaseModel):
    name: str
    value: Union[float, int, str, bool]


class Condition(BaseModel):
    indicator: str
    timeframe: str
    op: ConditionOperator
    lookback: Optional[int] = None
    params: List[IndicatorParam] = Field(default_factory=list)
    rhs: Optional[float] = None
    rhs_indicator: Optional[str] = None
    rhs_params: List[IndicatorParam] = Field(default_factory=list)


class ExitRule(BaseModel):
    kind: ExitRuleKind
    params: Dict[str, Any] = Field(default_factory=dict)


class StrategySide(BaseModel):
    entry_all: List[Condition] = Field(default_factory=list)
    entry_any: List[Condition] = Field(default_factory=list)
    exit_rules: List[ExitRule] = Field(default_factory=list)


class Objective(BaseModel):
    """
    Objective function to optimize
    
    Allowed variables:
    - sharpe, sortino, calmar
    - total_profit, max_dd, win_rate
    - profit_factor, avg_trade, trades, exposure
    """
    expression: str


class DataSpec(BaseModel):
    exchange: str
    symbols: List[str]
    timeframe: str
    since: int
    until: int
    higher_tf: List[str] = Field(default_factory=lambda: ["1h", "4h"])


class RiskSpec(BaseModel):
    leverage: Union[float, tuple] = 3.0
    position_sizing: str = "fixed_usd"
    size_value: float = 1000.0
    max_concurrent_positions: int = 1


class ParamRange(BaseModel):
    name: str
    low: float
    high: float
    step: Optional[float] = None
    log: Optional[bool] = False
    int_: Optional[bool] = False


class StrategyConfig(BaseModel):
    name: str
    long: StrategySide
    short: StrategySide
    data: DataSpec
    risk: RiskSpec
    objective: Objective
    param_space: List[ParamRange] = Field(default_factory=list)
    warmup_bars: int = 300


class ExchangeListResponse(BaseModel):
    exchanges: List[str]


class SymbolListResponse(BaseModel):
    symbols: List[str]


class IndicatorInfo(BaseModel):
    id: str
    name: str
    params: Dict[str, Any]
    supported_timeframes: List[str]
    description: str


class IndicatorCatalogResponse(BaseModel):
    indicators: List[IndicatorInfo]


class ValidateStrategyResponse(BaseModel):
    valid: bool
    features_required: List[str]
    errors: List[str] = Field(default_factory=list)


class RunResponse(BaseModel):
    run_id: str
    status: str


class RunStatus(BaseModel):
    run_id: str
    status: str
    progress: float
    current_trial: Optional[int] = None
    total_trials: Optional[int] = None
    best_score: Optional[float] = None
    started_at: Optional[int] = None
    completed_at: Optional[int] = None