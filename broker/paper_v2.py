"""
Paper Futures Broker v2 - With Regime-Adaptive Exit Plan Support

Features:
- Multi-target partial exits
- ExitPlan integration
- Structure-aware trailing
- Regime-adaptive parameters
- Full compatibility with old API
"""

import os
import csv
import time
from typing import Optional, Dict, Any


class PaperFuturesBrokerV2:
    """
    Paper broker with regime-adaptive exit plan support
    
    Supports both:
    - Legacy API (simple SL/TP)
    - New ExitPlan API (multi-target, regime-adaptive)
    """
    
    def __init__(
        self,
        equity: float = 100000.0,
        max_daily_loss_pct: float = 2.0,
        spread_bps: float = 1.0,
        taker_fee_bps: float = 5.0,
        maker_fee_bps: float = 2.0,
        data_dir: str = "data/paper"
    ):
        self.equity = float(equity)
        self.start_equity = float(equity)
        self.max_daily_loss_pct = float(max_daily_loss_pct)
        self.spread_bps = float(spread_bps)
        self.taker_fee_bps = float(taker_fee_bps)
        self.maker_fee_bps = float(maker_fee_bps)
        self.data_dir = data_dir
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.trades_path = os.path.join(self.data_dir, "trades.csv")
        self.equity_path = os.path.join(self.data_dir, "equity_curve.csv")
        
        self._init_files()
        
        # Position tracking
        self.position = None
        self.exit_plan = None  # NEW: Store ExitPlan
        self.equity_curve = []
        
        # Tracking for highest/lowest since entry
        self.highest_since_entry = None
        self.lowest_since_entry = None
    
    def _init_files(self):
        """Initialize CSV files"""
        if not os.path.exists(self.trades_path):
            with open(self.trades_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["ts_utc", "action", "side", "qty", "price", "pnl", "note"])
        
        if not os.path.exists(self.equity_path):
            with open(self.equity_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["ts", "equity"])
    
    def on_candle(
        self,
        ts: int,
        high: float,
        low: float,
        close: float,
        atr: float,
        spread_bps: float = None,
        taker_bps: float = None,
        maker_bps: float = None,
        st_line: Optional[float] = None,
        kel_lo: Optional[float] = None,
        kel_up: Optional[float] = None
    ):
        """
        Process candle and check exits
        
        Supports both legacy and ExitPlan modes
        """
        self._write_equity(ts)
        
        if not self.position:
            return
        
        # Update highest/lowest tracking
        if self.highest_since_entry is None:
            self.highest_since_entry = high
        else:
            self.highest_since_entry = max(self.highest_since_entry, high)
        
        if self.lowest_since_entry is None:
            self.lowest_since_entry = low
        else:
            self.lowest_since_entry = min(self.lowest_since_entry, low)
        
        # === NEW: ExitPlan Mode ===
        if self.exit_plan is not None:
            self._process_exit_plan(ts, high, low, close, atr, st_line, kel_lo, kel_up)
            return
        
        # === LEGACY: Old mode ===
        self._process_legacy_exits(ts, high, low, close, atr, st_line, kel_lo, kel_up)
    
    def _process_exit_plan(
        self,
        ts: int,
        high: float,
        low: float,
        close: float,
        atr: float,
        st_line: Optional[float],
        kel_lo: Optional[float],
        kel_up: Optional[float]
    ):
        """Process exits using ExitPlan"""
        from backend.agents.exits import update_trailing_stop, check_exits
        
        plan = self.exit_plan
        plan.bars_in_trade += 1
        
        # Build context for trailing
        ctx = {
            "tick_size": 0.1,
            "close": close,
            "high": high,
            "low": low,
            "highest_since_entry": self.highest_since_entry,
            "lowest_since_entry": self.lowest_since_entry
        }
        
        if st_line is not None:
            ctx["supertrend"] = st_line
        if kel_lo is not None:
            ctx["keltner_lo"] = kel_lo
        if kel_up is not None:
            ctx["keltner_up"] = kel_up
        
        # Update trailing stop
        update_trailing_stop(plan, ctx, ctx, atr)
        
        # Check exits
        exit_result = check_exits(plan, close, high, low)
        
        if exit_result:
            reason, price, partial_pct = exit_result
            
            if partial_pct:
                # Partial exit
                self._partial_exit(ts, price, reason, partial_pct)
            else:
                # Full exit
                self._close(ts, price, reason)
    
    def _process_legacy_exits(
        self,
        ts: int,
        high: float,
        low: float,
        close: float,
        atr: float,
        st_line: Optional[float],
        kel_lo: Optional[float],
        kel_up: Optional[float]
    ):
        """Process exits using legacy mode"""
        self.position["bars_in_trade"] += 1
        
        # Breakeven
        if self.position.get("breakeven_at_R") is not None:
            R = self.position.get("R", None)
            if R and not self.position.get("breakeven_done", False):
                if self.position["side"] == "LONG":
                    if close >= self.position["entry"] + self.position["breakeven_at_R"] * R:
                        self.position["sl"] = max(self.position["sl"], self.position["entry"])
                        self.position["breakeven_done"] = True
                else:
                    if close <= self.position["entry"] - self.position["breakeven_at_R"] * R:
                        self.position["sl"] = min(self.position["sl"], self.position["entry"])
                        self.position["breakeven_done"] = True
        
        # Trailing
        tstyle = self.position.get("trailing_style")
        if tstyle == "atr" and self.position.get("trail_atr_mult"):
            m = float(self.position["trail_atr_mult"])
            if self.position["side"] == "LONG":
                self.position["sl"] = max(self.position["sl"], close - m * (atr or close * 0.01))
            else:
                self.position["sl"] = min(self.position["sl"], close + m * (atr or close * 0.01))
        elif tstyle == "supertrend" and st_line is not None:
            if self.position["side"] == "LONG":
                self.position["sl"] = max(self.position["sl"], float(st_line))
            else:
                self.position["sl"] = min(self.position["sl"], float(st_line))
        elif tstyle == "keltner" and kel_lo is not None and kel_up is not None:
            if self.position["side"] == "LONG":
                self.position["sl"] = max(self.position["sl"], float(kel_lo))
            else:
                self.position["sl"] = min(self.position["sl"], float(kel_up))
        
        # Partial TP (legacy)
        if self.position.get("partial_tp_at_R") and not self.position.get("pt_taken"):
            R = self.position.get("R", None)
            if R:
                if self.position["side"] == "LONG" and close >= self.position["entry"] + self.position["partial_tp_at_R"] * R:
                    self._partial(ts, close, "TP_PARTIAL")
                if self.position["side"] == "SHORT" and close <= self.position["entry"] - self.position["partial_tp_at_R"] * R:
                    self._partial(ts, close, "TP_PARTIAL")
        
        # Time stop
        if self.position["bars_in_trade"] >= self.position.get("time_stop_bars", 999999):
            self._close(ts, close, "TIME_STOP")
            return
        
        # Check TP/SL
        if self.position["side"] == "LONG":
            if high >= self.position["tp"]:
                self._close(ts, float(self.position["tp"]), "TP_FULL")
            elif low <= self.position["sl"]:
                self._close(ts, float(self.position["sl"]), "STOP")
        else:
            if low <= self.position["tp"]:
                self._close(ts, float(self.position["tp"]), "TP_FULL")
            elif high >= self.position["sl"]:
                self._close(ts, float(self.position["sl"]), "STOP")
    
    def open(
        self,
        ts: int,
        side: str,
        qty: float,
        price: float,
        sl: float,
        tp: float,
        R: float,
        leverage: float,
        spread_bps: float = None,
        taker_bps: float = None,
        note_extra: str = "",
        trailing_style: str = "atr",
        trail_atr_mult: Optional[float] = None,
        breakeven_at_R: Optional[float] = None,
        partial_tp_at_R: Optional[float] = None,
        time_stop_bars: Optional[int] = None
    ) -> bool:
        """Open position (legacy API)"""
        if self.position:
            return False
        
        self.position = {
            "ts": ts,
            "side": side,
            "qty": qty,
            "entry": price,
            "sl": float(sl),
            "tp": float(tp),
            "R": float(R),
            "leverage": float(leverage),
            "bars_in_trade": 0,
            "trailing_style": trailing_style,
            "trail_atr_mult": trail_atr_mult,
            "breakeven_at_R": breakeven_at_R,
            "partial_tp_at_R": partial_tp_at_R,
            "time_stop_bars": time_stop_bars or 96,
            "breakeven_done": False,
            "pt_taken": False
        }
        
        # Reset tracking
        self.highest_since_entry = price
        self.lowest_since_entry = price
        
        self._log(ts, "OPEN_" + side, side, qty, price, 0.0, f"{note_extra} trail={trailing_style}")
        return True
    
    def open_with_plan(self, ts: int, qty: float, price: float, leverage: float, exit_plan, note: str = ""):
        """Open position with ExitPlan (NEW API)"""
        if self.position:
            return False
        
        self.position = {
            "ts": ts,
            "side": exit_plan.side,
            "qty": qty,
            "entry": price,
            "leverage": float(leverage),
            "bars_in_trade": 0
        }
        
        self.exit_plan = exit_plan
        
        # Reset tracking
        self.highest_since_entry = price
        self.lowest_since_entry = price
        
        self._log(ts, "OPEN_" + exit_plan.side, exit_plan.side, qty, price, 0.0, note)
        return True
    
    def _partial_exit(self, ts: int, price: float, reason: str, pct: float):
        """Partial exit (close X% of position)"""
        if not self.position:
            return
        
        qty_to_close = self.position["qty"] * pct
        if qty_to_close <= 0:
            return
        
        side = self.position["side"]
        entry = self.position["entry"]
        
        # Calculate PnL
        if side == "LONG":
            pnl = (price - entry) * qty_to_close
        else:
            pnl = (entry - price) * qty_to_close
        
        # Calculate fee
        fee = abs(entry * qty_to_close + price * qty_to_close) * (self.taker_fee_bps / 10000.0)
        
        # Update equity
        self.equity += pnl - fee
        
        # Log
        self._log(ts, reason, side, qty_to_close, price, pnl - fee, f"Partial {pct*100:.0f}%")
        
        # Reduce position size
        self.position["qty"] -= qty_to_close
        
        # If position fully closed, clear it
        if self.position["qty"] <= 0.0001:
            self.position = None
            self.exit_plan = None
            self.highest_since_entry = None
            self.lowest_since_entry = None
    
    def _partial(self, ts: int, price: float, reason: str):
        """Legacy partial exit (50%)"""
        self._partial_exit(ts, price, reason, 0.5)
    
    def _close(self, ts: int, price: float, reason: str):
        """Close full position"""
        if not self.position:
            return
        
        side = self.position["side"]
        qty = self.position["qty"]
        entry = self.position["entry"]
        
        # Calculate PnL
        if side == "LONG":
            pnl = (price - entry) * qty
        else:
            pnl = (entry - price) * qty
        
        # Calculate fee
        fee = abs(entry * qty + price * qty) * (self.taker_fee_bps / 10000.0)
        
        # Update equity
        self.equity += pnl - fee
        
        # Log
        self._log(ts, reason, side, qty, price, pnl - fee, "")
        
        # Clear position
        self.position = None
        self.exit_plan = None
        self.highest_since_entry = None
        self.lowest_since_entry = None
    
    def _log(self, ts: int, action: str, side: str, qty: float, price: float, pnl: float, note: str):
        """Log trade to CSV"""
        with open(self.trades_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([ts, action, side, qty, price, pnl, note])
    
    def _write_equity(self, ts: int):
        """Write equity to curve"""
        self.equity_curve.append([ts, self.equity])
        with open(self.equity_path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([ts, self.equity])


# Backwards compatibility alias
PaperFuturesBroker = PaperFuturesBrokerV2