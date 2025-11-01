
import os, csv, time

class PaperFuturesBroker:
    def __init__(self, equity=100000.0, max_daily_loss_pct=2.0, partial_tp_at_R=1.0, trail_atr_mult=2.0, time_stop_bars=96,
                 spread_bps=1.0, taker_fee_bps=5.0, maker_fee_bps=2.0, data_dir="data/paper"):
        self.equity = float(equity)
        self.start_equity = float(equity)
        self.max_daily_loss_pct = float(max_daily_loss_pct)
        self.partial_tp_at_R = float(partial_tp_at_R)
        self.time_stop_bars = int(time_stop_bars)
        self.spread_bps = float(spread_bps)
        self.taker_fee_bps = float(taker_fee_bps)
        self.maker_fee_bps = float(maker_fee_bps)
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.trades_path = os.path.join(self.data_dir, "trades.csv")
        self.equity_path = os.path.join(self.data_dir, "equity_curve.csv")
        self._init_files()
        self.position = None
        self.equity_curve = []

    def _init_files(self):
        if not os.path.exists(self.trades_path):
            with open(self.trades_path, "w", newline="") as f:
                w = csv.writer(f); w.writerow(["ts_utc","action","side","qty","price","pnl","note"])
        if not os.path.exists(self.equity_path):
            with open(self.equity_path, "w", newline="") as f:
                w = csv.writer(f); w.writerow(["ts","equity"])

    def on_candle(self, ts, high, low, close, atr5, spread_bps, taker_bps, maker_bps, st_line=None, kel_lo=None, kel_up=None):
        self._write_equity(ts)
        if not self.position: return

        self.position["bars_in_trade"] += 1

        # breakeven move
        if self.position.get("breakeven_at_R") is not None:
            R = self.position.get("R", None)
            if R and not self.position.get("breakeven_done", False):
                if self.position["side"]=="LONG":
                    if close >= self.position["entry"] + self.position["breakeven_at_R"]*R:
                        self.position["sl"] = max(self.position["sl"], self.position["entry"])
                        self.position["breakeven_done"] = True
                else:
                    if close <= self.position["entry"] - self.position["breakeven_at_R"]*R:
                        self.position["sl"] = min(self.position["sl"], self.position["entry"])
                        self.position["breakeven_done"] = True

        # trailing style
        tstyle = self.position.get("trailing_style")
        if tstyle == "atr" and self.position.get("trail_atr_mult"):
            m = float(self.position["trail_atr_mult"])
            if self.position["side"]=="LONG":
                self.position["sl"] = max(self.position["sl"], close - m*(atr5 or close*0.01))
            else:
                self.position["sl"] = min(self.position["sl"], close + m*(atr5 or close*0.01))
        elif tstyle == "supertrend" and st_line is not None:
            if self.position["side"]=="LONG":
                self.position["sl"] = max(self.position["sl"], float(st_line))
            else:
                self.position["sl"] = min(self.position["sl"], float(st_line))
        elif tstyle == "keltner" and kel_lo is not None and kel_up is not None:
            if self.position["side"]=="LONG":
                self.position["sl"] = max(self.position["sl"], float(kel_lo))
            else:
                self.position["sl"] = min(self.position["sl"], float(kel_up))

        # partial TP at R
        if self.partial_tp_at_R and not self.position.get("pt_taken"):
            R = self.position.get("R", None)
            if R:
                if self.position["side"]=="LONG" and close >= self.position["entry"] + self.partial_tp_at_R*R:
                    self._partial(ts, close, "TP_PARTIAL")
                if self.position["side"]=="SHORT" and close <= self.position["entry"] - self.partial_tp_at_R*R:
                    self._partial(ts, close, "TP_PARTIAL")

        # time stop
        if self.position["bars_in_trade"] >= self.time_stop_bars:
            self._close(ts, close, "TIME_STOP"); return

        # check exits
        if self.position["side"]=="LONG":
            if close >= self.position["tp"]:
                self._close(ts, float(self.position["tp"]), "TP_FULL")
            elif close <= self.position["sl"]:
                self._close(ts, float(self.position["sl"]), "STOP")
        else:
            if close <= self.position["tp"]:
                self._close(ts, float(self.position["tp"]), "TP_FULL")
            elif close >= self.position["sl"]:
                self._close(ts, float(self.position["sl"]), "STOP")

    def open(self, ts, side, qty, price, sl, tp, R, leverage, spread_bps, taker_bps, note_extra="", trailing_style="atr", trail_atr_mult=None, breakeven_at_R=None):
        if self.position: return False
        self.position = {
            "ts": ts, "side": side, "qty": qty, "entry": price, "sl": float(sl), "tp": float(tp),
            "R": float(R), "leverage": float(leverage), "bars_in_trade": 0,
            "trailing_style": trailing_style, "trail_atr_mult": trail_atr_mult, "breakeven_at_R": breakeven_at_R,
            "breakeven_done": False, "pt_taken": False
        }
        self._log(ts, "OPEN_"+side, side, qty, price, 0.0, f"{note_extra} trail={trailing_style}")
        return True

    def _partial(self, ts, price, reason):
        if not self.position: return
        qty = self.position["qty"] * 0.5
        if qty <= 0: return
        side = self.position["side"]
        entry = self.position["entry"]
        pnl = (price-entry)*qty if side=="LONG" else (entry-price)*qty
        fee = abs(entry*qty + price*qty)*(self.taker_fee_bps/10000.0)
        self.equity += pnl - fee
        self._log(ts, reason, side, qty, price, pnl-fee, "")
        self.position["qty"] -= qty
        self.position["pt_taken"] = True

    def _close(self, ts, price, reason):
        side = self.position["side"]; qty = self.position["qty"]; entry = self.position["entry"]
        pnl = (price-entry)*qty if side=="LONG" else (entry-price)*qty
        fee = abs(entry*qty + price*qty)*(self.taker_fee_bps/10000.0)
        self.equity += pnl - fee
        self._log(ts, reason, side, qty, price, pnl-fee, "")
        self.position = None

    def _log(self, ts, action, side, qty, price, pnl, note):
        with open(self.trades_path, "a", newline="") as f:
            w = csv.writer(f); w.writerow([ts, action, side, qty, price, pnl, note])

    def _write_equity(self, ts):
        self.equity_curve.append([ts, self.equity])
        with open(self.equity_path, "a", newline="") as f:
            csv.writer(f).writerow([ts, self.equity])
