"""
Backtest Single Strategy - Wrapper for Optimizer

This script runs a single strategy backtest and outputs JSON for the optimizer.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == '__main__':
    # Run single.py as subprocess with same args
    result = subprocess.run(
        [sys.executable, 'backtesting/single.py'] + sys.argv[1:],
        env={'PYTHONPATH': str(project_root)}
    )
    sys.exit(result.returncode)
