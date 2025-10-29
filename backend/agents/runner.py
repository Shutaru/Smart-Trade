"""
Agent Runner - Main execution loop
"""

import time
import uuid
import argparse
from pathlib import Path
from typing import Dict
import numpy as np

from .config import AgentConfig
from .schemas import Observation, Metrics
from .tools.market import MarketDataTool
from .tools.portfolio import PortfolioTool
from .tools.execution import ExecutionTool
from .policies.rule_based import RSIRulePolicy
from .risk import RiskGuard
from .utils.logging import AgentLogger


class AgentRunner:
    """Main agent execution loop"""
    
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
        self.policy = RSIRulePolicy(
  rsi_period=14,
 oversold=30.0,
          overbought=70.0,
            position_size=1000.0  # $1000 per position
     )
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
          is_valid, msg = self.risk_guard.validate_action(action, observation.portfolio)
   
            if not is_valid:
  print(f"[Risk] Action rejected: {msg}")
      self.logger.log_error(self.run_id, f"Risk rejection: {msg}", int(time.time() * 1000))
      else:
           # ACT
          current_prices = self._get_current_prices()
               filled_orders = self.execution.execute_orders(action.orders, current_prices)
      
     # Log fills
           for order in filled_orders:
       print(f"[Fill] {order.side} {order.quantity:.6f} {order.symbol} @ ${order.filled_price:.2f}")
      self.logger.log_fill(
            self.run_id,
           {
            'timestamp': order.timestamp,
             'symbol': order.symbol,
 'side': order.side,
          'quantity': order.quantity,
         'price': order.filled_price,
   'fees': order.fees
       }
         )
            
                # Update portfolio with current prices
  current_prices = self._get_current_prices()
    self.portfolio.mark_to_market(current_prices)
       
  # Log metrics
        portfolio_snapshot = self.portfolio.snapshot()
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
                
       print(f"[Portfolio] Equity: ${metrics.equity:,.2f} | PnL: ${metrics.total_pnl:+,.2f} | Positions: {metrics.num_positions}")
    
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
    
    def _shutdown(self):
        """Cleanup and final reporting"""
        print(f"\n[AgentRunner] Run complete: {self.run_id}")
   print(f"[AgentRunner] Logs saved to: {self.run_dir}")
        
     final_portfolio = self.portfolio.snapshot()
        print(f"\n=== FINAL PORTFOLIO ===")
     print(f"Equity: ${final_portfolio.equity:,.2f}")
        print(f"Cash: ${final_portfolio.cash:,.2f}")
      print(f"Realized PnL: ${final_portfolio.realized_pnl:+,.2f}")
        print(f"Unrealized PnL: ${final_portfolio.unrealized_pnl:+,.2f}")
        print(f"Total PnL: ${final_portfolio.total_pnl:+,.2f}")
        print(f"Positions: {len(final_portfolio.positions)}")


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
