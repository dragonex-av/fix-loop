import React, { useState, useEffect } from 'react';
import { getFollowups, updateFollowup } from '../services/api';
import { Clock, CheckCircle2, AlertCircle, Calendar, PhoneCall, UserCheck } from 'lucide-react';

export default function FollowUps({ onSelectTicket, onNavigateToAssistant }) {
  const [followups, setFollowups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all'); // all, overdue, due, upcoming
  const [actionMsg, setActionMsg] = useState(null);

  useEffect(() => {
    loadFollowups();
  }, []);

  const loadFollowups = async () => {
    try {
      setLoading(true);
      const res = await getFollowups();
      setFollowups(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (id) => {
    try {
      await updateFollowup(id, {
        status: 'completed',
        notes: 'Contacted customer by phone. Customer confirmed appliance is working without recurrence.'
      });
      setActionMsg(`Follow-up #${id} marked as completed.`);
      loadFollowups();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredFollowups = followups.filter((f) => {
    if (activeTab === 'all') return true;
    return f.status === activeTab;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-rose-600 font-bold text-xs uppercase tracking-wider mb-1">
            <Clock className="w-4 h-4" />
            <span>Flow D: Proactive Customer Rescue</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900">Follow-Up Task Center</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Staff-controlled commitment callbacks. FixLoop ensures promised check-ins never slip through the cracks.
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-lg text-xs font-medium">
          {['all', 'overdue', 'due', 'upcoming', 'completed'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded-md capitalize transition ${
                activeTab === tab ? 'bg-white text-slate-900 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionMsg}</span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Loading follow-up queue...</div>
      ) : filteredFollowups.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-400 text-xs">
          No follow-up commitments found for status '{activeTab}'.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredFollowups.map((item) => (
            <div
              key={item.id}
              className={`bg-white rounded-xl border p-5 shadow-sm space-y-3 transition ${
                item.status === 'overdue' ? 'border-rose-300 ring-1 ring-rose-200' :
                item.status === 'due' ? 'border-amber-300' :
                'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  item.status === 'overdue' ? 'bg-rose-100 text-rose-800' :
                  item.status === 'due' ? 'bg-amber-100 text-amber-800' :
                  item.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                  'bg-slate-100 text-slate-700'
                }`}>
                  {item.status}
                </span>

                <span className="font-mono text-xs font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                  {item.ticket_code}
                </span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-900">{item.customer_name}</h3>
                <p className="text-xs text-slate-600 mt-1">{item.notes || 'Customer verification follow-up.'}</p>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                  <span>Assigned: <strong>{item.owner}</strong></span>
                </div>
                <div>
                  Promised: <span className="font-mono font-medium text-slate-700">{new Date(item.promised_at).toLocaleString()}</span>
                </div>
              </div>

              {item.status !== 'completed' && (
                <div className="pt-2 flex gap-2">
                  <button
                    onClick={() => handleComplete(item.id)}
                    className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Complete Callback</span>
                  </button>

                  {onSelectTicket && (
                    <button
                      onClick={() => {
                        onSelectTicket(item.ticket_id);
                        if (onNavigateToAssistant) onNavigateToAssistant();
                      }}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
                    >
                      Inspect Ticket
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
