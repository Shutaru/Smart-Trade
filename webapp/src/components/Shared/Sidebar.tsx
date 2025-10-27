import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, BarChart, Sliders, Database, FileText, Settings, Target } from 'lucide-react';

const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/dashboard', icon: <LayoutDashboard size={20} />, text: 'Dashboard' },
    { to: '/smart', icon: <Target size={20} />, text: 'Smart Trade' },
    { to: '/bots', icon: <Bot size={20} />, text: 'Bots' },
    { to: '/lab', icon: <Sliders size={20} />, text: 'Strategy Lab' },
    { to: '/data', icon: <Database size={20} />, text: 'Data' },
    { to: '/reports', icon: <FileText size={20} />, text: 'Reports' },
    { to: '/settings', icon: <Settings size={20} />, text: 'Settings' },
  ];

  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h1 className="text-2xl font-bold">Smart Trade</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                isActive ? 'bg-primary text-primary-foreground' : 'hover:bg-secondary'
              }`
            }
          >
            {item.icon}
            <span>{item.text}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
