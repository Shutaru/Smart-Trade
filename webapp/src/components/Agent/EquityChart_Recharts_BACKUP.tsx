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
              console.log("[EquityChart] Fetching equity data...");
         const res = await fetch(`/api/agent/equity`);

    console.log("[EquityChart] Response status:", res.status);

  if (!res.ok) {
         throw new Error("Failed to fetch equity data");
      }

        const result = await res.json();
           console.log("[EquityChart] Received data:", result);
        
  const equityData: EquityPoint[] = result.equity || [];
        console.log("[EquityChart] Equity points:", equityData.length);

           if (equityData.length === 0) {
      setError("No equity data available yet. Start trading!");
       setLoading(false);
     return;
          }

          setData(equityData);
       setError(null);
   setLoading(false);
    } catch (err: any) {
console.error("[EquityChart] Error:", err);
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
    No equity data yet. Agent is starting...
 </div>
   );
    }

    const chartData = data.map((point) => ({
        time: new Date(point.ts).toLocaleTimeString(),
        equity: point.equity,
 }));

    return (
<ResponsiveContainer width="100%" height={300}>
    <LineChart data={chartData}>
   <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis 
          dataKey="time" 
    stroke="#94a3b8"
        style={{ fontSize: 12 }}
   />
     <YAxis 
           stroke="#94a3b8"
       style={{ fontSize: 12 }}
     domain={['auto', 'auto']}
         />
           <Tooltip 
    contentStyle={{ 
            backgroundColor: '#0f172a', 
            border: '1px solid #1e293b',
         borderRadius: '8px',
   color: '#e2e8f0'
        }}
  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
     />
           <Line 
           type="monotone" 
        dataKey="equity" 
        stroke="#3b82f6" 
    strokeWidth={2}
      dot={false}
          animationDuration={300}
       />
            </LineChart>
        </ResponsiveContainer>
    );
}
