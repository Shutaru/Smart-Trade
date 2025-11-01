"""
Smart-Trade Unified Interface

Single entry point for all trading system operations.
Designed for LLM control with natural language parameters.
"""

import sys
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class SmartTradeInterface:
    """Unified interface for all trading operations"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        
    def discovery(self, symbol='BTC/USDT:USDT', exchange='binance', timeframe='5m', strategies=10, parallel=2):
        """Run strategy discovery engine"""
        print(f"\n🔍 DISCOVERY MODE")
        print(f"Symbol: {symbol} | Exchange: {exchange} | Timeframe: {timeframe}")
        print(f"Testing {strategies} strategies with {parallel} parallel jobs\n")
        
        cmd = [sys.executable, 'discovery/run.py', '--symbol', symbol, '--exchange', exchange, 
               '--timeframe', timeframe, '--strategies', str(strategies), '--parallel', str(parallel), '--yes']
        return subprocess.call(cmd)
    
    def optimize(self, strategy, symbol='BTC/USDT:USDT', exchange='binance', timeframe='5m', 
                 trials=50, days=365, parallel=1):
        """Optimize strategy parameters"""
        print(f"\n⚙️  OPTIMIZATION MODE")
        print(f"Strategy: {strategy}")
        print(f"Symbol: {symbol} | Exchange: {exchange} | Timeframe: {timeframe}")
        print(f"Trials: {trials} | Days: {days}\n")
        
        cmd = [sys.executable, 'run_optimizer.py', '--strategy', strategy, '--symbol', symbol,
               '--exchange', exchange, '--timeframe', timeframe, '--trials', str(trials), 
               '--days', str(days), '--parallel', str(parallel)]
        return subprocess.call(cmd)
    
    def backtest(self, strategies='all', symbol=None, timeframe=None, days=90):
        """Run backtest for strategies"""
        print(f"\n📊 BACKTEST MODE")
        print(f"Strategies: {strategies} | Days: {days}\n")
        
        cmd = [sys.executable, 'run_backtest.py', '--days', str(days), '--strategies', strategies]
        return subprocess.call(cmd)
    
    def validate(self, symbol='BTC/USDT:USDT', exchange='binance', timeframe='5m', days=1460, trials=50):
        """Run complete validation pipeline"""
        print(f"\n✅ VALIDATION PIPELINE")
        print(f"Symbol: {symbol} | Exchange: {exchange} | Timeframe: {timeframe}")
        print(f"Period: {days} days (~{days/365:.1f} years) | Trials: {trials}\n")
        
        cmd = [sys.executable, 'run_validation_pipeline.py', '--symbol', symbol, '--exchange', exchange,
               '--timeframe', timeframe, '--days', str(days), '--trials', str(trials)]
        return subprocess.call(cmd)
    
    def live(self, mode='paper', strategy=None):
        """Start live trading (FUTURE)"""
        print(f"\n🔴 LIVE TRADING MODE: {mode}")
        print("⚠️  Not yet implemented\n")
        return 1


def main():
    parser = argparse.ArgumentParser(description='Smart-Trade Unified Interface')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discovery
    disc = subparsers.add_parser('discovery', help='Run strategy discovery')
    disc.add_argument('--symbol', default='BTC/USDT:USDT')
    disc.add_argument('--exchange', default='binance')
    disc.add_argument('--timeframe', default='5m')
    disc.add_argument('--strategies', type=int, default=10)
    disc.add_argument('--parallel', type=int, default=2)
    
    # Optimize
    opt = subparsers.add_parser('optimize', help='Optimize strategy')
    opt.add_argument('--strategy', required=True)
    opt.add_argument('--symbol', default='BTC/USDT:USDT')
    opt.add_argument('--exchange', default='binance')
    opt.add_argument('--timeframe', default='5m')
    opt.add_argument('--trials', type=int, default=50)
    opt.add_argument('--days', type=int, default=365)
    opt.add_argument('--parallel', type=int, default=1)
    
    # Backtest
    bt = subparsers.add_parser('backtest', help='Run backtest')
    bt.add_argument('--strategies', default='all')
    bt.add_argument('--days', type=int, default=90)
    
    # Validate
    val = subparsers.add_parser('validate', help='Run validation pipeline')
    val.add_argument('--symbol', default='BTC/USDT:USDT')
    val.add_argument('--exchange', default='binance')
    val.add_argument('--timeframe', default='5m')
    val.add_argument('--days', type=int, default=1460)
    val.add_argument('--trials', type=int, default=50)
    
    # Live
    live = subparsers.add_parser('live', help='Live trading (future)')
    live.add_argument('--mode', default='paper', choices=['paper', 'live'])
    live.add_argument('--strategy', default=None)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    interface = SmartTradeInterface()
    
    if args.command == 'discovery':
        return interface.discovery(args.symbol, args.exchange, args.timeframe, args.strategies, args.parallel)
    elif args.command == 'optimize':
        return interface.optimize(args.strategy, args.symbol, args.exchange, args.timeframe, 
                                  args.trials, args.days, args.parallel)
    elif args.command == 'backtest':
        return interface.backtest(args.strategies, None, None, args.days)
    elif args.command == 'validate':
        return interface.validate(args.symbol, args.exchange, args.timeframe, args.days, args.trials)
    elif args.command == 'live':
        return interface.live(args.mode, args.strategy)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())