import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';
import { Skeleton } from "@/components/ui/skeleton";

const fetchProfiles = async () => { 
    const { data } = await api.get('/api/profile/list'); 
    return data.profiles || []; // Corrigir para acessar o array de profiles
};
const applyProfile = (path: string) => api.post('/api/profile/apply', null, { params: { path } });
const exportProfile = (name: string) => api.post('/api/profile/export', null, { params: { name } });
const importProfile = (text: string) => api.post('/api/profile/import_text', { text });

const Profiles: React.FC = () => {
    const [importText, setImportText] = useState('');
    const [exportName, setExportName] = useState('');
    const { data: profiles, isLoading } = useQuery({ queryKey: ['profiles'], queryFn: fetchProfiles });
    
    const applyMutation = useMutation({ mutationFn: applyProfile, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['config'] }); toast.success("Profile applied!"); } });
    const exportMutation = useMutation({ mutationFn: exportProfile, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['profiles'] }); toast.success("Profile exported!"); } });
    const importMutation = useMutation({ mutationFn: importProfile, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['profiles'] }); toast.success("Profile imported!"); } });

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card className="shadow-soft">
                <CardHeader>
                    <CardTitle>Available Profiles</CardTitle>
                    <CardDescription>Apply a saved configuration profile.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader><TableRow><TableHead>Path</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
                        <TableBody>
                            {isLoading ? Array.from({ length: 3 }).map((_, i) => (
                                <TableRow key={i}><TableCell><Skeleton className="h-4 w-48" /></TableCell><TableCell className="text-right"><Skeleton className="h-8 w-20" /></TableCell></TableRow>
                            )) : profiles?.map((profile: any) => (
                                <TableRow key={profile.path}>
                                    <TableCell>{profile.path}</TableCell>
                                    <TableCell className="text-right"><Button onClick={() => applyMutation.mutate(profile.path)} variant="outline" size="sm">Apply</Button></TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
            <div className="space-y-8">
                <Card className="shadow-soft">
                    <CardHeader><CardTitle>Export Profile</CardTitle></CardHeader>
                    <CardContent><Input value={exportName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setExportName(e.target.value)} placeholder="New profile name..." /></CardContent>
                    <CardFooter><Button onClick={() => exportMutation.mutate(exportName)} disabled={exportMutation.isPending || !exportName}>Export Current Config</Button></CardFooter>
                </Card>
                <Card className="shadow-soft">
                    <CardHeader><CardTitle>Import Profile</CardTitle></CardHeader>
                    <CardContent><Textarea value={importText} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setImportText(e.target.value)} placeholder="Paste YAML config here..." /></CardContent>
                    <CardFooter><Button onClick={() => importMutation.mutate(importText)} disabled={importMutation.isPending || !importText}>Import</Button></CardFooter>
                </Card>
            </div>
        </div>
    );
};

export default Profiles;
