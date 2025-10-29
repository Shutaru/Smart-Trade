/**
 * Strategy Lab - Domain Models
 * 
 * Type-safe schemas for strategy configuration, indicators, and optimization
 */

// ============================================================================
// INDICATORS CATALOG
// ============================================================================

export type IndicatorType =
  | 'RSI'
  | 'EMA'
  | 'SMA'
  | 'MACD'
  | 'ADX'
  | 'ATR'
  | 'BB'   // Bollinger Bands
  | 'SuperTrend'
  | 'Donchian'
  | 'Keltner'
  | 'Stochastic'
  | 'CCI'
  | 'MFI'
  | 'OBV'
  | 'VWAP';

export type ComparisonOperator =
  | '>'
  | '<'
  | '>='
  | '<='
  | '=='
  | '!='
  | 'between'
  | 'crossesAbove'
  | 'crossesBelow';

/**
 * Indicator configuration with parameters
 */
export interface IndicatorConfig {
  id: string;           // Unique identifier (e.g., "RSI_14")
  type: IndicatorType;
  params: Record<string, number | string>;  // e.g., { period: 14 }
  timeframe?: string;   // Optional: use different timeframe (e.g., "1h" on 5m base)
}

/**
 * Predefined indicator catalog with defaults
 */
export const INDICATOR_CATALOG: Record<IndicatorType, {
  name: string;
  description: string;
  defaultParams: Record<string, number | string>;
  outputFields: string[];  // e.g., ['rsi'] or ['macd', 'signal', 'histogram']
}> = {
  RSI: {
    name: 'Relative Strength Index',
    description: 'Momentum oscillator (0-100)',
    defaultParams: { period: 14 },
    outputFields: ['rsi']
  },
  EMA: {
    name: 'Exponential Moving Average',
    description: 'Trend-following indicator',
    defaultParams: { period: 20 },
    outputFields: ['ema']
  },
  SMA: {
    name: 'Simple Moving Average',
    description: 'Average price over period',
    defaultParams: { period: 50 },
    outputFields: ['sma']
  },
  MACD: {
    name: 'Moving Average Convergence Divergence',
    description: 'Trend momentum indicator',
  defaultParams: { fast: 12, slow: 26, signal: 9 },
    outputFields: ['macd', 'signal', 'histogram']
  },
  ADX: {
    name: 'Average Directional Index',
    description: 'Trend strength indicator',
    defaultParams: { period: 14 },
    outputFields: ['adx', 'plus_di', 'minus_di']
  },
  ATR: {
    name: 'Average True Range',
    description: 'Volatility indicator',
    defaultParams: { period: 14 },
    outputFields: ['atr']
  },
  BB: {
    name: 'Bollinger Bands',
  description: 'Volatility bands',
    defaultParams: { period: 20, std: 2 },
    outputFields: ['bb_upper', 'bb_middle', 'bb_lower']
  },
  SuperTrend: {
    name: 'SuperTrend',
    description: 'Trend-following indicator',
    defaultParams: { period: 10, multiplier: 3 },
    outputFields: ['supertrend', 'direction']
  },
  Donchian: {
    name: 'Donchian Channels',
    description: 'Breakout indicator',
    defaultParams: { period: 20 },
    outputFields: ['donchian_upper', 'donchian_lower', 'donchian_middle']
  },
  Keltner: {
    name: 'Keltner Channels',
    description: 'Volatility-based channels',
    defaultParams: { period: 20, multiplier: 2 },
    outputFields: ['keltner_upper', 'keltner_middle', 'keltner_lower']
  },
  Stochastic: {
    name: 'Stochastic Oscillator',
    description: 'Momentum indicator (0-100)',
  defaultParams: { k_period: 14, d_period: 3 },
    outputFields: ['stoch_k', 'stoch_d']
  },
  CCI: {
    name: 'Commodity Channel Index',
    description: 'Momentum oscillator',
    defaultParams: { period: 20 },
outputFields: ['cci']
  },
  MFI: {
    name: 'Money Flow Index',
    description: 'Volume-weighted RSI',
    defaultParams: { period: 14 },
    outputFields: ['mfi']
  },
  OBV: {
    name: 'On-Balance Volume',
    description: 'Volume accumulation indicator',
    defaultParams: {},
    outputFields: ['obv']
  },
  VWAP: {
    name: 'Volume Weighted Average Price',
    description: 'Average price weighted by volume',
    defaultParams: {},
    outputFields: ['vwap']
  }
};

