from pydantic import BaseModel, Field
from typing import Optional, Union, List, Dict, Any


class IndicatorParam(BaseModel):
    name: str
    value: Union[float, int, str, bool]


class Condition(BaseModel):
    indicator: str
    timeframe: str
    op: str
    lookback: Optional[int] = None
    params: List[IndicatorParam] = []
    rhs: Optional[float] = None
    rhs_indicator: Optional[str] = None
    rhs_params: List[IndicatorParam] = []


class ExitRule(BaseModel):
    kind: str
    params: Dict[str, Any] = Field(default_factory=dict)


class StrategySide(BaseModel):
    entry_all: List[Condition] = Field(default_factory=list)
    entry_any: List[Condition] = Field(default_factory=list)
    exit_rules: List[ExitRule] = Field(default_factory=list)


class Objective(BaseModel):
    expression: str


class DataSpec(BaseModel):
    exchange: str
    symbols: List[str]
    timeframe: str
    since: int
    until: int
    higher_tf: List[str] = Field(default_factory=lambda: ["1h", "4h"])


class RiskSpec(BaseModel):
    leverage: Union[tuple, float] = 3.0
    position_sizing: str = "fixed_usd"
    size_value: float = 1000.0
    max_concurrent_positions: int = 1


class ParamRange(BaseModel):
    name: str
    low: float
    high: float
    step: Optional[float] = None
    log: Optional[bool] = None
    int_: Optional[bool] = None


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


class BackfillRequest(BaseModel):
    exchange: str
    symbol: str
    timeframe: str
    since: int
    until: int
    higher_tf: List[str] = Field(default_factory=lambda: ["1h", "4h"])


class BackfillResponse(BaseModel):
    success: bool
    message: str
    candles_downloaded: int
    db_path: str


class ValidateStrategyResponse(BaseModel):
    valid: bool
    features_required: List[str]
    errors: List[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    strategy: StrategyConfig
    mode: str
    n_trials: Optional[int] = None
    timeout_seconds: Optional[int] = None
    seed: Optional[int] = None


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


class TrialResult(BaseModel):
    trial_id: int
    params: Dict[str, Any]
    metrics: Dict[str, float]
    score: float


class RunResultsResponse(BaseModel):
    run_id: str
    trials: List[TrialResult]
    total: int