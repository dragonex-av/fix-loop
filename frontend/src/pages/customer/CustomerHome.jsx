import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getMyTickets } from '../../services/api';
import {
  Wrench, Clock, CheckCircle2, AlertCircle, PlusCircle,
  ArrowRight, Calendar, ChevronRight, Activity
} from 'lucide-react';

const STAGE_LABEL = {
  complaint_registered: 'Complaint Registered',
  support_review:       'Under Review',
  technician_assigned:  'Technician Assigned',
  visit_scheduled:      'Visit Scheduled',
  diagnosis_completed:  'Diagnosis Done',
  estimate_approval:    'Awaiting Your Approval',
  repair_in_progress:   'Repair In Progress',
  quality_check:        'Quality Check',
  resolved:             'Resolved',
};

function TicketCard({ ticket, onView }) {
  const isEstimate = ticket.stage === 'estimate_approval';
  const label = STAGE_LABEL[ticket.stage] || ticket.stage;
  return (
    <div
      onClick={() => onView(ticket.id)}
      className="bg-white rounded-xl border border-slate-200 p-4 hover:border-teal-400 hover:shadow-md transition cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold text-teal-600">{ticket.ticket_code}</span>
            {isEstimate && (
              <span className="text-[10px] font-bold bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full border border-orange-200">
                Action Required
              </span>
            )}
          </div>
          <p className="text-sm font-semibold text-slate-800 truncate">
            {ticket.product_type} — {ticket.product_model}
          </p>
          <p className="text-xs text-slate-500 truncate mt-0.5">{ticket.issue_description}</p>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-teal-500 flex-shrink-0 mt-1 transition" />
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${
          ticket.stage === 'resolved'          ? 'bg-green-100 text-green-700' :
          ticket.stage === 'estimate_approval' ? 'bg-orange-100 text-orange-700' :
          ticket.stage === 'repair_in_progress'? 'bg-teal-100 text-teal-700' :
                                                 'bg-blue-100 text-blue-700'
        }`}>
          {label}
        </span>
        {ticket.appointment?.scheduled_at && (
          <span className="flex items-center gap-1 text-[11px] text-slate-400">
            <Calendar className="w-3 h-3" />
            {new Date(ticket.appointment.scheduled_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
          </span>
        )}
      </div>
    </div>
  );
}

export default function CustomerHome({ onViewTicket, onRaise }) {
  const { user } = useAuth();
  const [data, setData]       = useState({ active_repairs: [], past_services: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyTickets()
      .then((r) => setData(r.data || { active_repairs: [], past_services: [] }))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const active   = data.active_repairs  || [];
  const resolved = data.past_services   || [];
  const needsAction = active.filter((t) => t.stage === 'estimate_approval');
  const total = active.length + resolved.length;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl p-6 text-white shadow-lg">
        <p className="text-sm text-teal-300 font-medium mb-1">Welcome back,</p>
        <h2 className="text-2xl font-bold">{user?.full_name || 'Customer'} 👋</h2>
        <p className="text-slate-400 text-sm mt-1">Track your repairs, raise complaints, and chat with our AI assistant.</p>
        <button
          onClick={onRaise}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm rounded-xl transition shadow-lg shadow-teal-500/30"
        >
          <PlusCircle className="w-4 h-4" /> Raise New Complaint
        </button>
      </div>

      {/* Action Required Alert */}
      {needsAction.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-orange-800">Action Required</p>
            <p className="text-xs text-orange-600 mt-0.5">
              {needsAction.length} ticket{needsAction.length > 1 ? 's' : ''} waiting for your estimate approval.
            </p>
          </div>
          <button
            onClick={() => onViewTicket(needsAction[0].id)}
            className="text-xs font-semibold text-orange-700 hover:text-orange-900 flex items-center gap-1 flex-shrink-0"
          >
            Review <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Active Repairs', value: active.length,   icon: Wrench,       color: 'teal'  },
          { label: 'Resolved',       value: resolved.length, icon: CheckCircle2, color: 'green' },
          { label: 'Total Tickets',  value: total,           icon: Activity,     color: 'blue'  },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 p-4 text-center">
            <div className={`w-9 h-9 mx-auto rounded-lg bg-${color}-100 flex items-center justify-center mb-2`}>
              <Icon className={`w-4 h-4 text-${color}-600`} />
            </div>
            <p className="text-2xl font-bold text-slate-800">{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Tickets */}
      {loading ? (
        <div className="flex items-center justify-center h-32 text-slate-400 text-sm gap-2">
          <span className="w-4 h-4 border-2 border-slate-300 border-t-teal-500 rounded-full animate-spin" />
          Loading your repairs...
        </div>
      ) : (
        <>
          {active.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-teal-600" /> Active Repairs
                </h3>
                <span className="text-xs text-slate-400">{active.length} ongoing</span>
              </div>
              <div className="space-y-3">
                {active.map((t) => <TicketCard key={t.id} ticket={t} onView={onViewTicket} />)}
              </div>
            </section>
          )}

          {resolved.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" /> Previous Services
                </h3>
                <span className="text-xs text-slate-400">{resolved.length} completed</span>
              </div>
              <div className="space-y-3">
                {resolved.map((t) => <TicketCard key={t.id} ticket={t} onView={onViewTicket} />)}
              </div>
            </section>
          )}

          {total === 0 && (
            <div className="bg-white rounded-xl border border-dashed border-slate-300 p-10 text-center">
              <Wrench className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-600">No repairs yet</p>
              <p className="text-sm text-slate-400 mt-1">Raise your first complaint to get started.</p>
              <button
                onClick={onRaise}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-teal-500 text-slate-950 font-bold text-sm rounded-xl hover:bg-teal-400 transition"
              >
                <PlusCircle className="w-4 h-4" /> Raise Complaint
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
