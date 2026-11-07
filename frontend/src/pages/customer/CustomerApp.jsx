import React, { useState } from 'react';
import { useAuth, DEMO_PERSONAS } from '../../context/AuthContext';
import CustomerHome from './CustomerHome';
import CustomerTracker from './CustomerTracker';
import CustomerRaiseComplaint from './CustomerRaiseComplaint';
import CustomerProfile from './CustomerProfile';
import CustomerChatWidget from './CustomerChatWidget';
import NotificationBell from '../../components/NotificationBell';
import {
  Home, List, PlusCircle, User, LogOut, MessageSquare, ChevronDown
} from 'lucide-react';

const NAV = [
  { id: 'home',     label: 'Home',          icon: Home },
  { id: 'tracker',  label: 'My Tickets',    icon: List },
  { id: 'raise',    label: 'New Complaint', icon: PlusCircle },
  { id: 'profile',  label: 'Profile',       icon: User },
];

function PersonaSwitcher({ user }) {
  const [open, setOpen] = useState(false);
  const { loginWithEmail } = useAuth();
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs rounded-lg transition"
      >
        <span className="font-medium">{user?.name || user?.email || 'Account'}</span>
        <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-white border border-slate-200 rounded-xl shadow-2xl z-50 py-2">
          <p className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Switch Demo Account</p>
          {DEMO_PERSONAS.map((p) => (
            <button
              key={p.email}
              onClick={async () => { setOpen(false); await loginWithEmail(p.email, 'password123'); }}
              className="w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-50 transition text-left"
            >
              <div className="flex-1">
                <p className="text-xs font-semibold text-slate-800">{p.name}</p>
                <p className="text-[11px] text-slate-400">{p.sub}</p>
              </div>
              <span className="text-[10px] uppercase font-semibold text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded">{p.role}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CustomerApp() {
  const { user, logout } = useAuth();
  const [tab, setTab]           = useState('home');
  const [chatOpen, setChatOpen] = useState(false);
  const [ticketId, setTicketId] = useState(null);

  const goToTracker = (tid) => {
    setTicketId(tid);
    setTab('tracker');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Nav */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center font-black text-slate-950 text-sm">FL</div>
            <span className="font-bold tracking-tight text-sm">FixLoop</span>
            <span className="text-[10px] bg-teal-500/20 text-teal-300 font-semibold px-1.5 py-0.5 rounded border border-teal-500/30">Customer Portal</span>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {NAV.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  tab === id ? 'bg-teal-500 text-slate-950' : 'text-slate-300 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <NotificationBell onSelectTicket={goToTracker} />
            <PersonaSwitcher user={user} />
            <button onClick={logout} title="Logout" className="p-1.5 text-slate-400 hover:text-rose-400 transition rounded-lg">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile Bottom Nav */}
        <div className="md:hidden border-t border-slate-700/50 flex">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex-1 flex flex-col items-center py-2 gap-0.5 text-[10px] font-semibold transition ${
                tab === id ? 'text-teal-400' : 'text-slate-400'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* Page Content */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-6">
        {tab === 'home'    && <CustomerHome    onViewTicket={goToTracker} onRaise={() => setTab('raise')} />}
        {tab === 'tracker' && <CustomerTracker selectedTicketId={ticketId} onSelectTicket={setTicketId} />}
        {tab === 'raise'   && <CustomerRaiseComplaint onCreated={(tid) => goToTracker(tid)} />}
        {tab === 'profile' && <CustomerProfile />}
      </main>

      {/* Floating AI Chat Button */}
      <button
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-teal-500 hover:bg-teal-400 text-slate-950 rounded-full shadow-2xl shadow-teal-500/40 flex items-center justify-center transition z-30"
        title="Chat with FixLoop AI"
      >
        <MessageSquare className="w-6 h-6" />
      </button>

      {/* Chat Widget */}
      {chatOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-full max-w-sm shadow-2xl rounded-2xl overflow-hidden">
          <CustomerChatWidget ticketId={ticketId} onClose={() => setChatOpen(false)} />
        </div>
      )}
    </div>
  );
}
