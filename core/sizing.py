"""
Position sizing utilities

Provides compute_qty used by backtest scripts. This is a pragmatic, well-documented
fallback implementation suitable for backtesting and paper trading.
"""
from typing import Tuple, Dict


def compute_qty(price: float, equity: float, sizing: Dict = None, stop_distance: float = None, atr1h_pct: float = None) -> Tuple[float, float, float, float]:
 """
 Compute position quantity and related sizing outputs.

 Args:
 price: current price
 equity: account equity in quote currency
 sizing: sizing configuration dict (may contain keys: mode, usd, portfolio_pct, max_risk_pct, leverage)
 stop_distance: absolute price distance from entry to stop (in quote currency)
 atr1h_pct: optional ATR1h percent (not used by default)

 Returns:
 qty: quantity in base asset (float)
 notional: qty * price
 margin_used: notional / leverage
 leverage: effective leverage used
 """
 sizing = sizing or {}
 mode = sizing.get('mode', 'fixed_fraction')

 # Defaults and safe conversions
 try:
  max_risk_pct = float(sizing.get('max_risk_pct', sizing.get('max_risk',1.0)))
 except Exception:
  max_risk_pct =1.0

 try:
  usd = float(sizing.get('usd',0.0))
 except Exception:
  usd =0.0

 try:
  portfolio_pct = float(sizing.get('portfolio_pct',0.0))
 except Exception:
  portfolio_pct =0.0

 try:
  leverage = float(sizing.get('leverage', sizing.get('lev',1.0)))
 except Exception:
  leverage =1.0

 qty =0.0
 notional =0.0

 try:
  if mode == 'fixed_usd' and usd >0:
   notional = min(usd, equity) # don't allocate more than equity
   qty = notional / price if price >0 else 0.0

  elif mode == 'portfolio_pct' and portfolio_pct >0:
   notional = equity * (portfolio_pct /100.0)
   qty = notional / price if price >0 else 0.0

  elif mode == 'fixed_fraction':
   # Risk-based sizing: risk per trade = equity * max_risk_pct/100
   # qty = risk_amount / (stop_distance * price) (stop_distance in price units)
   risk_amount = equity * (max_risk_pct /100.0)
   if stop_distance and stop_distance >0 and price >0:
    qty = risk_amount / (stop_distance * price)
   else:
    # fallback to small fraction of equity
    notional = equity *0.01
    qty = notional / price if price >0 else 0.0

  elif mode == 'volatility' and atr1h_pct:
   # ATR-based: target notional proportional to inverse volatility
   vol_factor = max(0.01, atr1h_pct /100.0)
   notional = equity * min(0.1,1.0 / (vol_factor *10.0))
   qty = notional / price if price >0 else 0.0

  else:
   # default conservative allocation
   notional = equity *0.02
   qty = notional / price if price >0 else 0.0

 except Exception:
  qty =0.0
  notional =0.0

 notional = qty * price
 margin_used = notional / max(1.0, leverage)

 # Ensure non-negative and proper types
 try:
  qty = max(0.0, float(qty))
 except Exception:
  qty =0.0
 try:
  notional = max(0.0, float(notional))
 except Exception:
  notional =0.0
 try:
  margin_used = max(0.0, float(margin_used))
 except Exception:
  margin_used =0.0
 try:
  leverage = float(leverage) if leverage and float(leverage) >0 else 1.0
 except Exception:
  leverage =1.0

 return qty, notional, margin_used, leverage
