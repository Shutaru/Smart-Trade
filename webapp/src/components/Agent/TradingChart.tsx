import { useEffect, useState, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";

interface TradingChartProps {
    runId: string;
}

interface Trade {
    timestamp: number;
    symbol: string;
    side: string;
    type: string;
    price: number;
    quantity: number;
}

interface Candle {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export function TradingChart({ runId }: TradingChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    const [candles, setCandles] = useState<Candle[]>([]);
    const [trades, setTrades] = useState<Trade[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 400,
            layout: {
                background: { color: "#0f172a" },
                textColor: "#94a3b8",
            },
            grid: {
                vertLines: { color: "#1e293b" },
                horzLines: { color: "#1e293b" },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: "#10b981",
            downColor: "#ef4444",
            borderVisible: false,
            wickUpColor: "#10b981",
            wickDownColor: "#ef4444",
        });

        chartRef.current = chart;
        candlestickSeriesRef.current = candlestickSeries;

        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, []);

    useEffect(() => {
        const fetchCandles = async () => {
            try {
                console.log("[TradingChart] Fetching candles...");
                const res = await fetch(`/api/agent/candles?limit=200`);

                console.log("[TradingChart] Response status:", res.status);

                if (!res.ok) {
                    throw new Error("Failed to fetch candles");
                }

                const data = await res.json();
                console.log("[TradingChart] Received candles:", data.candles?.length || 0);

                if (!data.candles || data.candles.length === 0) {
                    console.warn("[TradingChart] No candles received");
                    setError("No market data available. Make sure the database has candles.");
                    return;
                }

                setCandles(data.candles);
                setError(null);
            } catch (err: any) {
                console.error("[TradingChart] Error fetching candles:", err);
                setError(err.message);
            }
        };

        fetchCandles();
        const interval = setInterval(fetchCandles, 5000);

        return () => clearInterval(interval);
    }, [runId]);

    useEffect(() => {
        const fetchTrades = async () => {
            try {
                const res = await fetch(`/api/agent/logs/tail?n=100&kind=fill`);

                if (!res.ok) {
                    throw new Error("Failed to fetch trades");
                }

                const data = await res.json();
                const fillEvents = data.events || [];

                const parsedTrades: Trade[] = fillEvents.map((event: any) => ({
                    timestamp: event.ts,
                    symbol: event.data.symbol,
                    side: event.data.side,
                    type: event.data.type || "unknown",
                    price: event.data.price,
                    quantity: event.data.quantity,
                }));

                setTrades(parsedTrades);
            } catch (err: any) {
                console.error("[TradingChart] Error fetching trades:", err);
            }
        };

        fetchTrades();
        const interval = setInterval(fetchTrades, 2000);

        return () => clearInterval(interval);
    }, [runId]);

    useEffect(() => {
        if (!candlestickSeriesRef.current || candles.length === 0) return;

        const chartData: CandlestickData[] = candles.map((candle) => ({
            time: Math.floor(candle.time) as Time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        }));

        candlestickSeriesRef.current.setData(chartData);
        chartRef.current?.timeScale().fitContent();
    }, [candles]);

    useEffect(() => {
        if (!candlestickSeriesRef.current || trades.length === 0) return;

        const markers = trades.map((trade) => ({
            time: Math.floor(trade.timestamp / 1000) as Time,
            position: trade.side === "buy" ? "belowBar" as const : "aboveBar" as const,
            color: trade.side === "buy" ? "#10b981" : "#ef4444",
            shape: trade.side === "buy" ? "arrowUp" as const : "arrowDown" as const,
            text: `${trade.side.toUpperCase()} @ ${trade.price.toFixed(2)}`,
        }));

        candlestickSeriesRef.current.setMarkers(markers);
    }, [trades]);

    if (error) {
        return (
            <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                {error}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div ref={chartContainerRef} />

            <div className="bg-card rounded-lg border border-border p-4">
                <h3 className="text-sm font-medium mb-2">Recent Trades</h3>
                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {trades.length === 0 ? (
                        <p className="text-xs text-muted-foreground">No trades yet</p>
                    ) : (
                        trades.slice(0, 10).map((trade, idx) => (
                            <div
                                key={idx}
                                className="flex items-center justify-between text-xs py-1 border-b border-border last:border-0"
                            >
                                <span className="text-muted-foreground">
                                    {new Date(trade.timestamp).toLocaleTimeString()}
                                </span>
                                <span className={trade.side === "buy" ? "text-green-500" : "text-red-500"}>
                                    {trade.side.toUpperCase()}
                                </span>
                                <span className="font-mono">
                                    {trade.quantity.toFixed(6)}
                                </span>
                                <span className="font-mono">
                                    ${trade.price.toFixed(2)}
                                </span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}