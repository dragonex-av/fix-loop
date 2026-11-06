import React, { useState, useEffect } from 'react';
import { getCustomers, getCustomerHistory } from '../services/api';
import { User, Phone, Mail, Clock, Wrench, AlertCircle, CheckCircle, Calendar, ArrowRight } from 'lucide-react';

export default function CustomerHistory({ selectedCustomerId, onSelectTicket }) {
  const [customers, setCustomers] = useState([]);
  const [currentId, setCurrentId] = useState(selectedCustomerId || 1);
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCustomers();
  }, []);

  useEffect(() => {
    if (currentId) {
      loadHistory(currentId);
    }
  }, [currentId]);

  const loadCustomers = async () => {
    try {
      const res = await getCustomers();
      setCustomers(res.data);
      if (!selectedCustomerId && res.data.length > 0) {
        setCurrentId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadHistory = async (id) => {
    try {
      setLoading(true);
      const res = await getCustomerHistory(id);
      setHistoryData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Customer Selector Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="w-10 h-10 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Customer 360 Intelligence Profile</h2>
            <p className="text-xs text-slate-500">Every interaction and confirmed repair outcome remembered</p>
          </div>
        </div>

        <div className="w-full sm:w-72">
          <select
            value={currentId}
            onChange={(e) => setCurrentId(parseInt(e.target.value))}
            className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none"
          >
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} — {c.phone}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          Loading Customer 360 history...
        </div>
      ) : historyData ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Customer Profile Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4 h-fit">
            <h3 className="text-sm font-semibold text-slate-900 border-b border-slate-100 pb-3">Customer Information</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-3 text-slate-700">
                <User className="w-4 h-4 text-slate-400" />
                <span className="font-medium text-slate-900">{historyData.customer.name}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-700">
                <Phone className="w-4 h-4 text-slate-400" />
                <span>{historyData.customer.phone}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-700">
                <Mail className="w-4 h-4 text-slate-400" />
                <span>{historyData.customer.email || 'No email registered'}</span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <div className="p-3 bg-teal-50 rounded-lg border border-teal-100 text-xs text-teal-800 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5" /> FixLoop Collective Memory
                </div>
                <p className="text-teal-700 text-[11px]">
                  All confirmed repair outcomes for this customer are indexed in Hindsight Cloud to eliminate repeated troubleshooting errors.
                </p>
              </div>
            </div>
          </div>

          {/* Chronological Timeline */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-6">Service & Operational Experience Timeline</h3>

            {historyData.timeline.length === 0 ? (
              <p className="text-slate-400 text-xs py-8 text-center">No service history recorded for this customer yet.</p>
            ) : (
              <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pl-6">
                {historyData.timeline.map((item, idx) => (
                  <div key={idx} className="relative group">
                    {/* Timeline Node Badge */}
                    <div className={`absolute -left-[31px] top-0 w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-white ${
                      item.type === 'repair_performed' ? (
                        item.outcome === 'successful' ? 'bg-emerald-500' :
                        item.outcome === 'temporary' ? 'bg-amber-500' : 'bg-rose-500'
                      ) : item.type === 'followup_scheduled' ? 'bg-indigo-500' : 'bg-sky-500'
                    }`}>
                      {item.type === 'repair_performed' ? <Wrench className="w-3 h-3" /> :
                       item.type === 'followup_scheduled' ? <Calendar className="w-3 h-3" /> :
                       <AlertCircle className="w-3 h-3" />}
                    </div>

                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 hover:border-slate-300 transition">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-semibold text-teal-700 bg-teal-100/60 px-2 py-0.5 rounded">
                            {item.ticket_code}
                          </span>
                          <span className="text-sm font-bold text-slate-900">{item.title}</span>
                        </div>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {new Date(item.date).toLocaleDateString()}
                        </span>
                      </div>

                      <p className="text-xs text-slate-600 mb-2">{item.description}</p>

                      {item.type === 'repair_performed' && (
                        <div className="flex items-center gap-3 pt-2 border-t border-slate-200/60 text-xs">
                          <span className="font-medium text-slate-500">Confirmed Outcome:</span>
                          <span className={`px-2 py-0.5 rounded-full font-bold uppercase text-[10px] ${
                            item.outcome === 'successful' ? 'bg-emerald-100 text-emerald-800' :
                            item.outcome === 'temporary' ? 'bg-amber-100 text-amber-800' :
                            'bg-rose-100 text-rose-800'
                          }`}>
                            {item.outcome}
                          </span>
                          {item.confirmed_by && (
                            <span className="text-slate-400 text-[11px] ml-auto">Confirmed by {item.confirmed_by}</span>
                          )}
                        </div>
                      )}

                      {item.type === 'followup_scheduled' && (
                        <div className="flex items-center gap-2 pt-2 border-t border-slate-200/60 text-xs text-slate-500">
                          <span>Status: <strong className="uppercase font-semibold text-indigo-700">{item.status}</strong></span>
                        </div>
                      )}

                      {item.ticket_id && onSelectTicket && (
                        <div className="mt-2 text-right">
                          <button
                            onClick={() => onSelectTicket(item.ticket_id)}
                            className="text-[11px] font-semibold text-teal-600 hover:text-teal-700 inline-flex items-center gap-1"
                          >
                            Open in AI Assistant <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
