import React, { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Skeleton } from '../ui/skeleton';

interface EquityData {
    time: string;
    value: number;
}

const fetchAccountEquity = async (): Promise<EquityData[]> => {
    // Presumindo a existência deste novo endpoint
    const { data } = await api.get('/api/account/equity');
    return data;
};

// Dados de exemplo enquanto o endpoint não existe
const mockEquityData: EquityData[] = Array.from({ length: 100 }, (_, i) => ({
    time: new Date(Date.now() - (100 - i) * 24 * 3600 * 1000).toISOString().split('T')[0],
    value: 10000 + i * 50 + Math.random() * 300 - 150,
}));

const AccountEquityChart: React.FC = () => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chart = useRef<IChartApi | undefined>(undefined);
    const areaSeries = useRef<ISeriesApi<'Area'> | undefined>(undefined);
    
    // Para desenvolvimento, vamos usar os dados de exemplo.
    // Para ligar à API, basta remover a propriedade `initialData`.
    const { data, isLoading } = useQuery({ 
        queryKey: ['accountEquity'], 
        queryFn: fetchAccountEquity,
        initialData: mockEquityData, // Remover esta linha para usar a API
    });

    useEffect(() => {
        if (chartContainerRef.current && data && data.length > 0) {
            chart.current = createChart(chartContainerRef.current, {
                width: chartContainerRef.current.clientWidth,
                height: 300,
                layout: { background: { color: 'transparent' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: 'hsl(var(--border))' }, horzLines: { color: 'hsl(var(--border))' } },
                timeScale: { borderColor: 'hsl(var(--border))' },
                rightPriceScale: { borderColor: 'hsl(var(--border))' },
            });

            areaSeries.current = chart.current.addAreaSeries({
                lineColor: '#2563eb',
                topColor: 'rgba(37, 99, 235, 0.4)',
                bottomColor: 'rgba(37, 99, 235, 0)',
                lineWidth: 2,
            });

            areaSeries.current.setData(data);
            chart.current.timeScale().fitContent();
        }

        return () => chart.current?.remove();
    }, [data]);

    return (
        <Card className="shadow-soft lg:col-span-3">
            <CardHeader>
                <CardTitle>Evolução da Conta</CardTitle>
                <CardDescription>Performance do balanço total ao longo do tempo.</CardDescription>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <Skeleton className="h-[300px] w-full" />
                ) : (
                    <div ref={chartContainerRef} className="h-[300px] w-full" />
                )}
            </CardContent>
        </Card>
    );
};

export default AccountEquityChart;
