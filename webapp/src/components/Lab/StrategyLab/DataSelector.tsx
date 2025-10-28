import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Check, ChevronsUpDown, X, Loader2 } from 'lucide-react';
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
  };
  onChange: (value: any) => void;
}

export function DataSelector({ value, onChange }: DataSelectorProps) {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch exchanges
  const { data: exchangesData } = useQuery({
    queryKey: ['exchanges'],
    queryFn: async () => {
      const res = await fetch('/api/lab/exchanges');
      return res.json();
    }
  });

  // Fetch symbols for selected exchange
  const { data: symbolsData, isLoading: symbolsLoading } = useQuery({
    queryKey: ['symbols', value.exchange],
    queryFn: async () => {
      const res = await fetch(`/api/lab/symbols?exchange=${value.exchange}`);
      return res.json();
    },
    enabled: !!value.exchange
  });

  // Backfill mutation
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Configuration</CardTitle>
        <CardDescription>Select exchange, symbols, and timeframe for backtesting</CardDescription>
    </CardHeader>
      <CardContent className="space-y-4">
        {/* Exchange */}
        <div className="space-y-2">
          <Label>Exchange</Label>
      <Select value={value.exchange} onValueChange={(v) => onChange({ ...value, exchange: v, symbols: [] })}>
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

        {/* Symbols */}
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

 {/* Selected symbols badges */}
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

        {/* Timeframe */}
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

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
       <div className="space-y-2">
   <Label>Since (timestamp ms)</Label>
            <Input
  type="number"
       value={value.since}
     onChange={(e) => onChange({ ...value, since: parseInt(e.target.value) })}
            />
          </div>
          <div className="space-y-2">
     <Label>Until (timestamp ms)</Label>
   <Input
         type="number"
     value={value.until}
   onChange={(e) => onChange({ ...value, until: parseInt(e.target.value) })}
            />
          </div>
    </div>

        {/* Backfill Button */}
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
