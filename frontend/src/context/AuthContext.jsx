import React, { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, googleLogin as apiGoogleLogin, getMe } from '../services/api';

const AuthContext = createContext(null);

export const DEMO_PERSONAS = [
  { label: 'Customer: Rahul Sharma', email: 'rahul@example.com', role: 'CUSTOMER', name: 'Rahul Sharma', sub: 'Model X Washer (Repeat Case TCK-1010)' },
  { label: 'Customer: Priya Nair', email: 'priya@example.com', role: 'CUSTOMER', name: 'Priya Nair', sub: 'TCK-1003 (Estimate Pending)' },
  { label: 'Technician: Vikram Singh', email: 'tech.vikram@fixloop.com', role: 'TECHNICIAN', name: 'Vikram Singh', sub: 'Senior Field Specialist' },
  { label: 'Admin: Sarah Jenkins', email: 'admin@fixloop.com', role: 'ADMIN', name: 'Sarah Jenkins', sub: 'Central Operations Director' },
  { label: 'Admin: Amit Sharma', email: 'support@fixloop.com', role: 'ADMIN', name: 'Amit Sharma', sub: 'Operations Lead' },
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
          await loginWithEmail('admin@fixloop.com', 'password123');
        }
      } else {
        // Default to Admin Sarah Jenkins for instant dashboard demo
        await loginWithEmail('admin@fixloop.com', 'password123');
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

  const loginWithGoogle = async (idToken, targetRole = 'CUSTOMER') => {
    try {
      const res = await apiGoogleLogin({ id_token: idToken, target_role: targetRole });
      const { access_token, user: userData } = res.data;
      localStorage.setItem('fixloop_token', access_token);
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (err) {
      console.error('Google login error:', err);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('fixloop_token');
    setToken(null);
    setUser(null);
  };

  const role = user?.role ? user.role.toUpperCase() : '';
  const isCustomer = role === 'CUSTOMER';
  const isTechnician = role === 'TECHNICIAN';
  const isAdmin = role === 'ADMIN';
  const isEmployee = isTechnician || isAdmin;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        role,
        isCustomer,
        isTechnician,
        isAdmin,
        isEmployee,
        loginWithEmail,
        loginWithGoogle,
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
