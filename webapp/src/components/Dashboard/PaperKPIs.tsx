import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign, Activity } from 'lucide-react';

const fetchPaperStatus = async () => {
  const { data } = await api.get('/api/paper/status');
    return data;
};

const KpiCard: React.FC<{ title: string; value: string; icon: React.ReactNode; change?: string; changeColor?: string }> = 
({ title, value, icon, change, changeColor }) => (
    <Card className="shadow-soft">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
 {icon}
        </CardHeader>
        <CardContent>
<div className="text-2xl font-bold">{value}</div>
  {change && <p className={`text-xs ${changeColor}`}>{change}</p>}
        </CardContent>
    </Card>
);

const PaperKPIs: React.FC = () => {
    const { data, isLoading } = useQuery({ 
        queryKey: ['paperStatus'], 
        queryFn: fetchPaperStatus,
        refetchInterval: 5000 // Atualiza a cada 5 segundos
    });

    if (isLoading) {
 return (
    <>
        <Skeleton className="h-28 w-full" />
     <Skeleton className="h-28 w-full" />
            </>
     );
    }

    const equity = data?.equity || 0;
    const startEquity = data?.start_equity || 100000;
    const totalPnL = equity - startEquity;
  const totalPnLPct = ((equity / startEquity - 1) * 100);
    const isProfitable = totalPnL >= 0;

    const totalTrades = data?.total_trades || 0;
    const winRate = data?.win_rate || 0;

    return (
        <>
      <KpiCard 
            title="Equity (Paper)" 
  value={`$${equity.toFixed(2)}`}
   icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
  change={`${isProfitable ? '+' : ''}$${totalPnL.toFixed(2)} (${totalPnLPct.toFixed(2)}%)`}
        changeColor={isProfitable ? 'text-green-500' : 'text-red-500'}
            />
 <KpiCard 
     title="Performance" 
value={`${totalTrades} trades`}
   icon={<Activity className="h-4 w-4 text-muted-foreground" />}
   change={`Win Rate: ${winRate.toFixed(1)}%`}
      changeColor={winRate >= 50 ? 'text-green-500' : 'text-red-500'}
   />
 </>
    );
};

export default PaperKPIs;
