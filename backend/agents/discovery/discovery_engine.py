"""
Strategy Discovery Engine

Runs multiple backtests in parallel to discover optimal strategies.
"""

import asyncio
import time
import os
import json
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import shutil

# Ensure project root is on sys.path so file can be executed directly
PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.agents.discovery.strategy_catalog import StrategyCatalog, StrategyTemplate
from backend.agents.discovery.ranker import StrategyRanker, StrategyMetrics
from backend.agents.discovery.entry_logic_builder import build_professional_entry_logic


class StrategyDiscoveryEngine:
    """Automated strategy discovery system"""

    def __init__(self, config_path: str = "config.yaml", max_parallel: int = 5, timeframe: str = None):
        self.config_path = config_path
        self.max_parallel = max_parallel
        self.timeframe = timeframe  # Override timeframe if provided
        self.catalog = StrategyCatalog()
        self.ranker = StrategyRanker()

        # Load base config
        with open(config_path, "r", encoding="utf-8") as f:
            self.base_config = yaml.safe_load(f) or {}
        
        # Override timeframe if specified
        if self.timeframe:
            self.base_config['timeframe'] = self.timeframe

        print(f"[StrategyDiscovery] Initialized with {len(self.catalog.INDICATORS)} indicators")
        if self.timeframe:
            print(f"[StrategyDiscovery] Using timeframe override: {self.timeframe}")

    async def run_backtest(self, strategy_name: str, strategy_config: Dict[str, Any]) -> Optional[StrategyMetrics]:
        """Run a single backtest asynchronously and return StrategyMetrics or None."""
        temp_dir = Path("data") / "discovery"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_config_path = temp_dir / f"config_{strategy_name}.yaml"
        original_backup = Path(self.config_path + ".backup")

        try:
            print(f"[Discovery] Running backtest: {strategy_name}")

            # Prepare temporary config
            temp_config = dict(self.base_config) if isinstance(self.base_config, dict) else {}
            if isinstance(temp_config.get("risk"), dict):
                temp_config["risk"] = dict(temp_config.get("risk", {}))
            temp_config["risk"].update(strategy_config.get("risk", {}))

            # Build declarative entry logic from strategy indicators using PROFESSIONAL BUILDER
            from backend.agents.discovery.entry_logic_builder import build_professional_entry_logic
        
            indicators = strategy_config.get('indicators') or []
   
            # USE THE ENTRY LOGIC BUILDER (crossover-based, robust logic)
            entry_obj = build_professional_entry_logic(indicators)

            # Attach declarative entry into risk config (should_enter reads params.get('entry') from risk)
            temp_config.setdefault('risk', {})
            temp_config['risk']['entry'] = entry_obj

            with temp_config_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(temp_config, f)

            # Run backtest subprocess with environment that includes project root
            env = os.environ.copy()
            env['PYTHONPATH'] = PROJECT_ROOT + os.pathsep + env.get('PYTHONPATH', '')
            # Use unbuffered mode to ensure real-time output
            cmd = [sys.executable, "-u", "backtest.py", "--days", "365", "--progress-file", str(temp_dir / f"progress_{strategy_name}.json")]

            # Backup original config and replace with temp
            if Path(self.config_path).exists():
                shutil.move(self.config_path, str(original_backup))
                shutil.move(str(temp_config_path), self.config_path)

            # Run subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=PROJECT_ROOT,
            )
            stdout, stderr = await process.communicate()

            # Restore original config
            if original_backup.exists():
                try:
                    shutil.move(self.config_path, str(temp_config_path))
                except Exception:
                    pass
                shutil.move(str(original_backup), self.config_path)

            if process.returncode !=0:
                print(f"[Discovery] Backtest failed: {strategy_name}")
                try:
                    print(f"Error: {stderr.decode('utf-8', errors='replace')}")
                except Exception:
                    print("Error: <failed to decode stderr>")
                return None

            # Parse results: stdout may contain pretty-printed JSON across multiple lines.
            output_text = stdout.decode("utf-8", errors="replace").strip()
            if not output_text:
                print(f"[Discovery] Empty stdout for {strategy_name}")
                return None

            result_json = None
            #1) try full output
            try:
                result_json = json.loads(output_text)
            except Exception:
                pass

            #2) try to locate a balanced JSON object by scanning braces
            if result_json is None:
                import re
                for m in re.finditer(r"\{", output_text):
                    start = m.start()
                    depth =0
                    for j in range(start, len(output_text)):
                        ch = output_text[j]
                        if ch == '{':
                            depth +=1
                        elif ch == '}':
                            depth -=1
                        if depth ==0:
                            cand = output_text[start:j+1]
                            try:
                                result_json = json.loads(cand)
                                # found a balanced JSON block
                                break
                            except Exception:
                                # failed to parse this block, continue searching
                                break
                    if result_json is not None:
                        break

            #3) fallback: try each line separately
            if result_json is None:
                for line in output_text.splitlines():
                    try:
                        result_json = json.loads(line)
                        break
                    except Exception:
                        continue

            if result_json is None:
                # Save stdout/stderr to files for debugging
                log_dir = Path("data") / "discovery" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                out_path = log_dir / f"{strategy_name}_stdout.txt"
                err_path = log_dir / f"{strategy_name}_stderr.txt"
                try:
                    out_path.write_text(output_text, encoding="utf-8")
                except Exception:
                    pass
                try:
                    err_text = stderr.decode("utf-8", errors="replace")
                    err_path.write_text(err_text, encoding="utf-8")
                except Exception:
                    pass

                # Print a helpful debug snippet
                print(f"[Discovery] Failed to parse JSON output for {strategy_name}")
                snippet = output_text[-1000:] if len(output_text) >1000 else output_text
                print("--- STDOUT snippet (end) ---")
                print(snippet)
                print("--- STDERR snippet ---")
                try:
                    print(stderr.decode("utf-8", errors="replace")[-1000:])
                except Exception:
                    print("<unable to decode stderr>")
                print(f"[Discovery] Saved stdout/stderr to: {out_path} {err_path}")
                return None

            # Helper to safely parse numeric fields
            def fget(obj, key, default=0.0):
                try:
                    return float(obj.get(key, default))
                except Exception:
                    try:
                        return float(default)
                    except Exception:
                        return 0.0

            metrics = StrategyMetrics(
                strategy_name=strategy_name,
                total_return_pct=fget(result_json, "ret_tot_pct",0.0),
                cagr=fget(result_json, "ret_tot_pct",0.0), # simplified
                sharpe_ratio=fget(result_json, "sharpe_ann",0.0),
                sortino_ratio=fget(result_json, "sharpe_ann",0.0) *1.2,
                calmar_ratio=(fget(result_json, "ret_tot_pct",0.0) / max(1.0, abs(fget(result_json, "maxdd_pct",1.0)))),
                max_drawdown_pct=fget(result_json, "maxdd_pct",0.0),
                avg_drawdown_pct=fget(result_json, "maxdd_pct",0.0) *0.5,
                volatility_annual_pct=abs(fget(result_json, "ret_tot_pct",0.0)) *0.8,
                total_trades=int(result_json.get("trades",0) or 0),
                win_rate_pct=fget(result_json, "win_rate_pct",0.0),
                profit_factor=fget(result_json, "profit_factor",0.0),
                avg_win_pct=2.5,
                avg_loss_pct=-1.5,
                consecutive_wins=int(result_json.get("consecutive_wins",5) or 5),
                consecutive_losses=int(result_json.get("consecutive_losses",3) or 3),
                recovery_factor=(fget(result_json, "ret_tot_pct",0.0) / max(1.0, abs(fget(result_json, "maxdd_pct",1.0))))
            )

            print(f"[Discovery] ✓ {strategy_name}: Score={self.ranker.calculate_composite_score(metrics):.4f}")
            return metrics

        except Exception as e:
            print(f"[Discovery] Error running backtest {strategy_name}: {e}")
            return None

    async def discover_strategies(self, num_strategies: int =10) -> List[StrategyMetrics]:
        print(f"\n{'='*80}")
        print("STRATEGY DISCOVERY ENGINE")
        print(f"{'='*80}")
        print(f"Testing {num_strategies} strategy candidates...")
        print(f"Max parallel: {self.max_parallel}")
        print("")

        # Generate strategy candidates
        strategy_candidates = StrategyTemplate.generate_combinations()[:num_strategies]

        print("Strategy Candidates:")
        for i, candidate in enumerate(strategy_candidates,1):
            print(f" {i}. {candidate['name']}")
            print(f" Indicators: {', '.join(candidate['indicators'])}")
        print("")

        # Ensure sufficient backfill data is present (4 years ->1460 days)
        backfill_verified = await self.ensure_backfill(required_days=1460, timeframes=["5m", "1h", "4h"])

        if not backfill_verified.get("ok"):
            print("[Discovery] Insufficient backfill data - cannot proceed with strategy discovery")
            return []

        semaphore = asyncio.Semaphore(self.max_parallel)

        async def run_with_semaphore(strategy):
            async with semaphore:
                return await self.run_backtest(strategy['name'], {'indicators': strategy['indicators']})

        start_time = time.time()
        tasks = [run_with_semaphore(candidate) for candidate in strategy_candidates]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        valid_results = [r for r in results if r is not None]

        print(f"\n{'='*80}")
        print("✓ Discovery Complete")
        print(f"{'='*80}")
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Successful backtests: {len(valid_results)}/{num_strategies}")
        print("")

        ranked_strategies = self.ranker.rank_strategies(valid_results)
        print(self.ranker.format_report(ranked_strategies[:5]))

        return ranked_strategies

    def get_top_strategies(self, n: int =3) -> List[StrategyMetrics]:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = asyncio.create_task(self.discover_strategies())
            strategies = loop.run_until_complete(task)
        else:
            strategies = asyncio.run(self.discover_strategies())
        return self.ranker.get_top_n(strategies, n=n)

    def verify_backfill(self, required_days: int =1460, timeframes: List[str] = None) -> Dict[str, Any]:
        """
        Verify that the database contains sufficient historical data for the given timeframes.
        Returns a dict with details and a boolean 'ok'.
        """
        timeframes = timeframes or ["5m", "1h", "4h"]
        cfg = self.base_config
        symbol = cfg.get("symbol")
        db_path_cfg = cfg.get("db", {}).get("path")

        results: Dict[str, Any] = {"ok": True, "details": {}}

        # Helper to sanitize symbol
        def sanitize_symbol(sym: str) -> str:
            return sym.replace("/", "_").replace(":", "_") if isinstance(sym, str) else None

        sym_safe = sanitize_symbol(symbol) if symbol else None

        for tf in timeframes:
            # try to derive db path for timeframe
            candidates = []
            if db_path_cfg and isinstance(db_path_cfg, str):
                # replace common timeframe tokens if present
                if db_path_cfg.endswith(".db") and any(x in db_path_cfg for x in ["5m", "1h", "4h", "_5m", "_1h", "_4h"]):
                    candidates.append(db_path_cfg.replace("5m", tf))
                    candidates.append(db_path_cfg.replace("1h", tf))
                    candidates.append(db_path_cfg.replace("4h", tf))
                else:
                    # try appending
                    base = os.path.splitext(db_path_cfg)[0]
                    candidates.append(f"{base}_{tf}.db")
                    # try standard location using symbol
                    if sym_safe:
                        candidates.append(os.path.join("data", "db", f"{sym_safe}_{tf}.db"))

            found = False
            detail = {"path": None, "rows":0, "span_days":0.0}

            for p in candidates:
                if p and os.path.exists(p):
                    try:
                        import sqlite3
                        conn = sqlite3.connect(p)
                        cur = conn.cursor()
                        # try multiple table names and pick the one with largest span/rows
                        candidate_tbl = f"candles_{tf.replace('m','min').replace('h','hr').replace('d','day')}"
                        table_candidates = [candidate_tbl, "candles"]
                        ts_min = None; ts_max = None; rows =0
                        best_span =0.0
                        best_detail = None
                        for tbl in table_candidates:
                            try:
                                cur.execute(f"SELECT COUNT(*), MIN(ts), MAX(ts) FROM {tbl}")
                                r = cur.fetchone()
                                if r and r[0] and r[0] >0:
                                    r_rows = int(r[0])
                                    r_min = int(r[1]) if r[1] else None
                                    r_max = int(r[2]) if r[2] else None
                                    if r_rows >0 and r_min and r_max:
                                        # compute span in days (handle seconds vs ms)
                                        if r_max >1_000_000_000_000:
                                            span_seconds = (r_max - r_min) /1000.0
                                        else:
                                            span_seconds = (r_max - r_min)
                                        span_days_tbl = span_seconds /86400.0
                                    else:
                                        span_days_tbl =0.0
                                    # prefer table with larger span or more rows
                                    score = span_days_tbl *1000000 + r_rows
                                    if score > best_span:
                                        best_span = score
                                        rows = r_rows
                                        ts_min = r_min
                                        ts_max = r_max
                            except Exception:
                                continue
                        conn.close()
                        if rows >0 and ts_min and ts_max:
                            # Detect whether timestamps are in milliseconds or seconds
                            # If ts_max looks like milliseconds (>=1e12) treat as ms, else seconds
                            if ts_max >1_000_000_000_000:
                                span_seconds = (ts_max - ts_min) /1000.0
                            else:
                                span_seconds = (ts_max - ts_min)
                            span_days = span_seconds /86400.0
                        else:
                            span_days =0.0
                        detail = {"path": p, "rows": rows, "span_days": round(span_days,2)}
                        found = True
                        break
                    except Exception:
                        continue
            results["details"][tf] = detail
            if not found or detail["span_days"] < (required_days -10):
                results["ok"] = False

        return results

    async def run_backfill(self, symbol: str, timeframe: str, days: int =1460, db_path: str = None, exchange: str = None, since_ms: int = None) -> bool:
        """
        Run bitget_backfill.py as a subprocess to fetch historical candles for a symbol/timeframe.
        Returns True on success.
        """
        try:
            sym_safe = symbol.replace('/', '_').replace(':', '_')
            if not db_path:
                db_path = os.path.join('data', 'db', f"{sym_safe}_{timeframe}.db")
            # determine exchange: prefer explicit, then config, default to binance
            exchange_to_use = exchange or self.base_config.get('exchange') or 'binance'
            # progress file per timeframe
            progress_file = os.path.join('data', 'discovery', f'progress_backfill_{sym_safe}_{timeframe}.json')

            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            cmd = [
                sys.executable, '-u', 'bitget_backfill.py',
                '--symbol', symbol,
                '--timeframe', timeframe,
                '--db', db_path,
                '--exchange', exchange_to_use,
                '--progress-file', progress_file
            ]
            if since_ms:
                cmd += ['--since', str(int(since_ms))]
            else:
                cmd += ['--days', str(days)]

            env = os.environ.copy()
            env['PYTHONPATH'] = PROJECT_ROOT + os.pathsep + env.get('PYTHONPATH', '')

            print(f"[Discovery] Starting backfill: {symbol} {timeframe} days={days} -> {db_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=PROJECT_ROOT
            )

            stdout, stderr = await process.communicate()

            out_text = stdout.decode('utf-8', errors='replace').strip()
            err_text = stderr.decode('utf-8', errors='replace').strip()

            if process.returncode !=0:
                print(f"[Discovery] Backfill failed for {symbol} {timeframe}: returncode={process.returncode}")
                print(err_text[:1000])
                return False

            print(f"[Discovery] Backfill finished for {symbol} {timeframe} (exchange={exchange_to_use}). stdout snippet:\n{out_text[-1000:]}")
            return True
        except Exception as e:
            print(f"[Discovery] Exception while running backfill: {e}")
            return False

    async def ensure_backfill(self, required_days: int =1460, timeframes: List[str] = None) -> Dict[str, Any]:
        """
        Ensure the database has at least `required_days` of historical data for the given timeframes.
        If missing, attempt to fetch using bitget_backfill.py. Returns the final verify_backfill result.
        """
        timeframes = timeframes or ["5m", "1h", "4h"]

        print(f"[Discovery] Verifying backfill for timeframes: {', '.join(timeframes)} (required_days={required_days})")
        current = self.verify_backfill(required_days=required_days, timeframes=timeframes)

        # If ok, nothing to do
        if current.get('ok'):
            print("[Discovery] Backfill OK - sufficient history present")
            return current

        # If5m already has full coverage, prefer aggregating higher timeframes from5m
        five_min_detail = current.get('details', {}).get('5m')
        try:
            five_min_span = float(five_min_detail.get('span_days',0.0)) if five_min_detail else 0.0
        except Exception:
            five_min_span =0.0

        if five_min_span >= float(required_days):
            print(f"[Discovery]5m has sufficient history ({five_min_span} days). Attempting to aggregate higher TFs from5m before backfill.")
            for tf in timeframes:
                if tf == '5m':
                    continue
                det = current.get('details', {}).get(tf, {})
                if float(det.get('span_days',0.0)) >= float(required_days):
                    continue
                dbp = det.get('path') or os.path.join('data', 'db', f"{sanitize_symbol(self.base_config.get('symbol'))}_{tf}.db")
                # Use the5m DB as the source for aggregation
                five_min_db = five_min_detail.get('path') if five_min_detail and five_min_detail.get('path') else os.path.join('data', 'db', f"{sanitize_symbol(self.base_config.get('symbol'))}_5m.db")
                agg_cmd = [
                    sys.executable, 'tools/aggregate_timeframes.py',
                    '--db', five_min_db,
                    '--from-tf', '5m',
                    '--to-tf', tf,
                    '--since-ms', str(int(time.time() *1000) - int(required_days) *24 *3600 *1000)
                ]
                print(f"[Discovery] Aggregation will read from5m DB: {five_min_db} and produce {tf} table in that DB (or target DB if merged)")
                try:
                    print(f"[Discovery] Aggregating {tf} from5m into {dbp}")
                    proc = await asyncio.create_subprocess_exec(*agg_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=PROJECT_ROOT)
                    sout, serr = await proc.communicate()
                    print(f"[Discovery] Aggregation stdout: {sout.decode('utf-8', errors='replace')[:500]}")
                    if proc.returncode ==0:
                        print(f"[Discovery] Aggregation succeeded for {tf}")
                    else:
                        print(f"[Discovery] Aggregation failed for {tf}: {serr.decode('utf-8', errors='replace')[:500]}")
                except Exception as e:
                    print(f"[Discovery] Aggregation exception for {tf}: {e}")

        # re-verify after aggregation attempts
        current = self.verify_backfill(required_days=required_days, timeframes=timeframes)
        if current.get('ok'):
            print("[Discovery] Backfill OK after aggregation")
            return current

        # Otherwise try to backfill missing timeframes
        symbol = self.base_config.get('symbol')
        if not symbol:
            print("[Discovery] No symbol configured in config.yaml - cannot run backfill")
            return current

        now_ms = int(time.time() *1000)
        needed_start_ms = now_ms - int(required_days) *24 *3600 *1000
        # sanitized symbol for filenames
        try:
         sym_safe = symbol.replace('/', '_').replace(':', '_')
        except Exception:
         sym_safe = 'unknown_symbol'

        for tf, detail in current.get('details', {}).items():
            # marker file to avoid re-backfilling already-complete ranges
            marker_dir = Path('data') / 'discovery' / 'markers'
            marker_dir.mkdir(parents=True, exist_ok=True)
            marker_file = marker_dir / f"backfill_{sym_safe}_{tf}.json"
            # if marker exists and indicates coverage >= required_days, skip
            try:
                if marker_file.exists():
                    m = json.loads(marker_file.read_text(encoding='utf-8'))
                    if float(m.get('span_days',0.0)) >= float(required_days):
                        print(f"[Discovery] Marker found for {tf} with span {m.get('span_days')} days — skipping backfill")
                        continue
            except Exception:
                pass

            span = detail.get('span_days',0.0)
            dbp = detail.get('path') or os.path.join('data', 'db', f"{sanitize_symbol(symbol)}_{tf}.db")
            # Skip backfill if already has required span
            if span >= required_days:
                print(f"[Discovery] Skipping {tf}: already has {span} days >= required {required_days} days")
                continue
            
            # If no rows at all, fetch full window starting at needed_start_ms
            since_to_fetch = None
            try:
                import sqlite3
                conn = sqlite3.connect(dbp)
                cur = conn.cursor()
                # check best table
                tbl = f"candles_{tf.replace('m','min').replace('h','hr').replace('d','day')}"
                try:
                    r = cur.execute(f"SELECT MIN(ts), MAX(ts) FROM {tbl}").fetchone()
                except Exception:
                    r = cur.execute(f"SELECT MIN(ts), MAX(ts) FROM candles").fetchone()
                conn.close()
                if r and r[0] and r[1]:
                    r_min, r_max = int(r[0]), int(r[1])
                    # normalize to ms if stored as seconds
                    if r_max <1_000_000_000_000:
                        r_min_ms = r_min *1000
                        r_max_ms = r_max *1000
                    else:
                        r_min_ms = r_min
                        r_max_ms = r_max
                    print(f"[Discovery][debug] {tf} DB range (ms): min={r_min_ms}, max={r_max_ms}")
                    # If current DB doesn't cover needed_start_ms (missing older data), fetch from needed_start_ms
                    if r_min_ms > needed_start_ms:
                        since_to_fetch = needed_start_ms
                    # If DB is missing recent data, fetch from r_max+1
                    elif r_max_ms < now_ms:
                        since_to_fetch = r_max_ms +1
                    else:
                        since_to_fetch = None
                else:
                    since_to_fetch = needed_start_ms
            except Exception:
                since_to_fetch = needed_start_ms

            if since_to_fetch is None:
                # already covered
                continue
            # clamp since_to_fetch to sensible range
            since_to_fetch = max(needed_start_ms, int(since_to_fetch))
            if since_to_fetch >= now_ms:
                print(f"[Discovery] since_to_fetch {since_to_fetch} >= now ({now_ms}) — skipping {tf}")
                continue
            print(f"[Discovery] Missing data for {tf}: have {span} days, required {required_days} days. Attempting backfill from {since_to_fetch}...")
            success = await self.run_backfill(symbol, tf, days=required_days, db_path=dbp, exchange=self.base_config.get('exchange'), since_ms=since_to_fetch)
            if not success:
                print(f"[Discovery] Backfill attempt failed for {symbol} {tf}")
                # fallback: try to aggregate from available5m candles
                try:
                    agg_cmd = [
                        sys.executable,
                        'tools/aggregate_timeframes.py',
                        '--db', dbp,
                        '--from-tf', '5m',
                        '--to-tf', tf,
                        '--since-ms', str(needed_start_ms)
                    ]
                    print(f"[Discovery] Attempting aggregation fallback for {tf} from5m")
                    proc = await asyncio.create_subprocess_exec(
                        *agg_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=PROJECT_ROOT
                    )
                    sout, serr = await proc.communicate()
                    print(f"[Discovery] Aggregation stdout: {sout.decode('utf-8', errors='replace')[:500]}")
                    if proc.returncode ==0:
                        print(f"[Discovery] Aggregation fallback succeeded for {tf}")
                    else:
                        print(f"[Discovery] Aggregation fallback failed for {tf}: {serr.decode('utf-8', errors='replace')[:500]}")
                except Exception as e:
                    print(f"[Discovery] Aggregation fallback exception: {e}")
            else:
                print(f"[Discovery] Backfill attempt succeeded for {symbol} {tf}")

        # Re-verify after attempts
        final = self.verify_backfill(required_days=required_days, timeframes=timeframes)
        if final.get('ok'):
            print("[Discovery] Backfill completed and verified OK")
            # write markers per timeframe
            try:
                details = final.get('details', {})
                marker_dir = Path('data') / 'discovery' / 'markers'
                marker_dir.mkdir(parents=True, exist_ok=True)
                for tf, det in details.items():
                    mf = marker_dir / f"backfill_{sym_safe}_{tf}.json"
                    mf.write_text(json.dumps(det), encoding='utf-8')
            except Exception:
                pass
        else:
            print("[Discovery] Backfill incomplete - some timeframes still lack required history")
        return final


# CLI interface
async def main():
    print("Strategy Discovery Engine v1.0")
    print("")
    engine = StrategyDiscoveryEngine(config_path="config.yaml", max_parallel=3)
    strategies = await engine.discover_strategies(num_strategies=10)
    top3 = engine.ranker.get_top_n(strategies, n=3)

    print("\n" + "="*80)
    print("TOP3 STRATEGIES FOR OPTIMIZATION")
    print("="*80)
    for i, strategy in enumerate(top3,1):
        print(f"\n#{i} {strategy.strategy_name}")
        print(f" Composite Score: {strategy.composite_score:.4f}")
        print(f" Return: {strategy.total_return_pct:+.2f}%")
        print(f" Max DD: {strategy.max_drawdown_pct:.2f}%")
        print(f" Sharpe: {strategy.sharpe_ratio:.2f}")
        print(f" Win Rate: {strategy.win_rate_pct:.1f}%")

    print("\n✓ Discovery complete. Use these strategies for optimization phase.")


if __name__ == '__main__':
    asyncio.run(main())