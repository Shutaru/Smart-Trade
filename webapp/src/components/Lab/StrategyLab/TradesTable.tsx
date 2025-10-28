import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, Filter, TrendingUp, TrendingDown, Loader2 } from 'lucide-react';

interface Trade {
  entry_time: string;
  exit_time: string;
  side: 'long' | 'short';
entry_price?: number;
  exit_price?: number;
  pnl: number;
  pnl_pct: number;
}

interface TradesTableProps {
  runId: string;
  trialId?: number;
}

export function TradesTable({ runId, trialId }: TradesTableProps) {
  const [filter, setFilter] = useState<'all' | 'win' | 'loss'>('all');
  const [sideFilter, setSideFilter] = useState<'all' | 'long' | 'short'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Fetch trades from artifacts
  const { data: tradesData, isLoading, error } = useQuery({
    queryKey: ['trades', runId, trialId],
    queryFn: async () => {
      const url = trialId 
        ? `/api/lab/run/${runId}/artifacts/${trialId}/trades`
  : `/api/lab/run/${runId}/artifacts/trades`;
      
      const res = await fetch(url);
   if (!res.ok) throw new Error('Failed to fetch trades');
      return res.json() as Promise<{ trades: Trade[] }>;
    }
  });

  const trades = tradesData?.trades || [];

  // Apply filters
  const filteredTrades = trades.filter(trade => {
    // Win/Loss filter
if (filter === 'win' && trade.pnl <= 0) return false;
  if (filter === 'loss' && trade.pnl >= 0) return false;

    // Side filter
    if (sideFilter !== 'all' && trade.side !== sideFilter) return false;

    // Search filter (by date)
    if (searchQuery && !trade.entry_time.includes(searchQuery) && !trade.exit_time.includes(searchQuery)) {
    return false;
    }

    return true;
  });

  // Pagination
  const totalPages = Math.ceil(filteredTrades.length / pageSize);
  const paginatedTrades = filteredTrades.slice(
    (currentPage - 1) * pageSize,
  currentPage * pageSize
  );

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['Entry Time', 'Exit Time', 'Side', 'Entry Price', 'Exit Price', 'PnL', 'PnL %'];
    const rows = filteredTrades.map(t => [
   t.entry_time,
    t.exit_time,
      t.side,
      t.entry_price || '',
   t.exit_price || '',
      t.pnl.toFixed(2),
      t.pnl_pct.toFixed(2)
  ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades_${runId.substring(0, 8)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Calculate stats
  const totalPnL = filteredTrades.reduce((sum, t) => sum + t.pnl, 0);
  const winTrades = filteredTrades.filter(t => t.pnl > 0).length;
  const lossTrades = filteredTrades.filter(t => t.pnl <= 0).length;
  const winRate = filteredTrades.length > 0 ? (winTrades / filteredTrades.length) * 100 : 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
  );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-destructive">
        <p>Failed to load trades</p>
        <p className="text-sm mt-2">{(error as Error).message}</p>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
  <p>No trades found</p>
        <p className="text-sm mt-2">The backtest did not generate any trades</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Summary */}
      <div className="grid grid-cols-4 gap-4">
      <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-xs text-muted-foreground">Total Trades</p>
          <p className="text-2xl font-bold">{filteredTrades.length}</p>
        </div>
        <div className="bg-muted/50 rounded-lg p-4">
        <p className="text-xs text-muted-foreground">Win Rate</p>
          <p className="text-2xl font-bold">{winRate.toFixed(1)}%</p>
        </div>
      <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-xs text-muted-foreground">Winners / Losers</p>
          <p className="text-2xl font-bold text-green-500">{winTrades}</p>
       <p className="text-sm text-destructive">/ {lossTrades}</p>
        </div>
   <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-xs text-muted-foreground">Total PnL</p>
   <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-500' : 'text-destructive'}`}>
            {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
          </p>
  </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />
     
        <Select value={filter} onValueChange={(v: any) => setFilter(v)}>
    <SelectTrigger className="w-[120px]">
   <SelectValue />
          </SelectTrigger>
        <SelectContent>
       <SelectItem value="all">All Trades</SelectItem>
            <SelectItem value="win">Winners</SelectItem>
            <SelectItem value="loss">Losers</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sideFilter} onValueChange={(v: any) => setSideFilter(v)}>
     <SelectTrigger className="w-[120px]">
    <SelectValue />
          </SelectTrigger>
   <SelectContent>
            <SelectItem value="all">All Sides</SelectItem>
            <SelectItem value="long">Long</SelectItem>
       <SelectItem value="short">Short</SelectItem>
      </SelectContent>
        </Select>

        <Input
          placeholder="Search by date..."
     value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
  className="w-[200px]"
        />

        <Button variant="outline" size="sm" onClick={exportToCSV} className="ml-auto gap-2">
    <Download className="h-4 w-4" />
          Export CSV
  </Button>
      </div>

    {/* Trades Table */}
      <div className="border rounded-lg">
 <Table>
       <TableHeader>
  <TableRow>
              <TableHead>Entry Time</TableHead>
   <TableHead>Exit Time</TableHead>
  <TableHead>Side</TableHead>
              <TableHead className="text-right">Entry Price</TableHead>
      <TableHead className="text-right">Exit Price</TableHead>
    <TableHead className="text-right">PnL</TableHead>
      <TableHead className="text-right">PnL %</TableHead>
            </TableRow>
 </TableHeader>
        <TableBody>
       {paginatedTrades.map((trade, index) => (
              <TableRow key={index}>
         <TableCell className="font-mono text-xs">
          {new Date(trade.entry_time).toLocaleString()}
         </TableCell>
     <TableCell className="font-mono text-xs">
        {new Date(trade.exit_time).toLocaleString()}
     </TableCell>
         <TableCell>
  <Badge variant={trade.side === 'long' ? 'default' : 'secondary'}>
   {trade.side === 'long' ? (
    <TrendingUp className="h-3 w-3 mr-1" />
         ) : (
   <TrendingDown className="h-3 w-3 mr-1" />
           )}
    {trade.side.toUpperCase()}
 </Badge>
            </TableCell>
      <TableCell className="text-right font-mono">
     {trade.entry_price?.toFixed(2) || '-'}
</TableCell>
         <TableCell className="text-right font-mono">
           {trade.exit_price?.toFixed(2) || '-'}
   </TableCell>
           <TableCell className={`text-right font-bold ${trade.pnl >= 0 ? 'text-green-500' : 'text-destructive'}`}>
           {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                </TableCell>
      <TableCell className={`text-right font-bold ${trade.pnl_pct >= 0 ? 'text-green-500' : 'text-destructive'}`}>
  {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
</TableCell>
         </TableRow>
 ))}
       </TableBody>
    </Table>
    </div>

   {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
       <p className="text-sm text-muted-foreground">
   Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredTrades.length)} of {filteredTrades.length} trades
      </p>
          <div className="flex gap-2">
 <Button
  variant="outline"
   size="sm"
           onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
           disabled={currentPage === 1}
            >
    Previous
         </Button>
         <span className="flex items-center px-3 text-sm">
   Page {currentPage} of {totalPages}
   </span>
      <Button
              variant="outline"
            size="sm"
   onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
  >
    Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
