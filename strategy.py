import os
from typing import Any, Dict, List, Optional


def compute_exit_levels(side, price, atr5, params, regime_hint=None):
    style = (params.get("sl_tp_style") or "atr_fixed").lower()
    sl_mult = float(params.get("sl_atr_mult", 2.0))
    tp_rr = float(params.get("tp_rr_multiple", 2.0))
    trail_mult = float(params.get("trail_atr_mult", 2.0))
    if side == "LONG":
        sl = price - sl_mult * (atr5 or price * 0.01)
        R = price - sl
        tp = price + tp_rr * R
    else:
        sl = price + sl_mult * (atr5 or price * 0.01)
        R = sl - price
        tp = price - tp_rr * R
    extra = {}
    if style == "atr_trailing":
        extra["trail_atr_mult"] = trail_mult
    if style == "chandelier":
        # just reuse trail multiplier
        extra["trail_atr_mult"] = trail_mult
    if style == "breakeven_then_trail":
        extra["breakeven_at_R"] = float(params.get("breakeven_at_R", 1.0))
        extra["trail_atr_mult"] = trail_mult
    if style in ("supertrend", "keltner"):
        extra["trail_atr_mult"] = trail_mult
    return sl, tp, extra


# ------------------------
# Generic condition evaluator
# ------------------------

def _normalize_op(op: str) -> str:
    if not op:
        return ''
    o = str(op).strip().lower()
    # common mappings
    mapping = {
        '>': '>',
        'gt': '>',
        '<': '<',
        'lt': '<',
        '>=': '>=',
        'gte': '>=',
        '<=': '<=',
        'lte': '<=',
        '==': '==',
        '=': '==',
        '!=': '!=',
        'between': 'between',
        'crossesabove': 'crosses_above',
        'crosses_above': 'crosses_above',
        'crossesbelow': 'crosses_below',
        'crosses_below': 'crosses_below',
        'crossabove': 'crosses_above',
        'crossbelow': 'crosses_below'
    }
    o_key = o.replace(' ', '').replace('-', '').replace('_', '')
    # try direct mapping
    if o in mapping:
        return mapping[o]
    if o_key in mapping:
        return mapping[o_key]
    # fallback to raw
    return o


def _get_series_value(name: str, i: int, ts, o, h, l, c, feats: Dict[str, List[Any]]):
    # price fields
    if not name:
        return None
    n = str(name).lower()
    if n in ('close', 'c', 'price'):
        return c[i]
    if n in ('open', 'o'):
        return o[i]
    if n in ('high',):
        return h[i]
    if n in ('low',):
        return l[i]
    # features
    # direct key access
    if isinstance(feats, dict) and name in feats:
        try:
            return feats[name][i]
        except Exception:
            return None
    # try lowercased keys
    if isinstance(feats, dict):
        for k in feats.keys():
            if k.lower() == n:
                try:
                    return feats[k][i]
                except Exception:
                    return None
    return None


def evaluate_condition(cond: Dict[str, Any], i: int, ts, o, h, l, c, feats: Dict[str, List[Any]]) -> bool:
    """Evaluate a single condition dict at index i.

    Condition format (flexible):
    {
    'indicator': 'rsi14' or 'close' or 'ema20',
    'op': '>' | '<' | 'crosses_above' | 'between' | ...,
    'rhs': numeric OR None,
    'rhs_indicator': 'ema50' (optional)
    }
    """
    if not isinstance(cond, dict):
        return False

    op = _normalize_op(cond.get('op') or cond.get('operator') or '')
    lhs_name = cond.get('indicator') or cond.get('lhs') or cond.get('field')

    lhs = _get_series_value(lhs_name, i, ts, o, h, l, c, feats)
    if lhs is None:
        return False

    # resolve rhs
    rhs_val = None
    if 'rhs' in cond and cond.get('rhs') is not None:
        try:
            rhs_val = float(cond.get('rhs'))
        except Exception:
            rhs_val = None
    rhs_ind = cond.get('rhs_indicator') or cond.get('rhs_indicator') or cond.get('rhs_field')
    if rhs_ind:
        rhs_val = _get_series_value(rhs_ind, i, ts, o, h, l, c, feats)

    # For cross operators we need previous values
    lhs_prev = None
    rhs_prev = None
    if i > 0:
        lhs_prev = _get_series_value(lhs_name, i - 1, ts, o, h, l, c, feats)
        if rhs_ind:
            rhs_prev = _get_series_value(rhs_ind, i - 1, ts, o, h, l, c, feats)
        elif rhs_val is not None:
            # constant rhs_prev equals constant
            rhs_prev = rhs_val

    try:
        if op in ('>', 'gt'):
            return lhs > rhs_val if rhs_val is not None else False
        if op in ('<', 'lt'):
            return lhs < rhs_val if rhs_val is not None else False
        if op == '>=':
            return lhs >= rhs_val if rhs_val is not None else False
        if op == '<=':
            return lhs <= rhs_val if rhs_val is not None else False
        if op in ('==', '='):
            return lhs == rhs_val
        if op == '!=':
            return lhs != rhs_val
        if op == 'between':
            # rhs expected as [low,high] or a tuple in cond['rhs']
            r = cond.get('rhs')
            if isinstance(r, (list, tuple)) and len(r) >= 2:
                low, high = float(r[0]), float(r[1])
                return (lhs >= low) and (lhs <= high)
            return False
        if op == 'crosses_above':
            # lhs_prev < rhs_prev and lhs >= rhs
            if lhs_prev is None:
                return False
            if rhs_ind:
                if rhs_prev is None or rhs_val is None:
                    return False
                return (lhs_prev < rhs_prev) and (lhs >= rhs_val)
            else:
                if rhs_val is None:
                    return False
                return (lhs_prev < rhs_val) and (lhs >= rhs_val)
        if op == 'crosses_below':
            if lhs_prev is None:
                return False
            if rhs_ind:
                if rhs_prev is None or rhs_val is None:
                    return False
                return (lhs_prev > rhs_prev) and (lhs <= rhs_val)
            else:
                if rhs_val is None:
                    return False
                return (lhs_prev > rhs_val) and (lhs <= rhs_val)
    except Exception:
        return False

    # unknown operator
    return False


