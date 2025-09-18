import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-md border transition-colors
                 border-gray-300 text-gray-700 hover:bg-gray-100
                 dark:border-white/10 dark:text-gray-100 dark:hover:bg-white/10"
      aria-label="Toggle color theme"
      title="Toggle color theme"
    >
      <span className="hidden sm:inline">{theme === 'dark' ? 'Dark' : 'Light'}</span>
      {theme === 'dark' ? (
        // Moon icon
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
          <path d="M21.752 15.002A9.718 9.718 0 0012 22C6.477 22 2 17.523 2 12 2 7.06 5.657 2.999 10.398 2.17a.75.75 0 01.853.98A8 8 0 1020.57 12.75a.75.75 0 011.182.88z" />
        </svg>
      ) : (
        // Sun icon
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
          <path d="M12 18a6 6 0 100-12 6 6 0 000 12z" />
          <path fillRule="evenodd" d="M12 2.25a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0V3A.75.75 0 0112 2.25zm0 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0V18a.75.75 0 01.75-.75zM4.72 4.72a.75.75 0 011.06 0l1.06 1.06a.75.75 0 11-1.06 1.06L4.72 5.78a.75.75 0 010-1.06zm11.44 11.44a.75.75 0 011.06 0l1.06 1.06a.75.75 0 11-1.06 1.06l-1.06-1.06a.75.75 0 010-1.06zM2.25 12a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5H3A.75.75 0 012.25 12zm15 0a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5H18a.75.75 0 01-.75-.75zM4.72 19.28a.75.75 0 011.06 0l1.06-1.06a.75.75 0 11-1.06-1.06L4.72 18.22a.75.75 0 010 1.06zm11.44-11.44a.75.75 0 011.06 0l1.06-1.06a.75.75 0 11-1.06-1.06l-1.06 1.06a.75.75 0 010 1.06z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  );
};

export default ThemeToggle;