import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/cn';
import { Bot, Database, FlaskConical, LineChart, Settings, ShieldHalf, Sparkles } from 'lucide-react';

const links = [
  { to: '/smart', label: 'Smart Trade', icon: LineChart },
  { to: '/bots', label: 'Bots', icon: Sparkles },
  { to: '/lab', label: 'Strategy Lab', icon: FlaskConical },
  { to: '/data', label: 'Data', icon: Database },
  { to: '/reports', label: 'Reports', icon: ShieldHalf },
  { to: '/settings', label: 'Settings', icon: Settings },
];

type SidebarProps = {
  inDrawer?: boolean;
};

export const Sidebar = ({ inDrawer = false }: SidebarProps): JSX.Element => {
  return (
    <aside
      className={cn(
        'h-screen w-64 shrink-0 border-r border-border/60 bg-surface/50 backdrop-blur-lg',
        inDrawer ? 'block' : 'hidden lg:block',
      )}
    >
      <div className="flex h-full flex-col p-6">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-500 text-white">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Smart</p>
            <h1 className="text-lg font-semibold text-white">Trade Terminal</h1>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-2">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-indigo-500/10 hover:text-white',
                  isActive && 'bg-indigo-500/20 text-white shadow-soft',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4 text-xs text-slate-300">
          <p className="font-semibold text-white">v13 Pro UI</p>
          <p>Experience the next-gen futures terminal.</p>
        </div>
      </div>
    </aside>
  );
};
