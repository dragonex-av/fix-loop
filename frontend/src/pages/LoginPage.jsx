import React, { useState, useEffect } from 'react';
import { useAuth, DEMO_PERSONAS } from '../context/AuthContext';
import { ShieldCheck, User, Wrench, Settings, Eye, EyeOff, Zap, ArrowRight, Chrome } from 'lucide-react';

const PERSONA_ICONS = {
  CUSTOMER: User,
  TECHNICIAN: Wrench,
  ADMIN: Settings,
};

const PERSONA_COLORS = {
  CUSTOMER: 'teal',
  TECHNICIAN: 'amber',
  ADMIN: 'purple',
};

export default function LoginPage() {
  const { loginWithEmail, loginWithGoogle } = useAuth();
  const [activeTab, setActiveTab] = useState('customer'); // 'customer' | 'staff'
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [demoLoading, setDemoLoading] = useState(null);

  // Initialize Google Identity Services if client ID exists
  useEffect(() => {
    /* global google */
    if (window.google?.accounts?.id) {
      window.google.accounts.id.initialize({
        client_id: window.VITE_GOOGLE_CLIENT_ID || 'dummy-client-id',
        callback: (response) => {
          if (response.credential) {
            handleGoogleCredential(response.credential);
          }
        }
      });
    }
  }, [activeTab]);

  const handleGoogleCredential = async (credential) => {
    setLoading(true);
    setError('');
    try {
      const targetRole = activeTab === 'customer' ? 'CUSTOMER' : 'TECHNICIAN';
      await loginWithGoogle(credential, targetRole);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Google authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleMockGoogleLogin = async () => {
    // Convenient mock Google login for local demo when Google Client ID isn't live
    const mockEmail = activeTab === 'customer' ? 'google.customer@example.com' : 'tech.vikram@fixloop.com';
    const mockToken = `mock-google-token-${mockEmail}`;
    await handleGoogleCredential(mockToken);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await loginWithEmail(email, password);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Invalid credentials. Try a demo account below.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async (persona) => {
    setDemoLoading(persona.email);
    setError('');
    try {
      await loginWithEmail(persona.email, 'password123');
    } catch (err) {
      setError('Demo login failed. Ensure the backend is running.');
    } finally {
      setDemoLoading(null);
    }
  };

  const filteredPersonas = DEMO_PERSONAS.filter(p => {
    if (activeTab === 'customer') return p.role === 'CUSTOMER';
    return p.role === 'TECHNICIAN' || p.role === 'ADMIN';
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-4">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-teal-500 rounded-2xl shadow-xl shadow-teal-500/30 mb-3">
            <span className="text-slate-950 font-black text-2xl">FL</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center justify-center gap-2">
            <span>FixLoop</span>
            <span className="text-xs bg-teal-500/20 text-teal-300 font-semibold px-2 py-0.5 rounded border border-teal-500/30">v2.0</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">AI Repair Operations & Field Service Platform</p>
        </div>

        {/* Role Tab Switcher: Login as Customer vs Login as Technician/Admin */}
        <div className="grid grid-cols-2 p-1 bg-slate-900/80 border border-slate-700/60 rounded-xl mb-4 backdrop-blur">
          <button
            type="button"
            onClick={() => { setActiveTab('customer'); setError(''); }}
            className={`py-2 text-xs font-bold rounded-lg transition flex items-center justify-center gap-2 ${
              activeTab === 'customer'
                ? 'bg-teal-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            Login as Customer
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('staff'); setError(''); }}
            className={`py-2 text-xs font-bold rounded-lg transition flex items-center justify-center gap-2 ${
              activeTab === 'staff'
                ? 'bg-amber-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Technician / Admin
          </button>
        </div>

        {/* Login Card */}
        <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-6 shadow-2xl">
          <h2 className="text-base font-semibold text-white mb-4">
            {activeTab === 'customer' ? 'Customer Self-Service Portal' : 'Field Operations & Service Desk'}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-rose-500/15 border border-rose-500/30 rounded-lg text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* Google Login Button */}
          <button
            type="button"
            onClick={handleMockGoogleLogin}
            disabled={loading}
            className="w-full mb-4 flex items-center justify-center gap-3 px-4 py-2.5 bg-white hover:bg-slate-100 text-slate-900 font-semibold rounded-lg text-xs transition shadow-sm border border-slate-200"
          >
            <Chrome className="w-4 h-4 text-rose-500" />
            <span>Continue with Google</span>
          </button>

          <div className="flex items-center gap-2 mb-4">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Or email & password</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-3.5 mb-5">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={activeTab === 'customer' ? 'rahul@example.com' : 'admin@fixloop.com'}
                required
                className="w-full bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg px-3.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg px-3.5 py-2 pr-10 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  {showPw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full text-slate-950 font-bold py-2.5 rounded-lg text-xs transition flex items-center justify-center gap-2 ${
                activeTab === 'customer' ? 'bg-teal-500 hover:bg-teal-400' : 'bg-amber-500 hover:bg-amber-400'
              } disabled:opacity-50`}
            >
              {loading ? (
                <span className="inline-block w-4 h-4 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
              ) : (
                <>Sign In <ArrowRight className="w-3.5 h-3.5" /></>
              )}
            </button>
          </form>

          {/* Demo Quick Access Filtered by Tab */}
          <div>
            <div className="flex items-center gap-2 mb-2.5">
              <div className="flex-1 h-px bg-slate-700" />
              <span className="text-[10px] text-slate-500 flex items-center gap-1 font-semibold uppercase">
                <Zap className="w-3 h-3 text-amber-400" /> One-Click Demo Personas
              </span>
              <div className="flex-1 h-px bg-slate-700" />
            </div>
            <div className="space-y-1.5">
              {filteredPersonas.map((p) => {
                const Icon = PERSONA_ICONS[p.role] || User;
                const color = PERSONA_COLORS[p.role] || 'teal';
                const isLoading = demoLoading === p.email;
                return (
                  <button
                    key={p.email}
                    onClick={() => handleDemo(p)}
                    disabled={!!demoLoading}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg border border-slate-700 hover:border-slate-500 hover:bg-slate-700/30 bg-slate-900/40 transition text-left disabled:opacity-60"
                  >
                    <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0">
                      {isLoading ? (
                        <span className="w-3 h-3 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin" />
                      ) : (
                        <Icon className="w-3.5 h-3.5 text-teal-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{p.name}</p>
                      <p className="text-[10px] text-slate-400 truncate">{p.sub}</p>
                    </div>
                    <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-800 text-teal-300">
                      {p.role}
                    </span>
                  </button>
                );
              })}
            </div>
            <p className="text-center text-[10px] text-slate-500 mt-2.5">Demo Password: <code className="text-teal-400">password123</code></p>
          </div>
        </div>
      </div>
    </div>
  );
}
