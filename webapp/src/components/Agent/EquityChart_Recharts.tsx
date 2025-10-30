import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface EquityChartProps {
    runId: string;
}

interface EquityPoint {
    ts: number;
    equity: number;
    drawdown: number;
}

export function EquityChart({ runId }: EquityChartProps) {
    const [data, setData] = useState<EquityPoint[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchEquity = async () => {
    try {
    const res = await fetch(`/api/agent/equity`);

      if (!res.ok) {
      throw new Error("Failed to fetch equity data");
       }

        const result = await res.json();
       const equityData: EquityPoint[] = result.equity || [];

              if (equityData.length === 0) {
         setError("No equity data available yet");
   setLoading(false);
      return;
     }

         setData(equityData);
      setError(null);
                setLoading(false);
            } catch (err: any) {
     console.error("Failed to fetch equity:", err);
  setError(err.message);
       setLoading(false);
            }
        };

        fetchEquity();
    const interval = setInterval(fetchEquity, 2000);

        return () => clearInterval(interval);
    }, [runId]);

    if (loading) {
  return (
   <div className="flex items-center justify-center h-[300px] text-muted-foreground">
   Loading equity curve...
   </div>
   );
    }

    if (error) {
      return (
 <div className="flex items-center justify-center h-[300px] text-muted-foreground">
   {error}
        </div>
        );
    }

    if (data.length === 0) {
     return (
    <div className="flex items-center justify-center h-[300px] text-muted-foreground">
      No equity data yet. Start trading to see the curve!
        </div>
);
    }

    // Format data for Recharts
    const chartData = data.map((point) => ({
        time: new Date(point.ts).toLocaleTimeString(),
        equity: point.equity,
        drawdown: point.drawdown,
    }));

    return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
<XAxis 
            dataKey="time" 
     className="text-xs" 
       tick={{ fontSize: 12 }}
                />
                <YAxis 
        className="text-xs" 
       tick={{ fontSize: 12 }}
   domain={['auto', 'auto']}
  />
         <Tooltip 
           contentStyle={{ 
         backgroundColor: 'hsl(var(--popover))', 
            border: '1px solid hsl(var(--border))',
         borderRadius: '8px'
        }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
         />
                <Line 
                    type="monotone" 
      dataKey="equity" 
stroke="#2563eb" 
     strokeWidth={2}
       dot={false}
    animationDuration={300}
  />
            </LineChart>
 </ResponsiveContainer>
    );
}
