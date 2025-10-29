import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { IChartApi, ISeriesApi, Time, CandlestickData, LineData } from 'lightweight-charts';
import { createChart } from 'lightweight-charts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface TradingChartProps {
  runId: string;
}

interface Trade {
  entry_time: string;
  exit_time: string | null;
  side: 'long' | 'short';
  entry_price?: number;
  exit_price?: number;
  pnl: number;
  pnl_pct: number;
}

type MarkerPosition = 'belowBar' | 'aboveBar';
type MarkerShape = 'arrowUp' | 'arrowDown' | 'circle';

export function TradingChart({ runId }: TradingChartProps) {
  const equityChartRef = useRef<HTMLDivElement | null>(null);
  const candleChartRef = useRef<HTMLDivElement | null>(null);
  const equityChartInstance = useRef<IChartApi | null>(null);
  const candleChartInstance = useRef<IChartApi | null>(null);
  const equitySeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ddSeriesRef = useRef<ISeriesApi<'Area'> | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Fetch candles
  const { data: candlesData, isLoading: candlesLoading, error: candlesError } = useQuery({
    queryKey: ['candles', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/candles`);
      if (!res.ok) throw new Error('Failed to fetch candles');
      const data = await res.json();
      console.log('[TradingChart] Candles data:', data);
      return data;
    }
  });

  // Fetch equity
  const { data: equityData, isLoading: equityLoading, error: equityError } = useQuery({
    queryKey: ['equity', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/equity`);
      if (!res.ok) throw new Error('Failed to fetch equity');
      const data = await res.json();
      console.log('[TradingChart] Equity data:', data);
      return data;
    }
  });

  // Fetch trades for markers
  const { data: tradesData } = useQuery({
    queryKey: ['trades', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/artifacts/trades`);
      if (!res.ok) throw new Error('Failed to fetch trades');
      const data = await res.json();
      console.log('[TradingChart] Trades data:', data);
      return data;
    }
  });

  // Helper: Convert timestamp to seconds
  const toSeconds = (t: number): number => {
    return t > 2e10 ? Math.floor(t / 1000) : t;
  };

  // Initialize charts once
  useEffect(() => {
    if (!equityChartRef.current || !candleChartRef.current) return;
    if (equityChartInstance.current || candleChartInstance.current) return;

    console.log('[TradingChart] Creating chart instances...');

    // Create Equity Chart
    const equityChart = createChart(equityChartRef.current, {
      width: equityChartRef.current.clientWidth,
      height: 250,
      layout: {
        background: { color: 'transparent' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      rightPriceScale: {
        borderColor: '#374151',
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
      },
    });

    equitySeriesRef.current = equityChart.addLineSeries({
      color: '#10b981',
      lineWidth: 2,
      title: 'Equity',
    });

    ddSeriesRef.current = equityChart.addAreaSeries({
      topColor: 'rgba(239, 68, 68, 0.4)',
      bottomColor: 'rgba(239, 68, 68, 0.0)',
      lineColor: 'rgba(239, 68, 68, 0.8)',
      lineWidth: 1,
      title: 'Drawdown',
    });

    equityChartInstance.current = equityChart;

    // Create Candlestick Chart
    const candleChart = createChart(candleChartRef.current, {
      width: candleChartRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: 'transparent' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      rightPriceScale: {
        borderColor: '#374151',
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
      },
    });

    candleSeriesRef.current = candleChart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candleChartInstance.current = candleChart;

    // Sync time scales
    equityChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (range) {
        candleChart.timeScale().setVisibleLogicalRange(range);
      }
    });

    candleChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (range) {
        equityChart.timeScale().setVisibleLogicalRange(range);
      }
    });

    // Handle resize
    const handleResize = () => {
      if (equityChartRef.current) {
        equityChart.applyOptions({ width: equityChartRef.current.clientWidth });
      }
      if (candleChartRef.current) {
        candleChart.applyOptions({ width: candleChartRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    console.log('[TradingChart] Chart instances created');

    return () => {
      window.removeEventListener('resize', handleResize);
      equityChart.remove();
      candleChart.remove();
      equityChartInstance.current = null;
      candleChartInstance.current = null;
      equitySeriesRef.current = null;
      ddSeriesRef.current = null;
      candleSeriesRef.current = null;
    };
  }, []);

  // Update equity data
  useEffect(() => {
    if (!equitySeriesRef.current || !ddSeriesRef.current || !equityData?.equity) return;

    console.log('[TradingChart] Updating equity data...');

    const equityLineData: LineData[] = equityData.equity.map((e: any) => ({
      time: toSeconds(e.time) as Time,
      value: e.equity,
    }));

    const ddData: LineData[] = equityData.equity.map((e: any) => ({
      time: toSeconds(e.time) as Time,
      value: e.drawdown || 0,
    }));

    console.log('[TradingChart] Equity sample:', equityLineData.slice(0, 3));

    equitySeriesRef.current.setData(equityLineData);
    ddSeriesRef.current.setData(ddData);
  }, [equityData]);

  // Update candle data and markers
  useEffect(() => {
    if (!candleSeriesRef.current || !candlesData?.candles) return;

    console.log('[TradingChart] Updating candle data...');

    const candleSeriesData: CandlestickData[] = candlesData.candles.map((c: any) => ({
      time: toSeconds(c.time) as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    console.log('[TradingChart] Candles sample:', candleSeriesData.slice(0, 3));

    candleSeriesRef.current.setData(candleSeriesData);

    // Add trade markers
    if (tradesData?.trades && tradesData.trades.length > 0) {
      try {
        const markers = tradesData.trades
          .filter((trade: Trade) => trade.exit_time) // Only completed trades
          .flatMap((trade: Trade) => {
            const entryTime = Math.floor(new Date(trade.entry_time).getTime() / 1000);
            const exitTime = Math.floor(new Date(trade.exit_time!).getTime() / 1000);
            const isWin = trade.pnl > 0;

            const entryPosition: MarkerPosition = trade.side === 'long' ? 'belowBar' : 'aboveBar';
            const entryShape: MarkerShape = trade.side === 'long' ? 'arrowUp' : 'arrowDown';
            const exitPosition: MarkerPosition = trade.side === 'long' ? 'aboveBar' : 'belowBar';

            return [
              {
                time: entryTime as Time,
                position: entryPosition,
                color: trade.side === 'long' ? '#10b981' : '#ef4444',
                shape: entryShape,
                text: `Entry ${trade.side.toUpperCase()}`,
              },
              {
                time: exitTime as Time,
                position: exitPosition,
                color: isWin ? '#10b981' : '#ef4444',
                shape: 'circle' as MarkerShape,
                text: `${isWin ? '+' : ''}${trade.pnl.toFixed(2)}`,
              },
            ];
          });

        console.log('[TradingChart] Adding', markers.length, 'markers');
        candleSeriesRef.current.setMarkers(markers);
      } catch (err) {
        console.error('[TradingChart] Error adding markers:', err);
      }
    }
  }, [candlesData, tradesData]);

  if (candlesLoading || equityLoading) {
    return (
      <div className="flex items-center justify-center h-[650px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (candlesError || equityError) {
    return (
      <div className="text-center py-8 text-destructive">
        <p>Error loading chart data</p>
        <p className="text-sm mt-2">{(candlesError || equityError)?.toString()}</p>
      </div>
    );
  }

  if (!candlesData?.candles || !equityData?.equity) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No chart data available</p>
        <p className="text-sm mt-2">
          Candles: {candlesData?.candles?.length || 0} | Equity: {equityData?.equity?.length || 0}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Equity Curve</CardTitle>
          <CardDescription>Cumulative P&L over time ({equityData.equity.length} points)</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div ref={equityChartRef} className="w-full min-h-[250px]" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Price Action & Trades</CardTitle>
          <CardDescription>
            {candlesData.symbol} • {candlesData.timeframe} •
            <span className="text-green-500 ml-2">? Entry</span>
            <span className="text-red-500 ml-2">? Entry</span>
            <span className="ml-2">? Exit</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div ref={candleChartRef} className="w-full min-h-[400px]" />
        </CardContent>
      </Card>
    </div>
  );
}
