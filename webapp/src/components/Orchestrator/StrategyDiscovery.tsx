import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Rocket, Play, TrendingUp, Settings, CheckCircle2, AlertCircle, RefreshCw, Zap, Database, Clock } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api';

interface DiscoveryRequest {
    symbols: string[];
    exchange: string;
    timeframe: string;
    days: number;
    optimization_trials: number;
    top_n_to_optimize: number;
    auto_deploy_paper: boolean;
}

interface DiscoveryStatus {
    run_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    symbols: string[];
    current_symbol?: string;
    progress: number;
    best_strategies?: Record<string, any>;
    started_at: string;
    completed_at?: string;
    error?: string;
}

interface CachedResult {
    symbol: string;
    timeframe: string;
    strategy: string;
    optimized_profit: number;
    score: number;
    cached_at: string;
}

export default function StrategyDiscovery() {
    const [symbols, setSymbols] = useState<string[]>([]);
    const [symbolInput, setSymbolInput] = useState('');
    const [exchange, setExchange] = useState<string>('bitget');
    const [timeframe, setTimeframe] = useState<string>('5m');
    const [days, setDays] = useState(90);
    const [trials, setTrials] = useState(50);
    const [topN, setTopN] = useState(5);
    const [runId, setRunId] = useState<string | null>(null);
  
    // Cache verification state
    const [showCacheDialog, setShowCacheDialog] = useState(false);
  const [cachedResults, setCachedResults] = useState<CachedResult[]>([]);
    const [pendingRequest, setPendingRequest] = useState<DiscoveryRequest | null>(null);

    // DEBUG
    console.log('StrategyDiscovery render', { runId, symbols, exchange, timeframe });

    const { data: availableSymbols, isLoading: loadingSymbols, refetch: refetchSymbols } = useQuery<string[]>({
        queryKey: ['available-symbols', exchange],
        queryFn: async () => {
       const response = await api.get(`/api/lab/symbols?exchange=${exchange}`);
        return response.data.symbols;
        },
enabled: !!exchange
    });

    const startDiscovery = useMutation({
        mutationFn: async (request: DiscoveryRequest) => {
        const response = await api.post('/api/orchestrator/discover', request);
   return response.data;
        },
        onSuccess: (data) => {
            setRunId(data.run_id);
    toast.success(`Discovery started! Run ID: ${data.run_id}`);
     },
        onError: (error: any) => {
   toast.error(error.response?.data?.detail || 'Failed to start discovery');
}
    });

    const { data: status } = useQuery<DiscoveryStatus | null>({
      queryKey: ['discovery-status', runId],
queryFn: async () => {
    if (!runId) return null;
     const response = await api.get(`/api/orchestrator/status/${runId}`);
       return response.data;
        },
        enabled: !!runId,
        refetchInterval: (query) => {
        // query.state.data contém o DiscoveryStatus
            const data = query.state.data;
 if (data?.status === 'completed' || data?.status === 'failed') {
         return false;
 }
            return 2000;
        }
    });

    const deployToPaper = useMutation({
     mutationFn: async () => {
            if (!runId) throw new Error('No run ID');
      const response = await api.post('/api/orchestrator/deploy', {
                run_id: runId,
                mode: 'paper'
        });
    return response.data;
     },
      onSuccess: () => {
       toast.success('Strategies deployed to paper trading!');
        },
        onError: (error: any) => {
          toast.error(error.response?.data?.detail || 'Failed to deploy');
     }
    });

    const handleAddSymbol = () => {
        if (symbolInput && !symbols.includes(symbolInput)) {
       setSymbols([...symbols, symbolInput]);
            setSymbolInput('');
        }
    };

    const handleAddSymbolFromList = (symbol: string) => {
 if (!symbols.includes(symbol)) {
            setSymbols([...symbols, symbol]);
     }
    };

    const handleRemoveSymbol = (symbol: string) => {
        setSymbols(symbols.filter(s => s !== symbol));
    };

    const checkCachedResults = async (request: DiscoveryRequest): Promise<CachedResult[]> => {
        try {
            const response = await api.post('/api/orchestrator/check-cache', {
    symbols: request.symbols,
       exchange: request.exchange,
         timeframe: request.timeframe
     });
    return response.data.cached || [];
        } catch (error) {
  console.error('Error checking cache:', error);
   return [];
        }
    };

    const handleStartDiscovery = async () => {
     if (symbols.length === 0) {
    toast.error('Please add at least one symbol');
            return;
        }

    const request: DiscoveryRequest = {
            symbols,
  exchange,
      timeframe,
        days,
  optimization_trials: trials,
   top_n_to_optimize: topN,
       auto_deploy_paper: false
   };

        // Check for cached results
        const cached = await checkCachedResults(request);
        
        if (cached.length > 0) {
         setCachedResults(cached);
      setPendingRequest(request);
            setShowCacheDialog(true);
} else {
            startDiscovery.mutate(request);
  }
    };

    const handleUseCached = () => {
        setShowCacheDialog(false);
    toast.success(`Using cached results for ${cachedResults.length} symbol(s)`);
  // TODO: Load cached results into UI
  };

    const handleRerun = () => {
        setShowCacheDialog(false);
        if (pendingRequest) {
     startDiscovery.mutate(pendingRequest);
  }
  };

    const handleReset = () => {
        setRunId(null);
      setSymbols([]);
        setDays(90);
        setTrials(50);
     setTopN(5);
    };

    const isRunning = status?.status === 'running' || status?.status === 'pending';
    const isCompleted = status?.status === 'completed';
    const isFailed = status?.status === 'failed';

    const popularSymbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT', 'XRP/USDT:USDT', 'ADA/USDT:USDT'];

    const timeframes = [
        { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
    { value: '1h', label: '1 Hour' },
     { value: '4h', label: '4 Hours' },
      { value: '1d', label: '1 Day' }
    ];

  return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Cache Dialog */}
            <AlertDialog open={showCacheDialog} onOpenChange={setShowCacheDialog}>
      <AlertDialogContent>
          <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-blue-600" />
          Cached Results Found
    </AlertDialogTitle>
      <AlertDialogDescription>
          We found existing optimization results for {cachedResults.length} symbol(s):
   </AlertDialogDescription>
   </AlertDialogHeader>
           
   <div className="space-y-2 max-h-60 overflow-y-auto">
            {cachedResults.map((result) => (
        <div key={`${result.symbol}-${result.timeframe}`} className="p-3 bg-muted rounded-lg">
       <div className="flex items-center justify-between">
        <div>
      <p className="font-semibold">{result.symbol}</p>
    <p className="text-xs text-muted-foreground">
            {result.strategy} | {result.timeframe}
 </p>
      </div>
                 <div className="text-right">
    <p className="font-bold text-green-600">
            {result.optimized_profit?.toFixed(2)}%
       </p>
    <p className="text-xs text-muted-foreground">
         Score: {result.score?.toFixed(2)}
        </p>
    </div>
           </div>
      <p className="text-xs text-muted-foreground mt-1">
     <Clock className="inline h-3 w-3 mr-1" />
    Cached: {new Date(result.cached_at).toLocaleString()}
            </p>
             </div>
     ))}
             </div>

            <AlertDialogFooter>
           <AlertDialogCancel onClick={handleUseCached}>
 Use Cached Results
                </AlertDialogCancel>
      <AlertDialogAction onClick={handleRerun}>
    Re-run Optimization
             </AlertDialogAction>
   </AlertDialogFooter>
         </AlertDialogContent>
   </AlertDialog>

 {/* Header */}
     <div className="flex items-center justify-between">
    <div>
       <h1 className="text-3xl font-bold flex items-center gap-2">
     <Rocket className="h-8 w-8" />
      Strategy Discovery
         </h1>
        <p className="text-muted-foreground mt-1">
   Test all 38 strategies, optimize top performers, deploy to trading
      </p>
     </div>
      {isCompleted && (
     <Button onClick={handleReset} variant="outline">
     <RefreshCw className="mr-2 h-4 w-4" />
    New Discovery
          </Button>
        )}
    </div>

      {!runId && (
     <Card>
     <CardHeader>
         <CardTitle className="flex items-center gap-2">
       <Settings className="h-5 w-5" />
        Configuration
         </CardTitle>
            <CardDescription>
        Select exchange, timeframe, symbols and configure discovery parameters
    </CardDescription>
</CardHeader>
         <CardContent className="space-y-6">
        {/* Exchange & Timeframe */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div className="space-y-2">
   <Label>Exchange</Label>
         <Select value={exchange} onValueChange={setExchange}>
          <SelectTrigger>
  <SelectValue />
         </SelectTrigger>
       <SelectContent>
                   <SelectItem value="bitget">Bitget</SelectItem>
    <SelectItem value="binance">Binance</SelectItem>
          </SelectContent>
</Select>
   </div>
      <div className="space-y-2">
    <Label>Timeframe</Label>
         <Select value={timeframe} onValueChange={setTimeframe}>
          <SelectTrigger>
                <SelectValue />
          </SelectTrigger>
     <SelectContent>
             {timeframes.map((tf) => (
     <SelectItem key={tf.value} value={tf.value}>
{tf.label}
               </SelectItem>
          ))}
        </SelectContent>
      </Select>
     </div>
               </div>

   {/* Symbols */}
         <div className="space-y-2">
  <div className="flex items-center justify-between">
    <Label>Trading Symbols ({symbols.length} selected)</Label>
       <Button variant="ghost" size="sm" onClick={() => refetchSymbols()} disabled={loadingSymbols}>
             <RefreshCw className={`h-4 w-4 mr-1 ${loadingSymbols ? 'animate-spin' : ''}`} />
      Refresh
         </Button>
       </div>
           <div>
         <p className="text-xs text-muted-foreground mb-2">Quick add popular:</p>
   <div className="flex flex-wrap gap-2">
       {popularSymbols.map((symbol) => (
   <Button
      key={symbol}
   variant="outline"
  size="sm"
      onClick={() => handleAddSymbolFromList(symbol)}
 disabled={symbols.includes(symbol)}
          >
    {symbol.split('/')[0]}
      </Button>
 ))}
         </div>
    </div>
    <div className="flex gap-2">
               <Input
           placeholder="Search or type symbol..."
          value={symbolInput}
     onChange={(e) => setSymbolInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
       />
         <Button onClick={handleAddSymbol}>Add</Button>
   </div>
         {symbolInput && availableSymbols && (
    <div className="max-h-40 overflow-y-auto border rounded-md p-2 bg-muted/20">
     <p className="text-xs text-muted-foreground mb-2">Matching symbols ({exchange}):</p>
          <div className="space-y-1">
                 {availableSymbols
 .filter(s => s.toLowerCase().includes(symbolInput.toLowerCase()) && !symbols.includes(s))
     .slice(0, 10)
    .map((symbol) => (
              <Button
        key={symbol}
             variant="ghost"
size="sm"
        className="w-full justify-start text-xs"
     onClick={() => {
  handleAddSymbolFromList(symbol);
       setSymbolInput('');
     }}
          >
   {symbol}
            </Button>
))}
            </div>
     </div>
          )}
        <div className="flex flex-wrap gap-2 min-h-[40px] p-2 border rounded-md bg-muted/20">
{symbols.length === 0 ? (
     <p className="text-sm text-muted-foreground">No symbols selected</p>
            ) : (
       symbols.map((symbol) => (
            <Badge
key={symbol}
             variant="secondary"
   className="cursor-pointer hover:bg-destructive transition-colors"
           onClick={() => handleRemoveSymbol(symbol)}
 >
        {symbol} ×
       </Badge>
         ))
    )}
  </div>
                 </div>

        {/* Parameters */}
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
         <div className="space-y-2">
       <Label htmlFor="days">Historical Days</Label>
    <Input 
  id="days" 
        type="number" 
     value={days} 
          onChange={(e) => setDays(parseInt(e.target.value))} 
         min={7} 
      max={1460} 
     />
  <p className="text-xs text-muted-foreground">7-1460 days (up to 4 years)</p>
          </div>
      <div className="space-y-2">
      <Label htmlFor="trials">Optimization Trials</Label>
        <Input 
            id="trials" 
      type="number" 
          value={trials} 
   onChange={(e) => setTrials(parseInt(e.target.value))} 
                 min={10} 
           max={200} 
       />
          <p className="text-xs text-muted-foreground">10-200 trials</p>
  </div>
      <div className="space-y-2">
          <Label htmlFor="topN">Top N to Optimize</Label>
       <Input 
        id="topN" 
       type="number" 
   value={topN} 
        onChange={(e) => setTopN(parseInt(e.target.value))} 
       min={3} 
            max={10} 
         />
    <p className="text-xs text-muted-foreground">3-10 strategies</p>
        </div>
       </div>

      <Button 
       onClick={handleStartDiscovery} 
             disabled={startDiscovery.isPending || symbols.length === 0} 
        size="lg" 
               className="w-full"
             >
  <Play className="mr-2 h-5 w-5" />
            Start Strategy Discovery ({symbols.length} {symbols.length === 1 ? 'symbol' : 'symbols'})
   </Button>
        </CardContent>
                </Card>
       )}

   {/* Progress Card - mantém o código existente */}
            {runId && status && (
        <Card className="border-primary/50">
      <CardHeader>
             <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
         {isRunning && (
         <div className="relative">
                    <Zap className="h-5 w-5 text-yellow-500 animate-pulse" />
     <div className="absolute inset-0 h-5 w-5 animate-ping">
     <Zap className="h-5 w-5 text-yellow-500 opacity-75" />
            </div>
 </div>
     )}
{isCompleted && <CheckCircle2 className="h-5 w-5 text-green-600" />}
        {isFailed && <AlertCircle className="h-5 w-5 text-red-600" />}
       Discovery Progress
             </span>
           <Badge variant={isRunning ? 'default' : isCompleted ? 'outline' : 'destructive'} className={isRunning ? 'animate-pulse' : ''}>
  {status.status.toUpperCase()}
          </Badge>
   </CardTitle>
      {status.current_symbol && (
          <CardDescription className="flex items-center gap-2">
         <span className="inline-block w-2 h-2 bg-primary rounded-full animate-pulse" />
       Currently processing: <strong>{status.current_symbol}</strong>
      </CardDescription>
         )}
      </CardHeader>
          <CardContent className="space-y-6">
          <div className="space-y-2">
    <div className="flex justify-between text-sm font-medium">
     <span>Overall Progress</span>
             <span>{Math.round(status.progress)}%</span>
      </div>
              <Progress value={status.progress} className="h-3" />
         </div>
              <div className="space-y-2">
         <Label>Symbols ({status.symbols.length})</Label>
       <div className="flex flex-wrap gap-2 p-3 bg-muted/30 rounded-lg">
           {status.symbols.map((symbol) => (
         <Badge
            key={symbol}
                variant={symbol === status.current_symbol ? 'default' : status.progress === 100 ? 'outline' : 'secondary'}
      className={symbol === status.current_symbol ? 'animate-pulse' : ''}
        >
     {symbol}
            </Badge>
      ))}
       </div>
   </div>
      {status.error && (
                 <div className="p-4 bg-destructive/10 border border-destructive rounded-lg">
     <div className="flex items-start gap-2">
         <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
  <div>
            <p className="font-medium text-destructive">Error occurred:</p>
   <p className="text-sm text-muted-foreground mt-1">{status.error}</p>
                </div>
    </div>
    </div>
               )}
        </CardContent>
       </Card>
            )}

            {/* Results Card - mantém o código existente */}
        {isCompleted && status?.best_strategies && (
        <Card className="border-green-500/50">
          <CardHeader>
         <CardTitle className="flex items-center gap-2">
    <TrendingUp className="h-5 w-5 text-green-600" />
              Best Strategies Found
             </CardTitle>
    <CardDescription>Top performing strategy for each symbol</CardDescription>
       </CardHeader>
                    <CardContent className="space-y-4">
        {Object.entries(status.best_strategies).map(([symbol, strategy]: [string, any]) => (
          <div key={symbol} className="p-4 border rounded-lg space-y-3 hover:bg-accent/50 transition-all hover:shadow-md">
        <div className="flex items-center justify-between">
       <h3 className="text-lg font-bold">{symbol}</h3>
       <Badge variant="outline" className="font-mono">{strategy.strategy}</Badge>
          </div>
   <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-2 bg-muted/30 rounded">
              <p className="text-xs text-muted-foreground">Baseline</p>
    <p className="text-lg font-bold">{strategy.baseline_profit?.toFixed(2)}%</p>
        </div>
   <div className="text-center p-2 bg-green-500/10 rounded">
           <p className="text-xs text-muted-foreground">Optimized</p>
       <p className="text-lg font-bold text-green-600">{strategy.optimized_profit?.toFixed(2)}%</p>
                  </div>
 <div className="text-center p-2 bg-muted/30 rounded">
<p className="text-xs text-muted-foreground">Score</p>
          <p className="text-lg font-bold">{strategy.score?.toFixed(2)}</p>
             </div>
  <div className="text-center p-2 bg-blue-500/10 rounded">
       <p className="text-xs text-muted-foreground">Improvement</p>
    <p className="text-lg font-bold text-blue-600">
        +{((strategy.optimized_profit - strategy.baseline_profit) || 0).toFixed(2)}%
            </p>
     </div>
            </div>
     </div>
    ))}
 <Button onClick={() => deployToPaper.mutate()} disabled={deployToPaper.isPending} size="lg" className="w-full">
        <Rocket className="mr-2 h-5 w-5" />
            Deploy to Paper Trading
        </Button>
            </CardContent>
     </Card>
            )}
   </div>
    );
}