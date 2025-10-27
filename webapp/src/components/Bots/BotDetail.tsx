import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft } from 'lucide-react';
import BotKPIs from './BotKPIs';
import BotPerformanceChart from './BotPerformanceChart';
import BotTradesTable from './BotTradesTable';

// Dados de exemplo para desenvolvimento
const mockBotDetail = {
    name: 'BTC Scalper Pro',
    kpis: {
        pnl: 1250.75,
        winRate: 68.4,
        totalTrades: 212,
        sharpe: 1.87
    },
    performanceData: Array.from({ length: 100 }, (_, i) => ({
        time: new Date(Date.now() - (100 - i) * 3600 * 1000).toISOString().split('T')[0],
        value: 1000 + i * 10 + Math.random() * 50 - 25,
    })),
    trades: Array.from({ length: 15 }, (_, i) => ({
        id: i,
        timestamp: new Date(Date.now() - i * 3600 * 24 * 1000).toISOString(),
        symbol: 'BTC/USDT',
        side: i % 2 === 0 ? 'buy' : 'sell',
        price: 50000 + i * 100,
        amount: 0.01,
        pnl: Math.random() * 20 - 10,
    })).reverse(),
};

const fetchBotDetail = async (botId: string) => {
    // const { data } = await api.get(`/api/bots/detail?id=${botId}`);
    // return data;
    console.log(`Fetching data for botId: ${botId}`);
    await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay da API
    return mockBotDetail;
};

const BotDetail: React.FC = () => {
    const { botId } = useParams<{ botId: string }>();
    
    const { data: bot, isLoading } = useQuery({
        queryKey: ['botDetail', botId],
        queryFn: () => fetchBotDetail(botId!),
        enabled: !!botId,
    });

    return (
        <div>
            <Link to="/bots" className="inline-flex items-center mb-6 text-sm font-medium hover:text-primary">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Voltar para a lista de Bots
            </Link>
            
            {isLoading || !bot ? (
                <div className="space-y-4">
                    <Skeleton className="h-8 w-64" />
                    <Skeleton className="h-4 w-48" />
                </div>
            ) : (
                <div>
                    <h1 className="text-3xl font-bold">{bot.name}</h1>
                    <p className="text-muted-foreground">A monitorizar os detalhes do seu bot.</p>
                </div>
            )}

            <div className="mt-8 space-y-8">
                {isLoading || !bot ? <Skeleton className="h-24 w-full" /> : <BotKPIs data={bot.kpis} />}
                {isLoading || !bot ? <Skeleton className="h-80 w-full" /> : <BotPerformanceChart data={bot.performanceData} />}
                {isLoading || !bot ? <Skeleton className="h-96 w-full" /> : <BotTradesTable data={bot.trades} />}
            </div>
        </div>
    );
};

export default BotDetail;
