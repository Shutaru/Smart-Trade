"""
Simple rule-based policy using RSI
"""

import numpy as np
import time
from typing import List

from .base import Policy
from ..schemas import Observation, Action, ActionIntent, ActionOrder, OrderSide, OrderType, Candle


class RSIRulePolicy(Policy):
    """Simple RSI-based rule policy"""
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30.0, 
                 overbought: float = 70.0, position_size: float = 1000.0):
        super().__init__()
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.position_size = position_size
    
    def decide(self, observation: Observation) -> Action:
        """Make decision based on RSI"""
        
        orders = []
        intent = ActionIntent.HOLD
        notes = []
        
        for symbol, candles in observation.candles.items():
            if len(candles) < self.rsi_period + 1:
                continue
            
            # Calculate RSI
            rsi = self._calculate_rsi(candles, self.rsi_period)
            
            # Check if already have position
            has_position = any(p.symbol == symbol for p in observation.portfolio.positions)
            
            # Generate signals
            if rsi < self.oversold and not has_position:
                # Buy signal
                current_price = candles[-1].close
                quantity = self.position_size / current_price
                
                order = ActionOrder(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    type=OrderType.MARKET,
                    quantity=quantity
                )
                orders.append(order)
                intent = ActionIntent.OPEN_LONG
                notes.append(f"BUY {symbol} (RSI={rsi:.1f} oversold)")
            
            elif rsi > self.overbought and has_position:
                # Sell signal
                position = next(p for p in observation.portfolio.positions if p.symbol == symbol)
                
                order = ActionOrder(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    type=OrderType.MARKET,
                    quantity=position.quantity
                )
                orders.append(order)
                intent = ActionIntent.CLOSE_LONG
                notes.append(f"SELL {symbol} (RSI={rsi:.1f} overbought)")
        
        notes_str = "; ".join(notes) if notes else "No signals"
        
        return Action(
            timestamp=observation.timestamp,
            intent=intent,
            orders=orders,
            notes=notes_str,
            confidence=1.0
        )
    
    def _calculate_rsi(self, candles: List[Candle], period: int) -> float:
        """Calculate RSI indicator"""
        
        closes = np.array([c.close for c in candles])
        
        # Calculate price changes
        deltas = np.diff(closes)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def reset(self):
        """Reset policy state (stateless for now)"""
        pass