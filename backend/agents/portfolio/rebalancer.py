
"""
Portfolio Rebalancer

Handles dynamic rebalancing of multi-strategy portfolios.
"""

from typing import Dict, List
import time


class PortfolioRebalancer:
    """
    Dynamic portfolio rebalancing system
    """
    
    def __init__(self, rebalance_frequency_hours: int = 24):
        """
        Initialize rebalancer
        
        Args:
            rebalance_frequency_hours: Hours between rebalances
        """
        self.rebalance_frequency_hours = rebalance_frequency_hours
        self.last_rebalance_time = time.time()
        self.rebalance_history = []
    
    def should_rebalance(
        self,
        portfolio_status: Dict,
        threshold_pct: float = 10.0,
        force_time_based: bool = True
    ) -> bool:
        """
        Determine if rebalancing is needed
        
        Args:
            portfolio_status: Current portfolio status
            threshold_pct: Rebalance if drift > this %
            force_time_based: Force rebalance after time interval
        
        Returns:
            True if rebalancing needed
        """
        
        # Time-based rebalancing
        if force_time_based:
            hours_since_rebalance = (time.time() - self.last_rebalance_time) / 3600
            if hours_since_rebalance >= self.rebalance_frequency_hours:
                print(f"[Rebalancer] Time-based rebalance: {hours_since_rebalance:.1f}h since last")
                return True
        
        # Drift-based rebalancing
        max_drift = 0.0
        
        for name, strategy_data in portfolio_status['strategies'].items():
            current_weight = strategy_data['capital'] / portfolio_status['current_equity']
            target_weight = strategy_data['weight']
            drift_pct = abs((current_weight - target_weight) / target_weight) * 100
            
            if drift_pct > max_drift:
                max_drift = drift_pct
        
        if max_drift > threshold_pct:
            print(f"[Rebalancer] Drift-based rebalance: max drift {max_drift:.1f}%")
            return True
        
        return False
    
    def calculate_rebalance_trades(
        self,
        portfolio_status: Dict
    ) -> List[Dict]:
        """
        Calculate trades needed for rebalancing
        
        Args:
            portfolio_status: Current portfolio status
        
        Returns:
            List of trade instructions
        """
        
        trades = []
        
        total_equity = portfolio_status['current_equity']
        
        for name, strategy_data in portfolio_status['strategies'].items():
            current_capital = strategy_data['capital']
            target_capital = total_equity * strategy_data['weight']
            adjustment = target_capital - current_capital
            
            if abs(adjustment) > 100:  # Only rebalance if > $100
                trades.append({
                    'strategy': name,
                    'current_capital': current_capital,
                    'target_capital': target_capital,
                    'adjustment': adjustment,
                    'action': 'increase' if adjustment > 0 else 'decrease'
                })
        
        return trades
    
    def execute_rebalance(
        self,
        portfolio,
        trades: List[Dict]
    ):
        """
        Execute rebalancing trades
        
        Args:
            portfolio: Portfolio manager instance
            trades: List of trade instructions
        """
        
        print(f"\n[Rebalancer] Executing rebalance...")
        
        for trade in trades:
            print(f"  {trade['strategy']}: {trade['action']} ${abs(trade['adjustment']):,.2f}")
        
        # Execute via portfolio manager
        portfolio.rebalance()
        
        # Record rebalance event
        self.last_rebalance_time = time.time()
        self.rebalance_history.append({
            'timestamp': self.last_rebalance_time,
            'trades': trades
        })
        
        print(f"✅ Rebalance complete")


if __name__ == '__main__':
    print("Portfolio Rebalancer module loaded")