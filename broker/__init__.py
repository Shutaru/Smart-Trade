"""
Broker Module - Trade Execution Layer

Paper and live trading brokers:
- paper_v1.py: Paper broker (legacy)
- paper_v2.py: Paper broker with ExitPlan support
- bitget.py: Bitget exchange executor
"""

from .paper_v2 import PaperFuturesBrokerV2
from .bitget import BitgetExecutor

__all__ = ['PaperFuturesBrokerV2', 'BitgetExecutor']
