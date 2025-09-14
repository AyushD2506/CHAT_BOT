import React, { ReactNode } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`${isAdmin ? 'min-h-screen bg-gray-50' : 'min-h-screen bg-[#343541]'}`}>
      {/* Navigation Header */}
      <nav className={`${isAdmin ? 'bg-white border-b border-gray-200' : 'bg-[#202123] border-b border-black/20'} sticky top-0 z-30`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14">
            <div className="flex items-center">
              <h1 className={`${isAdmin ? 'text-lg font-semibold text-gray-900' : 'text-lg font-semibold text-gray-100'}`}>
                RAG Chatbot {isAdmin ? '- Admin' : ''}
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className={`${isAdmin ? 'text-sm text-gray-600' : 'text-sm text-gray-300'}`}>
                Welcome, {user?.username}
              </span>
              <button
                onClick={handleLogout}
                className={`${isAdmin
                  ? 'inline-flex items-center px-3 py-2 text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
                  : 'inline-flex items-center px-3 py-2 text-sm leading-4 font-medium rounded-md text-gray-100 bg-transparent border border-white/10 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/20'
                }`}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};

export default Layout;