// ============================================================================
// ENTRY CONDITIONS
// ============================================================================

/**
 * Entry condition comparing an indicator to a value or another indicator
 */
export interface EntryCondition {
  id: string;  // Unique ID for UI management
  
  // Left-hand side: indicator
  indicator: IndicatorConfig;
  field?: string;  // Which output field (e.g., 'macd' from MACD indicator)
  
  // Operator
  operator: ComparisonOperator;
  
  // Right-hand side: value or another indicator
  valueType: 'constant' | 'indicator' | 'price';
  constantValue?: number;  // e.g., RSI < 30
  referenceIndicator?: IndicatorConfig;  // e.g., EMA(20) crosses above EMA(50)
  referenceField?: string;
  priceField?: 'open' | 'high' | 'low' | 'close';  // e.g., close > EMA(200)
  
  // For 'between' operator
  rangeLow?: number;
  rangeHigh?: number;
  
  // Lookback for crosses (number of bars to check)
lookback?: number;
}

/**
 * Entry logic: combine conditions with AND/OR
 */
export interface EntryLogic {
  all: EntryCondition[];  // ALL conditions must be true (AND)
  any: EntryCondition[];  // ANY condition can be true (OR)
  // Final logic: (all[0] AND all[1] AND ...) OR (any[0] OR any[1] OR ...)
}

// ============================================================================
// EXIT RULES
// ============================================================================

export type ExitType =
  | 'fixed_pct'      // Fixed percentage (TP/SL)
  | 'fixed_atr'      // ATR-based (e.g., 2 * ATR)
  | 'trailing_pct'     // Trailing stop percentage
  | 'trailing_atr'     // Trailing stop ATR-based
  | 'indicator'        // Exit when indicator condition met
  | 'time'   // Time-based exit (bars)
  | 'breakeven';       // Move to breakeven after X% profit

export interface ExitRule {
  id: string;
  type: ExitType;
  
  // For fixed/trailing exits
  value?: number;  // Percentage or ATR multiplier
  
  // For ATR-based exits
  atrPeriod?: number;
  atrMultiplier?: number;
  
  // For indicator-based exits
  condition?: EntryCondition;
  
  // For time-based exits
  bars?: number;
  
  // For breakeven
  triggerProfitPct?: number;  // Move to breakeven after this profit %
  
  // Partial exits
  isPartial?: boolean;
  partialPercent?: number;  // Close X% of position
  
  // Priority (lower = higher priority)
  priority?: number;
}

/**
 * Exit configuration for a strategy side (LONG or SHORT)
 */
export interface ExitConfig {
  takeProfit: ExitRule[];   // Can have multiple TP levels
  stopLoss: ExitRule[];     // Usually one, but supports multiple
  trailing: ExitRule[];     // Trailing stops
  other: ExitRule[];        // Time-based, indicator-based, etc.
}

// ============================================================================
// RISK MANAGEMENT
// ============================================================================

export interface RiskConfig {
  // Portfolio
  initialEquity: number;       // Starting capital in USDT
  
  // Position sizing
  positionSizingMode: 'fixed_usd' | 'portfolio_pct' | 'risk_pct' | 'kelly';
  fixedUsdSize?: number;     // For 'fixed_usd' mode
  portfolioPct?: number;       // For 'portfolio_pct' mode
  riskPct?: number;   // For 'risk_pct' mode (% of equity to risk per trade)
  
  // Leverage
  maxLeverage: number;      // Max leverage allowed
  
  // Limits
  maxConcurrentPositions: number;
  maxDailyLoss?: number;       // Stop trading after losing X% in a day
  maxDrawdown?: number;        // Stop trading if drawdown exceeds X%
  
  // Fees
  makerFee: number;   // Maker fee %
  takerFee: number;   // Taker fee %
  slippage: number;  // Estimated slippage in bps
}

// ============================================================================
// STRATEGY DEFINITION
// ============================================================================

export interface StrategyDefinition {
  // Metadata
  id?: string;
  name: string;
  description?: string;
  version?: string;
  
