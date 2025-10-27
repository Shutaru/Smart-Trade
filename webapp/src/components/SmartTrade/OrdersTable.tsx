import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from '../ui/button';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { queryClient } from '@/lib/queryClient';
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

const fetchOrders = async () => {
    const { data } = await api.get('/api/live/orders');
    return data;
};

const cancelOrder = (orderId: string) => {
    return api.post(`/api/live/cancel`, { id: orderId });
};

export const useOrders = () => {
    return useQuery({ queryKey: ['orders'], queryFn: fetchOrders });
};

const OrdersTable: React.FC = () => {
    const { data: orders, isLoading } = useOrders();
    const mutation = useMutation({
        mutationFn: cancelOrder,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['orders'] });
            toast.success("Order cancelled successfully!");
        },
        onError: () => {
            toast.error("Failed to cancel order.");
        }
    });

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Open Orders</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Symbol</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Side</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                            <TableHead className="text-right">Price</TableHead>
                            <TableHead className="text-right">Stop Price</TableHead>
                            <TableHead className="text-right">Filled</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            Array.from({ length: 5 }).map((_, i) => (
                                <TableRow key={i}>
                                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-16" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-20" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-4 w-16" /></TableCell>
                                    <TableCell className="text-right"><Skeleton className="h-8 w-20" /></TableCell>
                                </TableRow>
                            ))
                        ) : (
                            orders?.map((order: any) => (
                                <TableRow key={order.id}>
                                    <TableCell>{order.symbol}</TableCell>
                                    <TableCell>{order.type}</TableCell>
                                    <TableCell className={order.side === 'buy' ? 'text-green-500' : 'text-red-500'}>
                                        {order.side}
                                    </TableCell>
                                    <TableCell className="text-right">{order.amount}</TableCell>
                                    <TableCell className="text-right">{order.price}</TableCell>
                                    <TableCell className="text-right">{order.stopPrice}</TableCell>
                                    <TableCell className="text-right">{order.filled}</TableCell>
                                    <TableCell className="text-right">
                                        <AlertDialog>
                                            <AlertDialogTrigger asChild>
                                                <Button variant="destructive" size="sm">Cancel</Button>
                                            </AlertDialogTrigger>
                                            <AlertDialogContent>
                                                <AlertDialogHeader>
                                                    <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                                                    <AlertDialogDescription>This action will permanently cancel the order.</AlertDialogDescription>
                                                </AlertDialogHeader>
                                                <AlertDialogFooter>
                                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                                    <AlertDialogAction onClick={() => mutation.mutate(order.id)}>Continue</AlertDialogAction>
                                                </AlertDialogFooter>
                                            </AlertDialogContent>
                                        </AlertDialog>
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

export default OrdersTable;
