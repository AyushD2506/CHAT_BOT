import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

// Lightweight inline toggle for login page
const InlineThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className="inline-flex items-center gap-2 px-2.5 py-1.5 text-xs rounded-md border transition-colors
                 border-gray-300 text-gray-700 hover:bg-gray-100
                 dark:border-white/10 dark:text-gray-100 dark:hover:bg-white/10"
      aria-label="Toggle color theme"
    >
      <span className="hidden sm:inline">{theme === 'dark' ? 'Dark' : 'Light'}</span>
      {theme === 'dark' ? (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5">
          <path d="M21.752 15.002A9.718 9.718 0 0012 22C6.477 22 2 17.523 2 12 2 7.06 5.657 2.999 10.398 2.17a.75.75 0 01.853.98A8 8 0 1020.57 12.75a.75.75 0 011.182.88z" />
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5">
          <path d="M12 18a6 6 0 100-12 6 6 0 000 12z" />
          <path fillRule="evenodd" d="M12 2.25a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0V3A.75.75 0 0112 2.25zm0 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0V18a.75.75 0 01.75-.75zM4.72 4.72a.75.75 0 011.06 0l1.06 1.06a.75.75 0 11-1.06 1.06L4.72 5.78a.75.75 0 010-1.06zm11.44 11.44a.75.75 0 011.06 0l1.06 1.06a.75.75 0 11-1.06 1.06l-1.06-1.06a.75.75 0 010-1.06zM2.25 12a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5H3A.75.75 0 012.25 12zm15 0a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5H18a.75.75 0 01-.75-.75zM4.72 19.28a.75.75 0 011.06 0l1.06-1.06a.75.75 0 11-1.06-1.06L4.72 18.22a.75.75 0 010 1.06zm11.44-11.44a.75.75 0 011.06 0l1.06-1.06a.75.75 0 11-1.06-1.06l-1.06 1.06a.75.75 0 010 1.06z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  );
};

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login({ username, password });
      // Navigation is handled by the auth context and router
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-blue-900 dark:from-gray-900 dark:via-gray-900 dark:to-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="relative max-w-md w-full space-y-8 bg-white/90 dark:bg-gray-800/80 backdrop-blur rounded-2xl shadow-2xl ring-1 ring-gray-200 dark:ring-gray-700 p-8">
        {/* Theme toggle in corner */}
        <div className="absolute right-4 top-4">
          {/* Inline toggle to avoid importing layout here */}
          <InlineThemeToggle />
        </div>
        <div>
          <h2 className="mt-2 text-center text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
            Welcome back
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-300">
            Or{' '}
            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              create a new account
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}
          <div className="rounded-xl shadow-sm">
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="relative block w-full px-4 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-400 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 rounded-t-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Username"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="relative block w-full px-4 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-400 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 rounded-b-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 text-sm font-semibold rounded-xl text-white bg-blue-600 shadow-lg shadow-blue-600/30 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center text-xs text-gray-500 dark:text-gray-400">
            <p>Demo accounts:</p>
            <p>Admin: admin / admin123</p>
            <p>User: user / user123</p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;