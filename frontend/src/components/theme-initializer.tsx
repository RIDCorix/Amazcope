import { useEffect } from 'react';

interface ThemeInitializerProps {
  theme?: 'light' | 'dark' | 'auto';
}

export function ThemeInitializer({ theme = 'auto' }: ThemeInitializerProps) {
  useEffect(() => {
    const root = document.documentElement;

    let effectiveTheme: 'light' | 'dark' = 'light';

    if (theme === 'auto') {
      // Check system preference
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
        .matches
        ? 'dark'
        : 'light';
      effectiveTheme = systemTheme;

      // Listen for system theme changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        root.classList.remove('light', 'dark');
        root.classList.add(e.matches ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handleChange);

      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      effectiveTheme = theme;
    }

    root.classList.remove('light', 'dark');
    root.classList.add(effectiveTheme);
  }, [theme]);

  return null;
}
