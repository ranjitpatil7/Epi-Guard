import React from 'react';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth/AuthContext';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="flex justify-center mb-6">
          <div className="bg-red-500/10 p-4 rounded-full border border-red-500/20">
            <ShieldAlert className="h-16 w-16 text-red-500" />
          </div>
        </div>
        
        <h2 className="text-3xl font-extrabold text-white mb-2">Access Restricted</h2>
        <p className="text-slate-400 mb-8">
          Your account role (<span className="text-indigo-400 font-semibold">{user?.role || 'Unknown'}</span>) 
          doesn't have permission to access this module.
        </p>
        
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-slate-800 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Return to Dashboard
        </button>
      </div>
    </div>
  );
};