  // Data configuration
  exchange: 'bitget' | 'binance';
  symbols: string[];           // Can backtest multiple symbols
  baseTimeframe: string;     // e.g., '5m'
  higherTimeframes?: string[]; // e.g., ['1h', '4h'] for multi-timeframe
  
  // Date range
  dateFrom: number;   // Unix timestamp (ms)
  dateTo: number;              // Unix timestamp (ms)
  
  // Entry logic
  long: {
    enabled: boolean;
    entry: EntryLogic;
    exits: ExitConfig;
  };
  
  short: {
 enabled: boolean;
 entry: EntryLogic;
    exits: ExitConfig;
  };
  
  // Risk management
  risk: RiskConfig;
  
  // Warmup period (bars to skip for indicator calculation)
  warmupBars?: number;
}

// ============================================================================
// OPTIMIZATION
// ============================================================================

export type ParameterType = 'int' | 'float' | 'choice' | 'bool';

export interface ParameterRange {
  id: string;              // Path to parameter (e.g., "long.entry.all[0].indicator.params.period")
  name: string;              // Display name
  type: ParameterType;
  
  // For int/float
  min?: number;
  max?: number;
  step?: number;
  
  // For choice
  choices?: (string | number)[];
  
  // Default value
  default: number | string | boolean;
  
  // Log scale for optimization
  logScale?: boolean;
}

export interface OptimizationSpace {
  parameters: ParameterRange[];
  
  // Objective function (evaluated as JavaScript expression)
  // Available variables: sharpe, sortino, calmar, total_profit, max_dd, win_rate, profit_factor, trades, avg_trade
  objective: string;  // e.g., "sharpe * 100 + total_profit - Math.abs(max_dd)"
  
  // Constraints
  minTrades?: number;        // Minimum trades required
  maxDrawdown?: number;        // Maximum acceptable drawdown %
  minSharpe?: number;     // Minimum Sharpe ratio
  
  // Optimization method
  method: 'grid' | 'random' | 'bayesian' | 'optuna';
  
  // For grid search
  gridPoints?: number;         // Points per parameter
  
  // For random/bayesian
  numTrials?: number;          // Number of trials
  
  // For Optuna
  optunaConfig?: {
    sampler?: 'TPE' | 'CmaEs' | 'Random';
    pruner?: 'Median' | 'Hyperband' | 'None';
    timeout?: number;          // Seconds
  };
}

// ============================================================================
// BACKTEST RESULTS
// ============================================================================

export interface Trade {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  
  // Entry
  entryTime: number;// Unix timestamp (ms)
  entryPrice: number;
  entryReason: string;     // Which condition triggered
  
  // Exit
  exitTime: number;
  exitPrice: number;
  exitReason: string;     // TP/SL/Trail/Time/Manual
  
  // Size
  quantity: number;
  notional: number;         // Position size in USDT
  leverage: number;
  
  // Results
  pnl: number;       // Absolute PnL in USDT
  pnlPct: number;        // PnL as % of entry notional
  fees: number;        // Total fees paid
  mae: number;     // Maximum Adverse Excursion (%)
  mfe: number;   // Maximum Favorable Excursion (%)
  
  // Duration
  durationBars: number;
  durationMs: number;
}

export interface EquityPoint {
  time: number;                // Unix timestamp (ms)
  equity: number;  // Portfolio value in USDT
  drawdown: number;            // Drawdown % from peak
}

export interface BacktestMetrics {
  // Return metrics
  totalProfit: number;      // Total profit %
  totalPnl: number;            // Total PnL in USDT
  cagr: number;                // Compound annual growth rate %
  
  // Risk metrics
  sharpe: number;     // Sharpe ratio (annualized)
  sortino: number;             // Sortino ratio (annualized)
  calmar: number; // Calmar ratio (return / max DD)
  maxDrawdown: number;  // Maximum drawdown %
  avgDrawdown: number;  // Average drawdown %
  
  // Trade metrics
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;          // Win rate %
  profitFactor: number;        // Gross profit / Gross loss
  avgWin: number;      // Average winning trade %
  avgLoss: number;    // Average losing trade %
  avgTrade: number;  // Average trade %
  largestWin: number;   // Largest winning trade %
  largestLoss: number;         // Largest losing trade %
  
  // Efficiency
  expectancy: number;          // Expected value per trade
  avgBarsInTrade: number;      // Average trade duration
  profitPerBar: number;        // Profit per bar held
  
