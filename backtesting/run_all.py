"""
Multi-Strategy Backtest Runner - Test All 38 Strategies

Runs backtests for all 38 strategies and generates comparison report.

Usage:
    python run_38_strategies.py --days 90 --strategies all
    python run_38_strategies.py --days 90 --strategies trend
    python run_38_strategies.py --days 90 --strategies "trendflow_supertrend,ema_cloud_trend"
"""

import argparse
import time
import os
import json
import yaml
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import concurrent.futures
from pathlib import Path

from core.database import connect, load_range
from core.features import compute_feature_rows
from core.indicators import supertrend as calc_supertrend, keltner as calc_keltner
from broker.paper_v2 import PaperFuturesBrokerV2
from core.sizing import compute_qty
from core.metrics import equity_metrics, trades_metrics
from strategies.regime import build_regime_exit_plan

from strategies.registry import (
    ALL_STRATEGIES,
    get_strategy,
    list_all_strategies,
    get_strategies_by_category,
    get_strategy_info,
    STRATEGY_PRESETS
)
from strategies.adapter import (
    build_indicator_dict,
    build_bar_dict,
    build_state_dict,
    extract_exit_params
)


def run_single_strategy_backtest(
    strategy_name: str,
    ts: List, o: List, h: List, l: List, c: List, v: List,
    feats: Dict,
    cfg: Dict,
    days: int,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run backtest for a single strategy
    
    Returns:
        Dictionary with strategy results
    """
    
    print(f"\n{'='*80}")
    print(f"Testing: {strategy_name}")
    print(f"{'='*80}")
    
    # Get strategy function
    strategy_fn = get_strategy(strategy_name)
    if not strategy_fn:
        print(f"❌ Strategy '{strategy_name}' not found!")
        return None
    
    # Get strategy info
    info = get_strategy_info(strategy_name)
    
    # Setup output directory
    timestamp = int(time.time())
    outdir = os.path.join("data", "backtest_38", strategy_name, str(timestamp))
    os.makedirs(outdir, exist_ok=True)
    
    # Calculate trailing indicators
    st_line, st_tr = calc_supertrend(h, l, c, n=10, mult=3.0)
    kel_mid, kel_lo, kel_up = calc_keltner(h, l, c, n=20, mult=1.5)
    
    # Initialize broker
    broker = PaperFuturesBrokerV2(
        equity=float(cfg.get("account", {}).get("starting_equity_usd", 100000)),
        max_daily_loss_pct=float(cfg.get("risk", {}).get("max_daily_loss_pct", 2.0)),
        spread_bps=float(cfg.get("fees", {}).get("spread_bps", 1.0)),
        taker_fee_bps=float(cfg.get("fees", {}).get("taker_fee_bps", 5.0)),
        maker_fee_bps=float(cfg.get("fees", {}).get("maker_fee_bps", 2.0)),
        data_dir=outdir
    )
    
    # Run backtest
    trade_count = 0
    cooldown_bars = 0
    
    for i in range(len(ts)):
        atr = feats.get("atr14", [c[i] * 0.01])[i] or (c[i] * 0.01)
        
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
        
        # Decrement cooldown
        if cooldown_bars > 0:
            cooldown_bars -= 1
        
        # Check for new entries
        if broker.position is None and cooldown_bars == 0:
            # Build inputs for strategy
            bar = build_bar_dict(i, o, h, l, c, v)
            ind = build_indicator_dict(i, ts, o, h, l, c, feats)
            state = build_state_dict(position=None, cooldown_bars_left=cooldown_bars)
            params = info.get('params', {}) if info else {}
            
            # Get signal from strategy
            try:
                signal = strategy_fn(bar, ind, state, params)
            except Exception as e:
                if verbose:
                    print(f"  [ERROR] Bar {i}: {e}")
                signal = None
            
            if signal and signal.get('side'):
                side = signal['side']
                
                # Build exit plan
                exit_plan = build_regime_exit_plan(
                    side, c[i], atr, i, h, l, feats, cfg.get('risk', {})
                )
                
                # Override with strategy-specific exit params
                exit_params = extract_exit_params(signal)
                if exit_params.get('sl_tp_style'):
                    # Update exit plan with strategy preferences
                    pass  # Exit plan already has good defaults
                
                # Calculate position size
                qty, notional, margin_used, lev = compute_qty(
                    c[i], broker.equity, cfg.get('sizing', {}),
                    stop_distance=abs(c[i] - exit_plan.sl),
                    atr1h_pct=feats.get('atr1h_pct', [1.0])[i]
                )
                
                if qty > 0:
                    # Open position
                    success = broker.open_with_plan(
                        ts[i], qty, c[i], lev, exit_plan,
                        note=f"{strategy_name}: {signal.get('reason', '')}"
                    )
                    
                    if success:
                        trade_count += 1
                        
                        if verbose and trade_count <= 5:
                            print(f"  [Trade #{trade_count}] {side} @ ${c[i]:,.2f}")
                            print(f"    Reason: {signal.get('reason', 'N/A')}")
                            print(f"    Regime: {signal.get('regime_hint', 'N/A')}")
    
    # Calculate metrics
    try:
        em = equity_metrics(broker.equity_curve)
        tm = trades_metrics(os.path.join(outdir, "trades.csv"))
    except Exception as e:
        print(f"  ⚠️  Error calculating metrics: {e}")
        em = {"ret_tot_pct": 0, "sharpe_ann": 0, "maxdd_pct": 0}
        tm = {"win_rate_pct": 0, "total_trades": 0}
    
    # Combine results
    result = {
        "strategy": strategy_name,
        "category": info.get("category", "unknown") if info else "unknown",
        "regime": info.get("regime", "unknown") if info else "unknown",
        "trades": trade_count,
        "return_pct": em.get("ret_tot_pct", 0),
        "sharpe": em.get("sharpe_ann", 0),
        "max_dd_pct": em.get("maxdd_pct", 0),
        "win_rate_pct": tm.get("win_rate_pct", 0),
        "final_equity": broker.equity,
        "outdir": outdir,
    }
    
    # Save individual result
    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"  [OK] Trades: {trade_count} | Return: {result['return_pct']:.2f}% | Sharpe: {result['sharpe']:.2f}")
    
    return result


def run_all_strategies(
    strategies: List[str],
    days: int,
    cfg: Dict,
    parallel: bool = False,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Run backtests for multiple strategies
    
    Args:
        strategies: List of strategy names
        days: Number of days to backtest
        cfg: Configuration dictionary
        parallel: Run strategies in parallel (experimental)
        verbose: Print detailed logs
    
    Returns:
        List of result dictionaries
    """
    
    print(f"\n{'='*80}")
    print(f"MULTI-STRATEGY BACKTEST - {len(strategies)} Strategies")
    print(f"{'='*80}")
    print(f"Period: {days} days")
    print(f"Parallel: {parallel}")
    print(f"{'='*80}\n")
    
    # Load data (shared across all strategies)
    conn = connect(cfg.get("db", {}).get("path", "data/bot.db"))
    now = int(time.time())
    start = now - days * 24 * 60 * 60
    
    print(f"[Data] Loading candles from {datetime.fromtimestamp(start).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(now).strftime('%Y-%m-%d')}")
    
    rows = load_range(conn, start, now)
    ts = [r[0] for r in rows]
    o = [r[1] for r in rows]
    h = [r[2] for r in rows]
    l = [r[3] for r in rows]
    c = [r[4] for r in rows]
    v = [r[5] for r in rows] if len(rows[0]) > 5 else None
    
    print(f"[Data] Loaded {len(rows)} candles\n")
    
    # Calculate features (shared)
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
    
    # Calculate EMA200 (not in features.py by default)
    def ema(prices, period):
        """Calculate EMA"""
        result = [None] * len(prices)
        k = 2 / (period + 1)
        result[period - 1] = sum(prices[:period]) / period
        for i in range(period, len(prices)):
            result[i] = prices[i] * k + result[i-1] * (1 - k)
        return result
    
    feat['ema200'] = ema(c, 200)
    print(f"[Features] Added EMA200\n")
    
    # Run strategies
    results = []
    
    if parallel:
        # Parallel execution (experimental)
        print("⚡ Running strategies in parallel...\n")
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    run_single_strategy_backtest,
                    strat, ts, o, h, l, c, v, feat, cfg, days, verbose
                )
                for strat in strategies
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
    else:
        # Sequential execution (recommended)
        for strategy_name in strategies:
            result = run_single_strategy_backtest(
                strategy_name, ts, o, h, l, c, v, feat, cfg, days, verbose
            )
            if result:
                results.append(result)
    
    return results


