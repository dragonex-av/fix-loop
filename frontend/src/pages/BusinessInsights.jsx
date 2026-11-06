import React, { useState, useEffect } from 'react';
import { getPatterns, reviewPattern } from '../services/api';
import { TrendingUp, AlertTriangle, Layers, CheckCircle2, ShieldCheck, ChevronDown, ChevronUp, Eye, ArrowRight } from 'lucide-react';

export default function BusinessInsights({ onSelectTicket, onNavigateToAssistant }) {
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [reviewNote, setReviewNote] = useState('');
  const [actionSuccess, setActionSuccess] = useState(null);

  useEffect(() => {
    loadPatterns();
  }, []);

  const loadPatterns = async () => {
    try {
      setLoading(true);
      const res = await getPatterns();
      setPatterns(res.data);
      if (res.data.length > 0) {
        setExpandedId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (alertId, status) => {
    try {
      await reviewPattern(alertId, {
        status: status,
        staff_notes: reviewNote || `Staff updated status to ${status}.`
      });
      setActionSuccess(`Pattern #${alertId} marked as ${status}.`);
      setReviewNote('');
      loadPatterns();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-gradient-to-r from-teal-900 to-slate-900 text-white rounded-xl p-6 shadow-md border border-teal-800/40">
        <div className="flex items-center gap-2.5 mb-2">
          <div className="p-1.5 bg-teal-500/20 text-teal-300 rounded-lg">
            <TrendingUp className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold uppercase tracking-wider text-teal-400">
            Collective Intelligence Level 3
          </span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight">The Ripple Effect Predictor</h2>
        <p className="text-slate-300 text-sm mt-1 max-w-3xl">
          Discovers hidden product-level failure patterns by analyzing recurring issues across multiple distinct customers.
          Grounded directly in database records to ensure zero AI fabrication.
        </p>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Scanning tickets for cross-customer patterns...</div>
      ) : patterns.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
          No cross-customer failure clusters meet the activation threshold yet (threshold: 3+ distinct customers).
        </div>
      ) : (
        <div className="space-y-6">
          {patterns.map((alert) => {
            const isExpanded = expandedId === alert.id;
            return (
              <div 
                key={alert.id}
                className="bg-white rounded-xl border border-slate-200/90 shadow-sm overflow-hidden"
              >
                {/* Cluster Header */}
                <div 
                  onClick={() => setExpandedId(isExpanded ? null : alert.id)}
                  className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer hover:bg-slate-50 transition"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-teal-100/70 text-teal-800 flex flex-col items-center justify-center font-bold">
                      <span className="text-lg leading-none">{alert.case_count}</span>
                      <span className="text-[9px] uppercase tracking-wider">Cases</span>
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-900">{alert.product_model}</span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {alert.issue_category}
                        </span>
                        <span className={`text-[11px] px-2 py-0.5 rounded-full font-bold uppercase ${
                          alert.status === 'active' ? 'bg-rose-100 text-rose-800' :
                          alert.status === 'investigating' ? 'bg-amber-100 text-amber-800' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {alert.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        Detected across {alert.supporting_cases?.length || alert.case_count} distinct customer tickets.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end md:self-center">
                    <span className="text-xs font-semibold text-teal-600 hover:text-teal-700">
                      {isExpanded ? 'Collapse Cases' : 'Inspect Supporting Cases'}
                    </span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </div>
                </div>

                {/* Expanded Cluster Details */}
                {isExpanded && (
                  <div className="border-t border-slate-100 bg-slate-50/50 p-6 space-y-6">
                    {/* Suggested Investigation Strategy */}
                    <div className="p-4 bg-teal-50 border border-teal-200/80 rounded-xl space-y-1.5">
                      <div className="text-xs font-bold text-teal-900 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-teal-700" />
                        <span>Recommended Operations Investigation Protocol</span>
                      </div>
                      <p className="text-xs text-teal-800 leading-relaxed">
                        {alert.suggested_investigation}
                      </p>
                      <div className="text-[11px] text-teal-700/80 italic pt-1">
                        * {alert.disclaimer}
                      </div>
                    </div>

                    {/* Supporting Customer Tickets Table */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3">
                        Supporting Evidence: Customer Ticket Records
                      </h4>
                      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-100/70 text-slate-600 border-b border-slate-200 font-semibold uppercase text-[10px]">
                            <tr>
                              <th className="py-2.5 px-3">Ticket</th>
                              <th className="py-2.5 px-3">Customer</th>
                              <th className="py-2.5 px-3">Status</th>
                              <th className="py-2.5 px-3">Recorded Action</th>
                              <th className="py-2.5 px-3">Confirmed Outcome</th>
                              <th className="py-2.5 px-3 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {alert.supporting_cases?.map((c) => (
                              <tr key={c.ticket_id} className="hover:bg-slate-50 transition">
                                <td className="py-2.5 px-3 font-mono font-semibold text-teal-700">
                                  {c.ticket_code}
                                </td>
                                <td className="py-2.5 px-3 font-medium text-slate-900">
                                  {c.customer_name}
                                </td>
                                <td className="py-2.5 px-3">
                                  <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[10px]">
                                    {c.status}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3 text-slate-600">
                                  {c.repair_action || 'None recorded'}
                                </td>
                                <td className="py-2.5 px-3">
                                  <span className={`px-2 py-0.5 rounded-full font-bold uppercase text-[10px] ${
                                    c.repair_outcome === 'successful' ? 'bg-emerald-100 text-emerald-800' :
                                    c.repair_outcome === 'temporary' ? 'bg-amber-100 text-amber-800' :
                                    c.repair_outcome === 'unsuccessful' ? 'bg-rose-100 text-rose-800' :
                                    'bg-slate-100 text-slate-600'
                                  }`}>
                                    {c.repair_outcome}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3 text-right">
                                  {onSelectTicket && (
                                    <button
                                      onClick={() => {
                                        onSelectTicket(c.ticket_id);
                                        if (onNavigateToAssistant) onNavigateToAssistant();
                                      }}
                                      className="text-teal-600 hover:text-teal-800 font-semibold inline-flex items-center gap-1"
                                    >
                                      Inspect <ArrowRight className="w-3 h-3" />
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Operational Review Controls */}
                    <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                      <input
                        type="text"
                        placeholder="Add engineering/management review notes..."
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                        className="w-full sm:w-96 text-xs border border-slate-300 rounded-lg p-2 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                      />
                      <div className="flex gap-2 w-full sm:w-auto">
                        <button
                          onClick={() => handleReview(alert.id, 'investigating')}
                          className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold shadow transition"
                        >
                          Mark for Investigation
                        </button>
                        <button
                          onClick={() => handleReview(alert.id, 'dismissed')}
                          className="px-3.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition"
                        >
                          Dismiss Pattern
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
