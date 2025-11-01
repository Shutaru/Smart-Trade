"""Fix ranker.py - Create clean version without encoding issues"""

ranker_code = '''# -*- coding: utf-8 -*-
"""Strategy Ranker - PROFIT-FIRST (RELAXED CONSTRAINTS)"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class StrategyMetrics:
    strategy_name: str
    total_return_pct: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    avg_drawdown_pct: float
 volatility_annual_pct: float
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    avg_win_pct: float
    avg_loss_pct: float
    consecutive_wins: int
    consecutive_losses: int
    recovery_factor: float
    composite_score: float = 0.0


class StrategyRanker:
    """PROFIT-FIRST Ranking with RELAXED constraints (Sharpe>=0.5, Trades>=5)"""
    
    @staticmethod
    def calculate_composite_score(metrics: StrategyMetrics) -> float:
        """Calculate score: 70% return, 10% Sortino, 10% WR, 5% trades, 5% DD penalty"""
if metrics.total_trades < 5:
        return -999.0
        if abs(metrics.max_drawdown_pct) > 50:
            return -999.0
  if metrics.sharpe_ratio < 0.5:
            return -999.0
        
     ret_comp = 0.70 * metrics.total_return_pct
        sortino_comp = 0.10 * min(metrics.sortino_ratio, 8.0)
        wr_comp = 0.10 * (metrics.win_rate_pct / 100.0) * 10.0
        trade_comp = 0.05 * min(metrics.total_trades / 1000.0, 3.0)
        
        dd_pct = abs(metrics.max_drawdown_pct)
        dd_penalty = 0.0 if dd_pct <= 15.0 else -0.05 * ((dd_pct - 15.0) / 10.0)
        
        return round(ret_comp + sortino_comp + wr_comp + trade_comp + dd_penalty, 4)
    
    @staticmethod
    def rank_strategies(strategies: List[StrategyMetrics]) -> List[StrategyMetrics]:
        for s in strategies:
            s.composite_score = StrategyRanker.calculate_composite_score(s)
 return sorted(strategies, key=lambda x: x.composite_score, reverse=True)
    
    @staticmethod
    def get_top_n(strategies: List[StrategyMetrics], n: int = 3) -> List[StrategyMetrics]:
        return StrategyRanker.rank_strategies(strategies)[:n]
    
    @staticmethod
    def format_report(strategies: List[StrategyMetrics]) -> str:
        lines = ["=" * 80, "PROFIT-FIRST RANKING (RELAXED)", "=" * 80, ""]
        for i, s in enumerate(strategies, 1):
      lines.append(f"#{i} {s.strategy_name}")
            lines.append(f"   Score: {s.composite_score:.4f}")
            lines.append(f"   Return: {s.total_return_pct:+.2f}% | Sharpe: {s.sharpe_ratio:.2f}")
            lines.append(f"   Sortino: {s.sortino_ratio:.2f} | DD: {s.max_drawdown_pct:.2f}%")
            lines.append(f"   WR: {s.win_rate_pct:.1f}% | Trades: {s.total_trades}")
            lines.append("")
   return "\\n".join(lines)


if __name__ == "__main__":
    print("Testing RELAXED constraints...")
    test = StrategyMetrics(
        "High Return Low Sharpe", 10.0, 10.0, 0.8, 1.2, 2.5, -4.0, -2.0, 20.0,
        100, 38.0, 0.55, 2.0, -1.0, 8, 3, 2.5
    )
    score = StrategyRanker.calculate_composite_score(test)
 print(f"Test: +10% return, Sharpe 0.8 => Score: {score:.4f}")
    print("? ACCEPTED (Sharpe 0.8 >= 0.5)" if score > 0 else "? REJECTED")
'''

with open('backend/agents/discovery/ranker.py', 'w', encoding='utf-8') as f:
    f.write(ranker_code)

print("? ranker.py fixed and saved!")
