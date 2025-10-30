"""
LLM Policy - Real Ollama Integration

Connects to local Ollama instance and makes trading decisions using LLM reasoning.

Workflow:
1. Format observation → structured prompt
2. Call Ollama API with retry logic
3. Parse JSON response → Action
4. Validate and return
"""

import json
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..schemas import Observation, Action, ActionIntent, ActionOrder, OrderSide, OrderType
from ..config import AgentConfig
from .base import Policy
from .rule_based import RSIRulePolicy  # Fallback


class OllamaClient:
    """
    HTTP client for Ollama API
    
    Endpoint: POST /api/generate
    Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
    """
    
    def __init__(self, endpoint: str, model: str, timeout: float = 10.0):
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
        self.generate_url = f"{endpoint}/api/generate"
    
    def generate(self, prompt: str, system: Optional[str] = None,
                temperature: float = 0.0, max_tokens: int = 512) -> str:
        """
        Generate completion from Ollama
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
        
        Returns:
            Generated text
        
        Raises:
            requests.RequestException: If API call fails
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
        
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")


class LLMPolicy(Policy):
    """
    LLM-powered trading policy using Ollama
    
    Features:
    - Structured prompt with observation data
    - JSON output parsing
    - Retry logic with exponential backoff
    - Fallback to rule-based policy
    - Prompt logging for debugging
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__()
        self.config = config
        
        # Validate LLM config
        if not config.llm:
            raise ValueError("LLM config required for LLMPolicy")
        
        # Initialize Ollama client
        self.client = OllamaClient(
            endpoint=config.llm.endpoint,
            model=config.llm.model,
            timeout=config.llm.timeout
        )
        
        # Fallback policy
        self.fallback_policy = None
        if config.fallback_policy == "rule_based":
            self.fallback_policy = RSIRulePolicy(
                rsi_period=14,
                oversold=30.0,
                overbought=70.0,
                position_size=1000.0
            )
            print(f"[LLMPolicy] Fallback policy: RSI Rule-Based")
        
        # Stats
        self.calls_total = 0
        self.calls_success = 0
        self.calls_failed = 0
        self.fallback_count = 0
        
        print(f"[LLMPolicy] Initialized")
        print(f"  - Model: {config.llm.model}")
        print(f"  - Endpoint: {config.llm.endpoint}")
        print(f"  - Temperature: {config.llm.temperature}")
        print(f"  - Max tokens: {config.llm.max_tokens}")
    
    def decide(self, observation: Observation) -> Action:
        """
        Make trading decision using LLM
        
        Args:
            observation: Current market and portfolio state
        
        Returns:
            Action with intent and orders
        """
        self.calls_total += 1
        
        try:
            # 1. Format observation into compact structure
            obs_data = self._format_observation(observation)
            
            # 2. Build prompt
            prompt = self._build_prompt(obs_data)
            system_prompt = self._get_system_prompt()
            
            # 3. Call LLM with retry
            response_text = self._call_llm_with_retry(
                prompt=prompt,
                system=system_prompt,
                max_retries=self.config.llm.retry_attempts
            )
            
            # 4. Parse JSON response
            action = self._parse_response(response_text, observation)
            
            # 5. Log if enabled
            if self.config.llm_advanced and self.config.llm_advanced.log_prompts:
                self._log_prompt_response(prompt, response_text, action)
            
            self.calls_success += 1
            return action
        
        except Exception as e:
            self.calls_failed += 1
            print(f"[LLMPolicy] ❌ Error: {e}")
            
            # Fallback to rule-based
            if self.fallback_policy:
                print(f"[LLMPolicy] 🔄 Using fallback policy")
                self.fallback_count += 1
                return self.fallback_policy.decide(observation)
            
            # No fallback - return HOLD
            return Action(
                timestamp=observation.timestamp,
                intent=ActionIntent.HOLD,
                orders=[],
                notes=f"LLM failed: {str(e)}",
                confidence=0.0
            )
    
    def _format_observation(self, observation: Observation) -> Dict[str, Any]:
        """Format observation into compact JSON for LLM"""
        
        formatted = {
            "timestamp": observation.timestamp,
            "datetime": datetime.fromtimestamp(observation.timestamp / 1000).isoformat(),
            "symbols": {}
        }
        
        # Market data per symbol
        for symbol, candles in observation.candles.items():
            if not candles or len(candles) < 50:
                continue
            
            # Get recent candles
            recent = candles[-10:]
            
            # Calculate indicators
            closes = [c.close for c in candles]
            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            
            indicators = self._calculate_indicators(closes, highs, lows)
            
            formatted["symbols"][symbol] = {
                "current_price": candles[-1].close,
                "price_change_pct": ((candles[-1].close - candles[-10].close) / candles[-10].close) * 100 if len(candles) >= 10 else 0,
                "recent_candles": [
                    {
                        "close": c.close,
                        "volume": c.volume,
                        "change_pct": ((c.close - c.open) / c.open) * 100
                    }
                    for c in recent[-5:]  # Last 5 candles only
                ],
                "indicators": indicators,
                "volatility": observation.volatility.get(symbol, 0.0)
            }
        
        # Portfolio state
        portfolio = observation.portfolio
        formatted["portfolio"] = {
            "equity": portfolio.equity,
            "cash": portfolio.cash,
            "total_pnl": portfolio.total_pnl,
            "total_pnl_pct": (portfolio.total_pnl / (portfolio.equity - portfolio.total_pnl)) * 100 if portfolio.equity > portfolio.total_pnl else 0,
            "num_positions": len(portfolio.positions),
            "exposure_pct": portfolio.exposure_pct,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "pnl_pct": pos.pnl_pct,
                    "unrealized_pnl": pos.unrealized_pnl
                }
                for pos in portfolio.positions
            ]
        }
        
        return formatted
    
    def _calculate_indicators(self, closes: List[float], 
                             highs: List[float], 
                             lows: List[float]) -> Dict[str, float]:
        """Calculate technical indicators"""
        
        indicators = {}
        
        # RSI(14)
        if len(closes) >= 15:
            rsi = self._rsi(closes, 14)
            indicators["rsi_14"] = round(rsi, 2)
        
        # EMA(20) and EMA(50)
        if len(closes) >= 20:
            ema20 = self._ema(closes, 20)
            indicators["ema_20"] = round(ema20, 2)
        
        if len(closes) >= 50:
            ema50 = self._ema(closes, 50)
            indicators["ema_50"] = round(ema50, 2)
        
        # Price vs EMAs
        if "ema_20" in indicators and "ema_50" in indicators:
            current = closes[-1]
            indicators["price_vs_ema20_pct"] = round(((current - indicators["ema_20"]) / indicators["ema_20"]) * 100, 2)
            indicators["price_vs_ema50_pct"] = round(((current - indicators["ema_50"]) / indicators["ema_50"]) * 100, 2)
        
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
    
    def _ema(self, closes: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        
        multiplier = 2 / (period + 1)
        ema = sum(closes[:period]) / period  # SMA for first value
        
        for close in closes[period:]:
            ema = (close * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _get_system_prompt(self) -> str:
        """Get system prompt from config or use default"""
        
        if self.config.llm.system_prompt:
            return self.config.llm.system_prompt
        
        # Default system prompt
        return """You are an expert cryptocurrency trading agent. 

Your role:
- Analyze market data (price, indicators, trends)
- Consider risk management (portfolio state, exposure, drawdown)
- Make rational trading decisions (LONG, SHORT, or HOLD)
- Always respond with valid JSON

Response format:
{
  "intent": "hold" | "open_long" | "open_short" | "close_long" | "close_short",
  "reasoning": "Brief explanation (1-2 sentences)",
  "confidence": 0.0-1.0,
  "orders": [
    {
      "symbol": "BTC/USDT:USDT",
      "side": "buy" | "sell",
      "type": "market" | "limit",
      "quantity": 0.001,
      "stop_loss": 49000.0,
      "take_profit": 52000.0
    }
  ]
}

Rules:
- Only trade when high confidence (>0.7)
- Always set stop-loss and take-profit
- Consider current positions before opening new ones
- Respect risk limits (max 1-2% risk per trade)
- Be conservative - when in doubt, HOLD"""
    
    def _build_prompt(self, obs_data: Dict[str, Any]) -> str:
        """Build user prompt from observation data"""
        
        prompt = f"""Analyze the current market and portfolio state, then decide on the next trading action.

MARKET DATA:
{json.dumps(obs_data['symbols'], indent=2)}

PORTFOLIO:
{json.dumps(obs_data['portfolio'], indent=2)}

RISK LIMITS:
- Max exposure per symbol: {self.config.max_exposure_pct}%
- Max total exposure: {self.config.max_total_exposure_pct}%
- Max drawdown: {self.config.max_drawdown_intraday_pct}%
- Per-trade risk: {self.config.per_trade_risk_pct}%
- Min R:R ratio: {self.config.min_risk_reward}

DECISION (respond with JSON only):"""
        
        return prompt
    
    def _call_llm_with_retry(self, prompt: str, system: str, 
                            max_retries: int = 2) -> str:
        """Call LLM with exponential backoff retry"""
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.generate(
                    prompt=prompt,
                    system=system,
                    temperature=self.config.llm.temperature,
                    max_tokens=self.config.llm.max_tokens
                )
                return response
            
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                    print(f"[LLMPolicy] Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise RuntimeError(f"LLM call failed after {max_retries + 1} attempts: {last_error}")
    
    def _parse_response(self, response_text: str, observation: Observation) -> Action:
        """Parse LLM JSON response into Action"""
        
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_text = self._extract_json(response_text)
            
            # Parse JSON
            data = json.loads(json_text)
            
            # Extract fields
            intent_str = data.get("intent", "hold").lower()
            reasoning = data.get("reasoning", "")
            confidence = float(data.get("confidence", 0.5))
            orders_data = data.get("orders", [])
            
            # Map intent string to ActionIntent enum
            intent_map = {
                "hold": ActionIntent.HOLD,
                "open_long": ActionIntent.OPEN_LONG,
                "open_short": ActionIntent.OPEN_SHORT,
                "close_long": ActionIntent.CLOSE_LONG,
                "close_short": ActionIntent.CLOSE_SHORT,
            }
            intent = intent_map.get(intent_str, ActionIntent.HOLD)
            
            # Parse orders
            orders = []
            for order_data in orders_data:
                try:
                    order = ActionOrder(
                        symbol=order_data["symbol"],
                        side=OrderSide.BUY if order_data["side"].lower() == "buy" else OrderSide.SELL,
                        type=OrderType.MARKET if order_data.get("type", "market").lower() == "market" else OrderType.LIMIT,
                        quantity=float(order_data["quantity"]),
                        price=float(order_data["price"]) if "price" in order_data else None,
                        stop_price=None,
                        take_profit=float(order_data["take_profit"]) if "take_profit" in order_data else None,
                        stop_loss=float(order_data["stop_loss"]) if "stop_loss" in order_data else None
                    )
                    orders.append(order)
                except (KeyError, ValueError) as e:
                    print(f"[LLMPolicy] ⚠️ Invalid order in response: {e}")
                    continue
            
            # Create Action
            action = Action(
                timestamp=observation.timestamp,
                intent=intent,
                orders=orders,
                notes=f"LLM: {reasoning}",
                confidence=confidence
            )
            
            # Check minimum confidence
            if self.config.llm_advanced and confidence < self.config.llm_advanced.min_confidence:
                print(f"[LLMPolicy] ⚠️ Low confidence ({confidence:.2f} < {self.config.llm_advanced.min_confidence}), forcing HOLD")
                action.intent = ActionIntent.HOLD
                action.orders = []
            
            return action
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}\nResponse: {response_text[:200]}")
        except Exception as e:
            raise ValueError(f"Failed to parse response: {e}")
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text (handles markdown code blocks)"""
        
        # Try to find JSON in markdown code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start >= 0 and end > start:
            return text[start:end]
        
        # Return as-is and let JSON parser fail
        return text
    
    def _log_prompt_response(self, prompt: str, response: str, action: Action):
        """Log prompt and response for debugging"""
        
        log_entry = {
            "timestamp": int(time.time() * 1000),
            "prompt_length": len(prompt),
            "response_length": len(response),
            "intent": action.intent.value,
            "confidence": action.confidence,
            "num_orders": len(action.orders),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "response_preview": response[:200] + "..." if len(response) > 200 else response
        }
        
        # Could save to file or just print
        print(f"[LLMPolicy] 📝 Logged prompt/response: intent={action.intent.value}, confidence={action.confidence:.2f}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy statistics"""
        return {
            "calls_total": self.calls_total,
            "calls_success": self.calls_success,
            "calls_failed": self.calls_failed,
            "fallback_count": self.fallback_count,
            "success_rate": (self.calls_success / self.calls_total * 100) if self.calls_total > 0 else 0
        }
    
    def reset(self):
        """Reset policy state (stats and counters)"""
        self.calls_total = 0
        self.calls_success = 0
        self.calls_failed = 0
        self.fallback_count = 0
        
        if self.fallback_policy:
            self.fallback_policy.reset()