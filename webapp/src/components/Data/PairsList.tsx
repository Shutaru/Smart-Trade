import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';
import { Check, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';

const fetchPairs = async () => {
    const { data } = await api.get('/api/bitget/pairs');
    return data;
};

const setSymbol = (symbol: string) => {
    return api.post('/api/config/set_symbol_db', null, { params: { symbol, db_path: `data/${symbol}.db` } });
};

const PairsList: React.FC = () => {
    const [open, setOpen] = useState(false);
    const [selectedPair, setSelectedPair] = useState<string | null>(null);
    const { data: pairs, isLoading } = useQuery({ queryKey: ['pairs'], queryFn: fetchPairs });
    const mutation = useMutation({
        mutationFn: setSymbol,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['config'] });
            toast.success("Symbol updated successfully!");
        },
        onError: () => {
            toast.error("Failed to update symbol.");
        }
    });

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Available Pairs</CardTitle>
                <CardDescription>Select a pair to use in the configuration.</CardDescription>
            </CardHeader>
            <CardContent>
                <Popover open={open} onOpenChange={setOpen}>
                    <PopoverTrigger asChild>
                        <Button variant="outline" role="combobox" aria-expanded={open} className="w-full justify-between">
                            {selectedPair || "Select a pair..."}
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
                        <Command>
                            <CommandInput placeholder="Search pair..." />
                            <CommandEmpty>No pair found.</CommandEmpty>
                            <CommandGroup>
                                {isLoading ? (
                                    <CommandItem>Loading...</CommandItem>
                                ) : (
                                    pairs?.map((pair: any) => (
                                        <CommandItem
                                            key={pair.symbol}
                                            onSelect={() => {
                                                setSelectedPair(pair.symbol);
                                                setOpen(false);
                                            }}
                                        >
                                            <Check className={cn("mr-2 h-4 w-4", selectedPair === pair.symbol ? "opacity-100" : "opacity-0")} />
                                            {pair.symbol}
                                        </CommandItem>
                                    ))
                                )}
                            </CommandGroup>
                        </Command>
                    </PopoverContent>
                </Popover>
            </CardContent>
            <CardFooter>
                <Button onClick={() => selectedPair && mutation.mutate(selectedPair)} disabled={!selectedPair || mutation.isPending}>
                    {mutation.isPending ? "Applying..." : "Apply to Config"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default PairsList;
