import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Eye, Loader2, CheckCircle2, XCircle, Clock, Filter } from 'lucide-react';

interface Run {
    run_id: string;
    status: string;
    progress: number;
    started_at?: number;
    completed_at?: number;
}

const fetchRuns = async (): Promise<Run[]> => {
    const res = await fetch('/api/lab/runs?limit=50');
    if (!res.ok) throw new Error('Failed to fetch runs');
    return res.json();
};

const RunsList: React.FC = () => {
    const navigate = useNavigate();
 const [statusFilter, setStatusFilter] = useState<string>('all');
    const { data: runs, isLoading } = useQuery({
     queryKey: ['lab-runs'],
      queryFn: fetchRuns,
        refetchInterval: 5000 // Refresh every 5 seconds
    });

    const getStatusBadge = (status: string) => {
        const config: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', icon: React.ReactNode }> = {
            completed: { variant: 'default', icon: <CheckCircle2 className="h-3 w-3" /> },
            running: { variant: 'secondary', icon: <Loader2 className="h-3 w-3 animate-spin" /> },
            failed: { variant: 'destructive', icon: <XCircle className="h-3 w-3" /> },
            pending: { variant: 'outline', icon: <Clock className="h-3 w-3" /> }
        };

        const { variant, icon } = config[status] || config.pending;

        return (
            <Badge variant={variant} className="gap-1">
                {icon}
       {status}
         </Badge>
   );
    };

    const filteredRuns = runs?.filter(run => 
        statusFilter === 'all' || run.status === statusFilter
    ) || [];

    return (
        <Card className="shadow-soft">
            <CardHeader>
          <div className="flex items-center justify-between">
         <div>
         <CardTitle>Recent Runs</CardTitle>
         <CardDescription>View and manage your backtest runs</CardDescription>
 </div>
    <div className="flex items-center gap-2">
  <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={statusFilter} onValueChange={setStatusFilter}>
      <SelectTrigger className="w-[140px]">
     <SelectValue />
       </SelectTrigger>
         <SelectContent>
     <SelectItem value="all">All Status</SelectItem>
           <SelectItem value="running">Running</SelectItem>
         <SelectItem value="completed">Completed</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
    <SelectItem value="pending">Pending</SelectItem>
          </SelectContent>
           </Select>
      </div>
        </div>
       </CardHeader>
  <CardContent>
     {isLoading ? (
  <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
     <Skeleton key={i} className="h-16 w-full" />
     ))}
 </div>
          ) : filteredRuns.length > 0 ? (
        <Table>
    <TableHeader>
              <TableRow>
  <TableHead>Run ID</TableHead>
             <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
       <TableHead>Completed</TableHead>
        <TableHead className="text-right">Actions</TableHead>
 </TableRow>
         </TableHeader>
       <TableBody>
 {filteredRuns.map((run) => (
     <TableRow key={run.run_id} className="cursor-pointer hover:bg-muted/50">
         <TableCell className="font-mono text-sm">
    {run.run_id.substring(0, 8)}...
           </TableCell>
         <TableCell>
   {getStatusBadge(run.status)}
   </TableCell>
  <TableCell>
{run.started_at 
     ? new Date(run.started_at * 1000).toLocaleString()
 : '-'
          }
  </TableCell>
       <TableCell>
        {run.completed_at 
     ? new Date(run.completed_at * 1000).toLocaleString()
    : run.status === 'running' ? 'In progress...' : '-'
      }
        </TableCell>
        <TableCell className="text-right">
      <Button
       variant="ghost"
        size="sm"
             onClick={() => navigate(`/lab/results/${run.run_id}`)}
                 className="gap-2"
    >
         <Eye className="h-4 w-4" />
           View
         </Button>
    </TableCell>
          </TableRow>
           ))}
 </TableBody>
            </Table>
           ) : (
   <div className="text-center py-12 text-muted-foreground">
    <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
           <p className="text-lg font-medium">No runs found</p>
         <p className="text-sm mt-2">
       {statusFilter !== 'all' 
     ? `No runs with status "${statusFilter}"`
           : 'Run a backtest to see results here'
  }
               </p>
     </div>
                )}
   </CardContent>
   </Card>
    );
};

export default RunsList;
