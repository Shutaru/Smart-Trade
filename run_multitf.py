"""
Smart-Trade - Multi-Timeframe Backtest Runner

Runs backtests across multiple timeframes.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now run the backtest
from backtesting.run_multi_tf import main

if __name__ == '__main__':
    main()
