import React, { useEffect, useState } from 'react';
import { getDashboard } from '../services/api';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Cpu, 
  Layers, 
  TrendingUp, 
  ArrowRight,
  ShieldCheck,
  Activity
} from 'lucide-react';

export default function Dashboard({ onNavigate, onSelectTicket, onSelectCustomer }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await getDashboard();
      setData(res.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Unable to load dashboard metrics. Check if backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        <Activity className="w-6 h-6 animate-spin mr-2 text-teal-600" />
        <span>Loading operational intelligence...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner / System Loop Summary */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-xl p-6 shadow-md border border-slate-700/60">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 mb-2">
              <Cpu className="w-3.5 h-3.5" /> Hindsight Memory Loop Active
            </div>
            <h2 className="text-xl md:text-2xl font-bold tracking-tight">
              FixLoop Operations & Repair Intelligence
            </h2>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              Every complaint is captured, prior confirmed outcomes are recalled, and cross-customer patterns alert the team before repeat failures spread.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onNavigate('new-complaint')}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold rounded-lg shadow transition flex items-center gap-1.5"
            >
              + New Complaint
            </button>
            <button
              onClick={() => onNavigate('memory-explorer')}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition flex items-center gap-1.5"
            >
              Inspect Memory
            </button>
          </div>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          onClick={() => onNavigate('new-complaint')} 
          className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm hover:border-slate-300 transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Tickets</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-sm">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900">{data?.total_tickets ?? 0}</span>
            <span className="text-xs text-slate-500 font-medium">{data?.open_tickets ?? 0} active</span>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('assistant')} 
          className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm hover:border-amber-300 transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Repeat Cases</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-sm">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-amber-600">{data?.repeat_cases ?? 0}</span>
            <span className="text-xs text-slate-500">reopened / recurrence</span>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('ripple-effect')} 
          className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm hover:border-teal-300 transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Ripple Effect Alerts</span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center font-bold text-sm">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-teal-700">{data?.active_patterns ?? 0}</span>
            <span className="text-xs text-teal-600 font-medium">model clusters</span>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('followups')} 
          className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm hover:border-rose-300 transition cursor-pointer"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Overdue Follow-ups</span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-sm">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-rose-600">{data?.overdue_followups ?? 0}</span>
            <span className="text-xs text-rose-600 font-medium">rescue required</span>
          </div>
        </div>
      </div>

      {/* Middle Section: "Needs Attention" Queue */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <h3 className="font-semibold text-slate-900 text-sm">Operational "Needs Attention" Queue</h3>
          </div>
          <span className="text-xs text-slate-500 font-medium">Cross-customer warnings & overdue tasks</span>
        </div>
        <div className="divide-y divide-slate-100">
          {data?.needs_attention?.length > 0 ? (
            data.needs_attention.map((item, idx) => (
              <div 
                key={idx} 
                className="p-4 hover:bg-slate-50 flex items-center justify-between transition cursor-pointer"
                onClick={() => {
                  if (item.type === 'overdue_followup') onNavigate('followups');
                  if (item.type === 'ripple_pattern') onNavigate('ripple-effect');
                }}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 p-1.5 rounded-lg ${
                    item.severity === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">{item.title}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">{item.detail}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs font-medium text-teal-600 hover:text-teal-700">
                  <span>Take action</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-xs text-slate-500">
              No critical operational blockers right now.
            </div>
          )}
        </div>
      </div>

      {/* Bottom Grid: Recent Cases & Recent Memory Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tickets */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900 text-sm">Recent Tickets & Repairs</h3>
            <button onClick={() => onNavigate('assistant')} className="text-xs text-teal-600 hover:underline font-medium">
              View all
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {data?.recent_tickets?.map((t) => (
              <div 
                key={t.id} 
                onClick={() => {
                  onSelectTicket(t.id);
                  onNavigate('assistant');
                }}
                className="p-4 hover:bg-slate-50 transition cursor-pointer flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                      {t.ticket_code}
                    </span>
                    <span className="text-sm font-medium text-slate-900">{t.customer_name}</span>
                    <span className="text-xs text-slate-500">({t.model})</span>
                  </div>
                  <div className="text-xs text-slate-600 mt-1">
                    {t.issue_category} — <span className="text-slate-500">Outcome: {t.latest_outcome || 'Pending'}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    t.status === 'Resolved' ? 'bg-emerald-100 text-emerald-800' :
                    t.status === 'Reopened' ? 'bg-amber-100 text-amber-800' :
                    'bg-slate-100 text-slate-800'
                  }`}>
                    {t.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Hindsight Memory Activity */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-teal-600" />
              <h3 className="font-semibold text-slate-900 text-sm">Hindsight Experience Memory Log</h3>
            </div>
            <button onClick={() => onNavigate('memory-explorer')} className="text-xs text-teal-600 hover:underline font-medium">
              Audit trail
            </button>
          </div>
          <div className="divide-y divide-slate-100 font-mono text-xs">
            {data?.recent_memory_events?.length > 0 ? (
              data.recent_memory_events.map((m) => (
                <div key={m.id} className="p-3.5 hover:bg-slate-50 flex items-center justify-between gap-3">
                  <div className="truncate">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-1.5 py-0.5 rounded uppercase font-bold text-[10px] ${
                        m.operation === 'retain' ? 'bg-indigo-100 text-indigo-800' : 'bg-cyan-100 text-cyan-800'
                      }`}>
                        {m.operation}
                      </span>
                      <span className="text-slate-700 truncate">{m.query_or_content}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-sans">
                      Ref: {m.provider_ref || 'Local audit'}
                    </div>
                  </div>
                  <span className="text-[11px] font-sans px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">
                    {m.status}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-slate-400 font-sans text-xs">
                No memory events yet. Submit a complaint or record a repair to trigger retain/recall.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
