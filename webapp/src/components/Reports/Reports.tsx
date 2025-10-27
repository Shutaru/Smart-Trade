import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import { Skeleton } from "@/components/ui/skeleton";
import { ExternalLink } from 'lucide-react';

const fetchRuns = async () => {
    const { data } = await api.get('/api/runs/list');
    // A API retorna { backtest: [], grid: [], wf: [], ml_bt: [], ml_optuna: [] }
    // Vamos combinar todos os runs num único array
    const allRuns = [
        ...(data.backtest || []).map((r: any) => ({ ...r, type: 'backtest' })),
        ...(data.grid || []).map((r: any) => ({ ...r, type: 'grid' })),
     ...(data.wf || []).map((r: any) => ({ ...r, type: 'walkforward' })),
        ...(data.ml_bt || []).map((r: any) => ({ ...r, type: 'ml_bt' })),
        ...(data.ml_optuna || []).map((r: any) => ({ ...r, type: 'ml_optuna' })),
    ];
    return allRuns;
};

const Reports: React.FC = () => {
    const { data: runs, isLoading } = useQuery({ queryKey: ['runs'], queryFn: fetchRuns });

    const handleViewReport = (runPath: string) => {
     // Verificar se existe report.html no path
      const reportUrl = `${runPath}/report.html`;
     window.open(reportUrl, '_blank');
    };

    return (
        <div>
    <h1 className="text-3xl font-bold mb-6">Reports</h1>
    <Card className="shadow-soft">
         <CardHeader>
     <CardTitle>Available Reports</CardTitle>
       <CardDescription>View reports from your backtests and optimizations.</CardDescription>
        </CardHeader>
                <CardContent>
    <Table>
      <TableHeader>
      <TableRow>
    <TableHead>Name</TableHead>
    <TableHead>Date</TableHead>
    <TableHead className="text-right">Actions</TableHead>
</TableRow>
           </TableHeader>
                <TableBody>
   {isLoading ? (
   Array.from({ length: 5 }).map((_, i) => (
         <TableRow key={i}>
 <TableCell><Skeleton className="h-4 w-48" /></TableCell>
  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
         <TableCell className="text-right"><Skeleton className="h-8 w-24" /></TableCell>
             </TableRow>
   ))
    ) : runs && runs.length > 0 ? (
        runs.map((run: any) => (
  <TableRow key={`${run.type}-${run.name}`}>
  <TableCell className="font-medium">
   <div className="flex items-center gap-2">
    <span className="text-xs px-2 py-1 rounded bg-secondary">{run.type}</span>
      <span>{run.name}</span>
   </div>
   </TableCell>
    <TableCell>{new Date(run.mtime * 1000).toLocaleString()}</TableCell>
           <TableCell className="text-right">
    <Button onClick={() => handleViewReport(run.path)} variant="outline" size="sm">
   <ExternalLink className="mr-2 h-4 w-4" /> Open Report
      </Button>
      </TableCell>
       </TableRow>
       ))
      ) : (
        <TableRow>
 <TableCell colSpan={3} className="text-center h-24 text-muted-foreground">
            No reports found. Run a backtest or optimization to generate reports.
        </TableCell>
     </TableRow>
        )}
           </TableBody>
   </Table>
       </CardContent>
     </Card>
        </div>
    );
};

export default Reports;
