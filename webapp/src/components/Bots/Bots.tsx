import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, Pause, StopCircle, Eye } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';
import { Skeleton } from "@/components/ui/skeleton";
import CreateBotSheet from './CreateBotSheet';
import DeleteBotDialog from './DeleteBotDialog';
import { Link } from 'react-router-dom';

const fetchBots = async () => {
    const { data } = await api.get('/api/bots/list');
    return data.bots || []; // Corrigir para acessar o array de bots
};

const controlBot = (action: 'start' | 'stop' | 'pause', botId: number) => {
    return api.post(`/api/bots/${action}`, { id: botId });
};

const Bots: React.FC = () => {
    const { data: bots, isLoading } = useQuery({ queryKey: ['bots'], queryFn: fetchBots });

    const controlMutation = useMutation({
        mutationFn: ({ action, botId }: { action: 'start' | 'stop' | 'pause', botId: number }) => controlBot(action, botId),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['bots'] });
            toast.success(`Bot action '${variables.action}' executed successfully.`);
        },
        onError: (_, variables) => {
            toast.error(`Failed to execute '${variables.action}' on bot.`);
        }
    });

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'Running': return <Badge variant="default" className="bg-green-500 hover:bg-green-600">Running</Badge>;
            case 'Paused': return <Badge variant="secondary">Paused</Badge>;
            case 'Stopped': return <Badge variant="destructive">Stopped</Badge>;
            default: return <Badge>{status}</Badge>;
        }
    };
    
    // Mock data if API returns nothing for development
    const displayBots = bots || [];

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Bots</h1>
                <CreateBotSheet />
            </div>

            <Card className="shadow-soft">
                <CardHeader>
                    <CardTitle>Meus Bots</CardTitle>
                    <CardDescription>Gestão dos seus bots de trading automatizados.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Nome</TableHead>
                                <TableHead>Estado</TableHead>
                                <TableHead>Modo</TableHead>
                                <TableHead className="text-right">PnL (%)</TableHead>
                                <TableHead className="text-right">Ações</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                Array.from({ length: 3 }).map((_, i) => (
                                    <TableRow key={`skeleton-${i}`}>
                                        <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                                        <TableCell><Skeleton className="h-6 w-20 rounded-full" /></TableCell>
                                        <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                                        <TableCell className="text-right"><Skeleton className="h-4 w-16 ml-auto" /></TableCell>
                                        <TableCell className="text-right space-x-2">
                                            <Skeleton className="h-8 w-8 inline-block" />
                                            <Skeleton className="h-8 w-8 inline-block" />
                                            <Skeleton className="h-8 w-8 inline-block" />
                                            <Skeleton className="h-8 w-8 inline-block" />
                                            <Skeleton className="h-8 w-8 inline-block" />
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : displayBots && displayBots.length > 0 ? (
                                displayBots.map((bot: any) => (
                                    <TableRow key={bot.id}>
                                        <TableCell className="font-medium">{bot.name}</TableCell>
                                        <TableCell>{getStatusBadge(bot.status)}</TableCell>
                                        <TableCell>{bot.mode}</TableCell>
                                        <TableCell className={`text-right ${bot.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                            {bot.pnl.toFixed(2)}%
                                        </TableCell>
                                        <TableCell className="text-right space-x-2">
                                            <Button variant="outline" size="icon" onClick={() => controlMutation.mutate({ action: 'start', botId: bot.id })}><Play className="h-4 w-4" /></Button>
                                            <Button variant="outline" size="icon" onClick={() => controlMutation.mutate({ action: 'pause', botId: bot.id })}><Pause className="h-4 w-4" /></Button>
                                            <Button variant="outline" size="icon" onClick={() => controlMutation.mutate({ action: 'stop', botId: bot.id })}><StopCircle className="h-4 w-4" /></Button>
                                            <Link to={`/bots/${bot.id}`}>
                                                <Button variant="outline" size="icon"><Eye className="h-4 w-4" /></Button>
                                            </Link>
                                            <DeleteBotDialog botId={bot.id} botName={bot.name} />
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center h-24">Ainda não tem bots. Crie um para começar.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
};

export default Bots;
