"""
Smart-Trade - Entry point for backtesting

Runs the 38-strategy backtest system with proper imports.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now run the backtest
from backtesting.run_all import main

if __name__ == '__main__':
    main()
