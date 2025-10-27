import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const fetchPositions = async () => {
    const { data } = await api.get('/api/live/positions');
    return data;
};

export const usePositions = () => {
    return useQuery({ queryKey: ['positions'], queryFn: fetchPositions });
};

const PositionsTable: React.FC = () => {
    const { data: positions, isLoading } = usePositions();

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Positions</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Symbol</TableHead>
                            <TableHead>Side</TableHead>
                            <TableHead className="text-right">Size</TableHead>
                            <TableHead className="text-right">Entry Price</TableHead>
                            <TableHead className="text-right">Mark Price</TableHead>
                            <TableHead className="text-right">Liq. Price</TableHead>
                            <TableHead className="text-right">Margin</TableHead>
                            <TableHead className="text-right">PNL</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            Array.from({ length: 3 }).map((_, i) => (
                                <TableRow key={i}>
                                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-16" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-16" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-16" /></TableCell>
                                </TableRow>
                            ))
                        ) : (
                            positions?.map((position: any) => (
                                <TableRow key={position.symbol}>
                                    <TableCell>{position.symbol}</TableCell>
                                    <TableCell className={position.side === 'buy' ? 'text-green-500' : 'text-red-500'}>
                                        {position.side}
                                    </TableCell>
                                    <TableCell className="text-right">{position.size}</TableCell>
                                    <TableCell className="text-right">{position.entryPrice}</TableCell>
                                    <TableCell className="text-right">{position.markPrice}</TableCell>
                                    <TableCell className="text-right">{position.liqPrice}</TableCell>
                                    <TableCell className="text-right">{position.margin}</TableCell>
                                    <TableCell className={`text-right ${position.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        {position.pnl}
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

export default PositionsTable;
