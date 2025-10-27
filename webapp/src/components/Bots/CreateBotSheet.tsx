import { useState } from 'react';
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

interface Profile {
    path: string;
    name: string;
    mtime?: number;
}

interface BotCreateRequest {
    name: string;
    profile: string;
    mode: 'paper' | 'live';
}

const fetchProfiles = async (): Promise<Profile[]> => {
    const { data } = await api.get('/api/profile/list');
    return data.profiles || [];
};

const createBot = (newBot: BotCreateRequest) => {
    return api.post('/api/bots/create', newBot);
};

const botSchema = z.object({
    name: z.string().min(3, "O nome deve ter pelo menos 3 caracteres."),
    profile: z.string().min(1, "Selecione uma estratégia."),
    mode: z.enum(["paper", "live"], { message: "Selecione um modo de operação." }),
});

type BotFormValues = z.infer<typeof botSchema>;

const CreateBotSheet = () => {
    const [open, setOpen] = useState(false);
    
    const { data: profiles = [], isLoading: isLoadingProfiles } = useQuery<Profile[]>({ 
        queryKey: ['profiles'], 
        queryFn: fetchProfiles 
    });
    
    const { register, handleSubmit, control, reset, formState: { errors } } = useForm<BotFormValues>({
        resolver: zodResolver(botSchema),
     defaultValues: {
       name: '',
            profile: '',
       mode: 'paper'
}
    });

    const mutation = useMutation({
mutationFn: createBot,
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['bots'] });
            toast.success("Bot criado com sucesso!");
       setOpen(false);
          reset();
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail || "Ocorreu um erro ao criar o bot.");
        }
    });

    const onSubmit = (data: BotFormValues) => {
        mutation.mutate(data);
    };

return (
        <Sheet open={open} onOpenChange={setOpen}>
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
      <Input 
    id="name" 
     {...register("name")} 
           className="col-span-3"
                placeholder="Ex: Bot BTC"
           />
      {errors.name && <p className="col-span-4 text-red-500 text-sm text-right">{errors.name.message}</p>}
           </div>
                 <div className="grid grid-cols-4 items-center gap-4">
    <Label htmlFor="profile" className="text-right">Estratégia</Label>
           <Controller 
           name="profile" 
          control={control} 
         render={({ field }) => (
  <Select onValueChange={field.onChange} value={field.value}>
            <SelectTrigger className="col-span-3">
     <SelectValue placeholder="Selecione um perfil..." />
   </SelectTrigger>
          <SelectContent>
      {isLoadingProfiles ? (
                <SelectItem value="loading" disabled>A carregar...</SelectItem>
         ) : profiles.length === 0 ? (
             <SelectItem value="empty" disabled>Nenhum perfil disponível</SelectItem>
      ) : (
      profiles.map((p) => (
   <SelectItem key={p.path} value={p.path}>
     {p.name || p.path}
       </SelectItem>
               ))
       )}
  </SelectContent>
        </Select>
                )} 
      />
{errors.profile && <p className="col-span-4 text-red-500 text-sm text-right">{errors.profile.message}</p>}
               </div>
       <div className="grid grid-cols-4 items-center gap-4">
         <Label htmlFor="mode" className="text-right">Modo</Label>
       <Controller 
         name="mode" 
  control={control} 
             render={({ field }) => (
       <Select onValueChange={field.onChange} value={field.value}>
       <SelectTrigger className="col-span-3">
         <SelectValue placeholder="Selecione o modo..." />
             </SelectTrigger>
        <SelectContent>
        <SelectItem value="paper">Paper Trading</SelectItem>
            <SelectItem value="live">Live Trading</SelectItem>
   </SelectContent>
   </Select>
     )} 
  />
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
