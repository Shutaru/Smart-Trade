import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GitCompare, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

interface Run {
    run_id: string;
    status: string;
 progress: number;
   started_at?: number;
    completed_at?: number;
}

interface ComparisonData {
    run_id: string;
  name: string;
    equity: Array<{ time: number; equity: number }>;
    metrics: Record<string, number>;
    status: string;
}

export function CompareRuns() {
    const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
    const [comparisonData, setComparisonData] = useState<ComparisonData[] | null>(null);

    const { data: runs } = useQuery({
queryKey: ['lab-runs'],
        queryFn: async (): Promise<Run[]> => {
  const res = await fetch('/api/lab/runs?limit=50');
            if (!res.ok) throw new Error('Failed to fetch runs');
    return res.json();
    }
    });

  const compareMutation = useMutation({
        mutationFn: async () => {
   const res = await fetch('/api/lab/compare', {
   method: 'POST',
    headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(selectedRuns)
  });
        if (!res.ok) throw new Error('Failed to compare runs');
            return res.json();
        },
        onSuccess: (data) => {
setComparisonData(data.runs);
        }
  });

    const toggleRun = (runId: string) => {
setSelectedRuns(prev => 
       prev.includes(runId) 
         ? prev.filter(id => id !== runId)
      : [...prev, runId]
        );
    };

    const completedRuns = runs?.filter(r => r.status === 'completed') || [];

    return (
        <div className="container mx-auto py-8 space-y-6">
            <div>
     <h1 className="text-3xl font-bold">Compare Runs</h1>
  <p className="text-muted-foreground">Select runs to overlay equity curves and compare metrics</p>
          </div>

         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Run Selection */}
 <Card className="lg:col-span-1">
         <CardHeader>
     <CardTitle>Select Runs ({selectedRuns.length}/10)</CardTitle>
        <CardDescription>Choose up to 10 completed runs</CardDescription>
         </CardHeader>
          <CardContent>
       <div className="max-h-[500px] overflow-y-auto space-y-2 pr-2">
       {completedRuns.map((run) => (
      <Button
       key={run.run_id}
      variant={selectedRuns.includes(run.run_id) ? 'default' : 'outline'}
 size="sm"
   onClick={() => toggleRun(run.run_id)}
    className="w-full justify-start"
      >
 <div className="flex-1 text-left">
      <p className="text-sm font-mono">{run.run_id.substring(0, 8)}...</p>
       <p className="text-xs opacity-70">
         {run.completed_at ? new Date(run.completed_at * 1000).toLocaleString() : '-'}
     </p>
        </div>
             </Button>
          ))}
    </div>

           <Button
            onClick={() => compareMutation.mutate()}
disabled={selectedRuns.length < 2 || compareMutation.isPending}
  className="w-full mt-4 gap-2"
     >
{compareMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
   <GitCompare className="h-4 w-4" />
      Compare {selectedRuns.length} Runs
    </Button>
    </CardContent>
      </Card>

        {/* Comparison Results */}
       <div className="lg:col-span-2 space-y-6">
      {!comparisonData ? (
           <Card>
          <CardContent className="flex items-center justify-center h-[500px]">
           <div className="text-center text-muted-foreground">
        <GitCompare className="h-16 w-16 mx-auto mb-4 opacity-50" />
 <p>Select at least 2 runs and click Compare</p>
     </div>
          </CardContent>
       </Card>
   ) : (
       <>
             {/* Equity Curves Overlay */}
      <Card>
       <CardHeader>
      <CardTitle>Equity Curves Overlay</CardTitle>
   <CardDescription>Comparing {comparisonData.length} runs</CardDescription>
</CardHeader>
            <CardContent>
    <div className="h-[400px] flex items-center justify-center bg-muted rounded-lg">
        <p className="text-muted-foreground">
       Equity curve chart would render here with Lightweight Charts
   </p>
                  </div>
    </CardContent>
            </Card>

     {/* Metrics Comparison Table */}
          <Card>
         <CardHeader>
         <CardTitle>Metrics Comparison</CardTitle>
          </CardHeader>
        <CardContent>
  <div className="overflow-x-auto">
 <table className="w-full text-sm">
   <thead>
    <tr className="border-b">
         <th className="text-left p-2">Run ID</th>
          <th className="text-right p-2">Sharpe</th>
 <th className="text-right p-2">Total Profit</th>
    <th className="text-right p-2">Max DD</th>
       <th className="text-right p-2">Trades</th>
     <th className="text-right p-2">Win Rate</th>
          </tr>
             </thead>
    <tbody>
       {comparisonData.map((run, idx) => {
             const colors = ['text-blue-500', 'text-green-500', 'text-orange-500', 'text-purple-500', 'text-pink-500'];
   const metrics = JSON.parse(run.metrics as any);
     
   return (
            <tr key={run.run_id} className="border-b hover:bg-muted/50">
          <td className="p-2">
  <Badge variant="outline" className={colors[idx % colors.length]}>
 {run.run_id.substring(0, 8)}
   </Badge>
          </td>
               <td className="text-right p-2 font-mono">{metrics.sharpe?.toFixed(2) || '-'}</td>
            <td className="text-right p-2 font-mono">{metrics.total_profit?.toFixed(2) || '-'}</td>
   <td className="text-right p-2 font-mono">{metrics.max_dd?.toFixed(2) || '-'}</td>
       <td className="text-right p-2 font-mono">{metrics.trades || '-'}</td>
      <td className="text-right p-2 font-mono">{metrics.win_rate?.toFixed(1)}%</td>
           </tr>
     );
        })}
  </tbody>
      </table>
     </div>
       </CardContent>
                   </Card>
         </>
         )}
       </div>
         </div>
        </div>
    );
}
