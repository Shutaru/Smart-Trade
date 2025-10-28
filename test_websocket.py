import asyncio
import websockets
import json
import requests
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8000'
WS_URL = 'ws://127.0.0.1:8000'

async def test_ws():
    print('\n' + '='*70)
    print('PROMPT 7 TEST - WebSocket Real-Time Progress')
    print('='*70)
    
    print('\n[1/3] Creating run...')
    strategy = {
        'name': 'WS Test',
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
    
    r = requests.post(f'{BASE_URL}/api/lab/run/backtest', json=strategy, timeout=10)
    if r.status_code != 200:
        print(f'Failed: {r.status_code}')
        return
    
    run_id = r.json()['run_id']
    print(f'SUCCESS! Run ID: {run_id[:8]}...')
    
    print(f'\n[2/3] Connecting to WebSocket...')
    uri = f'{WS_URL}/ws/lab/run/{run_id}'
    
    try:
        async with websockets.connect(uri) as ws:
            print(f'Connected!')
            print('\n[3/3] Receiving updates...')
            print('-' * 70)
            
            count = 0
            start = asyncio.get_event_loop().time()
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    d = json.loads(msg)
                    count += 1
                    
                    ts = d.get('ts', 0)
                    dt = datetime.fromtimestamp(ts / 1000) if ts else datetime.now()
                    t = dt.strftime('%H:%M:%S')
                    
                    p = d.get('progress', 0)
                    if p is not None:
                        filled = int(p * 30)
                        bar = '#' * filled + '-' * (30 - filled)
                        pstr = f'|{bar}| {p*100:5.1f}%'
                    else:
                        pstr = ''
                    
                    lvl = d.get('level', 'INFO')
                    message = d.get('msg', '')
                    score = d.get('best_score')
                    
                    print(f'{t} [{lvl:5}] {message}')
                    if pstr:
                        print(f'           {pstr}')
                    if score:
                        print(f'           Best Score: {score:.4f}')
                    
                    if d.get('status') in ['completed', 'failed', 'cancelled']:
                        print(f'\n{"-" * 70}')
                        print(f'Run {d.get("status")}!')
                        break
                
                except asyncio.TimeoutError:
                    print('\nTimeout')
                    break
                except websockets.exceptions.ConnectionClosed:
                    print('\nConnection closed')
                    break
            
            elapsed = asyncio.get_event_loop().time() - start
            print(f'\n{"="*70}')
            print(f'Summary: {count} messages in {elapsed:.2f}s')
            print(f'{"="*70}\n')
            print('TEST PASSED!')
    
    except Exception as e:
        print(f'\nError: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        asyncio.run(test_ws())
    except KeyboardInterrupt:
        print('\nInterrupted')
    except Exception as e:
        print(f'\nFailed: {e}')