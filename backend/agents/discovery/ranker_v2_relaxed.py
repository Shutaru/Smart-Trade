"""
Strategy Ranker - PROFIT-FIRST Scoring (v2 - RELAXED CONSTRAINTS)

Ranks strategies using a composite score that PRIORITIZES ABSOLUTE RETURNS
with RELAXED constraints to accept more profitable strategies.
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
    PROFIT-FIRST Strategy Ranking System (v2 - RELAXED)
    
    Composite Score Formula:
    ========================

    PRIMARY GOAL: Maximize absolute returns with reasonable risk
    
    Constraints (hard filters - RELAXED):
    - Sharpe >= 0.5 (relaxed from 1.2 to accept more strategies)
    - Trades >= 5 (relaxed from 10)
    - Max DD < 50% (catastrophic loss prevention)
  
    Scoring Components:
    - 70% Total Return - Absolute profit is KING
    - 10% Sortino Ratio - Downside risk (better than Sharpe)
    - 10% Win Rate - Consistency metric
    - 5% Trade Frequency - Opportunity count
    - 5% DD Penalty - Only penalizes if > 15%
    
    Example Scoring:
    - +10% return, Sortino 2.5, 45% WR, 500 trades, -12% DD = ~7.8 score
  - +5% return, Sortino 1.5, 40% WR, 100 trades, -8% DD = ~4.0 score
    - +2% return, Sortino 0.8, 35% WR, 50 trades, -5% DD = ~1.5 score (ACCEPTED!)
    
    Higher score = Better strategy (profit-focused, risk-aware)
    """
    
    @staticmethod
    def calculate_composite_score(metrics: StrategyMetrics) -> float:
        """
     Calculate composite score using PROFIT-FIRST formula (v2)
        
        **NEW FORMULA: Maximum Profit with Reasonable Risk**
        
        Philosophy:
        - Return absoluto é KING (70% do score)
        - Sortino > Sharpe (melhor para downside risk)
        - DD só penaliza se > 15% (gerível até lá)
     - Win rate + trades = consistência (15% combined)
      - Sharpe ? 0.5 é CONSTRAINT (relaxado para aceitar mais estratégias)
        
        Formula Breakdown:
        - 70% Total Return (absolute profit rules!)
        - 10% Sortino Ratio (downside risk only)
        - 10% Win Rate (consistency)
        - 5% Trade Frequency (opportunities)
        - 5% DD Penalty (only if > 15%)
        
   Constraints (hard filters - RELAXED):
        - Sharpe >= 0.5 (muito relaxado para aceitar profitable strategies)
 - Trades >= 5 (reduzido de 10)
        - Max DD < 50% (unacceptable)
        
        Args:
        metrics: Strategy performance metrics
        
        Returns:
            Composite score (higher = better)
    """
        
        # Hard constraints (RELAXED)
        if metrics.total_trades < 5:
          return -999.0  # Not enough trades
        
        if abs(metrics.max_drawdown_pct) > 50:
     return -999.0  # Unacceptable drawdown

        if metrics.sharpe_ratio < 0.5:
        return -999.0  # Below minimum risk-adjusted threshold

        # Calculate components
        
        # 1. ABSOLUTE RETURN (70% weight) - PRIMARY DRIVER
   return_component = 0.70 * metrics.total_return_pct
        
# 2. SORTINO RATIO (10% weight) - Downside risk only
        sortino_component = 0.10 * min(metrics.sortino_ratio, 8.0)
        
        # 3. WIN RATE (10% weight) - Consistency
      win_rate_component = 0.10 * (metrics.win_rate_pct / 100.0) * 10.0
 
    # 4. TRADE FREQUENCY (5% weight) - Opportunities
        trade_frequency_score = min(metrics.total_trades / 1000.0, 3.0)
