import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { 
  Popover,
  PopoverContent,
  PopoverTrigger
} from '@/components/ui/popover';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem
} from '@/components/ui/command';
import { 
  Database, 
  TrendingUp, 
  ShieldAlert, 
  Target,
  Check,
  ChevronsUpDown,
  Plus,
  Trash2,
  Download,
  Play,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  createDefaultStrategy, 
  validateStrategy,
  type StrategyDefinition,
  type EntryCondition,
  INDICATOR_CATALOG
} from '@/domain/strategy';
import * as LabAPI from '@/lib/api-lab';
import { useNavigate } from 'react-router-dom';

// ============================================================================
// VALIDATION SCHEMA (Zod)
// ============================================================================

const strategyFormSchema = z.object({
  name: z.string().min(3, 'Strategy name must be at least 3 characters'),
  exchange: z.enum(['bitget', 'binance']),
  symbols: z.array(z.string()).min(1, 'Select at least one symbol'),
  baseTimeframe: z.string(),
  dateFrom: z.number(),
  dateTo: z.number(),
  initialEquity: z.number().min(100, 'Minimum equity is $100'),
  maxLeverage: z.number().min(1).max(125),
  maxConcurrentPositions: z.number().min(1).max(10)
}).refine((data) => data.dateTo > data.dateFrom, {
  message: 'End date must be after start date',
  path: ['dateTo']
});

type StrategyFormValues = z.infer<typeof strategyFormSchema>;

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function StrategyLabV2() {
  const navigate = useNavigate();
  const [strategy, setStrategy] = useState<StrategyDefinition>(createDefaultStrategy());
  const [activeTab, setActiveTab] = useState('data');
  const [isBackfilling, setIsBackfilling] = useState(false);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);

  const form = useForm<StrategyFormValues>({
    resolver: zodResolver(strategyFormSchema),
    defaultValues: {
      name: strategy.name,
      exchange: strategy.exchange,
      symbols: strategy.symbols,
      baseTimeframe: strategy.baseTimeframe,
      dateFrom: strategy.dateFrom,
dateTo: strategy.dateTo,
  initialEquity: strategy.risk.initialEquity,
      maxLeverage: strategy.risk.maxLeverage,
      maxConcurrentPositions: strategy.risk.maxConcurrentPositions
    }
  });

  // Query symbols from API using new client
  const { data: symbols = [], isLoading: symbolsLoading } = useQuery({
    queryKey: ['symbols', form.watch('exchange')],
    queryFn: () => LabAPI.getSymbols(form.watch('exchange')),
    enabled: !!form.watch('exchange')
  });

  // Validate strategy
  const validation = validateStrategy(strategy);

  // Handle backfill with toast feedback
  const handleBackfill = async () => {
    setIsBackfilling(true);
    const toastId = toast.loading('Starting backfill...');
    
    try {
      const result = await LabAPI.backfillData({
      exchange: strategy.exchange,
        symbols: strategy.symbols,
        timeframe: strategy.baseTimeframe,
        since: strategy.dateFrom,
 until: strategy.dateTo,
        higher_tf: strategy.higherTimeframes || []
      });
      
      toast.success(
        `? Backfill complete! Downloaded ${result.total_candles.toLocaleString()} candles`,
        { id: toastId, duration: 5000 }
      );
      
      // Show detailed results
      result.results.forEach(r => {
        if (r.candles_inserted > 0) {
          toast.success(
       `${r.symbol} @ ${r.timeframe}: ${r.candles_inserted.toLocaleString()} candles`,
 { duration: 3000 }
        );
        }
  });
    } catch (error) {
      const err = error as LabAPI.ApiError;
   toast.error(
    `? Backfill failed: ${err.message}`,
        { id: toastId, duration: 5000 }
      );
    } finally {
      setIsBackfilling(false);
    }
  };

  // Handle backtest with navigation
  const handleBacktest = async () => {
    setIsBacktesting(true);
    const toastId = toast.loading('Starting backtest...');
    
    try {
      const result = await LabAPI.runBacktest(strategy);
    
   toast.success(
        `? Backtest started! Run ID: ${result.run_id.substring(0, 8)}...`,
    { id: toastId, duration: 3000 }
      );
      
      // Navigate to results page after 1 second
      setTimeout(() => {
        navigate(`/lab/results/${result.run_id}`);
      }, 1000);
    } catch (error) {
      const err = error as LabAPI.ApiError;
    toast.error(
        `? Backtest failed: ${err.message}`,
        { id: toastId, duration: 5000 }
      );
   setIsBacktesting(false);
    }
  };

  // Handle optimization
  const handleOptimize = async () => {
    setIsOptimizing(true);
    const toastId = toast.loading('Starting optimization...');
    
    try {
      const result = await LabAPI.runOptuna(strategy, 100);

      toast.success(
        `? Optimization started! Run ID: ${result.run_id.substring(0, 8)}...`,
        { id: toastId, duration: 3000 }
      );
      
      // Navigate to results page
      setTimeout(() => {
        navigate(`/lab/results/${result.run_id}`);
    }, 1000);
    } catch (error) {
      const err = error as LabAPI.ApiError;
      toast.error(
        `? Optimization failed: ${err.message}`,
        { id: toastId, duration: 5000 }
      );
      setIsOptimizing(false);
    }
  };

