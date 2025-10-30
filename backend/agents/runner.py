"""
Agent Runner - Main execution loop with RiskGuard integration
"""

import time
import uuid
import argparse
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any
import numpy as np
import json
import pandas as pd

from .config import AgentConfig
from .schemas import Observation, Metrics, OrderType
from .tools.market import MarketDataTool
from .tools.portfolio import PortfolioTool
from .tools.execution import ExecutionTool, OrderRequest
from .risk import RiskGuard
from .utils.logging import AgentLogger
from .schemas import OrderSide, PortfolioState


class AgentRunner:
    """Main agent execution loop with comprehensive risk management"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.config.ensure_directories()
        
        # Generate run ID
        self.run_id = str(uuid.uuid4())
        self.run_dir = config.runs_dir / self.run_id
    
        # Initialize components
        self.market = MarketDataTool(config)
        self.portfolio = PortfolioTool(config)
        self.execution = ExecutionTool(config, self.portfolio)
   
                # Initialize policy based on config
        if config.policy == "rule_based":
            from .policies.rule_based import RSIRulePolicy
            self.policy = RSIRulePolicy(
                rsi_period=14,
                oversold=30.0,
                overbought=70.0,
                position_size=1000.0
            )
            print(f"[AgentRunner] Using Rule-Based Policy (RSI)")
        
        elif config.policy == "llm":
            from .policies.llm_stub import LLMPolicy
            
            # LLMPolicy agora recebe config completo
            self.policy = LLMPolicy(config=config)
            print(f"[AgentRunner] Using LLM Policy")
            print(f"  - Model: {config.llm.model}")
            print(f"  - Provider: {config.llm.provider}")
            print(f"  - Fallback: {config.fallback_policy}")
        
        else:
            raise ValueError(f"Unknown policy: {config.policy}")
        
        self.risk_guard = RiskGuard(config)
        self.logger = AgentLogger(self.run_dir)
        
        # State
        self.running = True
        self.iteration = 0
        
        print(f"[AgentRunner] Initialized with run_id: {self.run_id}")
        print(f"[AgentRunner] Mode: {'PAPER' if config.paper_mode else 'LIVE'}")
        print(f"[AgentRunner] Exchange: {config.exchange}")
        print(f"[AgentRunner] Symbols: {config.symbols}")
        print(f"[AgentRunner] Initial cash: ${config.initial_cash:,.2f}")
    
    def run(self):
        """Main execution loop"""
        
        try:
            while self.running:
                self.iteration += 1
                
                # OBSERVE
                observation = self._observe()
                
                # Log observation
                self.logger.log_observation(
                    self.run_id,
                    {
                        'timestamp': observation.timestamp,
                        'portfolio': observation.portfolio.dict(),
                        'num_candles': {s: len(c) for s, c in observation.candles.items()}
                    }
                )
                
                # THINK
                action = self.policy.decide(observation)
                
                # Log action
                self.logger.log_action(
                    self.run_id,
                    {
                        'timestamp': action.timestamp,
                        'intent': action.intent,
                        'num_orders': len(action.orders)
                    }
                )
                
                print(f"\n[Iteration {self.iteration}] {action.intent}")
                
                # RISK CHECK
                if action.orders:
                    # Get current prices for risk validation
                    current_prices = self._get_current_prices()
                    
                    # Update portfolio prices before risk check
                    self.portfolio.mark_to_market(current_prices)
                    updated_portfolio = self.portfolio.snapshot()
                    
                    # Validate with RiskGuard (PASS PRICES!)
                    is_valid, reason, patched_action = self.risk_guard.validate_action(
                        action, 
                        updated_portfolio,
                        current_prices  # ✅ FIX: Pass prices to RiskGuard!
                    )
                    
                    if not is_valid:
                        print(f"[Risk] ❌ Action REJECTED: {reason}")
                        self.logger.log_error(self.run_id, f"Risk rejection: {reason}", int(time.time() * 1000))
                        
                        # Log risk metrics
                        risk_metrics = self.risk_guard.get_risk_metrics()
                        self.logger.log_event(
                            self.run_id,
                            'risk_rejection',
                            {
                                'reason': reason,
                                'original_intent': action.intent,
                                'num_orders': len(action.orders),
                                'risk_metrics': risk_metrics
                            }
                        )
                        
                        # If kill-switch active, force close all positions
                        if risk_metrics['kill_switch_active']:
                            print(f"[Risk] 🚨 KILL-SWITCH ACTIVE - Attempting to close all positions")
                            self._emergency_close_all(current_prices)
                    
                    else:
                        # Use patched action if provided
                        action_to_execute = patched_action if patched_action else action
                        
                        if patched_action and patched_action != action:
                            print(f"[Risk] ⚠️  Action PATCHED: {reason}")
                            self.logger.log_event(
                                self.run_id,
                                'risk_patch',
                                {
                                    'reason': reason,
                                    'original_orders': len(action.orders),
                                    'patched_orders': len(patched_action.orders)
                                }
                            )
                        
                        # ACT - Execute orders
                        order_requests = [
                            OrderRequest(
                                symbol=o.symbol,
                                side=o.side,
                                type=o.type,
                                quantity=o.quantity,
                                price=o.price,
                                stop_price=o.stop_price,
                                take_profit=getattr(o, 'take_profit', None),
                                stop_loss=getattr(o, 'stop_loss', None),
                                client_order_id=f"{self.run_id}_{self.iteration}_{i}"
                            )
                            for i, o in enumerate(action_to_execute.orders)
                        ]
                        
                        # Execute orders (returns filled and pending)
                        filled_orders, pending_orders = self.execution.execute_orders(order_requests, current_prices)
                        
                        # Log fills
                        for order in filled_orders:
                            print(f"[Fill] ✅ {order.side.value} {order.filled_quantity:.6f} {order.symbol} @ ${order.filled_price:.2f} (fee: ${order.fee:.2f})")
                            self.logger.log_fill(
                                self.run_id,
                                {
                                    'timestamp': order.timestamp,
                                    'symbol': order.symbol,
                                    'side': order.side.value,
                                    'quantity': order.filled_quantity,
                                    'price': order.filled_price,
                                    'fee': order.fee,
                                    'is_maker': order.is_maker,
                                    'slippage_bps': order.slippage_bps
                                }
                            )
                        
                        # Log pending orders
                        if pending_orders:
                            print(f"[Pending] 📋 {len(pending_orders)} orders pending")
                            for pending in pending_orders:
                                self.logger.log_event(
                                    self.run_id,
                                    'order_pending',
                                    {
                                        'order_id': pending.order_id,
                                        'symbol': pending.symbol,
                                        'side': pending.side.value,
                                        'type': pending.type.value,
                                        'quantity': pending.quantity,
                                        'price': pending.price,
                                        'stop_price': pending.stop_price
                                    }
                                )
                        
                        # Process any pending orders that might trigger
                        triggered_orders = self.execution.process_pending_orders(current_prices)
                        
                        if triggered_orders:
                            print(f"[Triggered] ⚡ {len(triggered_orders)} pending orders filled")
                            for order in triggered_orders:
                                print(f"[Fill] ✅ {order.side.value} {order.filled_quantity:.6f} {order.symbol} @ ${order.filled_price:.2f}")
                                self.logger.log_fill(
                                    self.run_id,
                                    {
                                        'timestamp': order.timestamp,
                                        'symbol': order.symbol,
                                        'side': order.side.value,
                                        'quantity': order.filled_quantity,
                                        'price': order.filled_price,
                                        'fee': order.fee,
                                        'type': 'triggered'
                                    }
                                )
                
                # Update portfolio with current prices
                current_prices = self._get_current_prices()
                self.portfolio.mark_to_market(current_prices)
                
                # Log metrics
                portfolio_snapshot = self.portfolio.snapshot()
                
                # Get risk metrics for display
                risk_metrics = self.risk_guard.get_risk_metrics()
                
                metrics = Metrics(
                    timestamp=int(time.time() * 1000),
                    equity=portfolio_snapshot.equity,
                    cash=portfolio_snapshot.cash,
                    realized_pnl=portfolio_snapshot.realized_pnl,
                    unrealized_pnl=portfolio_snapshot.unrealized_pnl,
                    total_pnl=portfolio_snapshot.total_pnl,
                    num_positions=len(portfolio_snapshot.positions)
                )
                self.logger.append_metrics(metrics)
                
                # Display with kill-switch indicator
                kill_switch_indicator = "🚨 KILL-SWITCH" if risk_metrics['kill_switch_active'] else ""
                print(f"[Portfolio] Equity: ${metrics.equity:,.2f} | PnL: ${metrics.total_pnl:+,.2f} | DD: {risk_metrics['current_drawdown_pct']:.2f}% | Pos: {metrics.num_positions} | Pending: {len(self.execution.get_pending_orders())} {kill_switch_indicator}")
                
                # Sleep until next iteration
                time.sleep(self.config.loop_interval_secs)
        
        except KeyboardInterrupt:
            print("\n[AgentRunner] Shutting down gracefully...")
        except Exception as e:
            print(f"\n[AgentRunner] Error: {e}")
            import traceback
            traceback.print_exc()
            self.logger.log_error(self.run_id, str(e), int(time.time() * 1000))
        finally:
            self._shutdown()
    
    def _observe(self) -> Observation:
        """Gather market observation"""
        
        timestamp = int(time.time() * 1000)
        candles_dict = {}
        volatility_dict = {}
        
        for symbol in self.config.symbols:
            # Fetch recent candles
            candles = self.market.get_recent_bars(
                symbol,
                self.config.timeframe,
                lookback=self.config.data_lookback_bars
            )
            
            if candles:
                candles_dict[symbol] = candles
                
                # Calculate recent volatility (standard deviation of returns)
                closes = np.array([c.close for c in candles[-20:]])
                returns = np.diff(closes) / closes[:-1]
                volatility_dict[symbol] = float(np.std(returns))
        
        portfolio = self.portfolio.snapshot(timestamp)
        
        return Observation(
            timestamp=timestamp,
            candles=candles_dict,
            portfolio=portfolio,
            volatility=volatility_dict
        )
    
    def _get_current_prices(self) -> Dict[str, float]:
        """Get current prices for all symbols"""
        prices = {}
        for symbol in self.config.symbols:
            price = self.market.get_current_price(symbol)
            if price:
                prices[symbol] = price
        return prices
    
    def _emergency_close_all(self, current_prices: Dict[str, float]):
        """Emergency close all positions (kill-switch activated)"""
        portfolio = self.portfolio.snapshot()
        
        if not portfolio.positions:
            print("[Risk] No positions to close")
            return
        
        print(f"[Risk] Closing {len(portfolio.positions)} positions...")
        
        for position in portfolio.positions:
            symbol = position.symbol
            price = current_prices.get(symbol)
            
            if price is None:
                print(f"[Risk] Cannot close {symbol}: no price available")
                continue
            
            # Create close order
            side = OrderSide.SELL if position.side == "long" else OrderSide.BUY
            
            order_request = OrderRequest(
                symbol=symbol,
                side=side,
                type=OrderType.MARKET,
                quantity=position.quantity,
                client_order_id=f"{self.run_id}_killswitch_{symbol}"
            )
            
            # Execute close
            filled, _ = self.execution.execute_orders([order_request], current_prices)
            
            if filled:
                print(f"[Risk] ✅ Closed {symbol}: {position.side.upper()} {position.quantity:.6f} @ ${price:.2f}")
    
    def _shutdown(self):
        """Cleanup and final reporting"""
        print(f"\n[AgentRunner] Run complete: {self.run_id}")
        print(f"[AgentRunner] Logs saved to: {self.run_dir}")
        
        final_portfolio = self.portfolio.snapshot()
        risk_metrics = self.risk_guard.get_risk_metrics()
        
        # Load metrics for final calculations
        metrics_df = self.logger.get_metrics_dataframe()
        
        # Calculate final metrics
        final_metrics = self._calculate_final_metrics(metrics_df, final_portfolio, risk_metrics)
        
        # Save summary
        self.logger.write_summary(final_metrics)
        
        # Display final report
        print(f"\n{'='*70}")
        print(f"=== FINAL PORTFOLIO ===")
        print(f"Equity: ${final_portfolio.equity:,.2f}")
        print(f"Cash: ${final_portfolio.cash:,.2f}")
        print(f"Realized PnL: ${final_portfolio.realized_pnl:+,.2f}")
        print(f"Unrealized PnL: ${final_portfolio.unrealized_pnl:+,.2f}")
        print(f"Total PnL: ${final_portfolio.total_pnl:+,.2f}")
        print(f"Total PnL %: {final_metrics['total_pnl_pct']:+.2f}%")
        print(f"Positions: {len(final_portfolio.positions)}")
        print(f"\n=== PERFORMANCE METRICS ===")
        print(f"Max Drawdown: {final_metrics['max_drawdown_pct']:.2f}%")
        print(f"Sharpe Ratio: {final_metrics['sharpe_ratio']:.3f}")
        print(f"Volatility (ann.): {final_metrics['volatility_annual']:.2f}%")
        print(f"Win Rate: {final_metrics['win_rate']:.1f}%")
        print(f"Total Trades: {final_metrics['total_trades']}")
        print(f"\n=== RISK METRICS ===")
        print(f"Kill-switch activated: {'YES' if risk_metrics['kill_switch_active'] else 'NO'}")
        print(f"Risk violations: {risk_metrics['violations_count']}")
        print(f"Session high equity: ${risk_metrics['session_high_equity']:,.2f}")
        print(f"\n=== FILES GENERATED ===")
        print(f"📊 Metrics CSV: {self.run_dir / 'metrics.csv'}")
        print(f"📈 Equity JSON: {self.run_dir / 'equity.json'}")
        print(f"📝 Trajectory: {self.run_dir / 'trajectory.jsonl'}")
        print(f"📋 Summary: {self.run_dir / 'summary.json'}")
        print(f"{'='*70}\n")
    
    def _calculate_final_metrics(self, metrics_df: pd.DataFrame, 
                                 portfolio: PortfolioState, 
                                 risk_metrics: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive final metrics
        
        Returns:
            Dict with all final metrics
        """
        if metrics_df.empty:
            return {
                'total_pnl_pct': 0.0,
                'max_drawdown_pct': 0.0,
                'sharpe_ratio': 0.0,
                'volatility_annual': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        # Calculate returns
        equities = metrics_df['equity'].values
        if len(equities) < 2:
            returns = []
        else:
            returns = np.diff(equities) / equities[:-1]
        
        # Max drawdown
        peak = np.maximum.accumulate(equities)
        drawdown = (equities - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (annualized)
        if len(returns) > 1:
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10)
            sharpe_annual = sharpe * np.sqrt(252)
        else:
            sharpe_annual = 0.0
        
        # Volatility (annualized)
        if len(returns) > 1:
            volatility_annual = np.std(returns) * np.sqrt(252) * 100
        else:
            volatility_annual = 0.0
        
        # Total PnL %
        initial_equity = equities[0] if len(equities) > 0 else self.config.initial_cash
        final_equity = portfolio.equity
        total_pnl_pct = ((final_equity - initial_equity) / initial_equity) * 100
        
        # Count trades (from trajectory)
        total_trades = self._count_trades()
        winning_trades = self._count_winning_trades()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        return {
            'run_id': self.run_id,
            'timestamp': int(time.time() * 1000),
            'initial_equity': initial_equity,
            'final_equity': final_equity,
            'total_pnl': portfolio.total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'realized_pnl': portfolio.realized_pnl,
            'unrealized_pnl': portfolio.unrealized_pnl,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_annual,
            'volatility_annual': volatility_annual,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'num_positions_final': len(portfolio.positions),
            'risk_violations': risk_metrics['violations_count'],
            'kill_switch_activated': risk_metrics['kill_switch_active'],
            'session_high_equity': risk_metrics['session_high_equity']
        }
    
    def _count_trades(self) -> int:
        """Count total trades from trajectory"""
        trajectory_path = self.run_dir / "trajectory.jsonl"
        
        if not trajectory_path.exists():
            return 0
        
        trade_count = 0
        with open(trajectory_path, 'r') as f:
            for line in f:
                event = json.loads(line)
                if event.get('kind') == 'fill':
                    trade_count += 1
        
        return trade_count
    
    def _count_winning_trades(self) -> int:
        """Count winning trades (closed positions with profit)"""
        # Simplified: count fills with positive PnL in notes or calculate from pairs
        # For now, return 0 (needs more sophisticated trade matching)
        # TODO: Implement proper trade matching (open → close)
        return 0    


def main():
    """CLI entry point"""
    
    parser = argparse.ArgumentParser(description="Agent Runner - Autonomous Trading Agent")
    parser.add_argument("--config", type=str, default="configs/agent_paper.yaml",
                        help="Path to config file")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        print("Creating default config...")
        
        config = AgentConfig()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config.to_yaml(str(config_path))
        print(f"Default config saved to: {config_path}")
    else:
        config = AgentConfig.from_yaml(str(config_path))
    
    # Run agent
    runner = AgentRunner(config)
    runner.run()


if __name__ == "__main__":
    main()