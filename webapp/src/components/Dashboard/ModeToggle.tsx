import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, TestTube2 } from 'lucide-react';
import { toast } from 'sonner';

const fetchConfig = async () => {
    const { data } = await api.get('/api/config/read');
    return data;
};

const setMode = async (mode: 'paper' | 'live') => {
    const config = await fetchConfig();
    config.mode = mode;
    await api.post('/api/config/write', config);
    return mode;
};

const ModeToggle: React.FC = () => {
 const { data: config, isLoading } = useQuery({ 
   queryKey: ['config'], 
        queryFn: fetchConfig 
    });

    const mutation = useMutation({
 mutationFn: setMode,
  onSuccess: (mode) => {
    queryClient.invalidateQueries({ queryKey: ['config'] });
          queryClient.invalidateQueries({ queryKey: ['accountStatus'] });
     queryClient.invalidateQueries({ queryKey: ['paperStatus'] });
            toast.success(`Modo alterado para ${mode === 'live' ? 'Live Trading' : 'Paper Trading'}`);
        },
     onError: () => {
    toast.error('Erro ao alterar modo');
 }
    });

    const handleToggle = (checked: boolean) => {
        const newMode = checked ? 'live' : 'paper';
        
        if (newMode === 'live') {
            // Confirmação extra para Live Mode
            if (!confirm('?? ATENÇÃO: Vai ativar o Live Trading com dinheiro real. Confirma?')) {
      return;
    }
 }
        
        mutation.mutate(newMode);
    };

    if (isLoading) return null;

    const isLive = config?.mode === 'live';

    return (
        <Card className="shadow-soft">
      <CardContent className="p-4">
         <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
    {isLive ? (
          <Zap className="h-5 w-5 text-yellow-500" />
  ) : (
        <TestTube2 className="h-5 w-5 text-blue-500" />
  )}
        <div>
       <Label htmlFor="mode-toggle" className="text-sm font-medium cursor-pointer">
    Modo de Trading
   </Label>
                <p className="text-xs text-muted-foreground">
   {isLive ? 'Dinheiro Real' : 'Simulação'}
  </p>
            </div>
           </div>
              <div className="flex items-center space-x-3">
         <Badge variant={isLive ? "destructive" : "secondary"}>
          {isLive ? 'LIVE' : 'PAPER'}
            </Badge>
    <Switch
        id="mode-toggle"
   checked={isLive}
         onCheckedChange={handleToggle}
              disabled={mutation.isPending}
       />
     </div>
    </div>
            </CardContent>
        </Card>
    );
};

export default ModeToggle;
