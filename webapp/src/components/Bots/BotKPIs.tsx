import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, Percent, CheckCircle, TrendingUp } from 'lucide-react';

interface BotKPIsProps {
    data: {
        pnl: number;
        winRate: number;
        totalTrades: number;
        sharpe: number;
    };
}

const KpiCard: React.FC<{ title: string; value: string; icon: React.ReactNode; color: string }> = ({ title, value, icon, color }) => (
    <Card className="shadow-soft">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
            {icon}
        </CardHeader>
        <CardContent>
            <div className={`text-2xl font-bold ${color}`}>
                {value}
            </div>
        </CardContent>
    </Card>
);


const BotKPIs: React.FC<BotKPIsProps> = ({ data }) => {
    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <KpiCard title="PnL Total (USDT)" value={`$${data.pnl.toFixed(2)}`} icon={<DollarSign className="h-4 w-4 text-muted-foreground" />} color={data.pnl > 0 ? 'text-green-500' : 'text-red-500'} />
            <KpiCard title="Win Rate" value={`${data.winRate.toFixed(1)}%`} icon={<CheckCircle className="h-4 w-4 text-muted-foreground" />} color="text-foreground" />
            <KpiCard title="Total de Trades" value={String(data.totalTrades)} icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />} color="text-foreground" />
            <KpiCard title="Sharpe Ratio" value={data.sharpe.toFixed(2)} icon={<Percent className="h-4 w-4 text-muted-foreground" />} color="text-foreground" />
        </div>
    );
};

export default BotKPIs;
