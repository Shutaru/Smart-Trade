import React from 'react';
import Sidebar from '@/components/Shared/Sidebar';
import Topbar from '@/components/Shared/Topbar';
import { Toaster } from "@/components/ui/sonner";
import { Outlet } from "react-router-dom";

const Layout: React.FC = () => {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-4 md:p-8">
          <Outlet /> {/* As rotas filhas serão renderizadas aqui */}
        </main>
      </div>
      <Toaster />
    </div>
  );
};

export default Layout;