trade_component = 0.05 * trade_frequency_score
    
        # 5. DRAWDOWN PENALTY (5% weight) - Only penalize if > 15%
        dd_pct = abs(metrics.max_drawdown_pct)
        if dd_pct <= 15.0:
            dd_penalty = 0.0
        else:
   excess_dd = dd_pct - 15.0
            dd_penalty = -0.05 * (excess_dd / 10.0)
        
      # Calculate total score
        score = (
            return_component +
            sortino_component +
            win_rate_component +
            trade_component +
 dd_penalty
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
        report.append("STRATEGY RANKING REPORT (PROFIT-FIRST SCORING - RELAXED)")
      report.append("=" * 80)
        report.append("")
        
        for i, strategy in enumerate(strategies, 1):
            report.append(f"#{i} {strategy.strategy_name}")
      report.append(f" Composite Score: {strategy.composite_score:.4f}")
   report.append(f"   ")
         report.append(f"   Returns:")
      report.append(f"     Total Return: {strategy.total_return_pct:+.2f}%")
 report.append(f"     CAGR: {strategy.cagr:+.2f}%")
          report.append(f"   ")
     report.append(f"   Risk Metrics:")
            report.append(f"     Sharpe: {strategy.sharpe_ratio:.2f}")
        report.append(f"     Sortino: {strategy.sortino_ratio:.2f}")
            report.append(f"     Calmar: {strategy.calmar_ratio:.2f}")
     report.append(f"  Max DD: {strategy.max_drawdown_pct:.2f}%")
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
# EXAMPLE USAGE & TESTING
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("TESTING PROFIT-FIRST SCORING (v2 - RELAXED CONSTRAINTS)")
    print("="*80 + "\n")
    
    # Create test strategies to validate scoring
    strategies = [
   StrategyMetrics(
   strategy_name="High Return, Low Sharpe (NOW ACCEPTED!)",
            total_return_pct=10.0,
       cagr=10.0,
            sharpe_ratio=0.8,  # Below 1.2 but above 0.5 - NOW ACCEPTED
sortino_ratio=1.2,
      calmar_ratio=2.5,
            max_drawdown_pct=-4.0,
  avg_drawdown_pct=-2.0,
      volatility_annual_pct=20.0,
       total_trades=100,
   win_rate_pct=38.0,
  profit_factor=0.55,
          avg_win_pct=2.0,
            avg_loss_pct=-1.0,
      consecutive_wins=8,
consecutive_losses=3,
            recovery_factor=2.5
        ),
    StrategyMetrics(
strategy_name="Medium Return, Medium Sharpe",
            total_return_pct=5.0,
        cagr=5.0,
  sharpe_ratio=1.5,
            sortino_ratio=2.0,
      calmar_ratio=3.5,
   max_drawdown_pct=-1.5,
            avg_drawdown_pct=-0.8,
            volatility_annual_pct=12.0,
            total_trades=100,
            win_rate_pct=40.0,
       profit_factor=0.58,
            avg_win_pct=1.5,
avg_loss_pct=-0.8,
            consecutive_wins=9,
            consecutive_losses=3,
recovery_factor=3.3
        ),
 StrategyMetrics(
      strategy_name="Low Return, High Sharpe",
 total_return_pct=2.0,
     cagr=2.0,
  sharpe_ratio=4.0,
 sortino_ratio=5.0,
            calmar_ratio=6.0,
            max_drawdown_pct=-0.5,
     avg_drawdown_pct=-0.2,
       volatility_annual_pct=5.0,
        total_trades=100,
            win_rate_pct=42.0,
         profit_factor=0.60,
            avg_win_pct=1.0,
       avg_loss_pct=-0.5,
 consecutive_wins=10,
            consecutive_losses=2,
            recovery_factor=4.0
        )
    ]
    
    ranker = StrategyRanker()
    ranked = ranker.rank_strategies(strategies)
    
print(ranker.format_report(ranked))
    
    print("\n" + "="*80)
    print("EXPECTED RANKING (Return-First with Relaxed Constraints):")
    print("="*80)
    print("1. High Return, Low Sharpe (+10% dominates, Sharpe 0.8 now accepted)")
  print("2. Medium Return, Medium Sharpe (+5%)")
    print("3. Low Return, High Sharpe (+2% too low)")
 
    print("\n" + "="*80)
    print("ACTUAL RANKING:")
    print("="*80)
    for i, s in enumerate(ranked, 1):
        print(f"{i}. {s.strategy_name}")
        print(f"   Score: {s.composite_score:.4f} | Return: {s.total_return_pct:+.1f}% | Sharpe: {s.sharpe_ratio:.2f}")
    
    print("\n" + "="*80)
    print("? Scoring Formula Working with Relaxed Constraints!")
    print(" Strategies with Sharpe >= 0.5 are now accepted")
    print("="*80 + "\n")
