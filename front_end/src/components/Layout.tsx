import React, { ReactNode, useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [hasAssignedSessions, setHasAssignedSessions] = useState<boolean>(false);

  // If not a global admin, check if the user has any assigned sessions
  useEffect(() => {
    let isMounted = true;
    const fetchAssigned = async () => {
      try {
        if (!isAdmin) {
          const mySessions = await api.sessionAdmin.listMySessions();
          if (isMounted) setHasAssignedSessions(mySessions.length > 0);
        } else {
          if (isMounted) setHasAssignedSessions(false);
        }
      } catch {
        if (isMounted) setHasAssignedSessions(false);
      }
    };
    fetchAssigned();
    return () => { isMounted = false; };
  }, [isAdmin]);

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
              {/* Quick links */}
              {isAdmin && (
                <a href={'/admin'} className={`text-sm text-blue-600 hover:text-blue-800`}>
                  Admin Dashboard
                </a>
              )}
              {!isAdmin && hasAssignedSessions && (
                <a href={'/session-admin'} className={`text-sm text-blue-300 hover:text-blue-200`}>
                  Session Admin
                </a>
              )}
              <a href="/chat" className={`${isAdmin ? 'text-sm text-gray-600 hover:text-gray-800' : 'text-sm text-gray-300 hover:text-gray-100'}`}>Chat</a>
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
