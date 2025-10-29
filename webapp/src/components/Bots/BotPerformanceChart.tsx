import React, { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts';
import { Card, CardContent } from "@/components/ui/card";

interface BotPerformanceChartProps {
    data: { time: string; value: number }[]; // Assumindo dados de equity
}

const BotPerformanceChart: React.FC<BotPerformanceChartProps> = ({ data }) => {
    const chartContainerRef = useRef<HTMLDivElement | null>(null);
    const chart = useRef<IChartApi | null>(null);
    const lineSeries = useRef<ISeriesApi<'Line'> | null>(null);

    useEffect(() => {
        if (chartContainerRef.current && data.length > 0) {
            chart.current = createChart(chartContainerRef.current, {
                width: chartContainerRef.current.clientWidth,
                height: 300,
                layout: { background: { color: 'transparent' }, textColor: '#d1d4dc' },
                grid: { vertLines: { color: 'hsl(var(--border))' }, horzLines: { color: 'hsl(var(--border))' } },
                timeScale: { borderColor: 'hsl(var(--border))' },
            });

            lineSeries.current = chart.current.addLineSeries({ color: '#2563eb', lineWidth: 2 });
            lineSeries.current.setData(data);
            chart.current.timeScale().fitContent();
        }

        return () => {
            if (chart.current) {
                chart.current.remove();
                chart.current = null;
            }
        };
    }, [data]);

    return (
        <Card className="shadow-soft">
            <CardContent ref={chartContainerRef} className="p-2 h-[300px]" />
        </Card>
    );
};

export default BotPerformanceChart;
