"""
Agent configuration management
"""

import os
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Dict, Any
from pathlib import Path
import yaml


class LLMConfig(BaseModel):
    """LLM provider configuration"""
    provider: Literal["ollama", "openai", "anthropic"] = "ollama"
    endpoint: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:14b-instruct"
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=50, le=4096)
    timeout: float = Field(10.0, ge=1.0, le=60.0, description="API timeout in seconds")
    retry_attempts: int = Field(2, ge=0, le=5)
    system_prompt: Optional[str] = None
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)


class LLMAdvancedConfig(BaseModel):
    """Advanced LLM settings"""
    enable_chain_of_thought: bool = True
    enable_self_critique: bool = False
    min_confidence: float = Field(0.7, ge=0.0, le=1.0)
    log_prompts: bool = True


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
    fallback_policy: Optional[Literal["rule_based", "llm"]] = Field(
        "rule_based",
        description="Fallback policy if primary fails"
    )
    
    # LLM Configuration (optional, only used if policy='llm')
    llm: Optional[LLMConfig] = None
    llm_advanced: Optional[LLMAdvancedConfig] = None
    
    # Risk limits
    max_exposure_pct: float = Field(50.0, ge=1.0, le=100.0, description="Max % of equity per symbol")
    max_total_exposure_pct: float = Field(95.0, ge=1.0, le=100.0, description="Total portfolio exposure")
    max_leverage: float = Field(3.0, ge=1.0, le=10.0)
    max_drawdown_intraday_pct: float = Field(5.0, ge=1.0, le=20.0)
    max_concurrent_positions: int = Field(3, ge=1, le=10)
    require_stop_loss: bool = True
    
    # Per-trade risk management (NEW)
    per_trade_risk_pct: float = Field(1.0, ge=0.1, le=5.0, description="Max % loss per trade")
    min_risk_reward: float = Field(1.5, ge=0.5, le=10.0, description="Minimum R:R ratio")
    max_position_size_pct: float = Field(20.0, ge=1.0, le=100.0, description="Max position size as % of equity")
    
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
    
    @validator('llm')
    def validate_llm_config(cls, llm, values):
        """Validate LLM config if policy is 'llm'"""
        policy = values.get('policy')
        if policy == 'llm' and llm is None:
            raise ValueError("LLM config required when policy='llm'")
        return llm
    
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