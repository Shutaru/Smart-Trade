import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from '@/components/ui/skeleton';
import { Bot, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const fetchBots = async () => {
    const { data } = await api.get('/api/bots/list');
    return data;
};

const ActiveBotsList: React.FC = () => {
    const { data: bots, isLoading } = useQuery({ queryKey: ['bots'], queryFn: fetchBots });

    const activeBots = bots?.filter((bot: any) => bot.status === 'Running') || [];

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Bots Ativos</CardTitle>
                <CardDescription>Monitorize os bots que estão a operar.</CardDescription>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <div className="space-y-4">
                        <Skeleton className="h-12 w-full" />
                        <Skeleton className="h-12 w-full" />
                        <Skeleton className="h-12 w-full" />
                    </div>
                ) : activeBots.length > 0 ? (
                    <div className="space-y-4">
                        {activeBots.map((bot: any) => (
                            <div key={bot.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-secondary">
                                <div className="flex items-center space-x-3">
                                    <Bot className="h-5 w-5 text-muted-foreground" />
                                    <div>
                                        <p className="font-medium">{bot.name}</p>
                                        <Badge variant={bot.mode === 'Live' ? 'destructive' : 'secondary'}>{bot.mode}</Badge>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-4">
                                    <span className={`font-semibold ${bot.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        {bot.pnl.toFixed(2)}%
                                    </span>
                                    <Link to={`/bots/${bot.id}`}>
                                        <Button variant="outline" size="icon">
                                            <Eye className="h-4 w-4" />
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center text-muted-foreground h-24 flex items-center justify-center">
                        Nenhum bot ativo de momento.
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default ActiveBotsList;
