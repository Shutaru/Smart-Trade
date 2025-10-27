import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Skeleton } from "@/components/ui/skeleton";
import { ExternalLink, Eye } from 'lucide-react';

const fetchRuns = async () => {
    const { data } = await api.get('/api/runs/list');
    return data;
};

const Reports: React.FC = () => {
    const { data: runs, isLoading } = useQuery({ queryKey: ['runs'], queryFn: fetchRuns });
    const [selectedReport, setSelectedReport] = useState<string | null>(null);

    const handleViewReport = (runName: string) => {
        if (runName.endsWith('.html')) {
            setSelectedReport(`/api/runs/get?name=${runName}`);
        } else {
            window.open(`/api/runs/get?name=${runName}`, '_blank');
        }
    };

    return (
        <Dialog onOpenChange={() => setSelectedReport(null)}>
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
                            ) : (
                                runs?.map((run: any) => (
                                    <TableRow key={run.name}>
                                        <TableCell className="font-medium">{run.name}</TableCell>
                                        <TableCell>{new Date(run.date).toLocaleString()}</TableCell>
                                        <TableCell className="text-right">
                                            {run.name.endsWith('.html') ? (
                                                <DialogTrigger asChild>
                                                    <Button onClick={() => handleViewReport(run.name)} variant="outline" size="sm">
                                                        <Eye className="mr-2 h-4 w-4" /> View
                                                    </Button>
                                                </DialogTrigger>
                                            ) : (
                                                <Button onClick={() => handleViewReport(run.name)} variant="outline" size="sm">
                                                    <ExternalLink className="mr-2 h-4 w-4" /> Open
                                                </Button>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
            <DialogContent className="max-w-4xl h-3/4">
                <DialogHeader>
                    <DialogTitle>Report Viewer</DialogTitle>
                </DialogHeader>
                {selectedReport && (
                    <iframe src={selectedReport} title="Report" className="w-full h-full border-0 rounded-lg" />
                )}
            </DialogContent>
        </Dialog>
    );
};

export default Reports;
