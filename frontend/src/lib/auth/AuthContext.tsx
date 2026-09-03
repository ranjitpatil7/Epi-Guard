import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import axios from 'axios';
import { apiClient } from '../api/client';
import { type User, Permission } from './permissions';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (access_token: string, refresh_token: string, session_id: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: Permission) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Setup axios interceptor to attach token
  useEffect(() => {
    const requestInterceptor = (config: any) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    };

    const responseErrorInterceptor = (error: any) => {
      if (error.response?.status === 401) {
        // In a real app, we'd try to refresh here. For now, just logout.
        logout();
      }
      return Promise.reject(error);
    };

    // Apply to global axios (used by AuthContext internally)
    const req1 = axios.interceptors.request.use(requestInterceptor);
    const res1 = axios.interceptors.response.use((r) => r, responseErrorInterceptor);
    
    // Apply to custom API Client (used by the rest of the application)
    const req2 = apiClient.interceptors.request.use(requestInterceptor);
    const res2 = apiClient.interceptors.response.use((r) => r, responseErrorInterceptor);

    return () => {
      axios.interceptors.request.eject(req1);
      axios.interceptors.response.eject(res1);
      apiClient.interceptors.request.eject(req2);
      apiClient.interceptors.response.eject(res2);
    };
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/v1/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (access_token: string, refresh_token: string, session_id: string) => {
    localStorage.setItem('access_token', access_token);
    // Secure cookie is ideal for refresh_token in production, storing in memory/local here for demo
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('session_id', session_id);
    await fetchUser();
  };

  const logout = async () => {
    try {
      const sessionId = localStorage.getItem('session_id');
      if (sessionId) {
        localStorage.removeItem('session_id'); // Clear first to prevent interceptor loop on 401
        await axios.post(`/api/v1/auth/logout?session_id=${sessionId}`);
      }
    } catch (e) {
      console.error('Logout error', e);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('session_id');
      setUser(null);
    }
  };

  const hasPermission = (permission: Permission): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
