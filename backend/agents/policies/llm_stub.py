"""
LLM Policy Stub - Placeholder for future LLM integration

This policy:
- Receives compact observation
- Currently returns HOLD (no orders)
- Ready for LLM API integration in the future

Future integration:
- Format observation as JSON/text prompt
- Call LLM API (OpenAI, Anthropic, etc)
- Parse LLM response into Action
"""

from typing import Dict, Any, List
import json

from ..schemas import Observation, Action, ActionIntent, ActionOrder
from .base import Policy


class LLMPolicy(Policy):
    """
    LLM-based policy (stub implementation)
    
    Future workflow:
    1. Format observation → prompt
    2. Call LLM API
    3. Parse response → Action
    4. Validate and return
    
    Current: Always returns HOLD
    """
    
    def __init__(self, 
                 model: str = "gpt-4",
                 temperature: float = 0.7,
                 max_position_size: float = 1000.0,
                 verbose: bool = True):
        """
        Initialize LLM policy
        
        Args:
            model: LLM model name (for future use)
            temperature: Sampling temperature (for future use)
            max_position_size: Max position size in USD
            verbose: Print debug info
        """
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_position_size = max_position_size
        self.verbose = verbose
        
        if verbose:
            print(f"[LLMPolicy] Initialized (STUB mode)")
            print(f"  - Model: {model}")
            print(f"  - Temperature: {temperature}")
            print(f"  - Max position size: ${max_position_size:,.2f}")
            print(f"  - Note: LLM integration not yet implemented")
    
    def decide(self, observation: Observation) -> Action:
        """
        Make trading decision based on observation
        
        Current: Always returns HOLD
        Future: Will call LLM API
        
        Args:
            observation: Current market and portfolio state
        
        Returns:
            Action with intent and orders
        """
        
        # Format compact observation
        compact_obs = self._format_observation(observation)
        
        if self.verbose:
            print(f"[LLMPolicy] Compact observation:")
            print(json.dumps(compact_obs, indent=2))
        
        # TODO: Future LLM integration
        # prompt = self._build_prompt(compact_obs)
        # response = self._call_llm_api(prompt)
        # action = self._parse_llm_response(response)
        
        # Current: Always HOLD
        return Action(
            timestamp=observation.timestamp,
            intent=ActionIntent.HOLD,
            orders=[],
            notes="LLM policy stub - no action",
            confidence=1.0
        )
    
    def _format_observation(self, observation: Observation) -> Dict[str, Any]:
        """
        Format observation into compact JSON structure
        
        Structure:
        {
            "timestamp": unix_ms,
            "symbols": {
                "BTC/USDT": {
                    "price": 50000.0,
                    "candles": [...recent 10],
                    "indicators": {"rsi_14": 45.2, "atr_14": 1200, "ema_50": 49500},
                    "volatility": 0.025
                }
            },
            "portfolio": {
                "equity": 10000.0,
                "cash": 9500.0,
                "positions": [...],
                "exposure_pct": 5.0
            }
        }
        """
        
        formatted = {
            "timestamp": observation.timestamp,
            "symbols": {}
        }
        
        # Format market data per symbol
        for symbol, candles in observation.candles.items():
            if not candles:
                continue
            
            # Get last N candles
            recent_candles = candles[-10:] if len(candles) >= 10 else candles
            
            # Calculate indicators inline
            closes = [c.close for c in candles]
            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            
            indicators = self._calculate_indicators(closes, highs, lows)
            
            formatted["symbols"][symbol] = {
                "price": candles[-1].close,
                "candles": [
                    {
                        "ts": c.ts,
                        "open": c.open,
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "volume": c.volume
                    }
                    for c in recent_candles
                ],
                "indicators": indicators,
                "volatility": observation.volatility.get(symbol, 0.0)
            }
        
        # Format portfolio
        portfolio = observation.portfolio
        formatted["portfolio"] = {
            "equity": portfolio.equity,
            "cash": portfolio.cash,
            "realized_pnl": portfolio.realized_pnl,
            "unrealized_pnl": portfolio.unrealized_pnl,
            "total_pnl": portfolio.total_pnl,
            "exposure_pct": portfolio.exposure_pct,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "pnl_pct": pos.pnl_pct
                }
                for pos in portfolio.positions
            ]
        }
        
        return formatted
    
    def _calculate_indicators(self, closes: List[float], 
                             highs: List[float], 
                             lows: List[float]) -> Dict[str, float]:
        """
        Calculate basic indicators inline
        
        Returns:
            Dict with RSI(14), ATR(14), EMA(50)
        """
        indicators = {}
        
        # RSI(14)
        if len(closes) >= 15:
            rsi = self._rsi(closes, 14)
            indicators["rsi_14"] = round(rsi, 2)
        
        # ATR(14)
        if len(closes) >= 15:
            atr = self._atr(highs, lows, closes, 14)
            indicators["atr_14"] = round(atr, 2)
        
        # EMA(50)
        if len(closes) >= 50:
            ema = self._ema(closes, 50)
            indicators["ema_50"] = round(ema, 2)
        
        # Current price
        if closes:
            indicators["close"] = closes[-1]
        
        return indicators
    
    def _rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50.0
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _atr(self, highs: List[float], lows: List[float], 
             closes: List[float], period: int = 14) -> float:
        """Calculate ATR"""
        if len(closes) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        atr = sum(true_ranges[-period:]) / period
        return atr
    
    def _ema(self, closes: List[float], period: int = 50) -> float:
        """Calculate EMA"""
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        
        multiplier = 2 / (period + 1)
        ema = sum(closes[:period]) / period  # SMA for first value
        
        for close in closes[period:]:
            ema = (close * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _build_prompt(self, observation: Dict[str, Any]) -> str:
        """
        Build LLM prompt from observation (FUTURE)
        
        Example prompt structure:
        ```
        You are a crypto trading agent. Analyze the market and decide:
        
        Market Data:
        - BTC/USDT: $50,000 (RSI: 45, ATR: 1200)
        - Recent trend: ...
        
        Portfolio:
        - Equity: $10,000
        - Cash: $9,500
        - Positions: 1 (5% exposure)
        
        Respond with JSON:
        {
            "intent": "open_long" | "open_short" | "close_long" | "close_short" | "hold",
            "symbol": "BTC/USDT",
            "quantity": 0.02,
            "reasoning": "..."
        }
        ```
        """
        # TODO: Implement prompt engineering
        return ""
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        Call LLM API (FUTURE)
        
        Integration points:
        - OpenAI: openai.ChatCompletion.create()
        - Anthropic: anthropic.Anthropic().messages.create()
        - Local: ollama, llama.cpp, etc
        """
        # TODO: Implement API call
        return ""
    
    def _parse_llm_response(self, response: str) -> Action:
        """
        Parse LLM response into Action (FUTURE)
        
        Expected response format:
        {
            "intent": "open_long",
            "symbol": "BTC/USDT",
            "quantity": 0.02,
            "stop_loss": 49000,
            "take_profit": 52000,
            "reasoning": "RSI oversold + uptrend confirmed"
        }
        """
        # TODO: Implement parsing with validation
        return Action(
            timestamp=0,
            intent=ActionIntent.HOLD,
            orders=[],
            notes="",
            confidence=1.0
        )