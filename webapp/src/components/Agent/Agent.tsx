import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Square, Activity, TrendingUp, AlertCircle } from "lucide-react";
import { EquityChart } from "./EquityChart";
import TradingChartAdvanced from "./TradingChartAdvanced";

interface AgentStatus {
    running: boolean;
    run_id?: string;
    started_at?: number;
    uptime_seconds?: number;
    iteration?: number;
    config?: {
        exchange: string;
        symbols: string[];
        timeframe: string;
        policy: string;
    };
    portfolio?: {
        equity: number;
        cash: number;
        realized_pnl: number;
        unrealized_pnl: number;
        total_pnl: number;
        num_positions: number;
        exposure_pct: number;
    };
    positions?: Array<{
        symbol: string;
        side: string;
        quantity: number;
        entry_price: number;
        current_price: number;
        unrealized_pnl: number;
        pnl_pct: number;
    }>;
    pending_orders?: number;
    risk?: {
        kill_switch_active: boolean;
        current_drawdown_pct: number;
        violations_count: number;
    };
    last_error?: string;
}

interface LogEvent {
    ts: number;
    kind: string;
    data: any;
}

export default function Agent() {
    const [status, setStatus] = useState<AgentStatus | null>(null);
    const [logs, setLogs] = useState<LogEvent[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch("/api/agent/status");
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
                setError(null);
            }
        } catch (err) {
            console.error("Failed to fetch status:", err);
        }
    }, []);

    const fetchLogs = useCallback(async () => {
        if (!status?.running) return;

        try {
            const res = await fetch("/api/agent/logs/tail?n=50");
            if (res.ok) {
                const data = await res.json();
                setLogs(data.events || []);
            }
        } catch (err) {
            console.error("Failed to fetch logs:", err);
        }
    }, [status?.running]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    useEffect(() => {
        if (status?.running) {
            fetchLogs();
            const interval = setInterval(fetchLogs, 2000);
            return () => clearInterval(interval);
        }
    }, [status?.running, fetchLogs]);

    const handleStart = async () => {
        setLoading(true);
        setError(null);

        try {
            const res = await fetch("/api/agent/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    config_path: "configs/agent_llm.yaml",
                }),
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Failed to start agent");
            }

            await fetchStatus();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async () => {
        setLoading(true);
        setError(null);

        try {
            const res = await fetch("/api/agent/stop", { method: "POST" });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Failed to stop agent");
            }

            await fetchStatus();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatUptime = (seconds: number) => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${h}h ${m}m ${s}s`;
    };

    const getLogIcon = (kind: string) => {
        switch (kind) {
            case "fill":
                return "💰";
            case "action":
                return "🎯";
            case "error":
                return "❌";
            case "risk_rejection":
                return "🚨";
            default:
                return "📝";
        }
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Activity className="h-8 w-8" />
                        Agent Runner
                        <Badge variant="outline" className="ml-2">
                            Beta
                        </Badge>
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Autonomous trading agent with LLM decision-making
                    </p>
                </div>

                <div className="flex gap-2">
                    {!status?.running ? (
                        <Button onClick={handleStart} disabled={loading} size="lg">
                            <Play className="mr-2 h-4 w-4" />
                            Start Agent
                        </Button>
                    ) : (
                        <Button
                            onClick={handleStop}
                            disabled={loading}
                            variant="destructive"
                            size="lg"
                        >
                            <Square className="mr-2 h-4 w-4" />
                            Stop Agent
                        </Button>
                    )}
                </div>
            </div>

            {/* Error Alert */}
            {error && (
                <Card className="border-destructive">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 text-destructive">
                            <AlertCircle className="h-5 w-5" />
                            <span className="font-medium">{error}</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Status Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Running</span>
                                <Badge variant={status?.running ? "default" : "secondary"}>
                                    {status?.running ? "Active" : "Stopped"}
                                </Badge>
                            </div>

                            {status?.running && (
                                <>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Uptime</span>
                                        <span className="text-sm font-mono">
                                            {formatUptime(status.uptime_seconds || 0)}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Iteration</span>
                                        <span className="text-sm font-mono">
                                            {status.iteration || 0}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Policy</span>
                                        <Badge variant="outline">
                                            {status.config?.policy || "N/A"}
                                        </Badge>
                                    </div>

                                    {status.risk?.kill_switch_active && (
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-destructive font-medium">
                                                🚨 Kill Switch
                                            </span>
                                            <Badge variant="destructive">ACTIVE</Badge>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Portfolio Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">Portfolio</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {status?.portfolio ? (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">Equity</span>
                                    <span className="text-lg font-bold">
                                        ${status.portfolio.equity.toFixed(2)}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">Total PnL</span>
                                    <span
                                        className={`text-sm font-medium ${status.portfolio.total_pnl >= 0
                                                ? "text-green-600"
                                                : "text-red-600"
                                            }`}
                                    >
                                        {status.portfolio.total_pnl >= 0 ? "+" : ""}$
                                        {status.portfolio.total_pnl.toFixed(2)}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">Positions</span>
                                    <span className="text-sm font-mono">
                                        {status.portfolio.num_positions}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">Exposure</span>
                                    <span className="text-sm font-mono">
                                        {status.portfolio.exposure_pct.toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">No data</p>
                        )}
                    </CardContent>
                </Card>

                {/* Risk Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">Risk</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {status?.risk ? (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">Drawdown</span>
                                    <span
                                        className={`text-sm font-medium ${status.risk.current_drawdown_pct < -3
                                                ? "text-red-600"
                                                : ""
                                            }`}
                                    >
                                        {status.risk.current_drawdown_pct.toFixed(2)}%
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">Violations</span>
                                    <span className="text-sm font-mono">
                                        {status.risk.violations_count}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">
                                        Pending Orders
                                    </span>
                                    <span className="text-sm font-mono">
                                        {status.pending_orders || 0}
                                    </span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">No data</p>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Equity Chart */}
            {status?.running && status?.run_id && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5" />
                            Equity Curve
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <EquityChart runId={status.run_id} />
                    </CardContent>
                </Card>
            )}

            {/* Trading Chart with Candles + Trades */}
            {status?.running && status?.run_id && (
                <TradingChartAdvanced />
            )}

            {/* Positions Table */}
            {status?.positions && status.positions.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Open Positions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {status.positions.map((pos, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between border-b pb-2"
                                >
                                    <div>
                                        <span className="font-medium">{pos.symbol}</span>
                                        <Badge
                                            variant={
                                                pos.side === "long" ? "default" : "destructive"
                                            }
                                            className="ml-2"
                                        >
                                            {pos.side.toUpperCase()}
                                        </Badge>
                                    </div>
                                    <div className="text-right">
                                        <div
                                            className={`font-medium ${pos.pnl_pct >= 0
                                                    ? "text-green-600"
                                                    : "text-red-600"
                                                }`}
                                        >
                                            {pos.pnl_pct >= 0 ? "+" : ""}
                                            {pos.pnl_pct.toFixed(2)}%
                                        </div>
                                        <div className="text-sm text-muted-foreground">
                                            ${pos.unrealized_pnl.toFixed(2)}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Logs */}
            <Card>
                <CardHeader>
                    <CardTitle>Event Log</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] overflow-y-auto">
                        <div className="space-y-2 font-mono text-xs">
                            {logs.length === 0 ? (
                                <p className="text-muted-foreground">No logs yet...</p>
                            ) : (
                                logs.map((log, idx) => (
                                    <div key={idx} className="flex gap-2">
                                        <span>{getLogIcon(log.kind)}</span>
                                        <span className="text-muted-foreground">
                                            {new Date(log.ts).toLocaleTimeString()}
                                        </span>
                                        <span className="font-medium">{log.kind}</span>
                                        <span className="text-muted-foreground">
                                            {JSON.stringify(log.data).slice(0, 100)}...
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}