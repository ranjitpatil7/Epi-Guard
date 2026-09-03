import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../lib/auth/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertCircle, User, Lock, Activity, LogIn } from 'lucide-react';

const DEMO_ACCOUNTS = [
  { name: 'Admin', user: 'admin', pass: 'admin123', role: 'System Admin' },
  { name: 'Epidemiologist', user: 'dr.sharma', pass: 'epi123', role: 'National' },
  { name: 'Government Official', user: 'collector.das', pass: 'gov123', role: 'Assam State' },
  { name: 'Field Officer', user: 'officer.kumar', pass: 'field123', role: 'Kamrup Metro' },
];

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post('/api/v1/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      await login(
        response.data.access_token,
        response.data.refresh_token,
        response.data.session_id
      );

      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSelect = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Demo Environment Banner */}
      <div className="absolute top-0 left-0 right-0 bg-indigo-600/20 border-b border-indigo-500/30 text-indigo-200 py-2 text-center text-sm font-medium tracking-wide">
        JalRakshak AI — Demo Environment
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="bg-indigo-500/10 p-3 rounded-xl border border-indigo-500/20">
            <Activity className="h-10 w-10 text-indigo-400" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-100 tracking-tight">
          Command Center Access
        </h2>
        <p className="mt-2 text-center text-sm text-slate-400">
          Sign in to access your assigned region and modules.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
        <div className="bg-slate-900 border border-slate-800 py-8 px-4 shadow-2xl sm:rounded-xl sm:px-10">
          
          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-slate-300">
                Username
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-700 rounded-lg bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors sm:text-sm"
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300">
                Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-700 rounded-lg bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors sm:text-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-md bg-red-500/10 border border-red-500/20 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-400">{error}</h3>
                  </div>
                </div>
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-slate-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="h-5 w-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <LogIn className="w-5 h-5 mr-2 -ml-1" />
                    Secure Login
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="mt-10">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-slate-900 text-slate-500">Demo Accounts</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.name}
                  onClick={() => handleDemoSelect(acc.user, acc.pass)}
                  className="w-full inline-flex justify-center flex-col items-center py-2 px-4 border border-slate-700 rounded-lg shadow-sm bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors group"
                >
                  <span className="font-semibold text-slate-200 group-hover:text-white">{acc.name}</span>
                  <span className="text-slate-500 mt-1 text-[10px] uppercase tracking-wider">{acc.role}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
