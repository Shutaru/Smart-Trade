import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from 'sonner';

const runGridSearch = (params: { days: number, max_combos: number, sort: string }) => {
    return api.post('/api/grid/run', null, { params });
};

const GridSearchCard: React.FC = () => {
    const [days, setDays] = React.useState(365);
    const [maxCombos, setMaxCombos] = React.useState(100);
    const mutation = useMutation({
        mutationFn: runGridSearch,
        onSuccess: () => toast.success("Grid search started successfully!"),
        onError: () => toast.error("Failed to start grid search.")
    });

    return (
        <Card className="shadow-soft hover:shadow-lg transition-shadow">
            <CardHeader>
                <CardTitle>Grid Search</CardTitle>
                <CardDescription>Find the best parameters.</CardDescription>
            </CardHeader>
            <CardContent>
                <form id="grid-form" onSubmit={(e) => {
                    e.preventDefault();
                    mutation.mutate({ days, max_combos: maxCombos, sort: "sharpe_ann" });
                }} className="space-y-4">
                    <div>
                        <Label htmlFor="days-grid">Days</Label>
                        <Input id="days-grid" type="number" value={days} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDays(parseInt(e.target.value))} />
                    </div>
                    <div>
                        <Label htmlFor="maxCombos">Max Combos</Label>
                        <Input id="maxCombos" type="number" value={maxCombos} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMaxCombos(parseInt(e.target.value))} />
                    </div>
                </form>
            </CardContent>
            <CardFooter>
                <Button form="grid-form" type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Running..." : "Run"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default GridSearchCard;
