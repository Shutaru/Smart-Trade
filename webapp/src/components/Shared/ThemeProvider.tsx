import { createContext, ReactNode, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'smart-trade.theme';

export type Theme = 'light' | 'dark';

type ThemeContextValue = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
};

export const ThemeContext = createContext<ThemeContextValue>({
  theme: 'dark',
  setTheme: () => undefined,
});

type ThemeProviderProps = {
  children: ReactNode;
};

export const ThemeProvider = ({ children }: ThemeProviderProps): JSX.Element => {
  const [theme, setThemeState] = useState<Theme>('dark');

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (saved === 'light' || saved === 'dark') {
      setThemeState(saved);
      document.documentElement.classList.toggle('dark', saved === 'dark');
    }
  }, []);

  const setTheme = (nextTheme: Theme): void => {
    setThemeState(nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
    window.localStorage.setItem(STORAGE_KEY, nextTheme);
  };

  const value = useMemo(() => ({ theme, setTheme }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};
