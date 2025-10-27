import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ConfigEditor from './ConfigEditor';
import Snapshots from './Snapshots';
import Profiles from './Profiles';
import ThemeToggle from './ThemeToggle';

const Settings: React.FC = () => {
  return (
    <div>
        <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Settings</h1>
            <ThemeToggle />
        </div>
        <Tabs defaultValue="config" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="config">Config</TabsTrigger>
                <TabsTrigger value="snapshots">Snapshots</TabsTrigger>
                <TabsTrigger value="profiles">Profiles</TabsTrigger>
            </TabsList>
            <TabsContent value="config" className="mt-6">
                <ConfigEditor />
            </TabsContent>
            <TabsContent value="snapshots" className="mt-6">
                <Snapshots />
            </TabsContent>
            <TabsContent value="profiles" className="mt-6">
                <Profiles />
            </TabsContent>
        </Tabs>
    </div>
  );
};

export default Settings;
