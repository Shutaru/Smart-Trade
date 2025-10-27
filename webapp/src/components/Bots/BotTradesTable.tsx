import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface BotTradesTableProps {
    data: any[]; // Assumindo uma lista de trades
}

const BotTradesTable: React.FC<BotTradesTableProps> = ({ data }) => {
    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Histórico de Trades</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Data</TableHead>
                            <TableHead>Par</TableHead>
                            <TableHead>Lado</TableHead>
                            <TableHead className="text-right">Preço</TableHead>
                            <TableHead className="text-right">Quantidade</TableHead>
                            <TableHead className="text-right">PnL</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.map((trade) => (
                            <TableRow key={trade.id}>
                                <TableCell>{new Date(trade.timestamp).toLocaleString()}</TableCell>
                                <TableCell>{trade.symbol}</TableCell>
                                <TableCell className={trade.side === 'buy' ? 'text-green-500' : 'text-red-500'}>{trade.side}</TableCell>
                                <TableCell className="text-right">{trade.price.toFixed(2)}</TableCell>
                                <TableCell className="text-right">{trade.amount}</TableCell>
                                <TableCell className={`text-right ${trade.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>{trade.pnl.toFixed(2)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
};

export default BotTradesTable;
