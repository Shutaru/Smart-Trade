"""
Strategy Registry Master - All 38 Strategies

Central registry for all implemented trading strategies.
Provides unified access to:
- 5 Trend Following strategies
- 5 Mean Reversion strategies
- 5 Breakout strategies
- 5 Volume strategies
- 5 Hybrid strategies
- 5 Advanced strategies
- 5 Refinement strategies
- 3 Final strategies

Total: 38 professional trading strategies

Usage:
    from strategies.registry import ALL_STRATEGIES, get_strategy, list_all_strategies
    
    # Get specific strategy
    strategy_fn = get_strategy("trendflow_supertrend")
    signal = strategy_fn(bar, indicators, state, params)
    
    # List all strategies
    all_names = list_all_strategies()
    
    # Get strategies by category
    trend_strats = get_strategies_by_category("trend")
    
    # Get strategies by regime
    range_strats = get_strategies_by_regime("range")
    
    # Get metadata
    info = get_strategy_info("trendflow_supertrend")
    print(info["description"])
"""

from typing import Dict, Callable, Optional, List, Any
import logging

# Import all strategy modules
from strategies.trend_following import TREND_FOLLOWING_STRATEGIES
from strategies.mean_reversion import MEAN_REVERSION_STRATEGIES
from strategies.breakout import BREAKOUT_STRATEGIES
from strategies.volume import VOLUME_STRATEGIES
from strategies.hybrid import HYBRID_STRATEGIES
from strategies.advanced import ADVANCED_STRATEGIES
from strategies.refinements import REFINEMENT_STRATEGIES
from strategies.final import FINAL_STRATEGIES

logger = logging.getLogger(__name__)


# ============================================================================
# MASTER REGISTRY - ALL 38 STRATEGIES
# ============================================================================

ALL_STRATEGIES: Dict[str, Callable] = {
    # Trend Following (1-5)
    **TREND_FOLLOWING_STRATEGIES,
    
    # Mean Reversion (6-10)
    **MEAN_REVERSION_STRATEGIES,
    
    # Breakout (11-15)
    **BREAKOUT_STRATEGIES,
    
    # Volume (16-20)
    **VOLUME_STRATEGIES,
    
    # Hybrid (21-25)
    **HYBRID_STRATEGIES,
    
    # Advanced (26-30)
    **ADVANCED_STRATEGIES,
    
    # Refinements (31-35)
    **REFINEMENT_STRATEGIES,
    
    # Final (36-38)
    **FINAL_STRATEGIES,
}


# ============================================================================
# COMPREHENSIVE STRATEGY METADATA
# ============================================================================

