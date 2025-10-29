/**
 * API Client for Strategy Lab
 * 
 * Type-safe client for all Strategy Lab endpoints
 */

import axios, { AxiosError } from 'axios';
import type { 
  StrategyDefinition,
  BacktestResult,
  OptimizationResult,
  BacktestMetrics
} from '@/domain/strategy';

// ============================================================================
// BASE CLIENT
// ============================================================================

const api = axios.create({
  baseURL: '/api/lab',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 300000 // 5 minutes for long-running operations
});

// Error handler
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function handleError(error: unknown): never {
  if (axios.isAxiosError(error)) {
 const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
 const message = axiosError.response?.data?.detail || 
  axiosError.response?.data?.message || 
     axiosError.message;
 throw new ApiError(
    message,
      axiosError.response?.status,
      axiosError.response?.data
    );
  }
  throw error;
}

// ============================================================================
// EXCHANGES & SYMBOLS
// ============================================================================

export interface ExchangeListResponse {
  exchanges: string[];
}

export interface SymbolListResponse {
  symbols: string[];
}

export async function getExchanges(): Promise<string[]> {
  try {
    const { data } = await api.get<ExchangeListResponse>('/exchanges');
    return data.exchanges;
  } catch (error) {
    return handleError(error);
  }
}

export async function getSymbols(exchange: string): Promise<string[]> {
  try {
    const { data } = await api.get<SymbolListResponse>('/symbols', {
      params: { exchange }
    });
    return data.symbols;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// BACKFILL
// ============================================================================

export interface BackfillRequest {
  exchange: string;
  symbols: string[];
  timeframe: string;
  since: number;
  until: number;
  higher_tf?: string[];
}

export interface BackfillResult {
  symbol: string;
  timeframe: string;
  candles_inserted: number;
  features_inserted: number;
  db_path: string;
}

export interface BackfillResponse {
  success: boolean;
  message: string;
  results: BackfillResult[];
  total_candles: number;
  total_features: number;
}

export async function backfillData(request: BackfillRequest): Promise<BackfillResponse> {
  try {
    const { data } = await api.post<BackfillResponse>('/backfill', request);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// INDICATORS
// ============================================================================

export interface IndicatorInfo {
  id: string;
  name: string;
  params: Record<string, any>;
  supported_timeframes: string[];
  description: string;
}

export interface IndicatorCatalogResponse {
  indicators: IndicatorInfo[];
}

export async function getIndicators(): Promise<IndicatorInfo[]> {
  try {
    const { data } = await api.get<IndicatorCatalogResponse>('/indicators');
    return data.indicators;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// STRATEGY VALIDATION
// ============================================================================

export interface ValidateStrategyResponse {
  valid: boolean;
  features_required: string[];
errors: string[];
}

export async function validateStrategy(strategy: StrategyDefinition): Promise<ValidateStrategyResponse> {
  try {
    const { data } = await api.post<ValidateStrategyResponse>('/strategy/validate', strategy);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// BACKTEST
// ============================================================================

export interface RunResponse {
  run_id: string;
  status: string;
}

export interface RunStatus {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_trial?: number;
  total_trials?: number;
  best_score?: number;
  started_at?: number;
  completed_at?: number;
}

export async function runBacktest(strategy: StrategyDefinition): Promise<RunResponse> {
  try {
 const { data } = await api.post<RunResponse>('/run/backtest', strategy);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

export async function getRunStatus(runId: string): Promise<RunStatus> {
  try {
    const { data } = await api.get<RunStatus>(`/run/${runId}/status`);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// RESULTS
// ============================================================================

export interface TrialResult {
  trial_id: number;
  params: Record<string, any>;
  metrics: BacktestMetrics;
  score: number;
}

export interface RunResultsResponse {
  run_id: string;
  trials: TrialResult[];
  total: number;
}

export async function getRunResults(runId: string, limit = 100, offset = 0): Promise<RunResultsResponse> {
  try {
    const { data } = await api.get<RunResultsResponse>(`/run/${runId}/results`, {
 params: { limit, offset }
    });
    return data;
  } catch (error) {
    return handleError(error);
  }
}

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandlesResponse {
  symbol: string;
  timeframe: string;
  candles: CandleData[];
}

export async function getRunCandles(runId: string): Promise<CandlesResponse> {
  try {
    const { data } = await api.get<CandlesResponse>(`/run/${runId}/candles`);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

export interface EquityPoint {
  time: number;
  equity: number;
  drawdown: number;
}

export interface EquityResponse {
  equity: EquityPoint[];
}

export async function getRunEquity(runId: string): Promise<EquityResponse> {
  try {
    const { data } = await api.get<EquityResponse>(`/run/${runId}/equity`);
    return data;
} catch (error) {
    return handleError(error);
  }
}

export interface Trade {
entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  side: string;
  pnl: number;
  pnl_pct: number;
}

export interface TradesResponse {
  trades: Trade[];
}

export async function getRunTrades(runId: string): Promise<TradesResponse> {
  try {
    const { data } = await api.get<TradesResponse>(`/run/${runId}/artifacts/trades`);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// OPTIMIZATION
// ============================================================================

export async function runGridSearch(strategy: StrategyDefinition): Promise<RunResponse> {
  try {
    const { data } = await api.post<RunResponse>('/run/grid', strategy);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

export async function runOptuna(strategy: StrategyDefinition, nTrials = 100): Promise<RunResponse> {
  try {
 const { data } = await api.post<RunResponse>('/run/optuna', strategy, {
   params: { n_trials: nTrials }
    });
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// RUNS LIST
// ============================================================================

export async function listRuns(limit = 100): Promise<RunStatus[]> {
  try {
    const { data } = await api.get<RunStatus[]>('/runs', {
      params: { limit }
    });
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// ============================================================================
// DOWNLOAD ARTIFACTS
// ============================================================================

export async function downloadArtifacts(runId: string): Promise<Blob> {
  try {
    const { data } = await api.get(`/run/${runId}/download`, {
      responseType: 'blob'
    });
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// Helper to trigger download
export function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// ============================================================================
// WEBSOCKET (for real-time updates)
// ============================================================================

export interface WebSocketMessage {
  ts: number;
  level: 'INFO' | 'WARNING' | 'ERROR';
  msg: string;
  progress?: number;
  best_score?: number;
  status?: string;
}

export function connectRunWebSocket(
  runId: string,
  onMessage: (message: WebSocketMessage) => void,
  onError?: (error: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/lab/run/${runId}`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;
      onMessage(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };
  
  if (onError) {
    ws.onerror = onError;
  }
  
  if (onClose) {
    ws.onclose = onClose;
  }
  
  return ws;
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Data
  getExchanges,
  getSymbols,
  backfillData,
  
  // Indicators
  getIndicators,
  
  // Strategy
  validateStrategy,
  
  // Backtest
  runBacktest,
  getRunStatus,
  getRunResults,
  getRunCandles,
  getRunEquity,
  getRunTrades,
  
  // Optimization
  runGridSearch,
  runOptuna,
  
  // Runs
  listRuns,
  
  // Downloads
  downloadArtifacts,
  triggerDownload,
  
  // WebSocket
  connectRunWebSocket
};
