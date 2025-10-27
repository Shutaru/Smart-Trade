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
    return data;
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
                        ) : (
                            runs?.map((run: any) => (
                                <TableRow key={run.name}>
                                    <TableCell className="font-medium">{run.name}</TableCell>
                                    <TableCell>{new Date(run.date).toLocaleString()}</TableCell>
                                    <TableCell className="text-right">
                                        <a href={`/api/runs/get?name=${run.name}`} target="_blank" rel="noreferrer">
                                            <Button variant="outline" size="sm">
                                                View Report
                                                <ExternalLink className="ml-2 h-4 w-4" />
                                            </Button>
                                        </a>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
};

export default RunsList;
