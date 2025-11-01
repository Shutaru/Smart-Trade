"""Generate clean ranker.py"""

RANKER_CODE = """from dataclasses import dataclass
from typing import List

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
    @staticmethod
    def calculate_composite_score(m):
        if m.total_trades < 5: return -999.0
        if abs(m.max_drawdown_pct) > 50: return -999.0
     if m.sharpe_ratio < 0.5: return -999.0
        ret = 0.70 * m.total_return_pct
    sortino = 0.10 * min(m.sortino_ratio, 8.0)
        wr = 0.10 * (m.win_rate_pct / 100.0) * 10.0
        trades = 0.05 * min(m.total_trades / 1000.0, 3.0)
        dd = abs(m.max_drawdown_pct)
        dd_pen = 0 if dd <= 15 else -0.05 * ((dd - 15) / 10)
     return round(ret + sortino + wr + trades + dd_pen, 4)
    
    @staticmethod
    def rank_strategies(ss):
      for s in ss:
      s.composite_score = StrategyRanker.calculate_composite_score(s)
 return sorted(ss, key=lambda x: x.composite_score, reverse=True)
    
    @staticmethod
    def get_top_n(ss, n=3):
     return StrategyRanker.rank_strategies(ss)[:n]
    
    @staticmethod
    def format_report(ss):
        r = ["="*80, "PROFIT-FIRST RANKING (RELAXED)", "="*80, ""]
for i, s in enumerate(ss, 1):
            r.append(f"#{i} {s.strategy_name}")
            r.append(f"   Score: {s.composite_score:.4f}")
   r.append(f"   Return: {s.total_return_pct:+.2f}% | Sharpe: {s.sharpe_ratio:.2f}")
        r.append(f"   Sortino: {s.sortino_ratio:.2f} | DD: {s.max_drawdown_pct:.2f}%")
   r.append(f"   Win Rate: {s.win_rate_pct:.1f}% | Trades: {s.total_trades}")
            r.append("")
      return "\\n".join(r)

if __name__ == "__main__":
    print("Testing RELAXED scoring...")
    test = StrategyMetrics("Test +10%", 10.0, 10.0, 0.8, 1.2, 2.5, -4.0, -2.0, 20.0,
   100, 38.0, 0.55, 2.0, -1.0, 8, 3, 2.5)
    score = StrategyRanker.calculate_composite_score(test)
    print(f"Test strategy: Score = {score:.4f}")
    print("? RELAXED constraints work!" if score > 0 else "? Still rejecting")
"""

with open('backend/agents/discovery/ranker.py', 'w', encoding='utf-8') as f:
    f.write(RANKER_CODE)

print("? backend/agents/discovery/ranker.py generated successfully!")
