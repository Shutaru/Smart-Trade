import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from 'sonner';

const runOptuna = (params: { trials: number, days: number }) => {
    return api.post('/api/ml_optuna/run', null, { params });
};

const OptunaCard: React.FC = () => {
    const [trials, setTrials] = React.useState(100);
    const [days, setDays] = React.useState(365);
    const mutation = useMutation({
        mutationFn: runOptuna,
        onSuccess: () => toast.success("Optuna optimization started!"),
        onError: () => toast.error("Failed to start Optuna optimization.")
    });

    return (
        <Card className="shadow-soft hover:shadow-lg transition-shadow">
            <CardHeader>
                <CardTitle>Optuna</CardTitle>
                <CardDescription>ML parameter optimization.</CardDescription>
            </CardHeader>
            <CardContent>
                <form id="optuna-form" onSubmit={(e) => {
                    e.preventDefault();
                    mutation.mutate({ trials, days });
                }} className="space-y-4">
                    <div>
                        <Label htmlFor="trials">Trials</Label>
                        <Input id="trials" type="number" value={trials} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTrials(parseInt(e.target.value))} />
                    </div>
                    <div>
                        <Label htmlFor="days-optuna">Days</Label>
                        <Input id="days-optuna" type="number" value={days} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDays(parseInt(e.target.value))} />
                    </div>
                </form>
            </CardContent>
            <CardFooter>
                <Button form="optuna-form" type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Running..." : "Run"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default OptunaCard;
