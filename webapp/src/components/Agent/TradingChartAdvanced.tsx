import { useState, useMemo, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { createChart, ColorType, type IChartApi, type ISeriesApi, type Time } from 'lightweight-charts';
import { TrendingUp, Settings } from 'lucide-react';

const TIMEFRAMES = [
    { value: '1m', label: '1 Minute' },
    { value: '3m', label: '3 Minutes' },
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '30m', label: '30 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' }
];

interface Indicator {
    id: string;
    label: string;
    color: string;
    enabled: boolean;
}

const DEFAULT_INDICATORS: Indicator[] = [
    { id: 'ema20', label: 'EMA 20', color: '#3b82f6', enabled: false },
    { id: 'ema50', label: 'EMA 50', color: '#f59e0b', enabled: false },
    { id: 'sma200', label: 'SMA 200', color: '#10b981', enabled: false },
    { id: 'bb', label: 'Bollinger Bands', color: '#8b5cf6', enabled: false },
];

const TradingChartAdvanced = () => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const indicatorSeriesRef = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());

    const [timeframe, setTimeframe] = useState('5m');
    const [indicators, setIndicators] = useState<Indicator[]>(DEFAULT_INDICATORS);

    const { data, isLoading } = useQuery({
        queryKey: ['agentCandles', timeframe],
        queryFn: async () => {
            const { data } = await api.get(`/api/agent/candles?limit=500&timeframe=${timeframe}`);
            return data;
        },
        refetchInterval: 5000,
    });

    const candles = data?.candles || [];

    // Calculate indicators
    const calculatedIndicators = useMemo(() => {
        if (candles.length === 0) return {};

        const closes = candles.map((c: any) => c.close);
        const times = candles.map((c: any) => c.time as Time);

        const result: Record<string, Array<{ time: Time; value: number }>> = {};

        // EMA 20
        if (indicators.find(i => i.id === 'ema20' && i.enabled)) {
            result.ema20 = calculateEMA(closes, 20).map((value, i) => ({
                time: times[i],
                value
            }));
        }

        // EMA 50
        if (indicators.find(i => i.id === 'ema50' && i.enabled)) {
            result.ema50 = calculateEMA(closes, 50).map((value, i) => ({
                time: times[i],
                value
            }));
        }

        // SMA 200
        if (indicators.find(i => i.id === 'sma200' && i.enabled)) {
            result.sma200 = calculateSMA(closes, 200).map((value, i) => ({
                time: times[i],
                value
            }));
        }

        // Bollinger Bands
        if (indicators.find(i => i.id === 'bb' && i.enabled)) {
            const bb = calculateBollingerBands(closes, 20, 2);
            result.bb_upper = bb.upper.map((value, i) => ({ time: times[i], value }));
            result.bb_middle = bb.middle.map((value, i) => ({ time: times[i], value }));
            result.bb_lower = bb.lower.map((value, i) => ({ time: times[i], value }));
        }

        return result;
    }, [candles, indicators]);

    // Initialize chart
    useEffect(() => {
        if (!chartContainerRef.current || candles.length === 0) return;

        if (!chartRef.current) {
            chartRef.current = createChart(chartContainerRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: 'transparent' },
                    textColor: '#9CA3AF',
                },
                grid: {
                    vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                    horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
                },
                width: chartContainerRef.current.clientWidth,
                height: 400,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                },
                crosshair: {
                    mode: 1,
                },
            });

            candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
                upColor: '#10b981',
                downColor: '#ef4444',
                borderUpColor: '#10b981',
                borderDownColor: '#ef4444',
                wickUpColor: '#10b981',
                wickDownColor: '#ef4444',
            });
        }

        // Update candlestick data
        if (candlestickSeriesRef.current) {
            candlestickSeriesRef.current.setData(candles);
        }

        // Handle window resize
        const handleResize = () => {
            if (chartRef.current && chartContainerRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, [candles]);

    // Update indicators
    useEffect(() => {
        if (!chartRef.current) return;

        // Clear old indicator series
        indicatorSeriesRef.current.forEach((series) => {
            chartRef.current?.removeSeries(series);
        });
        indicatorSeriesRef.current.clear();

        // Add new indicator series
        if (calculatedIndicators.ema20) {
            const series = chartRef.current.addLineSeries({
                color: '#3b82f6',
                lineWidth: 2,
                title: 'EMA 20',
            });
            series.setData(calculatedIndicators.ema20);
            indicatorSeriesRef.current.set('ema20', series);
        }

        if (calculatedIndicators.ema50) {
            const series = chartRef.current.addLineSeries({
                color: '#f59e0b',
                lineWidth: 2,
                title: 'EMA 50',
            });
            series.setData(calculatedIndicators.ema50);
            indicatorSeriesRef.current.set('ema50', series);
        }

        if (calculatedIndicators.sma200) {
            const series = chartRef.current.addLineSeries({
                color: '#10b981',
                lineWidth: 2,
                title: 'SMA 200',
            });
            series.setData(calculatedIndicators.sma200);
            indicatorSeriesRef.current.set('sma200', series);
        }

        if (calculatedIndicators.bb_upper && calculatedIndicators.bb_middle && calculatedIndicators.bb_lower) {
            const upperSeries = chartRef.current.addLineSeries({
                color: '#8b5cf6',
                lineWidth: 1,
                lineStyle: 2,
                title: 'BB Upper',
            });
            upperSeries.setData(calculatedIndicators.bb_upper);
            indicatorSeriesRef.current.set('bb_upper', upperSeries);

            const middleSeries = chartRef.current.addLineSeries({
                color: '#8b5cf6',
                lineWidth: 1,
                title: 'BB Middle',
            });
            middleSeries.setData(calculatedIndicators.bb_middle);
            indicatorSeriesRef.current.set('bb_middle', middleSeries);

            const lowerSeries = chartRef.current.addLineSeries({
                color: '#8b5cf6',
                lineWidth: 1,
                lineStyle: 2,
                title: 'BB Lower',
            });
            lowerSeries.setData(calculatedIndicators.bb_lower);
            indicatorSeriesRef.current.set('bb_lower', lowerSeries);
        }
    }, [calculatedIndicators]);

    const toggleIndicator = (id: string) => {
        setIndicators((prev) =>
            prev.map((ind) => (ind.id === id ? { ...ind, enabled: !ind.enabled } : ind))
        );
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Trading Chart
                    </CardTitle>
                    <CardDescription>Loading chart data...</CardDescription>
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-[400px] w-full" />
                </CardContent>
            </Card>
        );
    }

    if (candles.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Trading Chart
                    </CardTitle>
                    <CardDescription>No candle data available</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                        No market data available. Make sure the database has candles.
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5" />
                            Trading Chart
                        </CardTitle>
                        <CardDescription>
                            {data?.symbol} • {candles.length} candles
                        </CardDescription>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Timeframe Selector */}
                        <Select value={timeframe} onValueChange={setTimeframe}>
                            <SelectTrigger className="w-[140px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {TIMEFRAMES.map((tf) => (
                                    <SelectItem key={tf.value} value={tf.value}>
                                        {tf.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        {/* Indicators Settings */}
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button variant="outline" size="icon">
                                    <Settings className="h-4 w-4" />
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-64">
                                <div className="space-y-4">
                                    <h4 className="font-medium text-sm">Indicators</h4>
                                    {indicators.map((indicator) => (
                                        <div key={indicator.id} className="flex items-center justify-between">
                                            <Label htmlFor={indicator.id} className="flex items-center gap-2">
                                                <div
                                                    className="w-3 h-3 rounded-full"
                                                    style={{ backgroundColor: indicator.color }}
                                                />
                                                {indicator.label}
                                            </Label>
                                            <Switch
                                                id={indicator.id}
                                                checked={indicator.enabled}
                                                onCheckedChange={() => toggleIndicator(indicator.id)}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </PopoverContent>
                        </Popover>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div ref={chartContainerRef} className="w-full" />
            </CardContent>
        </Card>
    );
};

// ============================================================================
// INDICATOR CALCULATIONS
// ============================================================================

function calculateEMA(prices: number[], period: number): number[] {
    const k = 2 / (period + 1);
    const ema: number[] = [];

    const firstSMA = prices.slice(0, period).reduce((sum, p) => sum + p, 0) / period;
    ema[period - 1] = firstSMA;

    for (let i = period; i < prices.length; i++) {
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k);
    }

    for (let i = 0; i < period - 1; i++) {
        ema[i] = NaN;
    }

    return ema;
}

function calculateSMA(prices: number[], period: number): number[] {
    const sma: number[] = [];

    for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
            sma[i] = NaN;
        } else {
            const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
            sma[i] = sum / period;
        }
    }

    return sma;
}

function calculateBollingerBands(prices: number[], period: number, stdDev: number) {
    const sma = calculateSMA(prices, period);
    const upper: number[] = [];
    const middle: number[] = [];
    const lower: number[] = [];

    for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
            upper[i] = NaN;
            middle[i] = NaN;
            lower[i] = NaN;
        } else {
            const slice = prices.slice(i - period + 1, i + 1);
            const mean = sma[i];
            const variance = slice.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / period;
            const std = Math.sqrt(variance);

            middle[i] = mean;
            upper[i] = mean + stdDev * std;
            lower[i] = mean - stdDev * std;
        }
    }

    return { upper, middle, lower };
}

export default TradingChartAdvanced;