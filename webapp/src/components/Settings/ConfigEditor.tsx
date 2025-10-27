import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import JSONEditor from 'react-json-editor-ajrm';
// @ts-ignore
import locale from 'react-json-editor-ajrm/locale/en';
import { queryClient } from '@/lib/queryClient';
import { toast } from 'sonner';
import { Skeleton } from "@/components/ui/skeleton";

const fetchConfig = async () => {
    const { data } = await api.get('/api/config/read');
    return data;
};

const writeConfig = (config: any) => {
    return api.post('/api/config/write', config);
};

const ConfigEditor: React.FC = () => {
    const [config, setConfig] = useState<any>(null);
    const { data, isLoading } = useQuery({ queryKey: ['config'], queryFn: fetchConfig });
    const mutation = useMutation({
        mutationFn: writeConfig,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['config'] });
            toast.success("Configuration saved successfully!");
        },
        onError: () => {
            toast.error("Failed to save configuration.");
        }
    });

    useEffect(() => {
        if (data) {
            setConfig(data);
        }
    }, [data]);

    return (
        <Card className="shadow-soft">
            <CardHeader>
                <CardTitle>Config Editor</CardTitle>
                <CardDescription>
                    Modify the main configuration file. Be careful with your changes.
                </CardDescription>
            </CardHeader>
            <CardContent>
                {isLoading || !config ? (
                    <Skeleton className="h-[550px] w-full" />
                ) : (
                    <JSONEditor
                        id="config-editor"
                        placeholder={config}
                        locale={locale}
                        height="550px"
                        width="100%"
                        onChange={(e: any) => setConfig(e.jsObject)}
                        theme="dark_vscode_tribute"
                    />
                )}
            </CardContent>
            <CardFooter>
                <Button onClick={() => mutation.mutate(config)} disabled={mutation.isPending}>
                    {mutation.isPending ? "Saving..." : "Save Config"}
                </Button>
            </CardFooter>
        </Card>
    );
};

export default ConfigEditor;
