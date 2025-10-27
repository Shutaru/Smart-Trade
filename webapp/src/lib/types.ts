export type Candle = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type LiveStatus = {
  mode: 'paper' | 'live';
  symbol: string;
  equity: number;
  available: number;
  fundingRate?: number;
};
