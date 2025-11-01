"""
Strategy Selector

Selects top N strategies from discovery results based on composite scores.
"""

from typing import List, Dict, Any
from backend.agents.discovery.ranker from strategies import core as strategyMetrics


class StrategySelector:
    """
    Intelligent strategy selection system
    
    Selects optimal combination of strategies for portfolio allocation.
    """
    
    def __init__(self):
        self.selected_strategies: List[StrategyMetrics] = []
    
    def select_top_n(
        self, 
        strategies: List[StrategyMetrics], 
        n: int = 3,
        min_score: float = 1.0,
        max_correlation: float = 0.7
    ) -> List[StrategyMetrics]:
        """
        Select top N strategies with diversification
        
        Args:
            strategies: List of ranked strategies
            n: Number of strategies to select
            min_score: Minimum composite score required
            max_correlation: Maximum allowed correlation (future)
        
        Returns:
            Selected strategies
        """
        
        # Filter by minimum score
        qualified = [s for s in strategies if s.composite_score >= min_score]
        
        if len(qualified) < n:
            print(f"⚠️  Only {len(qualified)} strategies meet min_score={min_score}")
            n = len(qualified)
        
        # Select top N
        selected = qualified[:n]
        
        self.selected_strategies = selected
        
        return selected
    
    def categorize_strategies(
        self, 
        strategies: List[StrategyMetrics]
    ) -> Dict[str, StrategyMetrics]:
        """
        Categorize strategies by risk profile
        
        Categories:
        - Conservative: High Sharpe, Low DD, Low Vol
        - Balanced: Good Sharpe, Medium DD, Medium Vol
        - Aggressive: Lower Sharpe, High Return, High Vol
        
        Args:
            strategies: List of strategies
        
        Returns:
            Dict mapping category to strategy
        """
        
        categories = {
            "conservative": None,
            "balanced": None,
            "aggressive": None
        }
        
        for strategy in strategies:
            # Conservative: Sharpe > 2.0, DD < -10%, Vol < 15%
            if (strategy.sharpe_ratio > 2.0 and 
                abs(strategy.max_drawdown_pct) < 10 and
                strategy.volatility_annual_pct < 15):
                if categories["conservative"] is None:
                    categories["conservative"] = strategy
            
            # Aggressive: Return > 60%, DD > -25%, Vol > 30%
            elif (strategy.total_return_pct > 60 and
                  abs(strategy.max_drawdown_pct) > 25 and
                  strategy.volatility_annual_pct > 30):
                if categories["aggressive"] is None:
                    categories["aggressive"] = strategy
            
            # Balanced: Everything else
            else:
                if categories["balanced"] is None:
                    categories["balanced"] = strategy
        
        # Fill empty categories with best available
        available = [s for s in strategies]
        
        if categories["conservative"] is None and len(available) > 0:
            categories["conservative"] = available[0]
            available.pop(0)
        
        if categories["balanced"] is None and len(available) > 0:
            categories["balanced"] = available[0]
            available.pop(0)
        
        if categories["aggressive"] is None and len(available) > 0:
            categories["aggressive"] = available[0]
        
        return categories

    def get_allocation_weights(
        self,
        categories: Dict[str, StrategyMetrics],
        allocation_mode: str = "balanced"
    ) -> Dict[str, float]:
        """
        Calculate allocation weights for each category
        
        Args:
            categories: Categorized strategies
            allocation_mode: 'conservative', 'balanced', 'aggressive'
        
        Returns:
            Dict mapping category to allocation weight
        """
        
        presets = {
            "conservative": {
                "conservative": 0.70,
                "balanced": 0.25,
                "aggressive": 0.05
            },
            "balanced": {
                "conservative": 0.45,
                "balanced": 0.40,
                "aggressive": 0.15
            },
            "aggressive": {
                "conservative": 0.25,
                "balanced": 0.35,
                "aggressive": 0.40
            }
        }
        
        return presets.get(allocation_mode, presets["balanced"])

    def calculate_portfolio_metrics(
        self,
        categories: Dict[str, StrategyMetrics],
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate expected portfolio metrics
        
        Args:
            categories: Categorized strategies
            weights: Allocation weights
        
        Returns:
            Portfolio metrics (return, sharpe, DD, etc.)
        """
        
        portfolio_metrics = {
            "expected_return": 0.0,
            "expected_sharpe": 0.0,
            "expected_max_dd": 0.0,
            "expected_volatility": 0.0,
            "expected_win_rate": 0.0
        }
        
        for category, weight in weights.items():
            strategy = categories.get(category)
            if strategy is None:
                continue
            
            portfolio_metrics["expected_return"] += weight * strategy.total_return_pct
            portfolio_metrics["expected_sharpe"] += weight * strategy.sharpe_ratio
            portfolio_metrics["expected_max_dd"] += weight * strategy.max_drawdown_pct
            portfolio_metrics["expected_volatility"] += weight * strategy.volatility_annual_pct
            portfolio_metrics["expected_win_rate"] += weight * strategy.win_rate_pct
        
        return portfolio_metrics


if __name__ == '__main__':
    # Test strategy selector
    from backend.agents.discovery.ranker from strategies import core as strategyRanker, StrategyMetrics
    
    # Create sample strategies
    strategies = [
        StrategyMetrics(
            strategy_name="Conservative",
            total_return_pct=25.0,
            cagr=12.0,
            sharpe_ratio=2.50,
            sortino_ratio=3.20,
            calmar_ratio=5.00,
            max_drawdown_pct=-5.0,
            avg_drawdown_pct=-2.5,
            volatility_annual_pct=8.0,
            total_trades=150,
            win_rate_pct=72.0,
            profit_factor=2.80,
            avg_win_pct=1.8,
            avg_loss_pct=-0.8,
            consecutive_wins=12,
            consecutive_losses=2,
            recovery_factor=5.0,
            composite_score=4.16
        ),
        StrategyMetrics(
            strategy_name="Balanced",
            total_return_pct=52.0,
            cagr=21.0,
            sharpe_ratio=2.15,
            sortino_ratio=2.85,
            calmar_ratio=4.00,
            max_drawdown_pct=-13.0,
            avg_drawdown_pct=-5.5,
            volatility_annual_pct=16.0,
            total_trades=180,
            win_rate_pct=65.0,
            profit_factor=2.40,
            avg_win_pct=2.8,
            avg_loss_pct=-1.4,
            consecutive_wins=9,
            consecutive_losses=4,
            recovery_factor=4.0,
            composite_score=3.21
        ),
        StrategyMetrics(
            strategy_name="Aggressive",
            total_return_pct=85.0,
            cagr=42.0,
            sharpe_ratio=1.20,
            sortino_ratio=1.50,
            calmar_ratio=2.50,
            max_drawdown_pct=-34.0,
            avg_drawdown_pct=-15.0,
            volatility_annual_pct=45.0,
            total_trades=220,
            win_rate_pct=55.0,
            profit_factor=1.95,
            avg_win_pct=5.2,
            avg_loss_pct=-3.8,
            consecutive_wins=7,
            consecutive_losses=8,
            recovery_factor=2.5,
            composite_score=1.71
        )
    ]
    
    selector = StrategySelector()
    
    # Select top 3
    selected = selector.select_top_n(strategies, n=3, min_score=1.0)
    
    print("="*80)
    print("STRATEGY SELECTION")
    print("="*80)
    print(f"\n✅ Selected {len(selected)} strategies:")
    for i, s in enumerate(selected, 1):
        print(f"  {i}. {s.strategy_name} (Score: {s.composite_score:.4f})")
    
    # Categorize
    categories = selector.categorize_strategies(selected)
    
    print(f"\n📊 Categorization:")
    for category, strategy in categories.items():
        if strategy:
            print(f"  {category.capitalize()}: {strategy.strategy_name}")
    
    # Get allocation weights
    weights = selector.get_allocation_weights(categories, allocation_mode="balanced")
    
    print(f"\n💰 Allocation (Balanced Mode):")
    for category, weight in weights.items():
        print(f"  {category.capitalize()}: {weight*100:.1f}%")
    
    # Calculate portfolio metrics
    portfolio_metrics = selector.calculate_portfolio_metrics(categories, weights)
    
    print(f"\n📈 Expected Portfolio Metrics:")
    print(f"  Return: {portfolio_metrics['expected_return']:.2f}%")
    print(f"  Sharpe: {portfolio_metrics['expected_sharpe']:.2f}")
    print(f"  Max DD: {portfolio_metrics['expected_max_dd']:.2f}%")
    print(f"  Volatility: {portfolio_metrics['expected_volatility']:.2f}%")
    print(f"  Win Rate: {portfolio_metrics['expected_win_rate']:.1f}%")