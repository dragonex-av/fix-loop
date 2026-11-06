import React, { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, getMe } from '../services/api';

const AuthContext = createContext(null);

export const DEMO_PERSONAS = [
  { label: 'Customer: Rahul Sharma', email: 'rahul@example.com', role: 'customer', name: 'Rahul Sharma', sub: 'Model X Washer Issue' },
  { label: 'Customer: Priya Nair', email: 'priya@example.com', role: 'customer', name: 'Priya Nair', sub: 'Estimate Approval Pending' },
  { label: 'Support Exec: Amit Sharma', email: 'support@fixloop.com', role: 'executive', name: 'Amit Sharma', sub: 'Operations Lead' },
  { label: 'Admin: Sarah Jenkins', email: 'admin@fixloop.com', role: 'admin', name: 'Sarah Jenkins', sub: 'Central Operations Director' },
  { label: 'Technician: Vikram Singh', email: 'tech.vikram@fixloop.com', role: 'technician', name: 'Vikram Singh', sub: 'Senior Field Specialist' },
];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('fixloop_token'));
  const [loading, setLoading] = useState(true);

  // Initialize or restore session
  useEffect(() => {
    async function initUser() {
      if (token) {
        try {
          const res = await getMe();
          setUser(res.data);
        } catch (e) {
          console.warn('Session expired, logging in default demo persona...');
          await loginWithEmail('rahul@example.com', 'password123');
        }
      } else {
        // Default to Rahul Sharma for instant demo accessibility
        await loginWithEmail('rahul@example.com', 'password123');
      }
      setLoading(false);
    }
    initUser();
  }, []);

  const loginWithEmail = async (email, password = 'password123') => {
    try {
      const res = await apiLogin({ email, password });
      const { access_token, user: userData } = res.data;
      localStorage.setItem('fixloop_token', access_token);
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (err) {
      console.error('Login error:', err);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('fixloop_token');
    setToken(null);
    setUser(null);
  };

  const isCustomer = user?.role === 'customer';
  const isEmployee = ['admin', 'executive', 'technician'].includes(user?.role);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isCustomer,
        isEmployee,
        loginWithEmail,
        logout,
        setUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
