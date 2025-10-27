import { useEffect, useState, type Dispatch, type SetStateAction } from 'react';

export const useLocalStorageTheme = (): [string, Dispatch<SetStateAction<string>>] => {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  return [theme, setTheme];
};
