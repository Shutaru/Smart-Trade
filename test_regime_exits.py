"""
Test Regime-Adaptive Exit System

Simple example showing how the system works
"""

import sys
sys.path.append('.')

from backend.agents.exits import (
    build_exit_plan,
    update_trailing_stop,
    check_exits,
    RegimeDetector,
    get_swing_levels,
    build_context
)


def test_exit_plan():
    """Test basic exit plan creation"""
    
    print("\n" + "="*80)
    print("REGIME-ADAPTIVE EXIT SYSTEM - TEST")
    print("="*80)
    
    # Simulate BTC/USDT entry
    entry = 50000.0
    atr = 500.0  # $500 ATR
    
    # Test params
    params = {
        "sl_tp_style": "keltner",
        "sl_atr_mult": 2.2,
        "trail_atr_mult": 2.0,
        "breakeven_at_R": 1.0,
        "tp_rr_multiple": 2.0,
        "targets": [
            {"rr": 1.0, "pct": 0.35},
            {"rr": 2.0, "pct": 0.35},
            {"rr": 3.0, "pct": 0.30}
        ],
        "time_stop_bars": 96
    }
    
    # Test context
    ctx = {
        "tick_size": 0.1,
        "swing_low": 49500.0,
        "swing_high": 52000.0,
        "keltner_lo": 49700.0,
        "keltner_up": 50300.0
    }
    
    # === Test 1: LONG in TREND regime ===
    print("\n" + "-"*80)
    print("TEST 1: LONG Entry in TREND Regime")
    print("-"*80)
    
    plan = build_exit_plan(
        side="LONG",
        entry=entry,
        atr=atr,
        params=params,
        ctx=ctx,
        regime_hint="trend"
    )
    
    print(f"\n📊 Exit Plan:")
    print(f"  Entry: ${plan.entry:,.2f}")
    print(f"  SL: ${plan.sl:,.2f} (R = ${plan.R:,.2f})")
    print(f"  Primary TP: ${plan.tp_primary:,.2f}")
    print(f"  Trailing: {plan.trailing.mode} (breakeven @ {plan.trailing.breakeven_at_R}R)")
    print(f"  Time Stop: {plan.time_stop_bars} bars")
    
    print(f"\n🎯 Targets:")
    for i, target in enumerate(plan.targets, 1):
        print(f"  Target {i}: ${target.price:,.2f} ({target.rr:.1f}R) - Close {target.pct*100:.0f}%")
    
    # === Test 2: Simulate price movement ===
    print("\n" + "-"*80)
    print("TEST 2: Simulating Price Movement")
    print("-"*80)
    
    bars = [
        {"close": 50200, "high": 50250, "low": 50100, "highest": 50250, "lowest": 50100},
        {"close": 50500, "high": 50600, "low": 50400, "highest": 50600, "lowest": 50100},
        {"close": 51100, "high": 51200, "low": 50900, "highest": 51200, "lowest": 50100},  # Should hit Target 1
        {"close": 51800, "high": 51900, "low": 51600, "highest": 51900, "lowest": 50100},
        {"close": 52200, "high": 52300, "low": 52000, "highest": 52300, "lowest": 50100},  # Should hit Target 2
    ]
    
    for i, bar in enumerate(bars):
        plan.bars_in_trade = i + 1
        
        # Update context
        ctx_bar = {
            "tick_size": 0.1,
            "keltner_lo": bar["low"] - 300,  # Simulated
            "keltner_up": bar["high"] + 300,
            "close": bar["close"],
            "high": bar["high"],
            "low": bar["low"],
            "highest_since_entry": bar["highest"],
            "lowest_since_entry": bar["lowest"]
        }
        
        # Update trailing
        update_trailing_stop(
            plan,
            {
                "close": bar["close"],
                "high": bar["high"],
                "low": bar["low"],
                "highest_since_entry": bar["highest"],
                "lowest_since_entry": bar["lowest"]
            },
            ctx_bar,
            atr=500
        )
        
        # Check exits
        exit_result = check_exits(plan, bar["close"], bar["high"], bar["low"])
        
        print(f"\nBar {i+1}: ${bar['close']:,.0f}")
        print(f"  SL: ${plan.sl:,.2f} | Breakeven: {plan.breakeven_done}")
        
        if exit_result:
            reason, price, partial_pct = exit_result
            if partial_pct:
                print(f"  🎯 EXIT: {reason} @ ${price:,.2f} - Close {partial_pct*100:.0f}%")
            else:
                print(f"  🎯 EXIT: {reason} @ ${price:,.2f} - Close 100%")
    
    # === Test 3: RANGE regime ===
    print("\n" + "-"*80)
    print("TEST 3: SHORT Entry in RANGE Regime")
    print("-"*80)
    
    plan_range = build_exit_plan(
        side="SHORT",
        entry=entry,
        atr=atr,
        params=params,
        ctx=ctx,
        regime_hint="range"
    )
    
    print(f"\n📊 Exit Plan (RANGE):")
    print(f"  Entry: ${plan_range.entry:,.2f}")
    print(f"  SL: ${plan_range.sl:,.2f} (R = ${plan_range.R:,.2f})")
    print(f"  Primary TP: ${plan_range.tp_primary:,.2f}")
    
    print(f"\n🎯 Targets (Tighter for RANGE):")
    for i, target in enumerate(plan_range.targets, 1):
        print(f"  Target {i}: ${target.price:,.2f} ({target.rr:.1f}R) - Close {target.pct*100:.0f}%")
    
    # === Test 4: Regime Detection ===
    print("\n" + "-"*80)
    print("TEST 4: Regime Detection")
    print("-"*80)
    
    detector = RegimeDetector()
    
    # Simulate ADX/ATR history
    adx_trend = [25, 26, 27, 28, 30]
    adx_range = [15, 16, 14, 15, 18]
    atr_history = [400, 420, 450, 480, 500, 520, 550, 580, 600, 620]
    
    regime_trend = detector.detect_simple(
        adx_current=30.0,
        atr_current=500.0,
        atr_history=atr_history,
        close_current=50000.0,
        ema200_current=48000.0
    )
    
    regime_range = detector.detect_simple(
        adx_current=15.0,
        atr_current=500.0,
        atr_history=atr_history,
        close_current=50000.0,
        ema200_current=49900.0
    )
    
    print(f"\nADX=30, Price 4% above EMA200: {regime_trend.upper()}")
    print(f"ADX=15, Price near EMA200: {regime_range.upper()}")
    
    print("\n" + "="*80)
    print("✅ TESTS COMPLETE")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_exit_plan()