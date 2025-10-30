import { useEffect, useState, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, LineData } from "lightweight-charts";

interface EquityChartProps {
    runId: string;
}

interface EquityPoint {
    ts: number;
    equity: number;
    drawdown: number;
}

export function EquityChart({ runId }: EquityChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create chart
        const chart = createChart(chartContainerRef.current, {
   width: chartContainerRef.current.clientWidth,
          height: 300,
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

        const series = chart.addLineSeries({
         color: "#3b82f6",
            lineWidth: 2,
    });

      chartRef.current = chart;
        seriesRef.current = series;

  // Handle resize
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
      const fetchEquity = async () => {
            try {
      const res = await fetch(`/api/agent/equity`);

         if (!res.ok) {
throw new Error("Failed to fetch equity data");
       }

 const data = await res.json();
                const equityData: EquityPoint[] = data.equity || [];

       if (equityData.length === 0) {
  setError("No equity data available yet");
          return;
                }

   // Convert to lightweight-charts format
           const chartData: LineData[] = equityData.map((point) => ({
       time: Math.floor(point.ts / 1000) as any,
      value: point.equity,
  }));

                if (seriesRef.current) {
    seriesRef.current.setData(chartData);
         chartRef.current?.timeScale().fitContent();
           }

      setError(null);
            } catch (err: any) {
     console.error("Failed to fetch equity:", err);
     setError(err.message);
      }
        };

        fetchEquity();
        const interval = setInterval(fetchEquity, 2000);

  return () => clearInterval(interval);
    }, [runId]);

    if (error) {
        return (
         <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                {error}
            </div>
        );
    }

    return <div ref={chartContainerRef} />;
}
