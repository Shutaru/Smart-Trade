"""
Base policy interface
"""

from abc import ABC, abstractmethod
from ..schemas import Observation, Action


class Policy(ABC):
    """Abstract base class for trading policies"""
    
    @abstractmethod
    def decide(self, observation: Observation) -> Action:
        """
        Make trading decision based on observation
        
        Args:
  observation: Current market observation
        
        Returns:
            Action to take
        """
        pass
 
    @abstractmethod
    def reset(self):
        """Reset policy state"""
        pass
