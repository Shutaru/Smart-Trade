import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from 'sonner';

const runBacktest = (params: { days: number }) => {
    return api.post('/api/backtest/run', null, { params });
};

const BacktestCard: React.FC = () => {
    const [days, setDays] = React.useState(365);
    const mutation = useMutation({
        mutationFn: runBacktest,
        onSuccess: () => toast.success("Backtest started successfully!"),
        onError: () => toast.error("Failed to start backtest.")
    });

    return (
        <Card className="shadow-soft hover:shadow-lg transition-shadow">
            <CardHeader>
                <CardTitle>Backtest</CardTitle>
                <CardDescription>Run a single backtest.</CardDescription>
            </CardHeader>
            <CardContent>
                <form id="backtest-form" onSubmit={(e) => {
                    e.preventDefault();
                    mutation.mutate({ days });
                }}>
                    <Label htmlFor="days-backtest">Days</Label>
                    <Input id="days-backtest" type="number" value={days} onChange={(e) => setDays(parseInt(e.target.value))} />
                </form>
            </CardContent>
            <CardFooter>
                <Button form="backtest-form" type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Running..." : "Run"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default BacktestCard;
