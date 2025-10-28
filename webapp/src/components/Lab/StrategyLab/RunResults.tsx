import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Loader2, CheckCircle2, XCircle, Clock, TrendingUp, TrendingDown, Download } from 'lucide-react';
import { TradesTable } from './TradesTable';
import { TradingChart } from './TradingChart';

interface RunStatus {
  run_id: string;
  name: string;
  status: string;
  progress: number;
  best_score: number | null;
  current_trial: number | null;
  total_trials: number;
  started_at: number | null;
  completed_at: number | null;
}

interface TrialResult {
  trial_id: number;
  params: Record<string, any>;
  metrics: Record<string, number>;
  score: number;
  created_at: number;
}

interface WebSocketMessage {
  ts: number;
  level: string;
  msg: string;
  progress: number | null;
  best_score: number | null;
  status?: string;
}

export function RunResults() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [wsMessages, setWsMessages] = useState<WebSocketMessage[]>([]);
  const [liveProgress, setLiveProgress] = useState<number>(0);
  const [liveStatus, setLiveStatus] = useState<string>('running');

  // Fetch run status
  const { data: statusData, refetch: refetchStatus } = useQuery({
  queryKey: ['run-status', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/status`);
  if (!res.ok) throw new Error('Failed to fetch status');
return res.json() as Promise<RunStatus>;
  },
    refetchInterval: (query) => {
   return query.state.data?.status === 'running' ? 2000 : false;
    }
  });

  // Fetch run results
  const { data: resultsData } = useQuery({
    queryKey: ['run-results', runId],
    queryFn: async () => {
      const res = await fetch(`/api/lab/run/${runId}/results`);
      if (!res.ok) throw new Error('Failed to fetch results');
      const data = await res.json();
    return {
    total: data.total,
     trials: data.trials as TrialResult[]
  };
 },
    enabled: statusData?.status === 'completed'
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!runId) return;

    const wsUrl = `ws://${window.location.hostname}:${window.location.port || '8000'}/ws/lab/run/${runId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[WS] Connected to run:', runId);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setWsMessages(prev => [...prev, message]);

        if (message.progress !== null) {
 setLiveProgress(message.progress * 100);
        }

   if (message.status) {
     setLiveStatus(message.status);
    if (message.status === 'completed' || message.status === 'failed') {
      refetchStatus();
          }
        }
      } catch (err) {
        console.error('[WS] Parse error:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('[WS] Error:', error);
    };

    ws.onclose = () => {
    console.log('[WS] Connection closed');
    };

    return () => {
      ws.close();
    };
  }, [runId, refetchStatus]);

  const getStatusIcon = (status: string) => {
    switch (status) {
case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />;
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      default:
     return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      completed: 'default',
      running: 'secondary',
      failed: 'destructive',
      queued: 'secondary'
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  const formatMetricValue = (value: number): string => {
    if (Math.abs(value) >= 1000) {
      return value.toFixed(0);
    } else if (Math.abs(value) >= 1) {
    return value.toFixed(2);
    } else {
    return value.toFixed(4);
    }
  };

  const topTrial = resultsData?.trials?.[0];

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
   <div className="flex items-center gap-4">
      <Button
                variant="ghost"
       size="icon"
    onClick={() => navigate('/lab/strategy')}
            >
   <ArrowLeft className="h-4 w-4" />
            </Button>
 <div>
        <h1 className="text-3xl font-bold">Run Results</h1>
    <p className="text-sm text-muted-foreground">
  {statusData?.name || 'Loading...'} • Run ID: {runId?.substring(0, 8)}...
        </p>
     </div>
        </div>
<div className="flex items-center gap-2">
            {statusData?.status === 'completed' && (
 <Button
         variant="outline"
       size="sm"
        onClick={() => window.open(`/api/lab/run/${runId}/download`, '_blank')}
   className="gap-2"
    >
        <Download className="h-4 w-4" />
   Download Artifacts
         </Button>
 )}
            {statusData && getStatusBadge(statusData.status)}
   </div>
      </div>

      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
    {getStatusIcon(liveStatus || statusData?.status || 'queued')}
Run Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
       <div className="space-y-2">
   <div className="flex items-center justify-between text-sm">
    <span>Progress</span>
     <span className="font-mono">{liveProgress.toFixed(0)}%</span>
    </div>
 <Progress value={liveProgress} className="h-2" />
  </div>

          {statusData?.best_score !== null && statusData?.best_score !== undefined && (
            <div className="flex items-center justify-between">
   <span className="text-sm text-muted-foreground">Best Score</span>
            <span className="text-2xl font-bold">{statusData.best_score.toFixed(4)}</span>
            </div>
          )}

 <div className="grid grid-cols-2 gap-4 text-sm">
    {statusData?.started_at && (
            <div>
                <span className="text-muted-foreground">Started</span>
            <p className="font-medium">{new Date(statusData.started_at * 1000).toLocaleString()}</p>
        </div>
         )}
       {statusData?.completed_at && (
  <div>
 <span className="text-muted-foreground">Completed</span>
     <p className="font-medium">{new Date(statusData.completed_at * 1000).toLocaleString()}</p>
          </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Section (only show when completed) */}
      {statusData?.status === 'completed' && resultsData && (
   <Tabs defaultValue="metrics">
      <TabsList>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
            <TabsTrigger value="trades">Trades</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
          </TabsList>

       <TabsContent value="metrics" className="space-y-6">
          {topTrial && (
     <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {Object.entries(topTrial.metrics).map(([key, value]) => {
        const isPositive = value > 0;
       const isNegative = value < 0;

     return (
      <Card key={key}>
  <CardHeader className="pb-2">
<CardTitle className="text-sm font-medium text-muted-foreground">
                  {key.replace(/_/g, ' ').toUpperCase()}
     </CardTitle>
     </CardHeader>
             <CardContent>
              <div className="flex items-center gap-2">
   <span className="text-2xl font-bold">{formatMetricValue(value)}</span>
               {isPositive && <TrendingUp className="h-4 w-4 text-green-500" />}
         {isNegative && <TrendingDown className="h-4 w-4 text-destructive" />}
         </div>
                </CardContent>
      </Card>
  );
    })}
      </div>
      )}

        {/* Trading Chart - Equity + Candlesticks */}
        <TradingChart runId={runId!} />
    </TabsContent>

    <TabsContent value="trades">
          <Card>
      <CardHeader>
        <CardTitle>Trades</CardTitle>
    <CardDescription>All executed trades during the backtest</CardDescription>
            </CardHeader>
       <CardContent>
        <TradesTable runId={runId!} />
          </CardContent>
 </Card>
        </TabsContent>

          <TabsContent value="logs">
            <Card>
        <CardHeader>
           <CardTitle>Execution Logs</CardTitle>
 <CardDescription>Real-time logs from the backtest execution</CardDescription>
   </CardHeader>
           <CardContent>
             <div className="bg-muted rounded-lg p-4 max-h-[400px] overflow-auto">
   {wsMessages.length === 0 ? (
           <p className="text-sm text-muted-foreground">No logs yet...</p>
              ) : (
            <div className="space-y-1 font-mono text-xs">
   {wsMessages.map((msg, i) => (
       <div key={i} className="flex gap-2">
      <span className="text-muted-foreground">
            {new Date(msg.ts).toLocaleTimeString()}
      </span>
      <span className={msg.level === 'ERROR' ? 'text-destructive' : ''}>
             [{msg.level}]
        </span>
       <span>{msg.msg}</span>
  </div>
   ))}
            </div>
                  )}
         </div>
      </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

    {/* Loading state */}
    {statusData?.status === 'running' && (
     <Card>
 <CardHeader>
     <CardTitle>Backtest Running...</CardTitle>
            <CardDescription>Please wait while the backtest is being executed</CardDescription>
          </CardHeader>
       <CardContent>
            <div className="bg-muted rounded-lg p-4 max-h-[300px] overflow-auto">
        <div className="space-y-1 font-mono text-xs">
        {wsMessages.map((msg, i) => (
             <div key={i} className="flex gap-2">
   <span className="text-muted-foreground">
             {new Date(msg.ts).toLocaleTimeString()}
    </span>
   <span className={msg.level === 'ERROR' ? 'text-destructive' : ''}>
     [{msg.level}]
       </span>
           <span>{msg.msg}</span>
             </div>
     ))}
   </div>
     </div>
</CardContent>
        </Card>
      )}
    </div>
  );
}