return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
  <div className="flex items-center justify-between">
        <div>
     <h1 className="text-3xl font-bold tracking-tight">Strategy Lab v2</h1>
 <p className="text-muted-foreground">
   Build, backtest, and optimize quantitative trading strategies
      </p>
  </div>
        
        <div className="flex gap-2">
 <Button
 variant="outline"
     size="sm"
      onClick={handleBackfill}
disabled={!validation.valid || isBackfilling || strategy.symbols.length === 0}
     >
       {isBackfilling && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
   <Download className="mr-2 h-4 w-4" />
    Backfill Data
     </Button>
          
          <Button
            variant="outline"
         size="sm"
            onClick={handleBacktest}
          disabled={!validation.valid || isBacktesting}
 >
            {isBacktesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Play className="mr-2 h-4 w-4" />
 Run Backtest
          </Button>
  
          <Button
    size="sm"
         onClick={handleOptimize}
    disabled={!validation.valid || isOptimizing}
    >
         {isOptimizing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Sparkles className="mr-2 h-4 w-4" />
            Optimize
          </Button>
        </div>
      </div>

      {/* Strategy Name */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Name & Portfolio</CardTitle>
          <CardDescription>Give your strategy a unique identifier and set initial capital</CardDescription>
 </CardHeader>
 <CardContent>
    <Form {...form}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Strategy Name */}
            <FormField
      control={form.control}
           name="name"
            render={({ field }) => (
             <FormItem>
       <FormLabel>Strategy Name</FormLabel>
       <FormControl>
       <Input
     {...field}
  placeholder="My Awesome Strategy"
          onChange={(e) => {
    field.onChange(e);
    setStrategy({ ...strategy, name: e.target.value });
                    }}
     />
      </FormControl>
         <FormMessage />
              </FormItem>
           )}
       />

  {/* Initial Portfolio Size */}
              <FormField
        control={form.control}
                name="initialEquity"
             render={({ field }) => (
      <FormItem>
            <FormLabel className="flex items-center gap-2">
        <Target className="h-4 w-4" />
      Initial Portfolio Size (USDT)
          </FormLabel>
      <FormControl>
      <div className="relative">
    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
   <Input
    type="number"
  className="pl-7"
   {...field}
      onChange={(e) => {
           const value = parseFloat(e.target.value) || 10000;
       field.onChange(value);
      setStrategy({
    ...strategy,
         risk: { ...strategy.risk, initialEquity: value }
     });
     }}
      />
   </div>
  </FormControl>
     <FormDescription>
Starting capital for backtesting (min: $100)
         </FormDescription>
          <FormMessage />
       </FormItem>
   )}
       />
  </div>
    </Form>
    </CardContent>
      </Card>

      {/* Validation Status */}
      {validation.valid ? (
 <Card className="border-green-500/50 bg-green-50/50 dark:bg-green-950/20">
    <CardContent className="pt-6">
        <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
        <CheckCircle2 className="h-5 w-5" />
   <span className="font-medium">Strategy is valid and ready to run</span>
      </div>
          </CardContent>
        </Card>
   ) : (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
    <AlertCircle className="h-5 w-5" />
   Validation Errors
            </CardTitle>
   </CardHeader>
      <CardContent>
         <ul className="list-disc list-inside space-y-1 text-sm text-destructive">
              {validation.errors.map((error, i) => (
            <li key={i}>{error}</li>
   ))}
     </ul>
</CardContent>
        </Card>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="data">
  <Database className="mr-2 h-4 w-4" />
      Data
   </TabsTrigger>
        <TabsTrigger value="entries">
    <TrendingUp className="mr-2 h-4 w-4" />
            Entries
    </TabsTrigger>
       <TabsTrigger value="exits">
            <ShieldAlert className="mr-2 h-4 w-4" />
      Exits
          </TabsTrigger>
          <TabsTrigger value="risk">
            <Target className="mr-2 h-4 w-4" />
   Risk
     </TabsTrigger>
  <TabsTrigger value="preview">
    Preview
   </TabsTrigger>
        </TabsList>

        {/* DATA TAB */}
        <TabsContent value="data" className="space-y-4">
        <DataConfigSection
            strategy={strategy}
         setStrategy={setStrategy}
 form={form}
            symbols={symbols}
symbolsLoading={symbolsLoading}
   />
  </TabsContent>

        {/* ENTRIES TAB */}
        <TabsContent value="entries" className="space-y-4">
          <EntriesSection
        strategy={strategy}
     setStrategy={setStrategy}
          />
     </TabsContent>

 {/* EXITS TAB */}
        <TabsContent value="exits" className="space-y-4">
          <ExitsSection
   strategy={strategy}
      setStrategy={setStrategy}
   />
        </TabsContent>

        {/* RISK TAB */}
        <TabsContent value="risk" className="space-y-4">
 <RiskSection
            strategy={strategy}
            setStrategy={setStrategy}
            form={form}
          />
        </TabsContent>

  {/* PREVIEW TAB */}
        <TabsContent value="preview">
          <Card>
<CardHeader>
              <CardTitle>Strategy Configuration (JSON)</CardTitle>
           <CardDescription>Review the complete strategy definition</CardDescription>
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

// ============================================================================
// DATA CONFIG SECTION
// ============================================================================

interface DataConfigSectionProps {
  strategy: StrategyDefinition;
  setStrategy: (strategy: StrategyDefinition) => void;
  form: any;
  symbols: string[];
  symbolsLoading: boolean;
}

function DataConfigSection({ strategy, setStrategy, form, symbols, symbolsLoading }: DataConfigSectionProps) {
  const [symbolSearchOpen, setSymbolSearchOpen] = useState(false);
  const [symbolSearch, setSymbolSearch] = useState('');

  const filteredSymbols = symbols.filter(s => 
    s.toLowerCase().includes(symbolSearch.toLowerCase())
  );

  const toggleSymbol = (symbol: string) => {
    const newSymbols = strategy.symbols.includes(symbol)
      ? strategy.symbols.filter(s => s !== symbol)
      : [...strategy.symbols, symbol];
    
    setStrategy({ ...strategy, symbols: newSymbols });
    form.setValue('symbols', newSymbols);
  };

  return (
    <>
<Card>
        <CardHeader>
          <CardTitle>Exchange & Symbols</CardTitle>
      <CardDescription>Select exchange and trading pairs</CardDescription>
    </CardHeader>
     <CardContent className="space-y-4">
          {/* Exchange */}
          <Form {...form}>
  <FormField
        control={form.control}
              name="exchange"
            render={({ field }) => (
     <FormItem>
     <FormLabel>Exchange</FormLabel>
 <Select
        value={field.value}
  onValueChange={(value: 'bitget' | 'binance') => {
        field.onChange(value);
             setStrategy({ ...strategy, exchange: value, symbols: [] });
               }}
        >
  <FormControl>
            <SelectTrigger>
          <SelectValue />
           </SelectTrigger>
 </FormControl>
       <SelectContent>
           <SelectItem value="bitget">Bitget</SelectItem>
         <SelectItem value="binance">Binance</SelectItem>
         </SelectContent>
              </Select>
      <FormMessage />
    </FormItem>
              )}
            />
          </Form>

          {/* Symbols Multi-Select */}
   <div className="space-y-2">
<Label>Symbols ({strategy.symbols.length} selected)</Label>
        <Popover open={symbolSearchOpen} onOpenChange={setSymbolSearchOpen}>
              <PopoverTrigger asChild>
    <Button
      variant="outline"
   role="combobox"
           className="w-full justify-between"
      disabled={!strategy.exchange}
    >
            {strategy.symbols.length === 0 ? 'Select symbols...' : `${strategy.symbols.length} selected`}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
         </Button>
</PopoverTrigger>
  <PopoverContent className="w-[400px] p-0">
          <Command>
       <CommandInput
   placeholder="Search symbols..."
  value={symbolSearch}
      onValueChange={setSymbolSearch}
   />
          <CommandEmpty>
      {symbolsLoading ? (
     <div className="flex items-center justify-center p-4">
 <Loader2 className="h-4 w-4 animate-spin" />
               </div>
    ) : (
          'No symbols found'
      )}
       </CommandEmpty>
       <CommandGroup className="max-h-[300px] overflow-auto">
     {filteredSymbols.slice(0, 50).map((symbol) => (
 <CommandItem
        key={symbol}
          onSelect={() => toggleSymbol(symbol)}
               >
        <Check
           className={cn(
   'mr-2 h-4 w-4',
           strategy.symbols.includes(symbol) ? 'opacity-100' : 'opacity-0'
        )}
 />
           {symbol}
       </CommandItem>
         ))}
       </CommandGroup>
        </Command>
       </PopoverContent>
            </Popover>

  {strategy.symbols.length > 0 && (
    <div className="flex flex-wrap gap-2 mt-2">
          {strategy.symbols.map(symbol => (
         <Badge key={symbol} variant="secondary" className="gap-1">
      {symbol}
    <button
     onClick={() => toggleSymbol(symbol)}
               className="ml-1 hover:text-destructive"
           >
   ×
     </button>
            </Badge>
     ))}
    </div>
   )}
 </div>

          {/* Timeframe */}
   <Form {...form}>
  <FormField
       control={form.control}
     name="baseTimeframe"
render={({ field }) => (
    <FormItem>
         <FormLabel>Base Timeframe</FormLabel>
           <Select
        value={field.value}
    onValueChange={(value) => {
       field.onChange(value);
  setStrategy({ ...strategy, baseTimeframe: value });
            }}
       >
           <FormControl>
            <SelectTrigger>
             <SelectValue />
       </SelectTrigger>
       </FormControl>
         <SelectContent>
    <SelectItem value="1m">1 minute</SelectItem>
          <SelectItem value="5m">5 minutes</SelectItem>
             <SelectItem value="15m">15 minutes</SelectItem>
    <SelectItem value="1h">1 hour</SelectItem>
        <SelectItem value="4h">4 hours</SelectItem>
       <SelectItem value="1d">1 day</SelectItem>
         </SelectContent>
            </Select>
        <FormMessage />
        </FormItem>
     )}
      />
</Form>

 {/* Date Range */}
      <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
     <Label>Start Date</Label>
              <Input
        type="datetime-local"
 value={new Date(strategy.dateFrom).toISOString().slice(0, 16)}
    onChange={(e) => {
          const timestamp = new Date(e.target.value).getTime();
       setStrategy({ ...strategy, dateFrom: timestamp });
      form.setValue('dateFrom', timestamp);
      }}
  />
  </div>
    <div className="space-y-2">
 <Label>End Date</Label>
              <Input
     type="datetime-local"
  value={new Date(strategy.dateTo).toISOString().slice(0, 16)}
                onChange={(e) => {
        const timestamp = new Date(e.target.value).getTime();
           setStrategy({ ...strategy, dateTo: timestamp });
         form.setValue('dateTo', timestamp);
          }}
   />
     </div>
    </div>
        </CardContent>
      </Card>
    </>
  );
}

// ============================================================================
// ENTRIES SECTION (Placeholder)
// ============================================================================

interface EntriesSectionProps {
  strategy: StrategyDefinition;
setStrategy: (strategy: StrategyDefinition) => void;
}

function EntriesSection({ strategy, setStrategy }: EntriesSectionProps) {
  return (
    <Card>
 <CardHeader>
 <CardTitle>Entry Conditions</CardTitle>
        <CardDescription>Define when to enter LONG and SHORT positions</CardDescription>
      </CardHeader>
      <CardContent>
  <div className="space-y-4">
          {/* LONG Side */}
      <div className="space-y-2">
          <div className="flex items-center justify-between">
        <Label>LONG Entries</Label>
   <Switch
      checked={strategy.long.enabled}
      onCheckedChange={(checked) => {
       setStrategy({
  ...strategy,
     long: { ...strategy.long, enabled: checked }
         });
       }}
        />
            </div>
   {strategy.long.enabled && (
              <div className="p-4 border rounded-lg space-y-2">
            <p className="text-sm text-muted-foreground">
           Conditions: {strategy.long.entry.all.length} ALL, {strategy.long.entry.any.length} ANY
        </p>
                <Button size="sm" variant="outline">
       <Plus className="mr-2 h-4 w-4" />
         Add Condition
        </Button>
              </div>
      )}
          </div>

          <Separator />

          {/* SHORT Side */}
          <div className="space-y-2">
    <div className="flex items-center justify-between">
          <Label>SHORT Entries</Label>
     <Switch
     checked={strategy.short.enabled}
         onCheckedChange={(checked) => {
    setStrategy({
       ...strategy,
             short: { ...strategy.short, enabled: checked }
      });
    }}
  />
       </div>
            {strategy.short.enabled && (
   <div className="p-4 border rounded-lg space-y-2">
      <p className="text-sm text-muted-foreground">
       Conditions: {strategy.short.entry.all.length} ALL, {strategy.short.entry.any.length} ANY
   </p>
      <Button size="sm" variant="outline">
      <Plus className="mr-2 h-4 w-4" />
            Add Condition
   </Button>
  </div>
   )}
     </div>
    </div>
 </CardContent>
    </Card>
  );
}

// ============================================================================
// EXITS SECTION (Placeholder)
// ============================================================================

interface ExitsSectionProps {
  strategy: StrategyDefinition;
  setStrategy: (strategy: StrategyDefinition) => void;
}

function ExitsSection({ strategy, setStrategy }: ExitsSectionProps) {
  return (
    <Card>
      <CardHeader>
 <CardTitle>Exit Rules</CardTitle>
    <CardDescription>Define take-profit, stop-loss, and trailing stops</CardDescription>
      </CardHeader>
    <CardContent>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            ?? LONG: {strategy.long.exits.takeProfit.length} TP, {strategy.long.exits.stopLoss.length} SL, {strategy.long.exits.trailing.length} Trailing
          </p>
          <p className="text-sm text-muted-foreground">
            ?? SHORT: {strategy.short.exits.takeProfit.length} TP, {strategy.short.exits.stopLoss.length} SL, {strategy.short.exits.trailing.length} Trailing
      </p>
          <Button size="sm" variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            Add Exit Rule
     </Button>
    </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// RISK SECTION
// ============================================================================

interface RiskSectionProps {
  strategy: StrategyDefinition;
  setStrategy: (strategy: StrategyDefinition) => void;
  form: any;
}

function RiskSection({ strategy, setStrategy, form }: RiskSectionProps) {
  return (
    <Card>
   <CardHeader>
        <CardTitle>Risk Management</CardTitle>
    <CardDescription>Configure position sizing and risk parameters</CardDescription>
      </CardHeader>
    <CardContent className="space-y-4">
    <Form {...form}>
          {/* Initial Equity */}
     <FormField
            control={form.control}
            name="initialEquity"
   render={({ field }) => (
         <FormItem>
  <FormLabel>Initial Portfolio Size (USDT)</FormLabel>
       <FormControl>
    <Input
            type="number"
      {...field}
  onChange={(e) => {
       const value = parseFloat(e.target.value);
        field.onChange(value);
 setStrategy({
      ...strategy,
        risk: { ...strategy.risk, initialEquity: value }
        });
   }}
                  />
             </FormControl>
            <FormDescription>Starting capital for backtesting</FormDescription>
              <FormMessage />
     </FormItem>
  )}
          />

          {/* Max Leverage */}
          <FormField
  control={form.control}
            name="maxLeverage"
          render={({ field }) => (
              <FormItem>
     <FormLabel>Max Leverage</FormLabel>
   <FormControl>
               <Input
      type="number"
           {...field}
         onChange={(e) => {
 const value = parseFloat(e.target.value);
     field.onChange(value);
      setStrategy({
     ...strategy,
       risk: { ...strategy.risk, maxLeverage: value }
           });
 }}
           />
    </FormControl>
     <FormMessage />
        </FormItem>
       )}
        />

     {/* Max Concurrent Positions */}
  <FormField
            control={form.control}
  name="maxConcurrentPositions"
            render={({ field }) => (
    <FormItem>
     <FormLabel>Max Concurrent Positions</FormLabel>
       <FormControl>
      <Input
           type="number"
        {...field}
   onChange={(e) => {
            const value = parseInt(e.target.value);
             field.onChange(value);
   setStrategy({
            ...strategy,
                  risk: { ...strategy.risk, maxConcurrentPositions: value }
           });
            }}
     />
   </FormControl>
     <FormMessage />
  </FormItem>
       )}
          />

          {/* Position Sizing Mode */}
      <div className="space-y-2">
            <Label>Position Sizing Mode</Label>
            <Select
    value={strategy.risk.positionSizingMode}
              onValueChange={(value: any) => {
                setStrategy({
     ...strategy,
                risk: { ...strategy.risk, positionSizingMode: value }
  });
     }}
    >
       <SelectTrigger>
     <SelectValue />
   </SelectTrigger>
    <SelectContent>
    <SelectItem value="fixed_usd">Fixed USD</SelectItem>
        <SelectItem value="portfolio_pct">Portfolio %</SelectItem>
     <SelectItem value="risk_pct">Risk %</SelectItem>
         <SelectItem value="kelly">Kelly Criterion</SelectItem>
      </SelectContent>
            </Select>
        </div>

   {/* Size Value (conditional) */}
        {strategy.risk.positionSizingMode === 'fixed_usd' && (
            <div className="space-y-2">
        <Label>Fixed Size (USDT)</Label>
              <Input
     type="number"
  value={strategy.risk.fixedUsdSize || 1000}
        onChange={(e) => {
         setStrategy({
      ...strategy,
    risk: { ...strategy.risk, fixedUsdSize: parseFloat(e.target.value) }
        });
       }}
    />
      </div>
      )}

     {strategy.risk.positionSizingMode === 'portfolio_pct' && (
 <div className="space-y-2">
           <Label>Portfolio %</Label>
          <Input
    type="number"
    value={strategy.risk.portfolioPct || 10}
         onChange={(e) => {
          setStrategy({
  ...strategy,
       risk: { ...strategy.risk, portfolioPct: parseFloat(e.target.value) }
       });
       }}
        />
            </div>
        )}

          {strategy.risk.positionSizingMode === 'risk_pct' && (
            <div className="space-y-2">
              <Label>Risk % per Trade</Label>
              <Input
type="number"
   value={strategy.risk.riskPct || 1}
        onChange={(e) => {
            setStrategy({
           ...strategy,
          risk: { ...strategy.risk, riskPct: parseFloat(e.target.value) }
       });
          }}
/>
            </div>
          )}
        </Form>
      </CardContent>
    </Card>
  );
}
