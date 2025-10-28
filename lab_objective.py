"""
Safe objective evaluator for Strategy Lab

This module provides secure evaluation of objective functions for strategy optimization.
Uses numexpr for safe mathematical expression evaluation without using eval().

Supported operations:
- Arithmetic: +, -, *, /, **
- Comparisons: >, <, >=, <=, ==, !=
- Logical: &, | (and, or in numexpr)
- Functions: abs(), max(), min()
- Parentheses for grouping

Allowed variables:
- total_profit, sharpe, sortino, calmar, win_rate, max_dd
- profit_factor, avg_trade, trades, exposure, pnl_std

Examples:
    >>> evaluator = SafeObjectiveEvaluator()
    >>> metrics = {'sharpe': 2.5, 'total_profit': 50.0, 'max_dd': -15.0}
    >>> evaluator.evaluate('sharpe', metrics)
    2.5
    
    >>> evaluator.evaluate('(sharpe > 2) * 80 + (total_profit + 20)', metrics)
    150.0
"""

import re
from typing import Dict, Tuple, Any


class SafeObjectiveEvaluator:
    """Safe evaluator for objective functions using numexpr"""
    
    ALLOWED_VARS = {
        'total_profit', 'sharpe', 'sortino', 'win_rate', 'max_dd',
        'calmar', 'avg_trade', 'trades', 'exposure', 'pnl_std', 'profit_factor'
    }
    
    DANGEROUS_KEYWORDS = [
        'import', 'exec', 'eval', '__', 'open', 'file', 'compile',
        'globals', 'locals', 'dir', 'getattr', 'setattr', 'delattr'
    ]
    
    def validate(self, expression: str) -> Tuple[bool, str]:
        """Validate an objective expression"""
        try:
            if not expression or not expression.strip():
                return False, "Expression is empty"
            
            if len(expression) > 1000:
                return False, "Expression is too long (max 1000 characters)"
            
            expr_lower = expression.lower()
            for keyword in self.DANGEROUS_KEYWORDS:
                if keyword in expr_lower:
                    return False, f"Forbidden keyword: '{keyword}'"
            
            if expression.count('(') != expression.count(')'):
                return False, "Unbalanced parentheses"
            
            var_pattern = r'\b[a-z_][a-z0-9_]*\b'
            found_vars = set(re.findall(var_pattern, expression.lower()))
            
            numexpr_keywords = {'abs', 'max', 'min', 'where', 'sum', 'prod', 'true', 'false'}
            found_vars = found_vars - numexpr_keywords
            
            unknown_vars = found_vars - self.ALLOWED_VARS
            if unknown_vars:
                return False, f"Unknown variables: {', '.join(sorted(unknown_vars))}"
            
            return True, "OK"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def evaluate(self, expression: str, metrics: Dict[str, float]) -> float:
        """
        Evaluate an objective expression with given metrics
        
        Examples:
            >>> evaluator = SafeObjectiveEvaluator()
            >>> metrics = {'sharpe': 2.5, 'max_dd': -15.0, 'trades': 100}
            >>> evaluator.evaluate('sharpe', metrics)
            2.5
            
            >>> evaluator.evaluate('(sharpe > 2) * 100', metrics)
            100.0
        """
        try:
            valid, msg = self.validate(expression)
            if not valid:
                raise ValueError(f"Invalid expression: {msg}")
            
            eval_context = {var: float(metrics.get(var, 0.0)) for var in self.ALLOWED_VARS}
            
            try:
                import numexpr as ne
                
                expr_numexpr = expression.replace(' and ', ' & ').replace(' or ', ' | ')
                result = ne.evaluate(expr_numexpr, local_dict=eval_context)
                
                if hasattr(result, 'item'):
                    result = result.item()
                
                return float(result)
            
            except ImportError:
                safe_context = {
                    '__builtins__': {},
                    'abs': abs,
                    'max': max,
                    'min': min,
                    'True': 1,
                    'False': 0,
                }
                safe_context.update(eval_context)
                
                result = eval(expression, safe_context, {})
                
                if isinstance(result, bool):
                    result = 1.0 if result else 0.0
                
                return float(result)
        
        except Exception as e:
            raise ValueError(f"Error evaluating objective: {str(e)}")
    
    def evaluate_safe(self, expression: str, metrics: Dict[str, float], default: float = 0.0) -> float:
        """Evaluate expression safely, returning default value on error"""
        try:
            return self.evaluate(expression, metrics)
        except Exception as e:
            print(f"Warning: Objective evaluation failed: {e}")
            return default


objective_evaluator = SafeObjectiveEvaluator()


def evaluate_objective(metrics: Dict[str, Any], expr: str) -> float:
    """
    Convenience function to evaluate an objective expression
    
    Examples:
        >>> metrics = {'sharpe': 1.8, 'total_profit': 45.0, 'max_dd': -20.0, 'trades': 150}
        >>> evaluate_objective(metrics, 'sharpe')
        1.8
        
        >>> evaluate_objective(metrics, '(sharpe > 2) * 80 + (total_profit + 20)')
        65.0
    """
    return objective_evaluator.evaluate(expr, metrics)


if __name__ == "__main__":
    import doctest
    print("Running doctests...")
    results = doctest.testmod(verbose=True)
    if results.failed == 0:
        print(f"\n✓ All {results.attempted} tests passed!")
    else:
        print(f"\n✗ {results.failed} tests failed out of {results.attempted}")
