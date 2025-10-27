import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const AppLayout = ({ children }: { children: ReactNode }): JSX.Element => {
  return (
    <div className="flex min-h-screen bg-background text-slate-100">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-gradient-to-br from-background via-[#0d1425] to-[#101833]">
          <div className="mx-auto w-full max-w-7xl p-6 pb-16">{children}</div>
        </main>
      </div>
    </div>
  );
};
