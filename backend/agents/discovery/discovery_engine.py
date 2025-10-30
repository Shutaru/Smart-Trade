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


class StrategyDiscoveryEngine:
    """Automated strategy discovery system"""

    def __init__(self, config_path: str = "config.yaml", max_parallel: int =5):
        self.config_path = config_path
        self.max_parallel = max_parallel
        self.catalog = StrategyCatalog()
        self.ranker = StrategyRanker()

        # Load base config
        with open(config_path, "r", encoding="utf-8") as f:
            self.base_config = yaml.safe_load(f) or {}

        print(f"[StrategyDiscovery] Initialized with {len(self.catalog.INDICATORS)} indicators")

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

            # Parse results (expect last line JSON)
            output_text = stdout.decode("utf-8", errors="replace").strip()
            if not output_text:
                print(f"[Discovery] Empty stdout for {strategy_name}")
                return None

            try:
                last_line = output_text.splitlines()[-1]
                result_json = json.loads(last_line)
            except Exception:
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
                        # try multiple table names
                        table_candidates = ["candles", f"candles_{tf.replace('m','min').replace('h','hr').replace('d','day')}]"]
                        ts_min = None; ts_max = None; rows =0
                        for tbl in table_candidates:
                            try:
                                cur.execute(f"SELECT COUNT(*), MIN(ts), MAX(ts) FROM {tbl}")
                                r = cur.fetchone()
                                if r and r[0] and r[0] >0:
                                    rows = int(r[0])
                                    ts_min = int(r[1]) if r[1] else None
                                    ts_max = int(r[2]) if r[2] else None
                                    break
                            except Exception:
                                continue
                        conn.close()
                        if rows >0 and ts_min and ts_max:
                            span_days = (ts_max - ts_min) /1000.0 /86400.0
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

    async def run_backfill(self, symbol: str, timeframe: str, days: int =1460, db_path: str = None) -> bool:
        """
        Run bitget_backfill.py as a subprocess to fetch historical candles for a symbol/timeframe.
        Returns True on success.
        """
        try:
            sym_safe = symbol.replace('/', '_').replace(':', '_')
            if not db_path:
                db_path = os.path.join('data', 'db', f"{sym_safe}_{timeframe}.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            cmd = [
                sys.executable, '-u', 'bitget_backfill.py',
                '--symbol', symbol,
                '--days', str(days),
                '--timeframe', timeframe,
                '--db', db_path
            ]

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

            print(f"[Discovery] Backfill finished for {symbol} {timeframe}. stdout snippet:\n{out_text[-1000:]}")
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

        # Otherwise try to backfill missing timeframes
        symbol = self.base_config.get('symbol')
        if not symbol:
            print("[Discovery] No symbol configured in config.yaml - cannot run backfill")
            return current

        for tf, detail in current.get('details', {}).items():
            span = detail.get('span_days',0.0)
            if span >= required_days:
                continue
            print(f"[Discovery] Missing data for {tf}: have {span} days, required {required_days} days. Attempting backfill...")
            # Run backfill asking for full required_days (safer)
            success = await self.run_backfill(symbol, tf, days=required_days, db_path=detail.get('path') or None)
            if not success:
                print(f"[Discovery] Backfill attempt failed for {symbol} {tf}")
            else:
                print(f"[Discovery] Backfill attempt succeeded for {symbol} {tf}")

        # Re-verify after attempts
        final = self.verify_backfill(required_days=required_days, timeframes=timeframes)
        if final.get('ok'):
            print("[Discovery] Backfill completed and verified OK")
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