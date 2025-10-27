import React, { useState, useMemo } from 'react';
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { toast } from "sonner";

const orderSchema = z.object({
  type: z.enum(["market", "limit", "stop", "take_profit", "stop_loss"]),
  side: z.enum(["buy", "sell"]),
  amount: z.string().min(1, "Amount is required"),
  price: z.string().optional(),
  stopPrice: z.string().optional(),
  reduceOnly: z.boolean().optional(),
  postOnly: z.boolean().optional(),
  takeProfit: z.string().optional(),
  stopLoss: z.string().optional(),
});

type OrderFormValues = z.infer<typeof orderSchema>;

const fetchConfig = async () => {
    const { data } = await api.get('/api/config/read');
    return data;
};

const OrderPanel: React.FC = () => {
    const [isBracket, setIsBracket] = useState(false);
    const { register, handleSubmit, control, watch, reset, formState: { errors } } = useForm<OrderFormValues>({
        resolver: zodResolver(orderSchema),
    });

    const { data: config } = useQuery({ queryKey: ['config'], queryFn: fetchConfig });

    const mutation = useMutation({
        mutationFn: (newOrder: Partial<OrderFormValues>) => api.post('/api/live/order', newOrder),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['orders'] });
            toast.success("Order placed successfully!");
            reset();
        },
        onError: () => {
            toast.error("Failed to place order.");
        }
    });

    const onSubmit = (data: OrderFormValues) => {
        mutation.mutate(data);
        if (isBracket && data.takeProfit && data.stopLoss) {
            const tpOrder: Partial<OrderFormValues> = { type: "take_profit", side: data.side === "buy" ? "sell" : "buy", amount: data.amount, price: data.takeProfit, reduceOnly: true };
            const slOrder: Partial<OrderFormValues> = { type: "stop_loss", side: data.side === "buy" ? "sell" : "buy", amount: data.amount, stopPrice: data.stopLoss, reduceOnly: true };
            mutation.mutate(tpOrder);
            mutation.mutate(slOrder);
        }
    };
    
    const amount = watch("amount");
    const price = watch("price");
    const notionalValue = useMemo(() => parseFloat(amount) * parseFloat(price || "0"), [amount, price]);
    const isWithinLimits = notionalValue <= (config?.risk_limits?.max_notional || Infinity);

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Place Order</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label htmlFor="type">Type</Label>
                            <Controller name="type" control={control} render={({ field }) => (
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="market">Market</SelectItem>
                                        <SelectItem value="limit">Limit</SelectItem>
                                        <SelectItem value="stop">Stop</SelectItem>
                                        <SelectItem value="take_profit">Take Profit</SelectItem>
                                        <SelectItem value="stop_loss">Stop Loss</SelectItem>
                                    </SelectContent>
                                </Select>
                            )} />
                        </div>
                        <div>
                            <Label htmlFor="side">Side</Label>
                            <Controller name="side" control={control} render={({ field }) => (
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <SelectTrigger><SelectValue placeholder="Select side" /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="buy">Buy</SelectItem>
                                        <SelectItem value="sell">Sell</SelectItem>
                                    </SelectContent>
                                </Select>
                            )} />
                        </div>
                    </div>
                    <div>
                        <Label htmlFor="amount">Amount</Label>
                        <Input id="amount" {...register("amount")} />
                        {errors.amount && <p className="text-red-500 text-sm mt-1">{errors.amount.message}</p>}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label htmlFor="price">Price</Label>
                            <Input id="price" {...register("price")} />
                        </div>
                        <div>
                            <Label htmlFor="stopPrice">Stop Price</Label>
                            <Input id="stopPrice" {...register("stopPrice")} />
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <Controller name="reduceOnly" control={control} render={({ field }) => (<Switch id="reduceOnly" checked={field.value} onCheckedChange={field.onChange} />)} />
                            <Label htmlFor="reduceOnly">Reduce Only</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Controller name="postOnly" control={control} render={({ field }) => (<Switch id="postOnly" checked={field.value} onCheckedChange={field.onChange} />)} />
                            <Label htmlFor="postOnly">Post Only</Label>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        <Switch id="bracket" checked={isBracket} onCheckedChange={setIsBracket} />
                        <Label htmlFor="bracket">Bracket Order</Label>
                    </div>
                    {isBracket && (
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label htmlFor="takeProfit">Take Profit</Label>
                                <Input id="takeProfit" {...register("takeProfit")} />
                            </div>
                            <div>
                                <Label htmlFor="stopLoss">Stop Loss</Label>
                                <Input id="stopLoss" {...register("stopLoss")} />
                            </div>
                        </div>
                    )}
                    <div className="p-4 bg-surface rounded-lg">
                        <p>Notional Value: ${notionalValue.toFixed(2)}</p>
                        {isWithinLimits ? (
                            <p className="text-green-500 text-sm">Within risk limits</p>
                        ) : (
                            <p className="text-red-500 text-sm">Exceeds risk limits</p>
                        )}
                    </div>
                    <Button type="submit" disabled={!isWithinLimits || mutation.isPending} className="w-full">
                        {mutation.isPending ? "Placing Order..." : "Submit Order"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
};

export default OrderPanel;
