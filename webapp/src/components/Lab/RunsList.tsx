import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from '@/components/ui/button';
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

export const useRuns = () => {
    return useQuery({ queryKey: ['runs'], queryFn: fetchRuns });
};

const RunsList: React.FC = () => {
    const { data: runs, isLoading } = useRuns();

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Runs</CardTitle>
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
                                        <a href={run.path} target="_blank" rel="noreferrer">
                                            <Button variant="outline" size="sm">
                                                View Report
                                                <ExternalLink className="ml-2 h-4 w-4" />
                                            </Button>
                                        </a>
                                    </TableCell>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={3} className="text-center h-24 text-muted-foreground">
                                    No runs found. Run a backtest or optimization to see results here.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
};

export default RunsList;
