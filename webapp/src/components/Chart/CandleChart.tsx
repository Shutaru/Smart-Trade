import { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi, type CandlestickData, type HistogramSeriesPartialOptions } from 'lightweight-charts';

const sampleData: CandlestickData[] = Array.from({ length: 120 }, (_, index) => {
  const open = 60000 + index * 5 + Math.sin(index / 5) * 120;
  const close = open + Math.sin(index / 3) * 80;
  const high = Math.max(open, close) + Math.random() * 120;
  const low = Math.min(open, close) - Math.random() * 120;
  return {
    time: (1700000000 + index * 300) as CandlestickData['time'],
    open,
    high,
    low,
    close,
  };
});

export const CandleChart = (): JSX.Element => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#cbd5f5',
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(47, 61, 96, 0.2)' },
        horzLines: { color: 'rgba(47, 61, 96, 0.2)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(47, 61, 96, 0.6)',
      },
      timeScale: {
        borderColor: 'rgba(47, 61, 96, 0.6)',
      },
      crosshair: {
        mode: 1,
      },
    });

    chart.applyOptions({
      autoSize: true,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    const volumeSeriesOptions: HistogramSeriesPartialOptions = {
      color: 'rgba(79, 70, 229, 0.5)',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    };
    const volumeSeries = chart.addHistogramSeries(volumeSeriesOptions);
    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    candleSeries.setData(sampleData);
    volumeSeries.setData(
      sampleData.map((candle) => ({
        time: candle.time,
        value: Math.abs(candle.close - candle.open) * 2,
        color: candle.close >= candle.open ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)',
      })),
    );

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({
        width: containerRef.current?.clientWidth ?? 0,
        height: containerRef.current?.clientHeight ?? 0,
      });
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, []);

  return <div ref={containerRef} className="h-[420px] w-full" />;
};
