import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button";
import { Trash2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';

const deleteBot = (botId: number) => {
    return api.post('/api/bots/delete', { id: botId });
};

interface DeleteBotDialogProps {
    botId: number;
    botName: string;
}

const DeleteBotDialog: React.FC<DeleteBotDialogProps> = ({ botId, botName }) => {
    const mutation = useMutation({
        mutationFn: deleteBot,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bots'] });
            toast.success(`Bot "${botName}" removido com sucesso.`);
        },
        onError: () => {
            toast.error(`Ocorreu um erro ao remover o bot "${botName}".`);
        }
    });

    return (
        <AlertDialog>
            <AlertDialogTrigger asChild>
                <Button variant="destructive" size="icon" disabled={mutation.isPending}>
                    <Trash2 className="h-4 w-4" />
                </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Tem a certeza?</AlertDialogTitle>
                    <AlertDialogDescription>
                        Esta ação não pode ser desfeita. Isto irá remover permanentemente o bot
                        <strong className="mx-1">{botName}</strong>.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction onClick={() => mutation.mutate(botId)}>
                        Continuar
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
};

export default DeleteBotDialog;
