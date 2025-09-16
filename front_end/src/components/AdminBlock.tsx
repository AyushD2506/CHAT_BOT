import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Wrapper that prevents admins from using children UI (e.g., Chat)
const AdminBlock: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (user?.is_admin) {
    return <Navigate to="/admin" replace />;
  }
  return <>{children}</>;
};

export default AdminBlock;