def evaluate_entry_logic(entry_all: Optional[List[Dict[str, Any]]], entry_any: Optional[List[Dict[str, Any]]], i: int, ts, o, h, l, c, feats) -> bool:
    """Evaluate entry logic composed of ALL (AND) and ANY (OR) lists of conditions."""
    # ALL must be true (if present)
    if entry_all:
        for cond in entry_all:
            if not evaluate_condition(cond, i, ts, o, h, l, c, feats):
                return False
    # ANY if present: at least one must be true
    if entry_any and len(entry_any) > 0:
        any_ok = False
        for cond in entry_any:
            if evaluate_condition(cond, i, ts, o, h, l, c, feats):
                any_ok = True
                break
        if not any_ok:
            return False
    return True


def should_enter(i, ts, o, h, l, c, feats, params, allow_shorts=True):
    """
    Entry decision. Supports three modes (priority order):
    1) SIMPLE_RSI_TEST debug mode (env or risk.force_simple_rsi)
    2) If `params` contains declarative entry logic (long/short or entry_all/entry_any), evaluate it
    3) Fallback to original Donchian+RSI logic
    """
    # 1) Simple RSI debug mode
    try:
        force_simple = bool(params.get('force_simple_rsi', False))
    except Exception:
        force_simple = False
    force_simple = force_simple or (os.environ.get('SIMPLE_RSI_TEST') == '1')

    if force_simple:
        thresh = float(params.get('rsi_test_threshold', 20.0))
        rsi_curr = None
        rsi_prev = None
        if isinstance(feats, dict) and 'rsi14' in feats:
            try:
                rsi_curr = feats['rsi14'][i]
                rsi_prev = feats['rsi14'][i - 1] if i > 0 else None
            except Exception:
                rsi_curr = None
                rsi_prev = None
        if rsi_prev is not None and rsi_curr is not None:
            if rsi_prev < thresh and rsi_curr >= thresh:
                return 'LONG'
        return None

    # 2) Declarative entry logic in params
    # Accept either: params['entry'] = { 'long': {entry_all, entry_any}, 'short': {...} }
    entry_cfg = None
    try:
        entry_cfg = params.get('entry') if isinstance(params, dict) else None
    except Exception:
        entry_cfg = None

    if entry_cfg and isinstance(entry_cfg, dict):
        # LONG
        long_cfg = entry_cfg.get('long', {})
        long_all = long_cfg.get('entry_all') or long_cfg.get('all') or []
        long_any = long_cfg.get('entry_any') or long_cfg.get('any') or []
        long_ok = evaluate_entry_logic(long_all, long_any, i, ts, o, h, l, c, feats)
        if long_ok:
            return 'LONG'
        # SHORT
        short_cfg = entry_cfg.get('short', {})
        short_all = short_cfg.get('entry_all') or short_cfg.get('all') or []
        short_any = short_cfg.get('entry_any') or short_cfg.get('any') or []
        short_ok = evaluate_entry_logic(short_all, short_any, i, ts, o, h, l, c, feats)
        if short_ok and allow_shorts:
            return 'SHORT'

    # 3) Fallback to legacy Donchian + RSI
    try:
        dn55, up55 = feats['dn55'][i], feats['up55'][i]
        rsi14 = feats['rsi14'][i]
        regime = feats['regime'][i]
        long_sig = c[i] > up55 and rsi14 > params.get('rsi_buy', 30) and (regime != 'DOWNTREND')
        short_sig = allow_shorts and (c[i] < dn55 and rsi14 < params.get('rsi_sell', 70) and (regime != 'UPTREND'))
        if long_sig:
            return 'LONG'
        if short_sig:
            return 'SHORT'
    except Exception:
        pass

    return None