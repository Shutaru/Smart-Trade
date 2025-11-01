"""
Update all imports to reflect new modular structure

This script updates import statements across all Python files
to match the new organized folder structure.
"""

import os
import re
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Strategies
    'from strategy_registry import': 'from strategies.registry import',
    'import strategy_registry': 'import strategies.registry',
    'from strategy import': 'from strategies.core import',
    'import strategy': 'import strategies.core',
    'from strategy_regime import': 'from strategies.regime import',
    'from indicator_adapter import': 'from strategies.adapter import',
    
    # Individual strategy modules
    'from strategies_trend_following import': 'from strategies.trend_following import',
    'from strategies_mean_reversion import': 'from strategies.mean_reversion import',
    'from strategies_breakout import': 'from strategies.breakout import',
    'from strategies_volume import': 'from strategies.volume import',
 'from strategies_hybrid import': 'from strategies.hybrid import',
    'from strategies_advanced import': 'from strategies.advanced import',
    'from strategies_refinements import': 'from strategies.refinements import',
    'from strategies_final import': 'from strategies.final import',
    
    # Broker
    'from broker_futures_paper import': 'from broker.paper_v1 import',
    'from broker_futures_paper_v2 import': 'from broker.paper_v2 import',
    'import broker_futures_paper_v2': 'import broker.paper_v2',
    'from executor_bitget import': 'from broker.bitget import',
    
    # Core
    'from db_sqlite import': 'from core.database import',
    'import db_sqlite': 'import core.database',
  'from features import': 'from core.features import',
    'import features': 'import core.features',
    'from indicators import': 'from core.indicators import',
    'import indicators': 'import core.indicators',
    'from sizing import': 'from core.sizing import',
 'import sizing': 'import core.sizing',
    'from metrics import': 'from core.metrics import',
    'import metrics': 'import core.metrics',
    
    # Optimization
    'from strategy_optimizer import': 'from optimization.optimizer import',
    'from portfolio_manager import': 'from optimization.portfolio import',
    'from walkforward_validator import': 'from optimization.walkforward import',
    
    # ML
  'from ml_model import': 'from ml.model import',
    'from ml_data import': 'from ml.data import',
    
 # Lab
    'from lab_runner import': 'from lab.runner import',
    'from lab_schemas import': 'from lab.schemas import',
    'from lab_features import': 'from lab.features import',
    'from lab_indicators import': 'from lab.indicators import',
    'from lab_objective import': 'from lab.objective import',
    'from lab_backtest_adapter import': 'from lab.adapter import',
}

def update_imports_in_file(file_path: Path) -> int:
    """
    Update imports in a single file
    
    Returns:
        Number of replacements made
    """
 try:
        with open(file_path, 'r', encoding='utf-8') as f:
 content = f.read()
 
        original_content = content
        replacements = 0
 
    # Apply all mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
 if old_import in content:
        content = content.replace(old_import, new_import)
   replacements += 1
        
        # Only write if changes were made
        if content != original_content:
 with open(file_path, 'w', encoding='utf-8') as f:
     f.write(content)
            return replacements
        
        return 0
    
    except Exception as e:
        print(f"  ? Error processing {file_path}: {e}")
        return 0


def update_all_imports():
    """Update imports in all Python files"""
    print("?? Updating imports in all Python files...\n")
    
    # Get all Python files (excluding venv and node_modules)
    root = Path('.')
    python_files = []
    
    for folder in ['strategies', 'backtesting', 'optimization', 'broker', 
          'core', 'data_fetchers', 'ml', 'lab', 'discovery', 
       'server', 'utils', 'backend']:
        if os.path.exists(folder):
python_files.extend(Path(folder).rglob('*.py'))
    
 # Also process root-level Python files
    for file in root.glob('*.py'):
      if file.name not in ['update_imports.py', 'setup.py']:
            python_files.append(file)
    
  total_files = 0
    total_replacements = 0
  
    for file_path in python_files:
        replacements = update_imports_in_file(file_path)
        if replacements > 0:
       total_files += 1
            total_replacements += replacements
         print(f"  ? {file_path}: {replacements} imports updated")
    
    print(f"\n{'='*80}")
    print(f"? Import update complete!")
    print(f"   Files modified: {total_files}")
    print(f"   Total replacements: {total_replacements}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    update_all_imports()
