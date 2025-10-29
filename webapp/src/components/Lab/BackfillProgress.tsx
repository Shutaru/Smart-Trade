/**
 * Backfill Progress Component
 * 
 * Shows real-time progress during data backfill operations
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Loader2, AlertCircle, Clock, Database } from 'lucide-react';
import type { BackfillResult } from '@/lib/api-lab';

interface BackfillProgressProps {
  results: BackfillResult[];
  totalCandles: number;
  totalFeatures: number;
  isLoading: boolean;
}

export function BackfillProgress({ results, totalCandles, totalFeatures, isLoading }: BackfillProgressProps) {
  const [animatedCount, setAnimatedCount] = useState(0);

  // Animate candle count
  useEffect(() => {
    if (totalCandles > 0) {
      const duration = 1000; // 1 second animation
      const steps = 30;
      const increment = totalCandles / steps;
      let current = 0;

      const timer = setInterval(() => {
        current += increment;
        if (current >= totalCandles) {
       setAnimatedCount(totalCandles);
     clearInterval(timer);
        } else {
          setAnimatedCount(Math.floor(current));
        }
}, duration / steps);

 return () => clearInterval(timer);
    }
  }, [totalCandles]);

  const successCount = results.filter(r => r.candles_inserted > 0).length;
  const failedCount = results.filter(r => r.candles_inserted === 0).length;
  const progress = results.length > 0 ? (successCount / results.length) * 100 : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isLoading ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
        Backfilling Data...
   </>
          ) : (
     <>
   <CheckCircle2 className="h-5 w-5 text-green-500" />
           Backfill Complete
         </>
  )}
        </CardTitle>
        <CardDescription>
          Downloaded historical OHLCV data and calculated technical indicators
        </CardDescription>
      </CardHeader>
 <CardContent className="space-y-6">
        {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
  <div className="space-y-2">
  <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Database className="h-4 w-4" />
      Candles
  </div>
            <div className="text-2xl font-bold">
        {animatedCount.toLocaleString()}
       </div>
      <Progress value={progress} className="h-2" />
          </div>

          <div className="space-y-2">
   <div className="flex items-center gap-2 text-sm text-muted-foreground">
  <CheckCircle2 className="h-4 w-4" />
              Features
         </div>
  <div className="text-2xl font-bold">
    {totalFeatures.toLocaleString()}
   </div>
            <div className="text-xs text-muted-foreground">
        {results.length} combinations
     </div>
        </div>

       <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
    <Clock className="h-4 w-4" />
      Status
       </div>
 <div className="flex gap-2">
        <Badge variant="default" className="bg-green-500">
      {successCount} Success
    </Badge>
 {failedCount > 0 && (
       <Badge variant="destructive">
 {failedCount} Failed
         </Badge>
           )}
       </div>
     </div>
</div>

  {/* Detailed Results */}
        {results.length > 0 && (
          <div className="space-y-2">
   <h4 className="text-sm font-medium">Details</h4>
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
    {results.map((result, i) => (
     <div
         key={i}
      className={cn(
  'flex items-center justify-between p-3 rounded-lg border',
  result.candles_inserted > 0
   ? 'border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/20'
         : 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/20'
        )}
         >
       <div className="flex items-center gap-3">
               {result.candles_inserted > 0 ? (
<CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
<AlertCircle className="h-4 w-4 text-red-600" />
)}
     <div>
  <div className="font-medium text-sm">
        {result.symbol} @ {result.timeframe}
</div>
         <div className="text-xs text-muted-foreground">
                {result.db_path.split('/').pop()}
       </div>
       </div>
          </div>
  <div className="text-right">
<div className="font-medium text-sm">
        {result.candles_inserted.toLocaleString()}
    </div>
         <div className="text-xs text-muted-foreground">
   {result.features_inserted > 0 && `${result.features_inserted} features`}
        </div>
      </div>
    </div>
              ))}
     </div>
      </div>
        )}
      </CardContent>
    </Card>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}
