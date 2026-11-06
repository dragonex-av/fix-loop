import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  Users, 
  Wrench, 
  TrendingUp, 
  Clock, 
  Cpu, 
  ShieldCheck,
  RotateCcw
} from 'lucide-react';

import Dashboard from './pages/Dashboard';
import NewComplaint from './pages/NewComplaint';
import CustomerHistory from './pages/CustomerHistory';
import AIRepairAssistant from './pages/AIRepairAssistant';
import BusinessInsights from './pages/BusinessInsights';
import FollowUps from './pages/FollowUps';
import MemoryExplorer from './pages/MemoryExplorer';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [selectedTicketId, setSelectedTicketId] = useState(1);
  const [selectedCustomerId, setSelectedCustomerId] = useState(1);

  const handleTicketSelect = (ticketId) => {
    setSelectedTicketId(ticketId);
    setCurrentTab('assistant');
  };

  const handleCustomerSelect = (customerId) => {
    setSelectedCustomerId(customerId);
    setCurrentTab('customer-360');
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new-complaint', label: 'New Complaint', icon: PlusCircle },
    { id: 'customer-360', label: 'Customer 360', icon: Users },
    { id: 'assistant', label: 'AI Repair Assistant', icon: Wrench },
    { id: 'ripple-effect', label: 'Ripple Effect', icon: TrendingUp },
    { id: 'followups', label: 'Follow-Up Center', icon: Clock },
    { id: 'memory-explorer', label: 'Memory Explorer', icon: Cpu, badge: 'Trust' },
  ];

  return (
    <div className="flex h-screen bg-slate-100 font-sans text-slate-900 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-950 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800">
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-500 text-slate-950 flex items-center justify-center font-black text-lg shadow-lg shadow-teal-500/20">
            FL
          </div>
          <div>
            <h1 className="font-bold text-white text-base leading-tight tracking-tight flex items-center gap-1.5">
              <span>FixLoop</span>
              <span className="text-[10px] bg-teal-500/20 text-teal-300 font-semibold px-1.5 py-0.5 rounded border border-teal-500/30">
                v1.0
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">AI Repair Operations</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-semibold transition ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-600/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono uppercase ${
                    isActive ? 'bg-teal-700 text-teal-100' : 'bg-slate-800 text-cyan-400'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Memory System Status */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-semibold text-slate-200">Hindsight Memory</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-tight">
            Collective learning active: retain & recall connected.
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Workspace /</span>
            <span className="font-semibold text-slate-800 capitalize">{currentTab.replace('-', ' ')}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
              <span>Role: <strong>Operations Support Lead</strong></span>
            </div>
            
            <button
              onClick={() => setCurrentTab('new-complaint')}
              className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>+ New Complaint</span>
            </button>
          </div>
        </header>

        {/* Scrollable View Container */}
        <main className="flex-1 overflow-y-auto p-6">
          {currentTab === 'dashboard' && (
            <Dashboard 
              onNavigate={setCurrentTab} 
              onSelectTicket={handleTicketSelect}
              onSelectCustomer={handleCustomerSelect}
            />
          )}

          {currentTab === 'new-complaint' && (
            <NewComplaint 
              onTicketCreated={(tid) => {
                setSelectedTicketId(tid);
                setCurrentTab('assistant');
              }} 
            />
          )}

          {currentTab === 'customer-360' && (
            <CustomerHistory 
              selectedCustomerId={selectedCustomerId}
              onSelectTicket={handleTicketSelect}
            />
          )}

          {currentTab === 'assistant' && (
            <AIRepairAssistant 
              selectedTicketId={selectedTicketId}
              onNavigateToCustomer={handleCustomerSelect}
            />
          )}

          {currentTab === 'ripple-effect' && (
            <BusinessInsights 
              onSelectTicket={handleTicketSelect}
              onNavigateToAssistant={() => setCurrentTab('assistant')}
            />
          )}

          {currentTab === 'followups' && (
            <FollowUps 
              onSelectTicket={handleTicketSelect}
              onNavigateToAssistant={() => setCurrentTab('assistant')}
            />
          )}

          {currentTab === 'memory-explorer' && (
            <MemoryExplorer />
          )}
        </main>
      </div>
    </div>
  );
}
