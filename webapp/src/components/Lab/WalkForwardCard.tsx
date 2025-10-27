import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from 'sonner';

const runWalkForward = () => {
    return api.post('/api/wf/run');
};

const WalkForwardCard: React.FC = () => {
    const mutation = useMutation({
        mutationFn: runWalkForward,
        onSuccess: () => toast.success("Walk forward analysis started!"),
        onError: () => toast.error("Failed to start walk forward analysis.")
    });

    return (
        <Card className="shadow-soft hover:shadow-lg transition-shadow">
            <CardHeader>
                <CardTitle>Walk Forward</CardTitle>
                <CardDescription>Test strategy robustness.</CardDescription>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground">This will run a walk forward analysis on the current configuration.</p>
            </CardContent>
            <CardFooter>
                <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
                    {mutation.isPending ? "Running..." : "Run"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default WalkForwardCard;
