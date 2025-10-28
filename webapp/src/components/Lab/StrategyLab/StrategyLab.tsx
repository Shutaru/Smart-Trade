import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Loader2, Play } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

import { DataSelector } from './DataSelector';
import { StrategyBuilder } from './StrategyBuilder';
import { ExitRulesEditor } from './ExitRulesEditor';
import { RiskPanel } from './RiskPanel';
import { ObjectiveEditor } from './ObjectiveEditor';
import { ParamRangesEditor } from './ParamRangesEditor';

const defaultStrategy = {
    name: 'My Strategy',
    long: {
        entry_all: [],
        entry_any: [],
        exit_rules: []
    },
    short: {
        entry_all: [],
        entry_any: [],
        exit_rules: []
    },
    data: {
        exchange: 'bitget',
        symbols: [],
        timeframe: '5m',
        since: Date.now() - 365 * 24 * 60 * 60 * 1000,
        until: Date.now(),
        higher_tf: ['1h', '4h'],
        fees: {
            maker: 0.02,  // 0.02% default for Bitget
            taker: 0.06   // 0.06% default for Bitget
        },
        spread: 0.0  // 0 pips/points default (no spread)
    },
    risk: {
        leverage: 3,
        position_sizing: 'fixed_usd',
        size_value: 1000,
        max_concurrent_positions: 1
    },
    objective: {
        expression: 'sharpe'
    },
    param_space: [],
    warmup_bars: 300
};

export function StrategyLab() {
    const { toast } = useToast();
    const navigate = useNavigate();
    const [strategy, setStrategy] = useState(defaultStrategy);
    const [validationResult, setValidationResult] = useState<any>(null);

    const validateMutation = useMutation({
        mutationFn: async () => {
            const res = await fetch('/api/lab/strategy/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(strategy)
            });
            if (!res.ok) throw new Error('Validation failed');
            return res.json();
        },
        onSuccess: (data) => {
            setValidationResult(data);
            if (data.valid) {
                toast({
                    title: 'Strategy Valid',
                    description: `Requires ${data.features_required.length} features`
                });
            } else {
                toast({
                    title: 'Validation Errors',
                    description: `Found ${data.errors.length} errors`,
                    variant: 'destructive'
                });
            }
        }
    });

    const runBacktestMutation = useMutation({
        mutationFn: async () => {
            const res = await fetch('/api/lab/run/backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(strategy)
            });
            if (!res.ok) throw new Error('Failed to start backtest');
            return res.json();
        },
        onSuccess: (data) => {
            toast({
                title: 'Backtest Started',
                description: `Run ID: ${data.run_id.substring(0, 8)}... - Redirecting to results...`
            });

            setTimeout(() => {
                navigate(`/lab/results/${data.run_id}`);
            }, 1000);
        }
    });

    return (
        <div className="container mx-auto py-8 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Strategy Lab</h1>
                    <p className="text-muted-foreground">Build and backtest quantitative trading strategies</p>
                </div>
                <div className="flex gap-2">
                    <Button
                        onClick={() => validateMutation.mutate()}
                        disabled={validateMutation.isPending}
                        variant="outline"
                    >
                        {validateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Validate
                    </Button>
                    <Button
                        onClick={() => runBacktestMutation.mutate()}
                        disabled={!validationResult?.valid || runBacktestMutation.isPending}
                        className="gap-2"
                    >
                        {runBacktestMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        <Play className="h-4 w-4" />
                        Run Backtest
                    </Button>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Strategy Name</CardTitle>
                </CardHeader>
                <CardContent>
                    <Input
                        value={strategy.name}
                        onChange={(e) => setStrategy({ ...strategy, name: e.target.value })}
                        placeholder="My Strategy"
                    />
                </CardContent>
            </Card>

            {validationResult && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            {validationResult.valid ? (
                                <>
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                    Strategy Valid
                                </>
                            ) : (
                                <>
                                    <XCircle className="h-5 w-5 text-destructive" />
                                    Validation Errors
                                </>
                            )}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {validationResult.valid && (
                            <div className="space-y-2">
                                <Label>Required Features ({validationResult.features_required.length})</Label>
                                <div className="flex flex-wrap gap-2">
                                    {validationResult.features_required.map((feature: string) => (
                                        <Badge key={feature} variant="secondary">{feature}</Badge>
                                    ))}
                                </div>
                            </div>
                        )}

                        {validationResult.errors && validationResult.errors.length > 0 && (
                            <div className="space-y-2">
                                <Label>Errors</Label>
                                <ul className="list-disc list-inside space-y-1 text-sm text-destructive">
                                    {validationResult.errors.map((error: string, i: number) => (
                                        <li key={i}>{error}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            <Tabs defaultValue="data">
                <TabsList className="grid w-full grid-cols-6">
                    <TabsTrigger value="data">Data</TabsTrigger>
                    <TabsTrigger value="strategy">Strategy</TabsTrigger>
                    <TabsTrigger value="exits">Exits</TabsTrigger>
                    <TabsTrigger value="risk">Risk</TabsTrigger>
                    <TabsTrigger value="objective">Objective</TabsTrigger>
                    <TabsTrigger value="preview">Preview</TabsTrigger>
                </TabsList>

                <TabsContent value="data" className="mt-6">
                    <DataSelector
                        value={strategy.data}
                        onChange={(data) => setStrategy({ ...strategy, data })}
                    />
                </TabsContent>

                <TabsContent value="strategy" className="mt-6">
                    <StrategyBuilder
                        value={{ long: strategy.long, short: strategy.short }}
                        onChange={(sides) => setStrategy({ ...strategy, ...sides })}
                    />
                </TabsContent>

                <TabsContent value="exits" className="mt-6">
                    <ExitRulesEditor
                        value={{ long: strategy.long.exit_rules, short: strategy.short.exit_rules }}
                        onChange={(rules) => setStrategy({
                            ...strategy,
                            long: { ...strategy.long, exit_rules: rules.long },
                            short: { ...strategy.short, exit_rules: rules.short }
                        })}
                    />
                </TabsContent>

                <TabsContent value="risk" className="mt-6">
                    <RiskPanel
                        value={strategy.risk}
                        onChange={(risk) => setStrategy({ ...strategy, risk })}
                    />
                </TabsContent>

                <TabsContent value="objective" className="mt-6 space-y-6">
                    <ObjectiveEditor
                        value={strategy.objective}
                        onChange={(objective) => setStrategy({ ...strategy, objective })}
                    />
                    <ParamRangesEditor
                        value={strategy.param_space}
                        onChange={(param_space) => setStrategy({ ...strategy, param_space })}
                    />
                </TabsContent>

                <TabsContent value="preview" className="mt-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Strategy Configuration (JSON)</CardTitle>
                            <CardDescription>Preview the complete strategy configuration</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-[600px] text-xs">
                                {JSON.stringify(strategy, null, 2)}
                            </pre>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}