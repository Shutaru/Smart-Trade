"""
Agent configuration management
"""

import os
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from pathlib import Path
import yaml


class AgentConfig(BaseModel):
    """Agent runner configuration"""
    
    # Exchange settings
    exchange: Literal["bitget", "binance"] = "bitget"
    symbols: List[str] = Field(default_factory=lambda: ["BTC/USDT:USDT"])
    timeframe: str = "5m"
    base_currency: str = "USDT"
    
    # Trading mode
    paper_mode: bool = True
    
    # Policy selection
    policy: Literal["rule_based", "llm"] = "rule_based"
    
    # Risk limits
    max_exposure_pct: float = Field(50.0, ge=1.0, le=100.0, description="Max % of equity per symbol")
    max_leverage: float = Field(3.0, ge=1.0, le=10.0)
    max_drawdown_intraday_pct: float = Field(5.0, ge=1.0, le=20.0)
    max_concurrent_positions: int = Field(3, ge=1, le=10)
    require_stop_loss: bool = True
    
    # Data settings
    data_lookback_bars: int = Field(1000, ge=100, le=5000)
    
    # Execution
    loop_interval_secs: int = Field(2, ge=1, le=60, description="Seconds between decision cycles")
    initial_cash: float = Field(10000.0, ge=1000.0)
    
    # Fees (basis points)
    taker_fee_bps: float = 5.0
    maker_fee_bps: float = 2.0
    slippage_bps: float = 1.0
    
    # Paths
    runs_dir: Path = Field(default_factory=lambda: Path("runs"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))
    
    @validator('symbols')
    def validate_symbols(cls, symbols):
        if not symbols:
            raise ValueError("At least one symbol required")
        return symbols
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_yaml(cls, path: str) -> "AgentConfig":
        """Load config from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, path: str):
        """Save config to YAML file"""
        data = self.dict()
        # Convert Path objects to strings
        data['runs_dir'] = str(data['runs_dir'])
        data['logs_dir'] = str(data['logs_dir'])
        
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)