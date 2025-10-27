import { useMemo } from 'react';
import { Menu, Moon, Sun } from 'lucide-react';
import { Button } from '../ui/button';
import { useThemeToggle } from './useThemeToggle';
import { Sheet, SheetContent, SheetTrigger } from '../ui/sheet';
import { Sidebar } from './Sidebar';

export const Topbar = (): JSX.Element => {
  const { theme, toggleTheme } = useThemeToggle();

  const themeIcon = useMemo(() => (theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />), [theme]);

  return (
    <header className="sticky top-0 z-40 border-b border-border/50 bg-background/70 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 lg:px-6">
        <div className="flex items-center gap-3 lg:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" aria-label="Open navigation">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <Sidebar inDrawer />
            </SheetContent>
          </Sheet>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Smart</p>
            <h1 className="text-lg font-semibold text-white">Trade Terminal</h1>
          </div>
        </div>
        <div className="hidden lg:block">
          <h2 className="text-lg font-semibold text-white">Smart Terminal</h2>
          <p className="text-xs text-slate-400">Live trading, automation & analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-3 rounded-2xl border border-border/60 bg-surface px-4 py-2 text-xs text-slate-300 md:flex">
            <span className="font-semibold text-white">Mode:</span>
            <span className="rounded-full bg-emerald-500/20 px-2 py-1 text-emerald-300">Paper</span>
            <span className="font-semibold text-white">Symbol:</span>
            <span>BTCUSDT</span>
          </div>
          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
            {themeIcon}
          </Button>
        </div>
      </div>
    </header>
  );
};