  // Exposure
  exposurePct: number;         // % of time in market
  avgLeverage: number;   // Average leverage used
  
  // Consistency
  consecutiveWins: number;     // Max consecutive wins
  consecutiveLosses: number;   // Max consecutive losses
  
  // Risk-adjusted
  recoveryFactor: number;  // Net profit / Max DD
  ulcerIndex: number;       // Measure of downside volatility
}

export interface BacktestResult {
  strategyId: string;
  strategyName: string;
  
  // Configuration used
  strategy: StrategyDefinition;
  
  // Results
  metrics: BacktestMetrics;
  equity: EquityPoint[];
  trades: Trade[];
  
  // Execution info
  startTime: number;
  endTime: number;
  executionTimeMs: number;
  candlesProcessed: number;
  
  // Artifacts
  artifactUrls?: {
  equityCsv?: string;
    tradesCsv?: string;
    reportHtml?: string;
  };
}

export interface OptimizationResult {
  optimizationId: string;
  
  // Best strategy
  bestStrategy: StrategyDefinition;
  bestMetrics: BacktestMetrics;
  bestScore: number;
  
  // All trials
  trials: Array<{
    trialId: number;
  parameters: Record<string, number | string | boolean>;
    metrics: BacktestMetrics;
    score: number;
  }>;
  
  // Optimization info
  method: string;
  totalTrials: number;
  completedTrials: number;
  failedTrials: number;
  executionTimeMs: number;
  
  // Parameter importance (for Optuna)
  parameterImportance?: Record<string, number>;
}

// ============================================================================
// VALIDATION HELPERS
// ============================================================================

export function validateStrategy(strategy: StrategyDefinition): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Basic validation
  if (!strategy.name) errors.push('Strategy name is required');
  if (!strategy.exchange) errors.push('Exchange is required');
  if (!strategy.symbols || strategy.symbols.length === 0) errors.push('At least one symbol is required');
  if (!strategy.baseTimeframe) errors.push('Base timeframe is required');
  if (!strategy.dateFrom || !strategy.dateTo) errors.push('Date range is required');
  if (strategy.dateFrom >= strategy.dateTo) errors.push('Start date must be before end date');
  
  // Entry validation
  if (!strategy.long.enabled && !strategy.short.enabled) {
    errors.push('At least one side (LONG or SHORT) must be enabled');
  }
  
  if (strategy.long.enabled && strategy.long.entry.all.length === 0 && strategy.long.entry.any.length === 0) {
    errors.push('LONG side has no entry conditions');
  }
  
  if (strategy.short.enabled && strategy.short.entry.all.length === 0 && strategy.short.entry.any.length === 0) {
    errors.push('SHORT side has no entry conditions');
  }
  
  // Risk validation
  if (strategy.risk.initialEquity <= 0) errors.push('Initial equity must be positive');
  if (strategy.risk.maxLeverage <= 0) errors.push('Max leverage must be positive');
  if (strategy.risk.maxConcurrentPositions <= 0) errors.push('Max concurrent positions must be positive');
  
  return {
    valid: errors.length === 0,
    errors
  };
}

export function createDefaultStrategy(): StrategyDefinition {
  const now = Date.now();
  const oneYearAgo = now - 365 * 24 * 60 * 60 * 1000;
  
  return {
    name: 'New Strategy',
    exchange: 'bitget',
    symbols: ['BTC/USDT:USDT'],
baseTimeframe: '5m',
    dateFrom: oneYearAgo,
    dateTo: now,
  long: {
      enabled: true,
      entry: {
     all: [],
        any: []
      },
      exits: {
        takeProfit: [],
   stopLoss: [],
        trailing: [],
        other: []
      }
  },
    short: {
      enabled: false,
    entry: {
        all: [],
        any: []
      },
      exits: {
        takeProfit: [],
        stopLoss: [],
trailing: [],
        other: []
      }
  },
    risk: {
   initialEquity: 10000,
      positionSizingMode: 'portfolio_pct',
      portfolioPct: 10,
   maxLeverage: 3,
      maxConcurrentPositions: 1,
      makerFee: 0.02,
      takerFee: 0.06,
      slippage: 1
    },
    warmupBars: 200
  };
}
