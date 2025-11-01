"""
Backtest Single Strategy - Wrapper for Optimizer

This script runs a single strategy backtest and outputs JSON for the optimizer.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now run single backtest
from backtesting.single import main

if __name__ == '__main__':
    main()
