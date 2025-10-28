import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Check, ChevronsUpDown, X, Loader2, Calendar, DollarSign, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';

interface DataSelectorProps {
  value: {
    exchange: string;
    symbols: string[];
    timeframe: string;
    since: number;
    until: number;
    higher_tf: string[];
    fees?: {
      maker: number;
      taker: number;
    };
    spread?: number;
  };
  onChange: (value: any) => void;
}

// Default fees for each exchange (%)
const EXCHANGE_FEES: Record<string, { maker: number; taker: number }> = {
  bitget: { maker: 0.02, taker: 0.06 },  // 0.02% maker, 0.06% taker
  binance: { maker: 0.02, taker: 0.04 }, // 0.02% maker, 0.04% taker
};

export function DataSelector({ value, onChange }: DataSelectorProps) {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Set default fees when exchange changes
  useEffect(() => {
    if (value.exchange && !value.fees) {
      const defaultFees = EXCHANGE_FEES[value.exchange.toLowerCase()] || { maker: 0.02, taker: 0.06 };
      onChange({ 
        ...value, 
        fees: defaultFees,
     spread: value.spread || 0.0
      });
    }
  }, [value.exchange]);

  const { data: exchangesData } = useQuery({
    queryKey: ['exchanges'],
    queryFn: async () => {
      const res = await fetch('/api/lab/exchanges');
      return res.json();
 }
  });

  const { data: symbolsData, isLoading: symbolsLoading } = useQuery({
    queryKey: ['symbols', value.exchange],
    queryFn: async () => {
      const res = await fetch(`/api/lab/symbols?exchange=${value.exchange}`);
      return res.json();
    },
    enabled: !!value.exchange
  });

  const backfillMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/lab/backfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
          exchange: value.exchange,
          symbols: value.symbols,
    timeframe: value.timeframe,
     since: value.since,
          until: value.until,
          higher_tf: value.higher_tf
     })
      });
      if (!res.ok) throw new Error('Backfill failed');
  return res.json();
    },
    onSuccess: (data) => {
      toast({
        title: 'Backfill Complete',
   description: `Downloaded ${data.total_candles} candles and calculated ${data.total_features} features`
      });
    },
    onError: () => {
      toast({
        title: 'Backfill Failed',
        description: 'Failed to download data',
        variant: 'destructive'
      });
    }
  });

  const filteredSymbols = symbolsData?.symbols?.filter((s: string) =>
    s.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const toggleSymbol = (symbol: string) => {
    const newSymbols = value.symbols.includes(symbol)
      ? value.symbols.filter(s => s !== symbol)
      : [...value.symbols, symbol];
    onChange({ ...value, symbols: newSymbols });
  };

  const removeSymbol = (symbol: string) => {
    onChange({ ...value, symbols: value.symbols.filter(s => s !== symbol) });
  };

  const timestampToDatetimeLocal = (timestamp: number): string => {
    const date = new Date(timestamp);
    const year = date.getFullYear();
 const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const datetimeLocalToTimestamp = (datetimeLocal: string): number => {
    return new Date(datetimeLocal).getTime();
  };

  return (
    <Card>
   <CardHeader>
        <CardTitle>Data Configuration</CardTitle>
        <CardDescription>Select exchange, symbols, timeframe, fees and spread for backtesting</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
     <div className="space-y-2">
     <Label>Exchange</Label>
      <Select 
            value={value.exchange} 
 onValueChange={(v) => {
       const defaultFees = EXCHANGE_FEES[v.toLowerCase()] || { maker: 0.02, taker: 0.06 };
            onChange({ 
      ...value, 
        exchange: v, 
      symbols: [],
          fees: defaultFees
   });
   }}
          >
            <SelectTrigger>
      <SelectValue placeholder="Select exchange" />
            </SelectTrigger>
     <SelectContent>
    {exchangesData?.exchanges?.map((ex: string) => (
      <SelectItem key={ex} value={ex}>{ex}</SelectItem>
    ))}
       </SelectContent>
  </Select>
        </div>

        {/* Fees & Spread Section */}
        {value.exchange && (
   <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
    <div className="col-span-2">
              <Label className="flex items-center gap-2 text-sm font-semibold">
 <DollarSign className="h-4 w-4" />
         Trading Costs
    </Label>
        <p className="text-xs text-muted-foreground mt-1">
     Default fees for {value.exchange} exchange
              </p>
          </div>

 <div className="space-y-2">
            <Label className="text-xs">Maker Fee (%)</Label>
              <Input
                type="number"
    step="0.001"
        value={value.fees?.maker || 0}
         onChange={(e) => onChange({ 
          ...value, 
       fees: { ...value.fees!, maker: parseFloat(e.target.value) || 0 }
         })}
                className="h-9"
    />
         <p className="text-xs text-muted-foreground">
                Default: {EXCHANGE_FEES[value.exchange.toLowerCase()]?.maker || 0.02}%
            </p>
            </div>

          <div className="space-y-2">
         <Label className="text-xs">Taker Fee (%)</Label>
      <Input
    type="number"
                step="0.001"
                value={value.fees?.taker || 0}
    onChange={(e) => onChange({ 
       ...value, 
        fees: { ...value.fees!, taker: parseFloat(e.target.value) || 0 }
            })}
     className="h-9"
      />
    <p className="text-xs text-muted-foreground">
    Default: {EXCHANGE_FEES[value.exchange.toLowerCase()]?.taker || 0.06}%
      </p>
            </div>

          <div className="col-span-2 space-y-2">
       <Label className="text-xs flex items-center gap-2">
      <TrendingUp className="h-3 w-3" />
    Spread (pips/points)
         </Label>
            <Input
     type="number"
  step="0.1"
    value={value.spread || 0}
         onChange={(e) => onChange({ 
          ...value, 
    spread: parseFloat(e.target.value) || 0 
 })}
              placeholder="0.0"
     className="h-9"
      />
     <p className="text-xs text-muted-foreground">
     Bid-ask spread to simulate slippage (0 = no spread)
    </p>
       </div>
     </div>
      )}

      <div className="space-y-2">
      <Label>Symbols ({value.symbols.length} selected)</Label>
     <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
        <Button
       variant="outline"
        role="combobox"
     aria-expanded={open}
    className="w-full justify-between"
      disabled={!value.exchange}
    >
        {value.symbols.length === 0 ? 'Select symbols...' : `${value.symbols.length} selected`}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
            <PopoverContent className="w-[400px] p-0">
              <Command>
       <CommandInput
             placeholder="Search symbols..."
       value={searchQuery}
          onValueChange={setSearchQuery}
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
        {filteredSymbols.slice(0, 50).map((symbol: string) => (
       <CommandItem
           key={symbol}
   onSelect={() => toggleSymbol(symbol)}
   >
     <Check
           className={cn(
        'mr-2 h-4 w-4',
           value.symbols.includes(symbol) ? 'opacity-100' : 'opacity-0'
   )}
       />
    {symbol}
        </CommandItem>
        ))}
   </CommandGroup>
       </Command>
            </PopoverContent>
      </Popover>

          {value.symbols.length > 0 && (
       <div className="flex flex-wrap gap-2 mt-2">
              {value.symbols.map(symbol => (
                <Badge key={symbol} variant="secondary" className="gap-1">
 {symbol}
       <X
          className="h-3 w-3 cursor-pointer"
       onClick={() => removeSymbol(symbol)}
       />
</Badge>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-2">
    <Label>Base Timeframe</Label>
        <Select value={value.timeframe} onValueChange={(v) => onChange({ ...value, timeframe: v })}>
            <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
     <SelectContent>
     <SelectItem value="1m">1 minute</SelectItem>
        <SelectItem value="5m">5 minutes</SelectItem>
         <SelectItem value="15m">15 minutes</SelectItem>
   <SelectItem value="1h">1 hour</SelectItem>
      <SelectItem value="4h">4 hours</SelectItem>
              <SelectItem value="1d">1 day</SelectItem>
            </SelectContent>
          </Select>
  </div>

        <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2">
  <Label className="flex items-center gap-2">
    <Calendar className="h-4 w-4" />
       Start Date & Time
    </Label>
 <Input
         type="datetime-local"
   value={timestampToDatetimeLocal(value.since)}
      onChange={(e) => onChange({ ...value, since: datetimeLocalToTimestamp(e.target.value) })}
              className="w-full"
    />
     <p className="text-xs text-muted-foreground">
           Timestamp: {value.since}
       </p>
          </div>
     <div className="space-y-2">
       <Label className="flex items-center gap-2">
         <Calendar className="h-4 w-4" />
    End Date & Time
   </Label>
    <Input
 type="datetime-local"
   value={timestampToDatetimeLocal(value.until)}
 onChange={(e) => onChange({ ...value, until: datetimeLocalToTimestamp(e.target.value) })}
            className="w-full"
            />
       <p className="text-xs text-muted-foreground">
    Timestamp: {value.until}
            </p>
          </div>
        </div>

        <Button
   onClick={() => backfillMutation.mutate()}
          disabled={!value.exchange || value.symbols.length === 0 || backfillMutation.isPending}
          className="w-full"
     >
 {backfillMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
       Backfill Data
        </Button>
      </CardContent>
    </Card>
  );
}