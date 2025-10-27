import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger, SheetFooter } from "@/components/ui/sheet";
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';
import { PlusCircle } from 'lucide-react';

const fetchProfiles = async () => {
    const { data } = await api.get('/api/profile/list');
    return data.profiles || []; // Corrigir para acessar o array de profiles
};

const createBot = (newBot: any) => {
    return api.post('/api/bots/create', newBot);
};

const botSchema = z.object({
    name: z.string({ message: "O nome deve ter pelo menos 3 caracteres." }).min(3, "O nome deve ter pelo menos 3 caracteres."),
    profile: z.string({ message: "Selecione uma estratégia." }),
    mode: z.enum(["paper", "live"], { message: "Selecione um modo de operação." }),
});

type BotFormValues = z.infer<typeof botSchema>;

const CreateBotSheet: React.FC = () => {
    const { data: profiles, isLoading: isLoadingProfiles } = useQuery({ queryKey: ['profiles'], queryFn: fetchProfiles });
    const { register, handleSubmit, control, formState: { errors } } = useForm<BotFormValues>({
        resolver: zodResolver(botSchema),
    });

    const mutation = useMutation({
        mutationFn: createBot,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bots'] });
            toast.success("Bot criado com sucesso!");
            // TODO: Fechar o Sheet programaticamente
        },
        onError: () => {
            toast.error("Ocorreu um erro ao criar o bot.");
        }
    });

    const onSubmit = (data: BotFormValues) => {
        mutation.mutate(data);
    };

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button>
                    <PlusCircle className="mr-2 h-4 w-4" />
                    Criar Novo Bot
                </Button>
            </SheetTrigger>
            <SheetContent className="w-[400px] sm:w-[540px]">
                <form onSubmit={handleSubmit(onSubmit)}>
                    <SheetHeader>
                        <SheetTitle>Criar Novo Bot</SheetTitle>
                        <SheetDescription>Configure um novo bot de trading automatizado.</SheetDescription>
                    </SheetHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="name" className="text-right">Nome</Label>
                            <Input id="name" {...register("name")} className="col-span-3" />
                            {errors.name && <p className="col-span-4 text-red-500 text-sm text-right">{errors.name.message}</p>}
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="profile" className="text-right">Estratégia</Label>
                            <Controller name="profile" control={control} render={({ field }) => (
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <SelectTrigger className="col-span-3"><SelectValue placeholder="Selecione um perfil..." /></SelectTrigger>
                                    <SelectContent>
                                        {isLoadingProfiles ? <SelectItem value="loading" disabled>A carregar...</SelectItem> :
                                            profiles?.map((p: any) => <SelectItem key={p.path} value={p.path}>{p.path}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            )} />
                            {errors.profile && <p className="col-span-4 text-red-500 text-sm text-right">{errors.profile.message}</p>}
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="mode" className="text-right">Modo</Label>
                            <Controller name="mode" control={control} render={({ field }) => (
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <SelectTrigger className="col-span-3"><SelectValue placeholder="Selecione o modo..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="paper">Paper Trading</SelectItem>
                                        <SelectItem value="live">Live Trading</SelectItem>
                                    </SelectContent>
                                </Select>
                            )} />
                            {errors.mode && <p className="col-span-4 text-red-500 text-sm text-right">{errors.mode.message}</p>}
                        </div>
                    </div>
                    <SheetFooter>
                        <Button type="submit" disabled={mutation.isPending}>
                            {mutation.isPending ? "A criar..." : "Criar Bot"}
                        </Button>
                    </SheetFooter>
                </form>
            </SheetContent>
        </Sheet>
    );
};

export default CreateBotSheet;