STRATEGY_METADATA = {
    # TREND FOLLOWING (1-5)
    "trendflow_supertrend": {
        "id": 1,
        "name": "TrendFlow SuperTrend",
        "category": "trend",
        "description": "SuperTrend + ADX momentum with pullback entries. Waits for pullback to EMA20/50 in strong trends.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "chandelier",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:2",
        "win_rate_range": "45-55%",
        "indicators": ["supertrend", "adx14", "ema20", "ema50", "ema200", "rsi14", "prev_high", "prev_low"],
        "params": {
            "adx_min": 22,
            "rsi_pullback_low": 40,
            "rsi_pullback_high": 55,
        }
    },
    "ema_cloud_trend": {
        "id": 2,
        "name": "EMA Cloud Trend",
        "category": "trend",
        "description": "Pullback to EMA20/50 cloud in trending markets. Enters when price touches cloud and resumes.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "6-18 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.5",
        "win_rate_range": "50-60%",
        "indicators": ["ema20", "ema50", "ema200", "rsi14", "prev_high"],
        "params": {
            "rsi_pullback_low": 40,
            "rsi_pullback_high": 55,
        }
    },
    "donchian_continuation": {
        "id": 3,
        "name": "Donchian Continuation",
        "category": "trend",
        "description": "Donchian breakout with ADX momentum confirmation. Simple and effective trend following.",
        "regime": "trend",
        "complexity": "low",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "4-8 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:2",
        "win_rate_range": "40-50%",
        "indicators": ["donchian_high20", "donchian_low20", "adx14", "adx14_5bars_ago", "ema200", "supertrend"],
        "params": {
            "adx_min": 18,
        }
    },
    "macd_zero_trend": {
        "id": 4,
        "name": "MACD Zero Line Trend",
        "category": "trend",
        "description": "MACD histogram above/below zero with breakout confirmation. Captures strong momentum.",
        "regime": "trend",
        "complexity": "low",
        "exit_style": "supertrend",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["15m", "1h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "45-52%",
        "indicators": ["macd_hist", "rsi14", "prev_high", "prev_low", "ema200", "supertrend", "adx14"],
        "params": {
            "rsi_max": 70,
            "adx_min": 18,
        }
    },
    "adx_trend_filter_plus": {
        "id": 5,
        "name": "ADX Trend Filter Plus",
        "category": "trend",
        "description": "Strong ADX trend filter with RSI timing. Only trades in confirmed strong trends.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.4",
        "win_rate_range": "48-58%",
        "indicators": ["adx14", "ema200", "rsi14", "ema20"],
        "params": {
            "adx_min": 25,
            "rsi_pullback_low": 42,
            "rsi_pullback_high": 55,
        }
    },
    
    # MEAN REVERSION (6-10)
    "rsi_band_reversion": {
        "id": 6,
        "name": "RSI Band Reversion",
        "category": "mean_reversion",
        "description": "RSI oversold/overbought with Bollinger Band extremes. Mean reversion at extremes.",
        "regime": "range",
        "complexity": "medium",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "2-6 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:1.8",
        "win_rate_range": "55-65%",
        "indicators": ["rsi14", "bb_lower", "bb_upper", "ema50", "prev_high", "prev_low"],
        "params": {
            "rsi_oversold": 35,
            "rsi_overbought": 65,
        }
    },
    "stoch_signal_reversal": {
        "id": 7,
        "name": "Stochastic Signal Reversal",
        "category": "mean_reversion",
        "description": "Stochastic crossover in oversold/overbought zones. Fast reversal detection.",
        "regime": "range",
        "complexity": "low",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "1-4 hours",
        "best_timeframes": ["5m", "15m"],
        "risk_reward": "1:1.6",
        "win_rate_range": "58-68%",
        "indicators": ["stoch_k", "stoch_d", "stoch_k_prev", "stoch_d_prev", "ema50", "rsi14"],
        "params": {
            "stoch_oversold": 25,
            "stoch_overbought": 75,
        }
    },
    "bollinger_mean_reversion": {
        "id": 8,
        "name": "Bollinger Mean Reversion",
        "category": "mean_reversion",
        "description": "Price outside BB then closes back inside. Classic mean reversion.",
        "regime": "range",
        "complexity": "low",
        "exit_style": "keltner",
        "avg_trade_duration": "2-5 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:1.7",
        "win_rate_range": "60-70%",
        "indicators": ["bb_lower", "bb_upper", "bb_middle", "close_prev", "rsi14"],
        "params": {
            "rsi_oversold": 45,
            "rsi_overbought": 55,
        }
    },
    "cci_extreme_snapback": {
        "id": 9,
        "name": "CCI Extreme Snapback",
        "category": "mean_reversion",
        "description": "CCI extreme (<-100, >+100) then snapback. Captures extreme reversions.",
        "regime": "range",
        "complexity": "medium",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "2-6 hours",
        "best_timeframes": ["15m", "1h"],
        "risk_reward": "1:1.8",
        "win_rate_range": "56-64%",
        "indicators": ["cci", "cci_prev", "ema20", "ema50"],
        "params": {
            "cci_extreme_low": -100,
            "cci_extreme_high": 100,
        }
    },
    "mfi_divergence_reversion": {
        "id": 10,
        "name": "MFI Divergence Reversion",
        "category": "mean_reversion",
        "description": "MFI divergence detection with price confirmation. Volume-based reversal.",
        "regime": "range",
        "complexity": "high",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2",
        "win_rate_range": "52-62%",
        "indicators": ["mfi", "mfi_prev", "ema20", "close_prev", "low_prev", "high_prev"],
        "params": {
            "mfi_oversold": 40,
            "mfi_overbought": 60,
        }
    },
    
    # BREAKOUT (11-15)
    "bollinger_squeeze_breakout": {
        "id": 11,
        "name": "Bollinger Squeeze Breakout",
        "category": "breakout",
        "description": "BB squeeze detection then expansion breakout. Captures volatility explosions.",
        "regime": "low_vol",
        "complexity": "medium",
        "exit_style": "chandelier",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "45-55%",
        "indicators": ["bb_bw_pct", "boll_in_keltner", "bb_upper", "bb_lower", "adx14", "adx14_prev"],
        "params": {
            "squeeze_threshold": 35,
        }
    },
    "keltner_expansion": {
        "id": 12,
        "name": "Keltner Expansion",
        "category": "breakout",
        "description": "Keltner channel breakout with ADX rising. Simple volatility expansion.",
        "regime": "range",
        "complexity": "low",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:2",
        "win_rate_range": "42-52%",
        "indicators": ["keltner_upper", "keltner_lower", "adx14", "adx14_5bars_ago", "rsi14"],
        "params": {
            "rsi_max": 70,
        }
    },
    "atr_expansion_breakout": {
        "id": 13,
        "name": "ATR Expansion Breakout",
        "category": "breakout",
        "description": "ATR percentile expansion with breakout. Volatility filter for quality breakouts.",
        "regime": "high_vol",
        "complexity": "medium",
        "exit_style": "supertrend",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h"],
        "risk_reward": "1:2.4",
        "win_rate_range": "44-54%",
        "indicators": ["atr_norm_pct", "prev_high", "prev_low", "ema200", "supertrend_bull", "supertrend_bear", "adx14"],
        "params": {
            "atr_threshold": 70,
            "adx_min": 18,
        }
    },
    "donchian_volatility_breakout": {
        "id": 14,
        "name": "Donchian Volatility Breakout",
        "category": "breakout",
        "description": "Donchian breakout post-squeeze or ADX rising. Momentum confirmation.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.5",
        "win_rate_range": "46-56%",
        "indicators": ["donchian_high20", "donchian_low20", "bb_bw_pct", "bb_bw_pct_prev", "adx14", "adx14_5bars_ago"],
        "params": {
            "squeeze_threshold": 35,
        }
    },
    "channel_squeeze_plus": {
        "id": 15,
        "name": "Channel Squeeze Plus",
        "category": "breakout",
        "description": "BB inside Keltner squeeze then breakout. Multi-indicator squeeze detection.",
        "regime": "low_vol",
        "complexity": "medium",
        "exit_style": "chandelier",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "45-55%",
        "indicators": ["boll_in_keltner", "adx14", "adx14_prev", "keltner_upper", "keltner_lower"],
        "params": {}
    },
    
    # VOLUME (16-20)
    "vwap_institutional_trend": {
        "id": 16,
        "name": "VWAP Institutional Trend",
        "category": "volume",
        "description": "VWAP + MFI + ADX institutional trend following. Follows smart money.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "6-15 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "50-60%",
        "indicators": ["vwap", "ema200", "ema20", "mfi", "adx14", "prev_high", "prev_low"],
        "params": {
            "mfi_min": 50,
            "adx_min": 20,
        }
    },
    "vwap_breakout": {
        "id": 17,
        "name": "VWAP Breakout",
        "category": "volume",
        "description": "Consolidation near VWAP then breakout. Institutional level breakout.",
        "regime": "range",
        "complexity": "medium",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:2",
        "win_rate_range": "48-58%",
        "indicators": ["vwap", "prev_high", "prev_low"],
        "params": {
            "consolidation_bars": 3,
        }
    },
    "mfi_impulse_momentum": {
        "id": 18,
        "name": "MFI Impulse Momentum",
        "category": "volume",
        "description": "MFI crosses 50 with MACD confirmation. Volume momentum surge detection.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["15m", "1h"],
        "risk_reward": "1:2",
        "win_rate_range": "48-56%",
        "indicators": ["mfi", "mfi_prev", "macd_hist", "ema50"],
        "params": {}
    },
    "obv_trend_confirmation": {
        "id": 19,
        "name": "OBV Trend Confirmation",
        "category": "volume",
        "description": "OBV higher highs/lows with trend filters. Volume confirms price trend.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "supertrend",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "46-54%",
        "indicators": ["obv", "obv_prev", "obv_5bars_ago", "ema200", "supertrend_bull", "supertrend_bear", "adx14"],
        "params": {
            "adx_min": 18,
        }
    },
    "vwap_mean_reversion": {
        "id": 20,
        "name": "VWAP Mean Reversion",
        "category": "volume",
        "description": "Standard deviation bands from VWAP. Mean reversion around institutional level.",
        "regime": "range",
        "complexity": "medium",
        "exit_style": "keltner",
        "avg_trade_duration": "2-6 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:1.6",
        "win_rate_range": "58-68%",
        "indicators": ["vwap", "vwap_std", "rsi14", "prev_high", "prev_low"],
        "params": {
            "sigma_threshold": 1.5,
        }
    },
    
    # HYBRID (21-25)
    "triple_momentum_confluence": {
        "id": 21,
        "name": "Triple Momentum Confluence",
        "category": "hybrid",
        "description": "RSI + Stoch + MACD all aligned. Triple confirmation for momentum.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "chandelier",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "50-60%",
        "indicators": ["rsi14", "stoch_k", "stoch_d", "macd_hist", "ema50"],
        "params": {
            "rsi_min": 55,
            "stoch_range_low": 40,
            "stoch_range_high": 80,
        }
    },
    "trend_volume_combo": {
        "id": 22,
        "name": "Trend Volume Combo",
        "category": "hybrid",
        "description": "SuperTrend + VWAP + MFI + ADX. Complete trend + volume system.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "5-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.1",
        "win_rate_range": "52-62%",
        "indicators": ["supertrend_bull", "supertrend_bear", "vwap", "mfi", "adx14"],
        "params": {
            "mfi_min": 50,
            "adx_min": 20,
        }
    },
    "ema_stack_momentum": {
        "id": 23,
        "name": "EMA Stack Momentum",
        "category": "hybrid",
        "description": "EMA 20>50>200 with positive slopes. Classic trend stack confirmation.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "6-18 hours",
        "best_timeframes": ["1h", "4h"],
        "risk_reward": "1:2.4",
        "win_rate_range": "54-64%",
        "indicators": ["ema20", "ema50", "ema200", "ema20_prev", "ema50_prev", "prev_high", "prev_low"],
        "params": {}
    },
    "multi_oscillator_confluence": {
        "id": 24,
        "name": "Multi-Oscillator Confluence",
        "category": "hybrid",
        "description": "RSI + CCI + Stoch balanced zones. Multiple oscillator confirmation.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["15m", "1h"],
        "risk_reward": "1:2",
        "win_rate_range": "50-58%",
        "indicators": ["rsi14", "cci", "stoch_k", "stoch_d", "ema50"],
        "params": {
            "rsi_range_low": 50,
            "rsi_range_high": 60,
        }
    },
    "complete_system_5x": {
        "id": 25,
        "name": "Complete System 5x",
        "category": "hybrid",
        "description": "5-factor system with auto regime detection. Most comprehensive strategy.",
        "regime": "auto",
        "complexity": "high",
        "exit_style": "supertrend",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.3",
        "win_rate_range": "52-62%",
        "indicators": ["supertrend_bull", "supertrend_bear", "rsi14", "adx14", "vwap", "atr_norm_pct"],
        "params": {
            "rsi_range_low": 45,
            "rsi_range_high": 65,
            "adx_min": 20,
            "atr_min": 20,
            "atr_max": 80,
        }
    },
    
    # ADVANCED (26-30)
    "london_breakout_atr": {
        "id": 26,
        "name": "London Breakout ATR",
        "category": "advanced",
        "description": "London ORB with ATR filter. Session-based breakout trading.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "2-6 hours",
        "best_timeframes": ["5m", "15m"],
        "risk_reward": "1:2.2",
        "win_rate_range": "46-56%",
        "indicators": ["is_london_session", "or_high", "or_low", "atr_norm_pct"],
        "params": {
            "atr_threshold": 50,
        }
    },
    "ny_session_fade": {
        "id": 27,
        "name": "NY Session Fade",
        "category": "advanced",
        "description": "NY session spike fade (mean reversion). Fades opening range extremes.",
        "regime": "range",
        "complexity": "high",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "1-4 hours",
        "best_timeframes": ["5m", "15m"],
        "risk_reward": "1:1.8",
        "win_rate_range": "56-66%",
        "indicators": ["is_ny_session", "minutes_since_ny_open", "keltner_lower", "keltner_upper", "bb_lower", "bb_upper", "rsi14", "prev_high", "prev_low"],
        "params": {
            "max_minutes": 120,
        }
    },
    "regime_adaptive_core": {
        "id": 28,
        "name": "Regime Adaptive Core",
        "category": "advanced",
        "description": "Auto strategy selection (trend/squeeze/range). Adapts to market conditions.",
        "regime": "auto",
        "complexity": "very_high",
        "exit_style": "dynamic",
        "avg_trade_duration": "varies",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "varies",
        "win_rate_range": "50-62%",
        "indicators": ["adx14", "bb_bw_pct", "ema20", "ema50", "ema200", "rsi14", "keltner_upper", "keltner_lower", "donchian_high20", "donchian_low20", "bb_lower", "bb_upper", "vwap"],
        "params": {
            "adx_trend_threshold": 22,
            "adx_range_threshold": 18,
            "squeeze_threshold": 35,
        }
    },
    "pure_price_action_donchian": {
        "id": 29,
        "name": "Pure Price Action Donchian",
        "category": "advanced",
        "description": "Donchian with structure preservation. Clean price action breakout.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.3",
        "win_rate_range": "48-58%",
        "indicators": ["ema200", "donchian_high20", "donchian_low20"],
        "params": {}
    },
    "order_flow_momentum_vwap": {
        "id": 30,
        "name": "Order Flow Momentum VWAP",
        "category": "advanced",
        "description": "VWAP + MFI delta + ADX rising. Institutional order flow detection.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "supertrend",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "50-60%",
        "indicators": ["vwap", "mfi", "mfi_prev", "mfi_5bars_ago", "adx14", "adx14_prev", "prev_high", "prev_low"],
        "params": {
            "mfi_delta_threshold": 5,
        }
    },
    
    # REFINEMENTS (31-35)
    "rsi_supertrend_flip": {
        "id": 31,
        "name": "RSI SuperTrend Flip",
        "category": "refinement",
        "description": "SuperTrend direction change + RSI 50 cross. Early trend reversal detection.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "chandelier",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2",
        "win_rate_range": "48-58%",
        "indicators": ["supertrend_bull", "supertrend_bear", "supertrend_bull_prev", "supertrend_bear_prev", "rsi14", "rsi14_prev", "ema50"],
        "params": {}
    },
    "keltner_pullback_continuation": {
        "id": 32,
        "name": "Keltner Pullback Continuation",
        "category": "refinement",
        "description": "Pullback to Keltner midline then resume. Clean trend continuation.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.1",
        "win_rate_range": "52-62%",
        "indicators": ["keltner_mid", "keltner_upper", "keltner_lower", "ema20", "ema50", "ema200"],
        "params": {}
    },
    "ema200_tap_reversion": {
        "id": 33,
        "name": "EMA200 Tap Reversion",
        "category": "refinement",
        "description": "Light touch of EMA200 then bounce. Dynamic support/resistance tap.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "breakeven_then_trail",
        "avg_trade_duration": "3-8 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:1.9",
        "win_rate_range": "54-64%",
        "indicators": ["ema200", "rsi14", "prev_high", "prev_low"],
        "params": {
            "rsi_oversold": 35,
            "rsi_overbought": 50,
        }
    },
    "double_donchian_pullback": {
        "id": 34,
        "name": "Double Donchian Pullback",
        "category": "refinement",
        "description": "Multi-timeframe Donchian (20 + 10 period). Structure preservation.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "atr_fixed",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.4",
        "win_rate_range": "50-60%",
        "indicators": ["donchian_high20", "donchian_low20", "donchian_high10", "donchian_low10", "prev_high", "prev_low"],
        "params": {}
    },
    "volatility_weighted_breakout": {
        "id": 35,
        "name": "Volatility Weighted Breakout",
        "category": "refinement",
        "description": "Breakout only in ATR 40-80 percentile. Filtered volatility breakouts.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "supertrend",
        "avg_trade_duration": "4-10 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.3",
        "win_rate_range": "48-58%",
        "indicators": ["atr_norm_pct", "adx14", "adx14_prev", "donchian_high20", "donchian_low20", "keltner_upper", "keltner_lower"],
        "params": {
            "atr_min": 40,
            "atr_max": 80,
        }
    },
    
    # FINAL (36-38)
    "vwap_band_fade_pro": {
        "id": 36,
        "name": "VWAP Band Fade PRO",
        "category": "final",
        "description": "Advanced VWAP mean reversion with ADX blocking. Professional mean reversion.",
        "regime": "range",
        "complexity": "high",
        "exit_style": "keltner",
        "avg_trade_duration": "2-6 hours",
        "best_timeframes": ["5m", "15m", "1h"],
        "risk_reward": "1:1.6",
        "win_rate_range": "60-70%",
        "indicators": ["vwap", "vwap_std", "bb_lower", "bb_upper", "mfi", "adx14", "prev_high", "prev_low"],
        "params": {
            "sigma_threshold": 1.5,
            "adx_block_threshold": 25,
            "mfi_min": 40,
            "mfi_max": 60,
        }
    },
    "obv_confirmation_breakout_plus": {
        "id": 37,
        "name": "OBV Confirmation Breakout PLUS",
        "category": "final",
        "description": "OBV trend + Keltner breakout + ADX. Complete volume breakout system.",
        "regime": "trend",
        "complexity": "high",
        "exit_style": "chandelier",
        "avg_trade_duration": "4-12 hours",
        "best_timeframes": ["15m", "1h", "4h"],
        "risk_reward": "1:2.2",
        "win_rate_range": "50-60%",
        "indicators": ["obv", "obv_prev", "obv_5bars_ago", "keltner_upper", "keltner_lower", "adx14", "adx14_prev"],
        "params": {
            "obv_lookback_bars": 10,
        }
    },
    "ema_stack_regime_flip": {
        "id": 38,
        "name": "EMA Stack Regime Flip",
        "category": "final",
        "description": "Golden/Death cross detection. Classic institutional reversal signal.",
        "regime": "trend",
        "complexity": "medium",
        "exit_style": "atr_trailing",
        "avg_trade_duration": "6-24 hours",
        "best_timeframes": ["1h", "4h", "1d"],
        "risk_reward": "1:2.2",
        "win_rate_range": "48-58%",
        "indicators": ["ema20", "ema50", "ema200", "ema20_prev", "ema50_prev", "rsi14", "prev_high", "prev_low"],
        "params": {}
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_strategy(name: str) -> Optional[Callable]:
    """Get strategy function by name"""
    return ALL_STRATEGIES.get(name)


def list_all_strategies() -> List[str]:
    """Get list of all strategy names"""
    return sorted(ALL_STRATEGIES.keys())


def get_strategies_by_category(category: str) -> Dict[str, Callable]:
    """Get all strategies in a specific category"""
    return {
        name: func
        for name, func in ALL_STRATEGIES.items()
        if STRATEGY_METADATA.get(name, {}).get("category") == category
    }


def get_strategies_by_regime(regime: str) -> Dict[str, Callable]:
    """Get all strategies suitable for a specific regime"""
    return {
        name: func
        for name, func in ALL_STRATEGIES.items()
        if STRATEGY_METADATA.get(name, {}).get("regime") == regime
    }


def get_strategies_by_complexity(complexity: str) -> Dict[str, Callable]:
    """Get strategies by complexity level (low, medium, high, very_high)"""
    return {
        name: func
        for name, func in ALL_STRATEGIES.items()
        if STRATEGY_METADATA.get(name, {}).get("complexity") == complexity
    }


def get_strategies_by_exit_style(exit_style: str) -> Dict[str, Callable]:
    """Get strategies by exit style"""
    return {
        name: func
        for name, func in ALL_STRATEGIES.items()
        if STRATEGY_METADATA.get(name, {}).get("exit_style") == exit_style
    }


def get_strategy_info(name: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific strategy"""
    return STRATEGY_METADATA.get(name)


def get_all_metadata() -> Dict[str, Dict[str, Any]]:
    """Get metadata for all strategies"""
    return STRATEGY_METADATA.copy()


def validate_strategy_exists(name: str) -> bool:
    """Check if strategy exists"""
    return name in ALL_STRATEGIES


def get_strategies_summary() -> Dict[str, int]:
    """Get summary counts by category"""
    summary = {}
    for meta in STRATEGY_METADATA.values():
        cat = meta.get("category", "unknown")
        summary[cat] = summary.get(cat, 0) + 1
    return summary


def get_strategies_by_timeframe(timeframe: str) -> List[str]:
    """Get strategies suitable for a specific timeframe"""
    matching = []
    for name, meta in STRATEGY_METADATA.items():
        if timeframe in meta.get("best_timeframes", []):
            matching.append(name)
    return sorted(matching)


def search_strategies(keyword: str) -> List[str]:
    """Search strategies by keyword in name or description"""
    keyword_lower = keyword.lower()
    matches = []
    
    for name, meta in STRATEGY_METADATA.items():
        if (keyword_lower in name.lower() or
            keyword_lower in meta.get("name", "").lower() or
            keyword_lower in meta.get("description", "").lower()):
            matches.append(name)
    
    return sorted(matches)


# ============================================================================
# STRATEGY PRESETS (for UI/Config)
# ============================================================================

STRATEGY_PRESETS = {
    "conservative_trend": {
        "name": "Conservative Trend Following",
        "strategies": ["ema_cloud_trend", "adx_trend_filter_plus", "keltner_pullback_continuation"],
        "description": "Low-risk trend following with strong filters"
    },
    "aggressive_breakout": {
        "name": "Aggressive Breakout",
        "strategies": ["bollinger_squeeze_breakout", "atr_expansion_breakout", "donchian_volatility_breakout"],
        "description": "High-volatility breakout strategies"
    },
    "mean_reversion_range": {
        "name": "Mean Reversion Range",
        "strategies": ["rsi_band_reversion", "bollinger_mean_reversion", "vwap_mean_reversion"],
        "description": "Fade extremes in ranging markets"
    },
    "volume_based": {
        "name": "Volume-Based",
        "strategies": ["vwap_institutional_trend", "obv_trend_confirmation", "mfi_impulse_momentum"],
        "description": "Follow institutional money flow"
    },
    "institutional": {
        "name": "Institutional Grade",
        "strategies": ["vwap_institutional_trend", "order_flow_momentum_vwap", "ema_stack_regime_flip"],
        "description": "Professional institutional strategies"
    },
    "auto_adaptive": {
        "name": "Auto-Adaptive",
        "strategies": ["regime_adaptive_core", "complete_system_5x", "volatility_weighted_breakout"],
        "description": "Self-adapting to market conditions"
    },
    "scalping_5m": {
        "name": "Scalping (5min)",
        "strategies": ["stoch_signal_reversal", "vwap_breakout", "ny_session_fade"],
        "description": "Fast scalping strategies for 5min charts"
    },
    "swing_4h": {
        "name": "Swing Trading (4h)",
        "strategies": ["ema_cloud_trend", "complete_system_5x", "ema_stack_regime_flip"],
        "description": "Swing trading strategies for 4h charts"
    },
}


# ============================================================================
# VALIDATION
# ============================================================================

def validate_registry() -> tuple[bool, List[str]]:
    """Validate that registry is complete and consistent"""
    errors = []
    
    # Check count
    expected_count = 38
    actual_count = len(ALL_STRATEGIES)
    if actual_count != expected_count:
        errors.append(f"Expected {expected_count} strategies, found {actual_count}")
    
    # Check metadata completeness
    for name in ALL_STRATEGIES.keys():
        if name not in STRATEGY_METADATA:
            errors.append(f"Missing metadata for strategy: {name}")
        else:
            meta = STRATEGY_METADATA[name]
            required_fields = ["id", "name", "category", "description", "regime", "complexity"]
            for field in required_fields:
                if field not in meta:
                    errors.append(f"Strategy '{name}' missing required field: {field}")
    
    # Check for duplicate IDs
    ids = [m["id"] for m in STRATEGY_METADATA.values()]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate strategy IDs found in metadata")
    
    # Check ID sequence
    expected_ids = set(range(1, 39))
    actual_ids = set(ids)
    if expected_ids != actual_ids:
        missing = expected_ids - actual_ids
        extra = actual_ids - expected_ids
        if missing:
            errors.append(f"Missing strategy IDs: {missing}")
        if extra:
            errors.append(f"Extra strategy IDs: {extra}")
    
    # Check categories
    valid_categories = {"trend", "mean_reversion", "breakout", "volume", "hybrid", "advanced", "refinement", "final"}
    for name, meta in STRATEGY_METADATA.items():
        cat = meta.get("category")
        if cat not in valid_categories:
            errors.append(f"Strategy '{name}' has invalid category: {cat}")
    
    # Check regimes
    valid_regimes = {"trend", "range", "low_vol", "high_vol", "auto"}
    for name, meta in STRATEGY_METADATA.items():
        regime = meta.get("regime")
        if regime not in valid_regimes:
            errors.append(f"Strategy '{name}' has invalid regime: {regime}")
    
    return len(errors) == 0, errors


def print_registry_report():
    """Print comprehensive registry report"""
    print("=" * 80)
    print("STRATEGY REGISTRY REPORT")
    print("=" * 80)
    
    # Summary
    print(f"\n📊 Total Strategies: {len(ALL_STRATEGIES)}")
    
    # By category
    print("\n📋 By Category:")
    for cat, count in sorted(get_strategies_summary().items()):
        print(f"  - {cat:20s}: {count:2d} strategies")
    
    # By regime
    print("\n🌍 By Regime:")
    regime_counts = {}
    for meta in STRATEGY_METADATA.values():
        regime = meta.get("regime", "unknown")
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
    for regime, count in sorted(regime_counts.items()):
        print(f"  - {regime:15s}: {count:2d} strategies")
    
    # By complexity
    print("\n⚙️  By Complexity:")
    complexity_counts = {}
    for meta in STRATEGY_METADATA.values():
        complexity = meta.get("complexity", "unknown")
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
    for complexity, count in sorted(complexity_counts.items()):
        print(f"  - {complexity:15s}: {count:2d} strategies")
    
    # Validation
    print("\n✅ Validation:")
    is_valid, errors = validate_registry()
    if is_valid:
        print("  All checks passed!")
    else:
        print("  ❌ Errors found:")
        for error in errors:
            print(f"    - {error}")


if __name__ == "__main__":
    print_registry_report()