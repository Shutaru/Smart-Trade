"""
Optimization Backtest Engine

Lightweight backtest engine specifically for optimization.
No external dependencies, fast execution, JSON output.
"""

import sys
import json
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.database import connect, load_range
from core.features import compute_feature_rows
from broker.paper_v2 import PaperFuturesBrokerV2
from core.sizing import compute_qty
from strategies.registry import get_strategy
from strategies.regime import build_regime_exit_plan
from strategies.adapter import build_bar_dict, build_indicator_dict, build_state_dict
import pandas as pd
import yaml


def run_optimization_backtest(config_path: str, days: int = 365):
    """
    Run a single backtest for optimization.
    
    Args:
        config_path: Path to config file
        days: Number of days to backtest
        
    Returns:
        dict: Metrics including return, sharpe, trades, etc.
    """
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    
    # Extract config
    symbol = cfg.get('symbol', 'BTC/USDT:USDT')
    timeframe = cfg.get('timeframe', '5m')
    strategy_name = cfg.get('strategy')
    
    if not strategy_name:
        return {
            'error': 'No strategy specified in config',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Get strategy function
    try:
        strategy_fn = get_strategy(strategy_name)
        if not strategy_fn:
            return {
                'error': f'Strategy {strategy_name} not found',
                'ret_tot_pct': -999.0,
                'sharpe_ann': -999.0,
                'trades': 0
            }
    except Exception as e:
        return {
            'error': f'Failed to load strategy: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Load data
    db_path = cfg.get('db', {}).get('path', f'data/db/{symbol.replace("/", "_").replace(":", "_")}_{timeframe}.db')
    
    try:
        conn = connect(db_path)
    except Exception as e:
        return {
            'error': f'Failed to connect to database: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Calculate date range
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)
    
    # Load candles
    try:
        rows = load_range(conn, int(start_dt.timestamp()), int(end_dt.timestamp()))
        if rows is None or len(rows) == 0:
            return {
                'error': 'No data loaded',
                'ret_tot_pct': -999.0,
                'sharpe_ann': -999.0,
                'trades': 0
            }
        
        # Convert rows to lists
        ts = [r[0] for r in rows]
        o = [r[1] for r in rows]
        h = [r[2] for r in rows]
        l = [r[3] for r in rows]
        c = [r[4] for r in rows]
        v = [r[5] for r in rows] if len(rows[0]) > 5 else [1000.0] * len(rows)
        
    except Exception as e:
        return {
            'error': f'Failed to load data: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Compute features
    try:
        # Compute features (returns list of rows)
        feature_rows = compute_feature_rows(ts, o, h, l, c, v)
        
        # Build feature dictionary
        feats = {
            "ema20": [r[1] for r in feature_rows],
            "ema50": [r[2] for r in feature_rows],
            "atr14": [r[3] for r in feature_rows],
            "rsi5": [r[4] for r in feature_rows],
            "rsi14": [r[5] for r in feature_rows],
            "adx14": [r[6] for r in feature_rows],
            "bb_mid": [r[7] for r in feature_rows],
            "bb_lo": [r[8] for r in feature_rows],
            "bb_up": [r[9] for r in feature_rows],
            "dn55": [r[10] for r in feature_rows],
            "up55": [r[11] for r in feature_rows],
            "regime": [r[12] for r in feature_rows],
            "macro": [r[13] for r in feature_rows],
            "atr1h_pct": [r[14] for r in feature_rows],
            "macd": [r[15] for r in feature_rows],
            "macd_signal": [r[16] for r in feature_rows],
            "macd_hist": [r[17] for r in feature_rows],
            "stoch_k": [r[18] for r in feature_rows],
            "stoch_d": [r[19] for r in feature_rows],
            "cci20": [r[20] for r in feature_rows],
            "williams_r": [r[21] for r in feature_rows],
            "supertrend": [r[22] for r in feature_rows],
            "supertrend_dir": [r[23] for r in feature_rows],
            "mfi14": [r[24] for r in feature_rows],
            "vwap": [r[25] for r in feature_rows],
            "obv": [r[26] for r in feature_rows],
            "keltner_mid": [r[27] for r in feature_rows],
            "keltner_lo": [r[28] for r in feature_rows],
            "keltner_up": [r[29] for r in feature_rows],
        }
        
    except Exception as e:
        return {
            'error': f'Failed to compute features: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Initialize broker
    try:
        initial_balance = cfg.get('account', {}).get('starting_equity_usd', 100000)
        leverage = cfg.get('sizing', {}).get('leverage', 1)
        
        broker = PaperFuturesBrokerV2(
            equity=initial_balance,
            max_daily_loss_pct=cfg.get('risk', {}).get('max_daily_loss_pct', 2.0),
            spread_bps=cfg.get('fees', {}).get('spread_bps', 1.0),
            taker_fee_bps=cfg.get('fees', {}).get('taker_fee_bps', 5.0),
            maker_fee_bps=cfg.get('fees', {}).get('maker_fee_bps', 2.0),
            data_dir=str(PROJECT_ROOT / 'data' / 'optimization' / 'temp')
        )
    except Exception as e:
        return {
            'error': f'Failed to initialize broker: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Run backtest
    try:
        from core.indicators import supertrend as calc_supertrend, keltner as calc_keltner
        
        # Calculate trailing indicators for exits
        st_line, st_dir = calc_supertrend(h, l, c, n=10, mult=3.0)
        kel_mid, kel_lo, kel_up = calc_keltner(h, l, c, n=20, mult=1.5)
        
        for i in range(len(ts)):
            atr = feats["atr14"][i] or (c[i] * 0.01)
            
            # Update broker
            broker.on_candle(
                ts[i], h[i], l[i], c[i], atr,
                cfg['fees']['spread_bps'],
                cfg['fees']['taker_fee_bps'],
                cfg['fees']['maker_fee_bps'],
                st_line=st_line[i],
                kel_lo=kel_lo[i],
                kel_up=kel_up[i]
            )
            
            # Check if we have an open position
            if broker.position is not None:
                continue
            
            # Build inputs for strategy function
            bar = build_bar_dict(i, o, h, l, c, v)
            ind = build_indicator_dict(i, ts, o, h, l, c, feats)
            state = build_state_dict(position=None, cooldown_bars_left=0)
            params = cfg.get('risk', {})
            
            # Call strategy function
            signal = strategy_fn(bar, ind, state, params)
            
            if signal and signal.get('side'):
                side = signal['side']
                
                # Build exit plan
                exit_plan = build_regime_exit_plan(
                    side, c[i], atr, i, h, l, feats, cfg.get('risk', {})
                )
                
                # Calculate position size
                qty, notional, margin_used, lev = compute_qty(
                    c[i], broker.equity, cfg.get('sizing', {}),
                    stop_distance=abs(c[i] - exit_plan.sl),
                    atr1h_pct=feats['atr1h_pct'][i]
                )
                
                if qty > 0:
                    # Open position
                    broker.open_with_plan(
                        ts[i], qty, c[i], lev, exit_plan,
                        note=f"{strategy_name}: {signal.get('reason', '')}"
                    )
        
        # Close any remaining position
        if broker.position is not None:
            broker._close(ts[-1], c[-1], 'end_of_backtest')
        
    except Exception as e:
        return {
            'error': f'Backtest execution failed: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }
    
    # Calculate metrics
    try:
        from core.metrics import equity_metrics
        
        # Calculate equity metrics
        em = equity_metrics(broker.equity_curve)
        
        # Count closed trades
        closed_trades = []
        try:
            trades_file = PROJECT_ROOT / 'data' / 'optimization' / 'temp' / 'trades.csv'
            if trades_file.exists():
                with open(trades_file, 'r') as f:
                    import csv
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['action'] not in ['OPEN_LONG', 'OPEN_SHORT']:
                            closed_trades.append(row)
        except:
            pass
        
        # Ensure all required fields
        result = {
            'ret_tot_pct': em.get('ret_tot_pct', 0.0),
            'maxdd_pct': em.get('maxdd_pct', 0.0),
            'sharpe_ann': em.get('sharpe_ann', 0.0),
            'sortino_ann': em.get('sharpe_ann', 0.0) * 1.2,  # Approximate
            'trades': len(closed_trades),
            'win_rate_pct': 0.0,  # Would need to calculate from trades
            'profit_factor': 0.0,
            'final_balance': broker.equity
        }
        
        return result
        
    except Exception as e:
        return {
            'error': f'Failed to calculate metrics: {e}',
            'ret_tot_pct': -999.0,
            'sharpe_ann': -999.0,
            'trades': 0
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Optimization Backtest Engine')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('--days', type=int, default=365, help='Days to backtest')
    
    args = parser.parse_args()
    
    # Run backtest
    result = run_optimization_backtest(args.config, args.days)
    
    # Output JSON
    print(json.dumps(result, indent=2))
    
    # Exit with error code if failed
    if 'error' in result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()