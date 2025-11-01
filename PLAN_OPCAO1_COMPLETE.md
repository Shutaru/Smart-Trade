# ?? PLANO COMPLETO: OPÇÃO 1 - INDICADORES PARAMETRIZÁVEIS

## ?? FASE 1: ANÁLISE ?

### **INDICADORES ÚNICOS USADOS NAS 38 ESTRATÉGIAS:**

#### **TREND INDICATORS:**
- `ema20`, `ema50`, `ema200`, `ema20_prev`, `ema50_prev`
- `sma` (implícito)
- `macd_hist` (MACD histogram)
- `supertrend`, `supertrend_bull`, `supertrend_bear`, `supertrend_bull_prev`, `supertrend_bear_prev`
- `adx14`, `adx14_prev`, `adx14_5bars_ago`
- `donchian_high20`, `donchian_low20`, `donchian_high10`, `donchian_low10`

#### **MOMENTUM INDICATORS:**
- `rsi14`, `rsi14_prev`
- `stoch_k`, `stoch_d`, `stoch_k_prev`, `stoch_d_prev`
- `cci`, `cci_prev`
- `mfi`, `mfi_prev`, `mfi_5bars_ago`

#### **VOLATILITY INDICATORS:**
- `atr_norm_pct` (ATR percentile)
- `bb_upper`, `bb_lower`, `bb_middle` (Bollinger Bands)
- `bb_bw_pct`, `bb_bw_pct_prev` (Bollinger Bandwidth %)
- `boll_in_keltner` (BB inside Keltner squeeze)
- `keltner_upper`, `keltner_lower`, `keltner_mid`

#### **VOLUME INDICATORS:**
- `vwap`
- `vwap_std` (VWAP standard deviation bands)
- `obv`, `obv_prev`, `obv_5bars_ago`

#### **PRICE ACTION:**
- `prev_high`, `prev_low`, `high_prev`, `low_prev`, `close_prev`

#### **SESSION/TIME:**
- `is_london_session`, `is_ny_session`
- `or_high`, `or_low` (Opening Range)
- `minutes_since_ny_open`

---

## ?? FASE 2: IMPLEMENTAÇÃO

### **STEP 1: Criar `core/indicators_dynamic.py`**

Funções para calcular TODOS os indicadores com parâmetros customizáveis:

```python
def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series
def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> tuple
def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series
def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple
def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series
def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series
def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple
def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> tuple
def calculate_donchian(df: pd.DataFrame, period: int = 20) -> tuple
def calculate_keltner(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> tuple
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series
def calculate_obv(df: pd.DataFrame) -> pd.Series
def calculate_vwap(df: pd.DataFrame) -> pd.Series
```

### **STEP 2: Criar Cache System**

```python
class IndicatorCache:
    def __init__(self):
        self._cache = {}
    
 def get(self, key: str, df_hash: str):
        cache_key = f"{key}_{df_hash}"
        return self._cache.get(cache_key)
    
    def set(self, key: str, df_hash: str, value):
        cache_key = f"{key}_{df_hash}"
        self._cache[cache_key] = value
```

### **STEP 3: Modificar `optimization/backtest_engine.py`**

Adicionar função `calculate_indicators_with_params(df, params)` que:
1. Lê parâmetros do config `risk` dict
2. Calcula indicadores dinamicamente
3. Usa cache para performance
4. Retorna dict de indicadores

### **STEP 4: Definir EXIT METHODS fixos**

**4 MÉTODOS PRÉ-DEFINIDOS:**

1. **`atr_fixed`**: SL/TP fixo baseado em ATR
   - `sl_atr_mult`: 1.5-3.5
   - `tp_rr_ratio`: 1.5-4.0

2. **`atr_trailing`**: Trailing stop baseado em ATR
   - `trail_atr_mult`: 1.5-3.0
   - `tp_rr_ratio`: 1.5-4.0

3. **`breakeven_then_trail`**: Move para breakeven depois trail
   - `breakeven_r`: 0.5-1.5
   - `trail_atr_mult`: 1.5-3.0
   - `tp_rr_ratio`: 1.5-4.0

4. **`keltner`**: Exit baseado em Keltner channels
   - Fecha quando toca Keltner opposite

### **STEP 5: Auto-detect de Parâmetros por Estratégia**

```python
def get_optimizable_params_for_strategy(strategy_name: str) -> List[ParameterRange]:
    """
    Auto-detect which indicators a strategy uses and return
    their parameter ranges
    """
    metadata = STRATEGY_METADATA.get(strategy_name, {})
    indicators_used = metadata.get('indicators', [])
    
    ranges = []
    
    # Map indicator names to parameter ranges
    if any('rsi' in ind for ind in indicators_used):
   ranges.extend([
         ParameterRange('rsi_period', 'int', low=7, high=28, step=1),
            ParameterRange('rsi_oversold', 'int', low=20, high=35, step=5),
          ParameterRange('rsi_overbought', 'int', low=65, high=80, step=5),
        ])
    
    if any('ema' in ind for ind in indicators_used):
        ranges.extend([
            ParameterRange('ema_fast_period', 'int', low=8, high=30, step=2),
  ParameterRange('ema_slow_period', 'int', low=40, high=100, step=5),
            ParameterRange('ema_trend_period', 'int', low=150, high=250, step=10),
        ])
    
    # ... continue para todos os indicadores
    
    # Always add exit parameters
    ranges.append(ParameterRange('exit_method', 'categorical', 
   choices=['atr_fixed', 'atr_trailing', 'breakeven_then_trail', 'keltner']))
    
    return ranges
```

---

## ?? TEMPO ESTIMADO POR STEP:

- **STEP 1** (indicators_dynamic.py): ~2h
- **STEP 2** (Cache system): ~30min
- **STEP 3** (Backtest engine integration): ~1h
- **STEP 4** (Exit methods): ~30min
- **STEP 5** (Auto-detect params): ~1h

**TOTAL:** ~5 horas de trabalho focado

---

## ?? EXIT METHODS - CONFIGURAÇÃO:

```yaml
# Config exemplo com exit method selecionado
risk:
  exit_method: "breakeven_then_trail"  # Escolhe 1 de 4
  
  # Parâmetros do exit method
  breakeven_r: 1.0
  trail_atr_mult: 2.0
  tp_rr_ratio: 2.5
  sl_atr_mult: 1.5  # Apenas para initial stop
  time_stop_bars: 144
```

---

## ? BENEFITS:

1. **Verdadeira Optimização** - Optimiza os parâmetros que realmente importam
2. **Flexibilidade** - Qualquer indicador pode ser customizado
3. **Performance** - Cache evita recálculo
4. **Simplicidade nos Exits** - 4 métodos pré-definidos e testados
5. **Auto-detection** - Sistema detecta quais parâmetros optimizar por estratégia
6. **Escalável** - Fácil adicionar novos indicadores/estratégias

---

## ?? PRÓXIMO PASSO:

**Começamos por criar `core/indicators_dynamic.py` com TODOS os indicadores?**

Posso criar o ficheiro completo com todas as funções parametrizadas, seguindo as melhores práticas (pandas-ta, numpy vectorizado, etc.).

**Confirmas que vamos avançar com este plano?** ??
