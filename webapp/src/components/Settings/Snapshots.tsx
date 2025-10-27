import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';
import { Skeleton } from "@/components/ui/skeleton";

const fetchSnapshots = async () => {
    const { data } = await api.get('/api/config/snapshots');
    return data.snapshots || []; // Corrigir para acessar o array de snapshots
};

const createSnapshot = () => {
    return api.post('/api/config/snapshot');
};

const rollbackSnapshot = (path: string) => {
    return api.post('/api/config/rollback', null, { params: { path } });
};

const Snapshots: React.FC = () => {
    const { data: snapshots, isLoading } = useQuery({ queryKey: ['snapshots'], queryFn: fetchSnapshots });
    const createMutation = useMutation({
        mutationFn: createSnapshot,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['snapshots'] });
            toast.success("Snapshot created successfully!");
        },
        onError: () => toast.error("Failed to create snapshot.")
    });
    const rollbackMutation = useMutation({
        mutationFn: rollbackSnapshot,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['config', 'snapshots'] });
            toast.success("Rollback successful!");
        },
        onError: () => toast.error("Failed to rollback.")
    });

    return (
        <Card className="shadow-soft">
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>Snapshots</CardTitle>
                    <CardDescription>Create and restore configuration snapshots.</CardDescription>
                </div>
                <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
                    {createMutation.isPending ? "Creating..." : "Create Snapshot"}
                </Button>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Path</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            Array.from({ length: 3 }).map((_, i) => (
                                <TableRow key={i}>
                                    <TableCell><Skeleton className="h-4 w-64" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-8 w-24" /></TableCell>
                                </TableRow>
                            ))
                        ) : (
                            snapshots?.map((snapshot: any) => (
                                <TableRow key={snapshot.path}>
                                    <TableCell>{snapshot.path}</TableCell>
                                    <TableCell className="text-right">
                                        <Button onClick={() => rollbackMutation.mutate(snapshot.path)} disabled={rollbackMutation.isPending} variant="outline" size="sm">
                                            {rollbackMutation.isPending ? "Rolling back..." : "Rollback"}
                                        </Button>
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

export default Snapshots;
