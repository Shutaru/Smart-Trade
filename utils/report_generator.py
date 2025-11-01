"""
Optimization Report Generator

Generates beautiful HTML reports comparing optimization results across strategies.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def generate_optimization_report(
    results: List[Dict[str, Any]],
    output_file: str = None,
    title: str = "Strategy Optimization Report"
) -> str:
    """
    Generate HTML report from optimization results
    
    Args:
        results: List of optimization results
    output_file: Output HTML file path
     title: Report title
    
    Returns:
        HTML string
    """
    
    if not output_file:
      timestamp = int(datetime.now().timestamp())
        output_file = f"data/optimization/report_{timestamp}.html"
    
    # Sort by best value
    results_sorted = sorted(results, key=lambda r: r.get('best_value', 0), reverse=True)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
 * {{
        margin: 0;
    padding: 0;
 box-sizing: border-box;
        }}
        
      body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
     padding: 2rem;
        color: #333;
    }}
        
  .container {{
          max-width: 1400px;
            margin: 0 auto;
     }}
        
        .header {{
    background: white;
      padding: 2rem;
    border-radius: 12px;
 box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        
h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
  background-clip: text;
    margin-bottom: 0.5rem;
        }}
        
     .timestamp {{
    color: #666;
            font-size: 0.9rem;
        }}
        
        .summary {{
         display: grid;
         grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
   margin-bottom: 2rem;
        }}
        
 .summary-card {{
  background: white;
    padding: 1.5rem;
      border-radius: 12px;
       box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        
 .summary-label {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
         letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}
  
        .summary-value {{
    font-size: 2rem;
       font-weight: 700;
            color: #333;
        }}

        .strategy-grid {{
   display: grid;
     grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
   gap: 2rem;
          margin-bottom: 2rem;
        }}
 
        .strategy-card {{
            background: white;
       border-radius: 12px;
     padding: 1.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
     }}
        
    .strategy-card:hover {{
            transform: translateY(-4px);
   box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        
   .strategy-rank {{
     display: inline-block;
     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
       color: white;
            padding: 0.25rem 0.75rem;
        border-radius: 20px;
            font-size: 0.85rem;
       font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .strategy-name {{
     font-size: 1.25rem;
            font-weight: 600;
     color: #333;
       margin-bottom: 1rem;
        }}
        
        .metrics {{
            display: grid;
      grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        
     .metric {{
       padding: 0.75rem;
   background: #f8f9fa;
        border-radius: 8px;
        }}
        
        .metric-label {{
     font-size: 0.75rem;
 color: #666;
    text-transform: uppercase;
        letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
        }}
  
        .metric-value {{
   font-size: 1.25rem;
        font-weight: 700;
         color: #333;
      }}
        
   .metric-value.positive {{
   color: #10b981;
        }}
 
      .metric-value.negative {{
   color: #ef4444;
     }}
        
        .parameters {{
            background: #f8f9fa;
        padding: 1rem;
            border-radius: 8px;
margin-top: 1rem;
        }}
        
        .parameters-title {{
       font-size: 0.85rem;
 font-weight: 600;
      color: #666;
 text-transform: uppercase;
            letter-spacing: 0.5px;
      margin-bottom: 0.5rem;
      }}
      
        .param-list {{
 display: flex;
            flex-wrap: wrap;
gap: 0.5rem;
   }}
        
        .param {{
        font-size: 0.8rem;
      padding: 0.25rem 0.75rem;
    background: white;
    border-radius: 20px;
 color: #333;
    }}
        
        .chart {{
            background: white;
            padding: 2rem;
       border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
        }}
        
        .footer {{
            text-align: center;
          color: white;
      margin-top: 3rem;
         opacity: 0.8;
        }}
    </style>
</head>
<body>
  <div class="container">
        <div class="header">
    <h1>{title}</h1>
       <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="summary">
     <div class="summary-card">
          <div class="summary-label">Strategies Optimized</div>
    <div class="summary-value">{len(results)}</div>
       </div>
   <div class="summary-card">
 <div class="summary-label">Best Sharpe</div>
         <div class="summary-value">{max([r.get('best_value', 0) for r in results]):.2f}</div>
    </div>
         <div class="summary-card">
        <div class="summary-label">Avg Return</div>
    <div class="summary-value">{sum([r.get('best_metrics', {}).get('return', 0) for r in results]) / len(results):.1f}%</div>
            </div>
    <div class="summary-card">
     <div class="summary-label">Total Trials</div>
          <div class="summary-value">{sum([r.get('n_trials', 0) for r in results])}</div>
            </div>
     </div>
   
    <div class="chart" id="comparison-chart"></div>
        
        <div class="strategy-grid">
"""
  
    # Add strategy cards
    for i, result in enumerate(results_sorted, 1):
        strategy_name = result.get('strategy_name', 'Unknown')
        best_value = result.get('best_value', 0)
  metrics = result.get('best_metrics', {})
     params = result.get('best_params', {})
        
     sharpe = metrics.get('sharpe', 0)
        ret = metrics.get('return', 0)
  dd = metrics.get('max_dd', 0)
        trades = metrics.get('trades', 0)
        win_rate = metrics.get('win_rate', 0)
        pf = metrics.get('profit_factor', 0)
        
 ret_class = 'positive' if ret > 0 else 'negative'
        
        html += f"""
          <div class="strategy-card">
             <div class="strategy-rank">#{i}</div>
     <div class="strategy-name">{strategy_name}</div>
         
         <div class="metrics">
        <div class="metric">
         <div class="metric-label">Sharpe</div>
      <div class="metric-value">{sharpe:.2f}</div>
          </div>
        <div class="metric">
    <div class="metric-label">Return</div>
   <div class="metric-value {ret_class}">{ret:+.2f}%</div>
             </div>
  <div class="metric">
                 <div class="metric-label">Max DD</div>
 <div class="metric-value">{dd:.2f}%</div>
        </div>
         <div class="metric">
         <div class="metric-label">Win Rate</div>
              <div class="metric-value">{win_rate:.1f}%</div>
     </div>
     </div>
  
           <div class="metrics">
         <div class="metric">
          <div class="metric-label">Trades</div>
              <div class="metric-value">{trades}</div>
 </div>
            <div class="metric">
      <div class="metric-label">Profit Factor</div>
         <div class="metric-value">{pf:.2f}</div>
          </div>
         </div>
    
       <div class="parameters">
    <div class="parameters-title">Best Parameters</div>
     <div class="param-list">
"""
        
     for param_name, param_value in params.items():
       if isinstance(param_value, float):
          param_str = f"{param_name}: {param_value:.2f}"
     else:
              param_str = f"{param_name}: {param_value}"
   html += f'<div class="param">{param_str}</div>'
 
        html += """
    </div>
                </div>
         </div>
"""
    
    html += """
 </div>
    
     <div class="footer">
        <p>Generated by Smart-Trade Strategy Optimizer</p>
        </div>
    </div>
    
    <script>
"""
    
    # Add Plotly chart data
    chart_data = {
        'strategies': [r.get('strategy_name', '') for r in results_sorted],
        'sharpe': [r.get('best_metrics', {}).get('sharpe', 0) for r in results_sorted],
        'return': [r.get('best_metrics', {}).get('return', 0) for r in results_sorted],
        'max_dd': [r.get('best_metrics', {}).get('max_dd', 0) for r in results_sorted]
    }
    
    html += f"""
        const data = {{
    strategies: {json.dumps(chart_data['strategies'])},
     sharpe: {json.dumps(chart_data['sharpe'])},
         return: {json.dumps(chart_data['return'])},
            maxDD: {json.dumps(chart_data['max_dd'])}
    }};
        
        const trace1 = {{
     x: data.strategies,
     y: data.sharpe,
            name: 'Sharpe Ratio',
        type: 'bar',
 marker: {{
    color: '#667eea'
        }}
        }};
        
      const trace2 = {{
            x: data.strategies,
       y: data.return,
            name: 'Return %',
            type: 'bar',
      marker: {{
                color: '#10b981'
            }}
   }};
        
        const layout = {{
   title: 'Strategy Performance Comparison',
            barmode: 'group',
         xaxis: {{
           title: 'Strategy',
       tickangle: -45
            }},
            yaxis: {{
    title: 'Value'
            }},
        showlegend: true,
          legend: {{
   x: 1,
 xanchor: 'right',
   y: 1
            }},
            margin: {{
              b: 150
            }}
    }};
     
        Plotly.newPlot('comparison-chart', [trace1, trace2], layout, {{responsive: true}});
    </script>
</body>
</html>
"""
    
    # Save HTML file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
      f.write(html)
    
    print(f"[Report] Generated: {output_file}")
    
    return html


if __name__ == '__main__':
    # Example usage
    example_results = [
        {
            'strategy_name': 'obv_range_fade',
        'best_value': 4.43,
            'best_metrics': {
       'sharpe': 4.36,
          'return': 4.40,
            'max_dd': 0.65,
                'trades': 3076,
  'win_rate': 39.6,
           'profit_factor': 0.55
    },
            'best_params': {
           'rsi_period': 14,
    'adx_threshold': 22,
          'atr_sl_mult': 2.0
     },
      'n_trials': 30
        },
        {
            'strategy_name': 'stoch_fast_reversal',
  'best_value': 3.07,
     'best_metrics': {
        'sharpe': 2.56,
       'return': 2.63,
'max_dd': 0.69,
      'trades': 3184,
      'win_rate': 38.9,
         'profit_factor': 0.52
            },
     'best_params': {
     'stoch_k_period': 12,
'stoch_d_period': 3,
                'atr_sl_mult': 1.8
  },
            'n_trials': 30
   }
]
    
    generate_optimization_report(example_results)
    print("? Example report generated!")
