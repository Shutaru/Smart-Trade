import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { createChart, IChartApi, CandlestickData, LineData, Time } from 'lightweight-charts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface TradingChartProps {
  runId: string;
}

interface Trade {
  entry_time: string;
  exit_time: string;
  side: 'long' | 'short';
  entry_price?: number;
  exit_price?: number;
  pnl: number;
  pnl_pct: number;
}

export function TradingChart({ runId }: TradingChartProps) {
  const equityChartRef = useRef<HTMLDivElement>(null);
  const candleChartRef = useRef<HTMLDivElement>(null);
  const equityChartInstance = useRef<IChartApi | null>(null);
  const candleChartInstance = useRef<IChartApi | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Fetch candles
  const { data: candlesData, isLoading: candlesLoading } = useQuery({
    queryKey: ['candles', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/candles`);
      if (!res.ok) throw new Error('Failed to fetch candles');
      return res.json();
    }
  });

  // Fetch equity
  const { data: equityData, isLoading: equityLoading } = useQuery({
    queryKey: ['equity', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/equity`);
      if (!res.ok) throw new Error('Failed to fetch equity');
      return res.json();
}
  });

  // Fetch trades for markers
  const { data: tradesData } = useQuery({
    queryKey: ['trades', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/artifacts/trades`);
      if (!res.ok) throw new Error('Failed to fetch trades');
      return res.json();
    }
  });

  useEffect(() => {
    if (!equityChartRef.current || !candleChartRef.current || isInitialized) return;
    if (candlesLoading || equityLoading) return;
 if (!candlesData?.candles || !equityData?.equity) return;

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

    const equityLine = equityChart.addLineSeries({
      color: '#10b981',
      lineWidth: 2,
      title: 'Equity',
  });

    const equityLineData: LineData[] = equityData.equity.map((e: any) => ({
      time: e.time as Time,
  value: e.equity,
    }));

    equityLine.setData(equityLineData);

    // Add drawdown as area series
    const ddArea = equityChart.addAreaSeries({
      topColor: 'rgba(239, 68, 68, 0.4)',
      bottomColor: 'rgba(239, 68, 68, 0.0)',
      lineColor: 'rgba(239, 68, 68, 0.8)',
      lineWidth: 1,
      title: 'Drawdown',
    });

    const ddData: LineData[] = equityData.equity.map((e: any) => ({
 time: e.time as Time,
      value: e.drawdown,
    }));

    ddArea.setData(ddData);

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

    const candleSeries = candleChart.addCandlestickSeries({
      upColor: '#10b981',
   downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    const candleSeriesData: CandlestickData[] = candlesData.candles.map((c: any) => ({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    candleSeries.setData(candleSeriesData);

    // Add trade markers
 if (tradesData?.trades) {
      const markers = tradesData.trades.flatMap((trade: Trade) => {
 const entryTime = Math.floor(new Date(trade.entry_time).getTime() / 1000);
        const exitTime = Math.floor(new Date(trade.exit_time).getTime() / 1000);
        const isWin = trade.pnl > 0;

    const entryMarker = {
      time: entryTime as Time,
          position: (trade.side === 'long' ? 'belowBar' : 'aboveBar') as 'belowBar' | 'aboveBar',
     color: trade.side === 'long' ? '#10b981' : '#ef4444',
          shape: (trade.side === 'long' ? 'arrowUp' : 'arrowDown') as 'arrowUp' | 'arrowDown',
text: `Entry ${trade.side.toUpperCase()}`,
        };

        const exitMarker = {
          time: exitTime as Time,
          position: (trade.side === 'long' ? 'aboveBar' : 'belowBar') as 'belowBar' | 'aboveBar',
     color: isWin ? '#10b981' : '#ef4444',
          shape: 'circle' as 'circle',
   text: `Exit ${isWin ? '+' : ''}${trade.pnl.toFixed(2)}`,
        };

     return [entryMarker, exitMarker];
      });

      candleSeries.setMarkers(markers);
    }

    candleChartInstance.current = candleChart;

    // Sync time scales
    const syncCharts = (targetChart: IChartApi, sourceChart: IChartApi) => {
      targetChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) {
          sourceChart.timeScale().setVisibleLogicalRange(range);
   }
  });
    };

  syncCharts(equityChart, candleChart);
    syncCharts(candleChart, equityChart);

    setIsInitialized(true);

    // Handle resize
    const handleResize = () => {
      if (equityChartRef.current && equityChart) {
   equityChart.applyOptions({ width: equityChartRef.current.clientWidth });
      }
      if (candleChartRef.current && candleChart) {
    candleChart.applyOptions({ width: candleChartRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
   equityChart.remove();
      candleChart.remove();
    };
  }, [candlesData, equityData, tradesData, isInitialized, candlesLoading, equityLoading, runId]);

  if (candlesLoading || equityLoading) {
    return (
      <div className="flex items-center justify-center h-[650px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!candlesData?.candles || !equityData?.equity) {
    return (
    <div className="text-center py-8 text-muted-foreground">
        <p>No chart data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
  <CardTitle className="text-sm">Equity Curve</CardTitle>
          <CardDescription>Cumulative P&L over time</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div ref={equityChartRef} />
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
          <div ref={candleChartRef} />
        </CardContent>
      </Card>
    </div>
  );
}
