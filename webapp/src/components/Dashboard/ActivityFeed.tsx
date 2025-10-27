import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from '@/components/ui/skeleton';
import { Bell, Zap } from 'lucide-react';

const fetchAlerts = async () => {
    const { data } = await api.get('/api/alerts/list');
    return data;
};

// Dados de exemplo
const mockAlerts = [
    { id: 1, timestamp: new Date().toISOString(), message: "Bot 'BTC Scalper' iniciado em modo Live." },
    { id: 2, timestamp: new Date(Date.now() - 3600*1000).toISOString(), message: "Ordem de Venda para ETH/USDT executada." },
    { id: 3, timestamp: new Date(Date.now() - 3600*2*1000).toISOString(), message: "Alerta de Preço: BTC ultrapassou $52,000." },
];

const ActivityFeed: React.FC = () => {
    // Usar mockAlerts por enquanto. Remover `initialData` para usar a API.
    const { data: alerts, isLoading } = useQuery({ 
        queryKey: ['alerts'], 
        queryFn: fetchAlerts,
        initialData: mockAlerts,
    });

    const getIcon = (message: string) => {
        if (message.toLowerCase().includes('bot')) return <Bell className="h-4 w-4 text-blue-500" />;
        if (message.toLowerCase().includes('ordem')) return <Zap className="h-4 w-4 text-yellow-500" />;
        return <Bell className="h-4 w-4 text-muted-foreground" />;
    }

    return (
        <Card className="shadow-soft lg:col-span-2">
            <CardHeader>
                <CardTitle>Feed de Atividade</CardTitle>
                <CardDescription>Últimos eventos e alertas.</CardDescription>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <div className="space-y-4">
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                    </div>
                ) : alerts && alerts.length > 0 ? (
                    <div className="space-y-4">
                        {alerts.map((alert: any) => (
                            <div key={alert.id} className="flex items-start space-x-3">
                                <div className="mt-1">{getIcon(alert.message)}</div>
                                <div>
                                    <p className="text-sm">{alert.message}</p>
                                    <p className="text-xs text-muted-foreground">
                                        {new Date(alert.timestamp).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center text-muted-foreground h-24 flex items-center justify-center">
                        Nenhuma atividade recente.
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default ActivityFeed;
