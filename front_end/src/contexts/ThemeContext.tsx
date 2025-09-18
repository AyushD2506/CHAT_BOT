import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

// Type for theme
export type Theme = 'light' | 'dark';

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// Detect initial theme from localStorage or system preference
function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem('theme');
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {}
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  return prefersDark ? 'dark' : 'light';
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  const applyTheme = (t: Theme) => {
    const root = document.documentElement; // <html>
    if (t === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  useEffect(() => {
    applyTheme(theme);
    try { localStorage.setItem('theme', theme); } catch {}
  }, [theme]);

  useEffect(() => {
    // Keep in sync with system changes if user hasn't explicitly chosen
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem('theme');
      if (stored !== 'light' && stored !== 'dark') {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };
    try {
      media.addEventListener('change', handler);
      return () => media.removeEventListener('change', handler);
    } catch {
      // Safari fallback
      media.addListener(handler as any);
      return () => media.removeListener(handler as any);
    }
  }, []);

  const value = useMemo(
    () => ({
      theme,
      toggleTheme: () => setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark')),
      setTheme: (t: Theme) => setThemeState(t),
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within a ThemeProvider');
  return ctx;
};