import React, { useState } from 'react';
import { useAuth, DEMO_PERSONAS } from '../context/AuthContext';
import { ShieldCheck, User, Wrench, Settings, Eye, EyeOff, Zap, ArrowRight } from 'lucide-react';

const PERSONA_ICONS = {
  customer: User,
  executive: ShieldCheck,
  admin: Settings,
  technician: Wrench,
};

const PERSONA_COLORS = {
  customer: 'teal',
  executive: 'blue',
  admin: 'purple',
  technician: 'amber',
};

export default function LoginPage() {
  const { loginWithEmail } = useAuth();
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [demoLoading, setDemoLoading] = useState(null);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-4">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-teal-500 rounded-2xl shadow-xl shadow-teal-500/30 mb-4">
            <span className="text-slate-950 font-black text-2xl">FL</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">FixLoop</h1>
          <p className="text-slate-400 text-sm mt-1">AI-Powered Repair Operations Platform</p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-lg font-semibold text-white mb-6">Sign in to your account</h2>

          {error && (
            <div className="mb-4 p-3 bg-rose-500/15 border border-rose-500/30 rounded-lg text-rose-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 mb-6">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg px-4 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold py-2.5 rounded-lg text-sm transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <span className="inline-block w-4 h-4 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
              ) : (
                <>Sign In <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          {/* Demo Quick Access */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 h-px bg-slate-700" />
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Zap className="w-3 h-3" /> Quick Demo Access
              </span>
              <div className="flex-1 h-px bg-slate-700" />
            </div>
            <div className="space-y-2">
              {DEMO_PERSONAS.map((p) => {
                const Icon = PERSONA_ICONS[p.role] || User;
                const color = PERSONA_COLORS[p.role] || 'teal';
                const isLoading = demoLoading === p.email;
                return (
                  <button
                    key={p.email}
                    onClick={() => handleDemo(p)}
                    disabled={!!demoLoading}
                    className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg border transition text-left disabled:opacity-60
                      border-slate-700 hover:border-${color}-500/50 hover:bg-${color}-500/5 bg-slate-900/40`}
                  >
                    <div className={`w-8 h-8 rounded-lg bg-${color}-500/15 flex items-center justify-center flex-shrink-0`}>
                      {isLoading
                        ? <span className={`w-3.5 h-3.5 border-2 border-${color}-400/30 border-t-${color}-400 rounded-full animate-spin`} />
                        : <Icon className={`w-3.5 h-3.5 text-${color}-400`} />
                      }
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{p.name}</p>
                      <p className="text-[11px] text-slate-400 truncate">{p.sub}</p>
                    </div>
                    <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-${color}-500/15 text-${color}-400`}>
                      {p.role}
                    </span>
                  </button>
                );
              })}
            </div>
            <p className="text-center text-[11px] text-slate-500 mt-3">All demo passwords: <code className="text-teal-400">password123</code></p>
          </div>
        </div>
      </div>
    </div>
  );
}