def generate_comparison_report(results: List[Dict[str, Any]], output_dir: str):
    """Generate comprehensive comparison report"""
    
    if not results:
        print("No results to report")
        return
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by return
    df = df.sort_values('return_pct', ascending=False)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "comparison.csv")
    df.to_csv(csv_path, index=False)
    
    # Print report
    print(f"\n{'='*100}")
    print("STRATEGY COMPARISON REPORT")
    print(f"{'='*100}\n")
    
    print(f"{'Rank':<6}{'Strategy':<35}{'Trades':<8}{'Return %':<12}{'Sharpe':<10}{'Max DD %':<12}{'Win Rate %':<12}")
    print("-" * 100)
    
    for idx, row in df.iterrows():
        rank = list(df.index).index(idx) + 1
        print(f"{rank:<6}{row['strategy']:<35}{row['trades']:<8}{row['return_pct']:>10.2f}%  {row['sharpe']:>8.2f}  {row['max_dd_pct']:>10.2f}%  {row['win_rate_pct']:>10.1f}%")
    
    # Summary stats
    print(f"\n{'='*100}")
    print("SUMMARY STATISTICS")
    print(f"{'='*100}")
    print(f"Total strategies tested: {len(df)}")
    print(f"Average return: {df['return_pct'].mean():.2f}%")
    print(f"Average Sharpe: {df['sharpe'].mean():.2f}")
    print(f"Average trades: {df['trades'].mean():.1f}")
    print(f"Best strategy: {df.iloc[0]['strategy']} ({df.iloc[0]['return_pct']:.2f}%)")
    print(f"Worst strategy: {df.iloc[-1]['strategy']} ({df.iloc[-1]['return_pct']:.2f}%)")
    
    # By category
    print(f"\n{'='*100}")
    print("BY CATEGORY")
    print(f"{'='*100}")
    cat_summary = df.groupby('category').agg({
        'return_pct': 'mean',
        'sharpe': 'mean',
        'trades': 'mean'
    }).round(2)
    print(cat_summary)
    
    print(f"\nFull report saved to: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(description='Run backtest for all 38 strategies')
    parser.add_argument('--days', type=int, default=90, help='Backtest period in days')
    parser.add_argument('--strategies', type=str, default='all', help='Strategies to test (all, trend, breakout, or comma-separated list)')
    parser.add_argument('--parallel', action='store_true', help='Run strategies in parallel (experimental)')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    args = parser.parse_args()
    
    # Load config
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    
    # Determine which strategies to run
    if args.strategies == 'all':
        strategies = list_all_strategies()
    elif args.strategies in ['trend', 'mean_reversion', 'breakout', 'volume', 'hybrid', 'advanced', 'refinement', 'final']:
        strategies = list(get_strategies_by_category(args.strategies).keys())
    elif args.strategies in STRATEGY_PRESETS:
     strategies = STRATEGY_PRESETS[args.strategies]['strategies']
    else:
        strategies = [s.strip() for s in args.strategies.split(',')]
    
    print(f"\nSelected {len(strategies)} strategies to test")
    
    # Create output directory
    timestamp = int(time.time())
    output_dir = os.path.join("data", "backtest_38", f"comparison_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Run backtests
    start_time = time.time()
    results = run_all_strategies(strategies, args.days, cfg, args.parallel, args.verbose)
    elapsed = time.time() - start_time
    
    # Generate report
    generate_comparison_report(results, output_dir)
 
    print(f"\nTotal time: {elapsed:.1f} seconds ({elapsed/len(strategies):.1f}s per strategy)")
    print(f"Results saved to: {output_dir}\n")


if __name__ == '__main__':
    main()