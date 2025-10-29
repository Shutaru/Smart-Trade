import { createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts';
import React, { useEffect, useRef } from 'react';
import { useCandles } from '@/hooks/useCandles';
import { useWS } from '@/hooks/useWS';
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const CandleChart: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chart = useRef<IChartApi | null>(null);
  const candleSeries = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const { data: initialData, isLoading } = useCandles();

  useEffect(() => {
    if (chartContainerRef.current) {
      chart.current = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: 500,
        layout: {
          background: { color: 'transparent' },
          textColor: '#d1d4dc',
        },
        grid: {
          vertLines: { color: 'hsl(var(--border))' },
          horzLines: { color: 'hsl(var(--border))' },
        },
        timeScale: {
          borderColor: 'hsl(var(--border))',
        },
      });

      candleSeries.current = chart.current.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderDownColor: '#ef5350',
        borderUpColor: '#26a69a',
        wickDownColor: '#ef5350',
        wickUpColor: '#26a69a',
      });

      if (initialData) {
        candleSeries.current.setData(initialData);
      }
    }

    return () => {
      if (chart.current) {
        chart.current.remove();
        chart.current = null;
      }
    };
  }, [initialData]);

  useWS('ws://127.0.0.1:8000/ws/price', (data) => {
    if (candleSeries.current) {
      candleSeries.current.update(data);
    }
  });

  return (
    <Card className="shadow-soft">
        <CardContent className="p-0">
            {isLoading ? (
                <Skeleton className="w-full h-[500px]" />
            ) : (
                <div ref={chartContainerRef} className="w-full h-[500px]" />
            )}
        </CardContent>
    </Card>
  );
};

export default CandleChart;
