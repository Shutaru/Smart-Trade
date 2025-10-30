"""
Strategy Ranker - Advanced Scoring Formula

Ranks strategies using a composite score that:
- Minimizes drawdown
- Maximizes stable returns (penalizes volatility)
- Rewards consistency (Sortino, Calmar)
- Penalizes consecutive losses
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import math


@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    strategy_name: str
    
    # Return metrics
    total_return_pct: float
    cagr: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    avg_drawdown_pct: float
    volatility_annual_pct: float
    
    # Trade metrics
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    avg_win_pct: float
    avg_loss_pct: float
    
    # Consistency metrics
    consecutive_wins: int
    consecutive_losses: int
    recovery_factor: float
    
    # Composite score (calculated)
    composite_score: float = 0.0


class StrategyRanker:
    """
    Advanced strategy ranking system
    
    Composite Score Formula:
    ========================
    
    ADJUSTED FORMULA (favors Balanced strategies):
    - Increased weight on Calmar Ratio (return/DD)
    - Reduced volatility penalty
    - Reduced drawdown penalty
    - Rewards higher absolute returns
    
    Higher score = Better strategy (stable, profitable, low DD)
    """
    
    @staticmethod
    def calculate_composite_score(metrics: StrategyMetrics) -> float:
        """
        Calculate composite score using advanced formula
        
        ADJUSTED FORMULA (favors Balanced strategies):
        - Increased weight on Calmar Ratio (return/DD)
        - Reduced volatility penalty
        - Reduced drawdown penalty
        - Rewards higher absolute returns
        
        Args:
            metrics: Strategy performance metrics
        
        Returns:
            Composite score (higher = better)
        """
        
        # Safety checks
        if metrics.total_trades < 10:
            return -999.0  # Not enough trades
        
        if abs(metrics.max_drawdown_pct) > 50:
            return -999.0  # Unacceptable drawdown
        
        # Calculate components
        
        # 1. Risk-adjusted return (Calmar Ratio) - INCREASED WEIGHT
        calmar_component = 0.30 * metrics.calmar_ratio  # Was 0.25
        
        # 2. Consistency (Sharpe + Sortino)
        sharpe_component = 0.20 * min(metrics.sharpe_ratio, 5.0)  # Cap at 5
        sortino_component = 0.15 * min(metrics.sortino_ratio, 5.0)
        
        # 3. Stability (inverse of volatility) - REDUCED PENALTY
        stability_score = 1.0 / max(0.01, metrics.volatility_annual_pct / 100)
        stability_component = 0.10 * min(stability_score, 10.0)  # Was 0.15
        
        recovery_component = 0.10 * min(metrics.recovery_factor, 5.0)
        
        # 4. Trade quality
        win_rate_component = 0.08 * (metrics.win_rate_pct / 100)  # Was 0.10
        profit_factor_component = 0.05 * min(metrics.profit_factor, 3.0)
        
        # 5. Absolute return bonus (rewards higher returns)
        return_bonus = 0.02 * min(metrics.total_return_pct / 100, 2.0)  # NEW
        
        # 6. Penalties - REDUCED
        drawdown_penalty = 0.03 * (abs(metrics.max_drawdown_pct) / 10)  # Was 0.05
        losing_streak_penalty = 0.02 * (metrics.consecutive_losses / 5)  # Was 0.05
        
        # Calculate total score
        score = (
            calmar_component +
            sharpe_component +
            sortino_component +
            stability_component +
            recovery_component +
            win_rate_component +
            profit_factor_component +
            return_bonus -
            drawdown_penalty -
            losing_streak_penalty
        )
        
        return round(score, 4)
    
    @staticmethod
    def rank_strategies(strategies: List[StrategyMetrics]) -> List[StrategyMetrics]:
        """
        Rank strategies by composite score
        
        Args:
            strategies: List of strategy metrics
        
        Returns:
            Sorted list (best first)
        """
        
        # Calculate composite score for each
        for strategy in strategies:
            strategy.composite_score = StrategyRanker.calculate_composite_score(strategy)
        
        # Sort by score (descending)
        ranked = sorted(strategies, key=lambda s: s.composite_score, reverse=True)
        
        return ranked
    
    @staticmethod
    def get_top_n(strategies: List[StrategyMetrics], n: int = 3) -> List[StrategyMetrics]:
        """
        Get top N strategies
        
        Args:
            strategies: List of strategy metrics
            n: Number of top strategies to return
        
        Returns:
            Top N strategies
        """
        ranked = StrategyRanker.rank_strategies(strategies)
        return ranked[:n]
    
    @staticmethod
    def format_report(strategies: List[StrategyMetrics]) -> str:
        """
        Format ranking report
        
        Args:
            strategies: Ranked strategies
        
        Returns:
            Formatted report string
        """
        
        report = []
        report.append("=" * 80)
        report.append("STRATEGY RANKING REPORT")
        report.append("=" * 80)
        report.append("")
        
        for i, strategy in enumerate(strategies, 1):
            report.append(f"#{i} {strategy.strategy_name}")
            report.append(f"   Composite Score: {strategy.composite_score:.4f}")
            report.append(f"   ")
            report.append(f"   Returns:")
            report.append(f"     Total Return: {strategy.total_return_pct:+.2f}%")
            report.append(f"     CAGR: {strategy.cagr:+.2f}%")
            report.append(f"   ")
            report.append(f"   Risk Metrics:")
            report.append(f"     Sharpe: {strategy.sharpe_ratio:.2f}")
            report.append(f"     Sortino: {strategy.sortino_ratio:.2f}")
            report.append(f"     Calmar: {strategy.calmar_ratio:.2f}")
            report.append(f"     Max DD: {strategy.max_drawdown_pct:.2f}%")
            report.append(f"     Volatility: {strategy.volatility_annual_pct:.2f}%")
            report.append(f"   ")
            report.append(f"   Trade Quality:")
            report.append(f"     Total Trades: {strategy.total_trades}")
            report.append(f"     Win Rate: {strategy.win_rate_pct:.1f}%")
            report.append(f"     Profit Factor: {strategy.profit_factor:.2f}")
            report.append(f"     Consecutive Losses: {strategy.consecutive_losses}")
            report.append(f"")
            report.append("-" * 80)
            report.append("")
        
        return "\n".join(report)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Create sample strategies
    strategies = [
        StrategyMetrics(
            strategy_name="EMA_RSI_Trend",
            total_return_pct=45.2,
            cagr=18.5,
            sharpe_ratio=1.85,
            sortino_ratio=2.30,
            calmar_ratio=3.20,
            max_drawdown_pct=-14.1,
            avg_drawdown_pct=-5.2,
            volatility_annual_pct=18.5,
            total_trades=125,
            win_rate_pct=62.4,
            profit_factor=1.85,
            avg_win_pct=2.8,
            avg_loss_pct=-1.5,
            consecutive_wins=8,
            consecutive_losses=4,
            recovery_factor=3.2
        ),
        StrategyMetrics(
            strategy_name="MACD_Bollinger",
            total_return_pct=38.5,
            cagr=15.2,
            sharpe_ratio=1.52,
            sortino_ratio=1.95,
            calmar_ratio=2.10,
            max_drawdown_pct=-18.3,
            avg_drawdown_pct=-6.8,
            volatility_annual_pct=22.3,
            total_trades=98,
            win_rate_pct=58.2,
            profit_factor=1.65,
            avg_win_pct=3.2,
            avg_loss_pct=-1.8,
            consecutive_wins=6,
            consecutive_losses=5,
            recovery_factor=2.1
        ),
        StrategyMetrics(
            strategy_name="SuperTrend_ADX",
            total_return_pct=52.8,
            cagr=21.2,
            sharpe_ratio=2.15,
            sortino_ratio=2.85,
            calmar_ratio=4.10,
            max_drawdown_pct=-12.9,
            avg_drawdown_pct=-4.5,
            volatility_annual_pct=15.8,
            total_trades=87,
            win_rate_pct=68.9,
            profit_factor=2.25,
            avg_win_pct=3.5,
            avg_loss_pct=-1.2,
            consecutive_wins=10,
            consecutive_losses=3,
            recovery_factor=4.1
        )
    ]
    
    # Rank strategies
    ranker = StrategyRanker()
    ranked = ranker.rank_strategies(strategies)
    
    # Print report
    print(ranker.format_report(ranked))
    
    # Get top 3
    top3 = ranker.get_top_n(ranked, n=3)
    print("\n🏆 TOP 3 STRATEGIES:")
    for i, s in enumerate(top3, 1):
        print(f"{i}. {s.strategy_name} (Score: {s.composite_score:.4f})")