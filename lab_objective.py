"""Safe objective evaluator for Strategy Lab"""


class SafeObjectiveEvaluator:
    ALLOWED_VARS = {
        'total_profit', 'sharpe', 'sortino', 'win_rate', 'max_dd',
        'calmar', 'avg_trade', 'trades', 'exposure', 'pnl_std'
    }
    
    def validate(self, expression: str):
        try:
            if not expression or len(expression) > 500:
                return False, "Expression empty or too long"
            
            dangerous = ['import', 'exec', 'eval', '__', 'open', 'file']
            for word in dangerous:
                if word in expression.lower():
                    return False, f"Dangerous keyword: {word}"
            
            if expression.count('(') != expression.count(')'):
                return False, "Unbalanced parentheses"
            
            return True, "OK"
        except Exception as e:
            return False, str(e)
    
    def evaluate(self, expression: str, metrics: dict):
        try:
            valid, msg = self.validate(expression)
            if not valid:
                raise ValueError(f"Invalid expression: {msg}")
            
            expr = expression
            for var in self.ALLOWED_VARS:
                value = metrics.get(var, 0.0)
                expr = expr.replace(var, str(float(value)))
            
            try:
                import numexpr as ne
                result = float(ne.evaluate(expr))
            except ImportError:
                allowed_names = {
                    '__builtins__': {
                        'abs': abs, 'max': max, 'min': min,
                        'float': float, 'int': int
                    }
                }
                result = float(eval(expr, allowed_names, {}))
            
            return result
        except Exception as e:
            print(f"Error evaluating objective: {e}")
            return 0.0


objective_evaluator = SafeObjectiveEvaluator()