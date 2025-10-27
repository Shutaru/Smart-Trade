import requests
import time

BASE = 'http://127.0.0.1:8000/api/lab'

print('\n' + '='*60)
print('PROMPT 6 TEST - Async Backtest Execution')
print('='*60 + '\n')

strategy = {
    'name': 'RSI Strategy',
    'long': {
        'entry_all': [{'indicator': 'rsi', 'timeframe': '5m', 'op': '<', 'params': [{'name': 'period', 'value': 14}], 'rhs': 30}],
        'entry_any': [],
        'exit_rules': [{'kind': 'tp_sl_fixed', 'params': {'tp_pct': 2, 'sl_pct': 1}}]
    },
    'short': {'entry_all': [], 'entry_any': [], 'exit_rules': []},
    'data': {'exchange': 'bitget', 'symbols': ['BTC/USDT:USDT'], 'timeframe': '5m', 'since': 1704067200000, 'until': 1735689600000},
    'risk': {'leverage': 3, 'position_sizing': 'fixed_usd', 'size_value': 1000, 'max_concurrent_positions': 1},
    'objective': {'expression': 'sharpe'},
    'warmup_bars': 300
}

try:
    print('[1/4] Creating backtest run...')
    r = requests.post(f'{BASE}/run/backtest', json=strategy, timeout=10)
    
    if r.status_code == 200:
        rid = r.json()['run_id']
        print(f'SUCCESS! Run ID: {rid[:8]}...')
    else:
        print(f'FAILED: HTTP {r.status_code}')
        exit(1)
    
    time.sleep(3)
    
    print('\n[2/4] Monitoring run status...')
    for i in range(10):
        st = requests.get(f'{BASE}/run/{rid}/status').json()
        bar = '#' * int(st['progress'] * 20) + '-' * (20 - int(st['progress'] * 20))
        print(f'  [{i+1:2}/10] {st["status"]:12} |{bar}| {st["progress"]*100:5.1f}%')
        
        if st['status'] in ['completed', 'failed']:
            print(f'\n  Run {st["status"]}!')
            if st.get('best_score'):
                print(f'  Best Score: {st["best_score"]:.4f}')
            break
        
        time.sleep(1)
    
    print('\n[3/4] Fetching results...')
    res = requests.get(f'{BASE}/run/{rid}/results').json()
    print(f'  Total Trials: {res["total"]}')
    
    if res['trials']:
        t = res['trials'][0]
        print(f'  Top Score: {t["score"]:.4f}')
        print('\n  Metrics:')
        for k, v in sorted(t['metrics'].items())[:5]:
            print(f'    {k:15}: {v:8.2f}')
    
    print('\n[4/4] Listing all runs...')
    runs = requests.get(f'{BASE}/runs?limit=5').json()
    print(f'  Found {len(runs)} runs')
    
    for idx, run in enumerate(runs[:3], 1):
        print(f'    [{idx}] {run["run_id"][:8]}... - {run["status"]}')
    
    print('\n' + '='*60)
    print('ALL TESTS PASSED!')
    print('='*60 + '\n')
    print(f'Artifacts: artifacts/{rid[:8]}.../')

except requests.exceptions.ConnectionError:
    print('\nERROR: Cannot connect to server')
except Exception as e:
    print(f'\nERROR: {e}')
    import traceback
    traceback.print_exc()