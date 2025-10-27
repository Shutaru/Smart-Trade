import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';

interface AccountEquityChartProps {
    mode: 'live' | 'paper';
}

const fetchLiveEquity = async () => {
    const { data } = await api.get('/api/live/equity_curve');
    return data.curve || [];
};

const fetchPaperEquity = async () => {
    const { data } = await api.get('/api/paper/equity_curve');
    return data.curve || [];
};

const AccountEquityChart: React.FC<AccountEquityChartProps> = ({ mode }) => {
    const { data, isLoading } = useQuery({ 
        queryKey: ['equityCurve', mode], 
      queryFn: mode === 'live' ? fetchLiveEquity : fetchPaperEquity,
        refetchInterval: 10000 // Atualiza a cada 10 segundos
    });

    if (isLoading) {
        return (
            <Card className="shadow-soft">
      <CardHeader>
      <CardTitle>Equity Curve</CardTitle>
           <CardDescription>{mode === 'live' ? 'Live Trading' : 'Paper Trading'}</CardDescription>
                </CardHeader>
            <CardContent>
        <Skeleton className="h-80 w-full" />
                </CardContent>
    </Card>
        );
    }

    const chartData = (data || []).map((point: any) => ({
 date: new Date(point.ts * 1000).toLocaleDateString(),
     equity: point.equity
    }));

  return (
<Card className="shadow-soft">
            <CardHeader>
        <CardTitle>Equity Curve</CardTitle>
          <CardDescription>
            {mode === 'live' ? '💰 Live Trading Account' : '🧪 Paper Trading Simulation'}
           </CardDescription>
       </CardHeader>
     <CardContent>
     {chartData.length === 0 ? (
               <div className="h-80 flex items-center justify-center text-muted-foreground">
        Sem dados disponíveis
  </div>
          ) : (
          <ResponsiveContainer width="100%" height={320}>
         <AreaChart data={chartData}>
   <defs>
         <linearGradient id={`colorEquity-${mode}`} x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%" stopColor={mode === 'live' ? '#10b981' : '#3b82f6'} stopOpacity={0.3} />
            <stop offset="95%" stopColor={mode === 'live' ? '#10b981' : '#3b82f6'} stopOpacity={0} />
</linearGradient>
        </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
           <XAxis dataKey="date" className="text-xs" />
    <YAxis className="text-xs" />
   <Tooltip 
        contentStyle={{ 
 backgroundColor: 'hsl(var(--popover))', 
           border: '1px solid hsl(var(--border))',
              borderRadius: '8px'
           }}
  />
          <Area 
         type="monotone" 
     dataKey="equity" 
     stroke={mode === 'live' ? '#10b981' : '#3b82f6'} 
              strokeWidth={2}
    fillOpacity={1} 
     fill={`url(#colorEquity-${mode})`} 
   />
         </AreaChart>
    </ResponsiveContainer>
       )}
            </CardContent>
        </Card>
    );
};

export default AccountEquityChart;
