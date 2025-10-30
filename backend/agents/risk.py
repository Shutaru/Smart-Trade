"""
Risk Guard - Comprehensive risk management and kill-switch
"""

from typing import Tuple, Optional, Dict
from dataclasses import dataclass
import time

from .schemas import Action, ActionIntent, ActionOrder, PortfolioState, OrderSide
from .config import AgentConfig


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    max_exposure_per_symbol_pct: float
    max_total_exposure_pct: float
    max_positions: int
    max_leverage: float
    require_stop_loss: bool
    stop_loss_threshold_usd: float
    max_drawdown_intraday_pct: float
    max_order_size_pct: float


@dataclass
class RiskState:
    """Current risk state"""
    kill_switch_active: bool = False
    kill_switch_reason: str = ""
    kill_switch_triggered_at: Optional[int] = None
    session_start_equity: float = 0.0
    session_high_equity: float = 0.0
    current_drawdown_pct: float = 0.0
    violations_count: int = 0


class RiskGuard:
    """Comprehensive risk management system"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        self.limits = RiskLimits(
            max_exposure_per_symbol_pct=config.max_exposure_pct,
            max_total_exposure_pct=95.0,
            max_positions=config.max_concurrent_positions,
            max_leverage=config.max_leverage,
            require_stop_loss=config.require_stop_loss,
            stop_loss_threshold_usd=1000.0,
            max_drawdown_intraday_pct=config.max_drawdown_intraday_pct,
            max_order_size_pct=50.0
        )
        
        self.state = RiskState(
            session_start_equity=config.initial_cash,
            session_high_equity=config.initial_cash
        )
 
        print(f"[RiskGuard] Initialized with limits:")
        print(f"  - Session start equity: ${config.initial_cash:,.2f}")
        print(f"  - Max exposure per symbol: {self.limits.max_exposure_per_symbol_pct:.1f}%")
        print(f"  - Max total exposure: {self.limits.max_total_exposure_pct:.1f}%")
        print(f"  - Max positions: {self.limits.max_positions}")
        print(f"  - Max leverage: {self.limits.max_leverage:.1f}x")
        print(f"  - Kill-switch DD: {self.limits.max_drawdown_intraday_pct:.1f}%")
    
    def validate_action(self, action: Action, portfolio: PortfolioState, 
                       current_prices: Dict[str, float] = None) -> Tuple[bool, str, Optional[Action]]:
        """Validate action against risk limits"""
        
        # Update risk state
        self._update_risk_state(portfolio)
        
        # Check kill-switch first
        if self.state.kill_switch_active:
            if action.intent in [ActionIntent.CLOSE_LONG, ActionIntent.CLOSE_SHORT, ActionIntent.SCALE_OUT]:
                return True, "Kill-switch active: allowing close order", action
            else:
                return False, f"Kill-switch active: {self.state.kill_switch_reason}", None
        
        # HOLD intent - always allowed
        if action.intent == ActionIntent.HOLD or not action.orders:
            return True, "No orders to validate", action
        
        # Validate each order
        patched_orders = []
        rejection_reasons = []
        
        for order in action.orders:
            is_valid, reason, patched_order = self._validate_order(
                order, portfolio, action.intent, current_prices or {}
            )
            
            if patched_order:
                patched_orders.append(patched_order)
            elif not is_valid:
                rejection_reasons.append(f"{order.symbol}: {reason}")
        
        # If all orders rejected
        if not patched_orders and rejection_reasons:
            self.state.violations_count += 1
            return False, "; ".join(rejection_reasons), None
        
        # If some orders patched
        if patched_orders and len(patched_orders) < len(action.orders):
            patched_action = Action(
                timestamp=action.timestamp,
                intent=action.intent,
                orders=patched_orders,
                notes=f"PATCHED: {action.notes}. Rejected: {'; '.join(rejection_reasons)}",
                confidence=action.confidence * 0.8
            )
            return True, f"Action patched: {len(patched_orders)}/{len(action.orders)} orders allowed", patched_action
        
        # All orders valid
        return True, "All checks passed", action
    
    def _validate_order(self, order: ActionOrder, portfolio: PortfolioState, 
                       intent: ActionIntent, current_prices: Dict[str, float]) -> Tuple[bool, str, Optional[ActionOrder]]:
        """Validate single order and potentially patch it"""
        
        # Get current price from provided prices dict
        current_price = current_prices.get(order.symbol)
        
        # Fallback: try to estimate from portfolio positions
        if current_price is None:
            current_price = self._estimate_price(order.symbol, portfolio)
        
        if current_price is None:
            return False, "Cannot determine current price", None
        
        # Calculate order notional
        notional = order.quantity * current_price
        
        # 1. Check max order size
        max_order_notional = portfolio.equity * (self.limits.max_order_size_pct / 100)
        if notional > max_order_notional:
            max_qty = max_order_notional / current_price
            if max_qty > 0:
                patched_order = ActionOrder(
                    symbol=order.symbol,
                    side=order.side,
                    type=order.type,
                    quantity=max_qty,
                    price=order.price,
                    stop_price=order.stop_price,
                    take_profit=order.take_profit,
                    stop_loss=order.stop_loss
                )
                return True, f"Order size reduced from {order.quantity:.6f} to {max_qty:.6f}", patched_order
            else:
                return False, f"Order too large: ${notional:.2f} > max ${max_order_notional:.2f}", None
        
        # 2. Check position count limit
        if intent in [ActionIntent.OPEN_LONG, ActionIntent.OPEN_SHORT, ActionIntent.SCALE_IN]:
            current_positions = len(portfolio.positions)
            has_position = any(pos.symbol == order.symbol for pos in portfolio.positions)
            
            if not has_position and current_positions >= self.limits.max_positions:
                return False, f"Max positions limit reached ({self.limits.max_positions})", None
        
        # 3. Check exposure limits
        if intent in [ActionIntent.OPEN_LONG, ActionIntent.OPEN_SHORT, ActionIntent.SCALE_IN]:
            symbol_exposure = sum(
                pos.quantity * pos.current_price 
                for pos in portfolio.positions 
                if pos.symbol == order.symbol
            )
            new_symbol_exposure = symbol_exposure + notional
            max_symbol_exposure = portfolio.equity * (self.limits.max_exposure_per_symbol_pct / 100)
            
            if new_symbol_exposure > max_symbol_exposure:
                available_exposure = max_symbol_exposure - symbol_exposure
                if available_exposure > 0:
                    max_qty = available_exposure / current_price
                    patched_order = ActionOrder(
                        symbol=order.symbol,
                        side=order.side,
                        type=order.type,
                        quantity=max_qty,
                        price=order.price,
                        stop_price=order.stop_price,
                        take_profit=order.take_profit,
                        stop_loss=order.stop_loss
                    )
                    return True, f"Qty reduced to fit symbol exposure limit", patched_order
                else:
                    return False, f"Symbol exposure limit reached: {self.limits.max_exposure_per_symbol_pct}%", None
            
            # Total portfolio exposure
            total_exposure = portfolio.exposure
            new_total_exposure = total_exposure + notional
            max_total_exposure = portfolio.equity * (self.limits.max_total_exposure_pct / 100)
            
            if new_total_exposure > max_total_exposure:
                available_exposure = max_total_exposure - total_exposure
                if available_exposure > 0:
                    max_qty = available_exposure / current_price
                    patched_order = ActionOrder(
                        symbol=order.symbol,
                        side=order.side,
                        type=order.type,
                        quantity=max_qty,
                        price=order.price,
                        stop_price=order.stop_price,
                        take_profit=order.take_profit,
                        stop_loss=order.stop_loss
                    )
                    return True, f"Qty reduced to fit total exposure limit", patched_order
                else:
                    return False, f"Total exposure limit reached: {self.limits.max_total_exposure_pct}%", None
        
        # 4. Check stop-loss requirement
        if self.limits.require_stop_loss and intent in [ActionIntent.OPEN_LONG, ActionIntent.OPEN_SHORT]:
            if notional >= self.limits.stop_loss_threshold_usd:
                if not order.stop_loss:
                    return False, f"Stop-loss required for positions > ${self.limits.stop_loss_threshold_usd:.0f}", None
        
        # 5. Check leverage limit
        if intent in [ActionIntent.OPEN_LONG, ActionIntent.OPEN_SHORT, ActionIntent.SCALE_IN]:
            total_notional = portfolio.exposure + notional
            implied_leverage = total_notional / portfolio.equity if portfolio.equity > 0 else 0
            
            if implied_leverage > self.limits.max_leverage:
                max_notional = (portfolio.equity * self.limits.max_leverage) - portfolio.exposure
                if max_notional > 0:
                    max_qty = max_notional / current_price
                    patched_order = ActionOrder(
                        symbol=order.symbol,
                        side=order.side,
                        type=order.type,
                        quantity=max_qty,
                        price=order.price,
                        stop_price=order.stop_price,
                        take_profit=order.take_profit,
                        stop_loss=order.stop_loss
                    )
                    return True, f"Qty reduced to fit leverage limit", patched_order
                else:
                    return False, f"Leverage limit reached: {self.limits.max_leverage:.1f}x", None
        
        # All checks passed
        return True, "Order valid", order
    
    def _update_risk_state(self, portfolio: PortfolioState):
        """Update risk state and check for kill-switch conditions"""
        current_equity = portfolio.equity
        
        if current_equity > self.state.session_high_equity:
            self.state.session_high_equity = current_equity
        
        drawdown_pct = ((current_equity - self.state.session_high_equity) / self.state.session_high_equity) * 100
        self.state.current_drawdown_pct = drawdown_pct
        
        if not self.state.kill_switch_active and drawdown_pct < -self.limits.max_drawdown_intraday_pct:
            self._activate_kill_switch(
                f"Intraday drawdown limit breached: {drawdown_pct:.2f}% < -{self.limits.max_drawdown_intraday_pct:.2f}%"
            )
    
    def _activate_kill_switch(self, reason: str):
        """Activate kill-switch"""
        self.state.kill_switch_active = True
        self.state.kill_switch_reason = reason
        self.state.kill_switch_triggered_at = int(time.time() * 1000)
        
        print(f"\n{'='*70}")
        print(f"🚨 KILL-SWITCH ACTIVATED 🚨")
        print(f"Reason: {reason}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current equity: ${self.state.session_high_equity * (1 + self.state.current_drawdown_pct/100):,.2f}")
        print(f"Session high: ${self.state.session_high_equity:,.2f}")
        print(f"Drawdown: {self.state.current_drawdown_pct:.2f}%")
        print(f"{'='*70}\n")
    
    def deactivate_kill_switch(self, reason: str = "Manual override"):
        """Deactivate kill-switch"""
        if self.state.kill_switch_active:
            print(f"\n[RiskGuard] Kill-switch DEACTIVATED: {reason}")
            self.state.kill_switch_active = False
            self.state.kill_switch_reason = ""
    
    def reset_session(self, current_equity: float):
        """Reset session metrics"""
        self.state.session_start_equity = current_equity
        self.state.session_high_equity = current_equity
        self.state.current_drawdown_pct = 0.0
        self.state.violations_count = 0
        self.state.kill_switch_active = False
        print(f"[RiskGuard] Session reset: starting equity ${current_equity:,.2f}")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            'kill_switch_active': self.state.kill_switch_active,
            'kill_switch_reason': self.state.kill_switch_reason,
            'current_drawdown_pct': self.state.current_drawdown_pct,
            'session_high_equity': self.state.session_high_equity,
            'violations_count': self.state.violations_count,
            'max_drawdown_limit': self.limits.max_drawdown_intraday_pct
        }
    
    def _estimate_price(self, symbol: str, portfolio: PortfolioState) -> Optional[float]:
        """Estimate current price from portfolio positions"""
        for pos in portfolio.positions:
            if pos.symbol == symbol:
                return pos.current_price
        return None