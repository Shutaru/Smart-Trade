import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from 'sonner';

const backfill = (params: { symbol: string, days: number }) => {
    return api.post('/api/bitget/backfill', null, { params });
};

const Backfill: React.FC = () => {
    const [symbol, setSymbol] = React.useState('');
    const [days, setDays] = React.useState(30);
    const queryClient = useQueryClient();
    const mutation = useMutation({
        mutationFn: backfill,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['candles'] });
            toast.success("Backfill started successfully!");
        },
        onError: () => {
            toast.error("Failed to start backfill.");
        }
    });

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Backfill Data</CardTitle>
                <CardDescription>Download historical data for a symbol.</CardDescription>
            </CardHeader>
            <CardContent>
                <form id="backfill-form" onSubmit={(e) => {
                    e.preventDefault();
                    mutation.mutate({ symbol, days });
                }} className="space-y-4">
                    <div>
                        <Label htmlFor="symbol-backfill">Symbol</Label>
                        <Input id="symbol-backfill" value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="e.g., BTC/USDT" />
                    </div>
                    <div>
                        <Label htmlFor="days-backfill">Days</Label>
                        <Input id="days-backfill" type="number" value={days} onChange={(e) => setDays(parseInt(e.target.value))} />
                    </div>
                </form>
            </CardContent>
            <CardFooter>
                <Button form="backfill-form" type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Backfilling..." : "Start Backfill"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default Backfill;
