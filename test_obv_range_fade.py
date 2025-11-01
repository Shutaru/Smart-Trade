"""
Test OBV Range Fade Strategy - With Regime-Adaptive Exits

Strategy Logic:
- LONG: OBV crosses above 0 AND price near range bottom
- SHORT: OBV crosses below 0 AND price near range top
- EXITS: Multi-target, regime-adaptive, structure-aware
"""

import argparse
import time
import os
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime

from db_sqlite import connect, load_range
from features import compute_feature_rows
from indicators import supertrend, keltner
from broker_futures_paper_v2 import PaperFuturesBrokerV2
from sizing import compute_qty
from metrics import equity_metrics, trades_metrics
from strategy_regime import build_regime_exit_plan
from strategy import should_enter  # Import the REAL entry logic


def main():
    parser = argparse.ArgumentParser(description='Test Strategy with Regime Exits')
    parser.add_argument('--days', type=int, default=90, help='Backtest days (default: 90)')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("OBV RANGE FADE + REGIME-ADAPTIVE EXITS - BACKTEST")
    print("="*80)
    print(f"Period: {args.days} days")
    print(f"Timeframe: 5min")
    print(f"Strategy: OBV Range Fade + Multi-Target Exits")
    print("="*80 + "\n")
    
    # Load config
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    
    # Load data
    conn = connect(cfg.get("db", {}).get("path", "data/bot.db"))
    now = int(time.time())
    start = now - args.days * 24 * 60 * 60
    
    print(f"[Data] Loading candles from {datetime.fromtimestamp(start).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(now).strftime('%Y-%m-%d')}")
    
    rows = load_range(conn, start, now)
    ts = [r[0] for r in rows]
    o = [r[1] for r in rows]
    h = [r[2] for r in rows]
    l = [r[3] for r in rows]
    c = [r[4] for r in rows]
    v = [r[5] for r in rows] if len(rows[0]) > 5 else None
    
    print(f"[Data] Loaded {len(rows)} candles\n")
    
    # Calculate features
    print("[Features] Calculating indicators...")
    feats_rows = compute_feature_rows(ts, o, h, l, c, v)
    
    feat = {
        "ema20": [r[1] for r in feats_rows],
        "ema50": [r[2] for r in feats_rows],
        "atr14": [r[3] for r in feats_rows],
        "rsi5": [r[4] for r in feats_rows],
        "rsi14": [r[5] for r in feats_rows],
        "adx14": [r[6] for r in feats_rows],
        "bb_mid": [r[7] for r in feats_rows],
        "bb_lo": [r[8] for r in feats_rows],
        "bb_up": [r[9] for r in feats_rows],
        "dn55": [r[10] for r in feats_rows],
        "up55": [r[11] for r in feats_rows],
        "regime": [r[12] for r in feats_rows],
        "macro": [r[13] for r in feats_rows],
        "atr1h_pct": [r[14] for r in feats_rows],
        "macd": [r[15] for r in feats_rows],
        "macd_signal": [r[16] for r in feats_rows],
        "macd_hist": [r[17] for r in feats_rows],
        "stoch_k": [r[18] for r in feats_rows],
        "stoch_d": [r[19] for r in feats_rows],
        "cci20": [r[20] for r in feats_rows],
        "williams_r": [r[21] for r in feats_rows],
        "supertrend": [r[22] for r in feats_rows],
        "supertrend_dir": [r[23] for r in feats_rows],
        "mfi14": [r[24] for r in feats_rows],
        "vwap": [r[25] for r in feats_rows],
        "obv": [r[26] for r in feats_rows],
        "keltner_mid": [r[27] for r in feats_rows],
        "keltner_lo": [r[28] for r in feats_rows],
        "keltner_up": [r[29] for r in feats_rows],
    }
    
    print(f"[Features] Calculated {len(feat)} indicators\n")
    
    # Calculate trailing indicators
    st_line, st_tr = supertrend(h, l, c, n=10, mult=3.0)
    kel_mid, kel_lo, kel_up = keltner(h, l, c, n=20, mult=1.5)
    
    # Initialize broker V2
    outdir = os.path.join("data", "test_obv_regime", str(int(time.time())))
    os.makedirs(outdir, exist_ok=True)
    
    broker = PaperFuturesBrokerV2(
        equity=float(cfg.get("account", {}).get("starting_equity_usd", 100000)),
        max_daily_loss_pct=float(cfg.get("risk", {}).get("max_daily_loss_pct", 2.0)),
        spread_bps=float(cfg.get("fees", {}).get("spread_bps", 1.0)),
        taker_fee_bps=float(cfg.get("fees", {}).get("taker_fee_bps", 5.0)),
        maker_fee_bps=float(cfg.get("fees", {}).get("maker_fee_bps", 2.0)),
        data_dir=outdir
    )
    
    print("[Broker] Initialized V2 broker with regime-adaptive exits")
    print(f"[Broker] Starting equity: ${broker.equity:,.2f}")
    print(f"[Broker] Output directory: {outdir}\n")

    # Run backtest
    print("[Backtest] Starting simulation...")
    print("="*80)
    
    trade_count = 0
    long_count = 0
    short_count = 0
    
    for i in range(len(ts)):
        atr = feat["atr14"][i] or (c[i] * 0.01)
        
        # Update broker (check exits)
        broker.on_candle(
            ts[i], h[i], l[i], c[i], atr,
            cfg['fees']['spread_bps'],
            cfg['fees']['taker_fee_bps'],
            cfg['fees']['maker_fee_bps'],
            st_line=st_line[i],
            kel_lo=kel_lo[i],
            kel_up=kel_up[i]
        )
        
        # Check for new entries
        if broker.position is None:
            side = should_enter(
                i, ts, o, h, l, c, feat,
                cfg.get("risk", {}),
                allow_shorts=cfg.get("risk", {}).get("allow_shorts", True)
            )
   
            # DEBUG: First 10 bars
            if i < 10 or (i % 5000 == 0):
                print(f"[DEBUG] Bar {i}: close={c[i]:.2f}, rsi14={feat.get('rsi14', [None]*len(c))[i]}, dn55={feat.get('dn55', [None]*len(c))[i]:.2f}, side={side}")
            
            if side:
                # Build regime-adaptive exit plan
                exit_plan = build_regime_exit_plan(
                    side, c[i], atr, i, h, l, feat, cfg.get('risk', {})
                )
                
                # Calculate position size
                qty, notional, margin_used, lev = compute_qty(
                    c[i], broker.equity, cfg.get('sizing', {}),
                    stop_distance=abs(c[i] - exit_plan.sl),
                    atr1h_pct=feat['atr1h_pct'][i]
                )
                
                if qty > 0:
                    # Open position with exit plan
                    success = broker.open_with_plan(
                        ts[i], qty, c[i], lev, exit_plan,
                        note=f"OBV={feat['obv'][i]:.0f} RSI={feat['rsi14'][i]:.1f} Trailing={exit_plan.trailing.mode}"
                    )
                    
                    if success:
                        trade_count += 1
                        if side == "LONG":
                            long_count += 1
                        else:
                            short_count += 1
                        
                        if args.verbose or trade_count <= 10:
                            print(f"\n[Trade #{trade_count}] {side} Entry")
                            print(f"  Time: {datetime.fromtimestamp(ts[i]/1000).strftime('%Y-%m-%d %H:%M')}")
                            print(f"  Price: ${c[i]:,.2f}")
                            print(f"  Quantity: {qty:.6f}")
                            print(f"  SL: ${exit_plan.sl:,.2f} | Primary TP: ${exit_plan.tp_primary:,.2f}")
                            print(f"  R: ${exit_plan.R:,.2f}")
                            print(f"  Targets: {len(exit_plan.targets)}")
                            for idx, target in enumerate(exit_plan.targets, 1):
                                print(f"    Target {idx}: ${target.price:,.2f} ({target.rr:.1f}R) - {target.pct*100:.0f}%")
                            print(f"  Trailing: {exit_plan.trailing.mode}")
                            print(f"  Time Stop: {exit_plan.time_stop_bars} bars")
    
    print("\n" + "="*80)
    print("[Backtest] Simulation complete")
    print("="*80)
    
    # Calculate metrics
    print("\n[Metrics] Calculating performance...")
    
    em = equity_metrics(broker.equity_curve)
    tm = trades_metrics(os.path.join(outdir, "trades.csv"))
    
    summary = {**em, **tm, "outdir": outdir}
    
    # Save summary
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80)
    print(f"\nTrading Activity:")
    print(f"  Total Trades: {trade_count}")
    print(f"  LONG Trades:  {long_count} ({long_count/max(trade_count,1)*100:.1f}%)")
    print(f"  SHORT Trades: {short_count} ({short_count/max(trade_count,1)*100:.1f}%)")
    
    print(f"\nPerformance:")
    print(f"  Total Return: {summary.get('ret_tot_pct', 0):.2f}%")
    print(f"  Sharpe Ratio: {summary.get('sharpe_ann', 0):.2f}")
    print(f"  Max Drawdown: {summary.get('maxdd_pct', 0):.2f}%")
    print(f"  Win Rate:     {summary.get('win_rate_pct', 0):.1f}%")
    
    print(f"\nEquity:")
    print(f"  Start: ${broker.start_equity:,.2f}")
    print(f"  End:   ${broker.equity:,.2f}")
    print(f"  P&L:   ${broker.equity - broker.start_equity:+,.2f}")
    
    # Load and display trades table
    print("\n" + "="*80)
    print("TRADE DETAILS")
    print("="*80)
    
    trades_df = pd.read_csv(os.path.join(outdir, "trades.csv"))
    
    # Filter only entry and exit events
    entries = trades_df[trades_df['action'].str.contains('OPEN')]
    exits = trades_df[trades_df['action'].isin(['TARGET_1', 'TARGET_2', 'TARGET_3', 'TP_FULL', 'STOP', 'TIME_STOP', 'TP_PARTIAL'])]
    
    print(f"\nTrade Log (showing first 20 and last 10):")
    print("-"*80)
    
    # Show entries
    print("\nENTRIES:")
    for idx, row in entries.head(20).iterrows():
        side_mark = "[LONG]" if "LONG" in row['action'] else "[SHORT]"
        print(f"{side_mark} {datetime.fromtimestamp(row['ts_utc']/1000).strftime('%Y-%m-%d %H:%M')} | " +
              f"{row['action']:15s} | Price: ${row['price']:>8,.2f} | Qty: {row['qty']:.6f}")
    
    # Show exits
    print("\nEXITS:")
    for idx, row in exits.head(20).iterrows():
        pnl_mark = "[WIN]" if row['pnl'] > 0 else "[LOSS]"
        print(f"{pnl_mark} {datetime.fromtimestamp(row['ts_utc']/1000).strftime('%Y-%m-%d %H:%M')} | " +
              f"{row['action']:15s} | Price: ${row['price']:>8,.2f} | PnL: ${row['pnl']:>8,.2f}")
    
    if len(exits) > 20:
        print(f"\n... ({len(exits) - 30} more exits) ...\n")
        
        print("LAST 10 EXITS:")
        for idx, row in exits.tail(10).iterrows():
            pnl_mark = "[WIN]" if row['pnl'] > 0 else "[LOSS]"
            print(f"{pnl_mark} {datetime.fromtimestamp(row['ts_utc']/1000).strftime('%Y-%m-%d %H:%M')} | " +
                  f"{row['action']:15s} | Price: ${row['price']:>8,.2f} | PnL: ${row['pnl']:>8,.2f}")
    
    # Exit breakdown
    print("\n" + "="*80)
    print("EXIT BREAKDOWN")
    print("="*80)
    
    exit_counts = exits['action'].value_counts()
    exit_pnl = exits.groupby('action')['pnl'].agg(['sum', 'mean', 'count'])
    
    print("\nExit Types:")
    for exit_type in exit_counts.index:
        count = exit_counts[exit_type]
        pct = (count / len(exits)) * 100
        avg_pnl = exit_pnl.loc[exit_type, 'mean']
        total_pnl = exit_pnl.loc[exit_type, 'sum']
        print(f"  {exit_type:15s}: {count:3d} exits ({pct:5.1f}%) | Avg PnL: ${avg_pnl:>8,.2f} | Total: ${total_pnl:>10,.2f}")
    
    print("\n" + "="*80)
    print(f"Results saved to: {outdir}")
    print("="*80 + "\n")
    
    return summary


if __name__ == '__main__':
    main()