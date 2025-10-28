import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { InfoIcon } from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';

interface RiskPanelProps {
    value: {
        starting_equity: number;
        max_risk_pct: number;
        leverage: number;
        position_sizing: string;
        size_value: number;
        max_concurrent_positions: number;
    };
    onChange: (value: any) => void;
}

export function RiskPanel({ value, onChange }: RiskPanelProps) {
    // Calculate suggested values based on starting equity
    const suggestedPositionSize = Math.floor((value.starting_equity || 10000) * 0.1); // 10% of equity
    const maxPositionSize = Math.floor((value.starting_equity || 10000) * 0.25); // 25% max
    const conservativeRisk = 0.5; // 0.5% risk per trade
    const moderateRisk = 1.0; // 1.0% risk per trade
    const aggressiveRisk = 2.0; // 2.0% risk per trade

    return (
        <Card>
            <CardHeader>
                <CardTitle>Risk Management</CardTitle>
                <CardDescription>
                    Configure portfolio size, position sizing method, and risk parameters
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Portfolio Size */}
                <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold">Portfolio Configuration</h3>
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="starting-equity">Starting Equity (USDT)</Label>
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs">Initial portfolio value in USDT. This is the base amount used for all position size calculations.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                        <Input
                            id="starting-equity"
                            type="number"
                            value={value.starting_equity || 10000}
                            onChange={(e) => onChange({ ...value, starting_equity: parseFloat(e.target.value) })}
                            placeholder="10000"
                            min={1000}
                            max={10000000}
                        />
                        <p className="text-xs text-muted-foreground">
                            Min: $1,000 | Max: $10M | Current: ${(value.starting_equity || 10000).toLocaleString()}
                        </p>
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label htmlFor="max-risk-pct">Max Risk per Trade (%)</Label>
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p className="max-w-xs">Maximum percentage of portfolio to risk on a single trade. Used for fixed_fraction and volatility sizing.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                        <Input
                            id="max-risk-pct"
                            type="number"
                            value={value.max_risk_pct || 1.0}
                            onChange={(e) => onChange({ ...value, max_risk_pct: parseFloat(e.target.value) })}
                            placeholder="1.0"
                            min={0.1}
                            max={5.0}
                            step={0.1}
                        />
                        <div className="flex gap-2 text-xs">
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => onChange({ ...value, max_risk_pct: conservativeRisk })}
                                className="h-6 text-xs"
                            >
                                Conservative (0.5%)
                            </Button>
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => onChange({ ...value, max_risk_pct: moderateRisk })}
                                className="h-6 text-xs"
                            >
                                Moderate (1%)
                            </Button>
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => onChange({ ...value, max_risk_pct: aggressiveRisk })}
                                className="h-6 text-xs"
                            >
                                Aggressive (2%)
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Position Sizing */}
                <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold">Position Sizing</h3>
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label>Position Sizing Method</Label>
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <div className="max-w-sm space-y-2">
                                            <p><strong>Fixed USD:</strong> Fixed dollar amount per trade</p>
                                            <p><strong>Fixed %:</strong> Fixed percentage of portfolio</p>
                                            <p><strong>Volatility:</strong> ATR-based dynamic sizing</p>
                                            <p><strong>Kelly:</strong> Optimal fraction based on edge</p>
                                        </div>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                        <Select value={value.position_sizing} onValueChange={(v) => onChange({ ...value, position_sizing: v })}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="fixed_usd">Fixed USD</SelectItem>
                                <SelectItem value="fixed_fraction">Fixed Fraction (Risk-based)</SelectItem>
                                <SelectItem value="volatility">Volatility (ATR-based)</SelectItem>
                                <SelectItem value="kelly_truncated">Kelly Criterion</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label>Position Size Value</Label>
                        <Input
                            type="number"
                            value={value.size_value}
                            onChange={(e) => onChange({ ...value, size_value: parseFloat(e.target.value) })}
                            placeholder="1000"
                            min={100}
                        />
                        <div className="flex flex-col gap-2">
                            <p className="text-xs text-muted-foreground">
                                {value.position_sizing === 'fixed_usd' && 'Fixed USD value per trade'}
                                {value.position_sizing === 'fixed_fraction' && `Risk ${value.max_risk_pct || 1}% = $${((value.starting_equity || 10000) * (value.max_risk_pct || 1) / 100).toFixed(2)} per trade`}
                                {value.position_sizing === 'volatility' && `ATR-based with ${value.max_risk_pct || 1}% max risk`}
                                {value.position_sizing === 'kelly_truncated' && 'Optimal Kelly fraction (max 25%)'}
                            </p>
                            {value.position_sizing === 'fixed_usd' && (
                                <div className="flex gap-2 text-xs">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onChange({ ...value, size_value: suggestedPositionSize })}
                                        className="h-6 text-xs"
                                    >
                                        Suggested: ${suggestedPositionSize.toLocaleString()}
                                    </Button>
                                    <span className="text-muted-foreground self-center">
                                        (10% of equity, max: ${maxPositionSize.toLocaleString()})
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Leverage & Limits */}
                <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold">Leverage & Limits</h3>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label>Leverage</Label>
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p className="max-w-xs">Leverage multiplier for position size. Higher leverage = higher risk. Typical: 1x-5x for conservative, 10x-20x for aggressive.</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>
                            <Input
                                type="number"
                                value={value.leverage}
                                onChange={(e) => onChange({ ...value, leverage: parseFloat(e.target.value) })}
                                min={1}
                                max={125}
                                step={1}
                            />
                            <p className="text-xs text-muted-foreground">
                                {value.leverage}x leverage
                            </p>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label>Max Concurrent Positions</Label>
                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <InfoIcon className="h-4 w-4 text-muted-foreground cursor-help" />
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p className="max-w-xs">Maximum number of simultaneous open positions. Limits exposure and diversification.</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>
                            <Input
                                type="number"
                                value={value.max_concurrent_positions}
                                onChange={(e) => onChange({ ...value, max_concurrent_positions: parseInt(e.target.value) })}
                                min={1}
                                max={10}
                            />
                            <p className="text-xs text-muted-foreground">
                                {value.max_concurrent_positions} position{value.max_concurrent_positions > 1 ? 's' : ''}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Risk Summary */}
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg space-y-2">
                    <h4 className="text-sm font-semibold text-blue-600 dark:text-blue-400">Risk Summary</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                            <span className="text-muted-foreground">Portfolio:</span>
                            <span className="ml-2 font-mono">${(value.starting_equity || 10000).toLocaleString()}</span>
                        </div>
                        <div>
                            <span className="text-muted-foreground">Max Risk/Trade:</span>
                            <span className="ml-2 font-mono">{value.max_risk_pct || 1}%</span>
                        </div>
                        <div>
                            <span className="text-muted-foreground">Leverage:</span>
                            <span className="ml-2 font-mono">{value.leverage}x</span>
                        </div>
                        <div>
                            <span className="text-muted-foreground">Max Positions:</span>
                            <span className="ml-2 font-mono">{value.max_concurrent_positions}</span>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}