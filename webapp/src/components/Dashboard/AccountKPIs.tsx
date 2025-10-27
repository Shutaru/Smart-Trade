import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';

const fetchAccountStatus = async () => {
    const { data } = await api.get('/api/live/status');
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

const AccountKPIs: React.FC = () => {
    const { data, isLoading } = useQuery({ queryKey: ['accountStatus'], queryFn: fetchAccountStatus });

    if (isLoading) {
        return (
            <>
                <Skeleton className="h-28 w-full" />
                <Skeleton className="h-28 w-full" />
            </>
        )
    }

    const todayIncome = data?.today_income || 0;
    const isIncomePositive = todayIncome >= 0;

    return (
        <>
            <KpiCard 
                title="Balanço Total (USD)" 
                value={`$${(data?.total_balance || 0).toFixed(2)}`}
                icon={<DollarSign className="h-4 w-4 text-muted-foreground" />} 
            />
            <KpiCard 
                title="Lucro do Dia" 
                value={`$${todayIncome.toFixed(2)}`}
                icon={isIncomePositive ? <TrendingUp className="h-4 w-4 text-muted-foreground" /> : <TrendingDown className="h-4 w-4 text-muted-foreground" />}
                change={`${isIncomePositive ? '+' : ''}${(data?.daily_change_perc || 0).toFixed(2)}% hoje`}
                changeColor={isIncomePositive ? 'text-green-500' : 'text-red-500'}
            />
        </>
    );
};

export default AccountKPIs;
