import { useContext, useMemo } from 'react';
import { ThemeContext } from './ThemeProvider';

export const useThemeToggle = () => {
  const { theme, setTheme } = useContext(ThemeContext);

  return useMemo(
    () => ({
      theme,
      toggleTheme: () => setTheme(theme === 'dark' ? 'light' : 'dark'),
    }),
    [setTheme, theme],
  );
};
