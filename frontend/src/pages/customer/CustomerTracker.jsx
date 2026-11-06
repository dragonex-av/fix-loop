import React, { useEffect, useState } from 'react';
import { getMyTickets, getMyTicket, reviewEstimate, payInvoice, rateService } from '../../services/api';
import {
  CheckCircle2, Circle, Clock, Calendar, Star, ThumbsUp,
  ThumbsDown, CreditCard, ChevronDown, Loader2, AlertCircle
} from 'lucide-react';

const ALL_STAGES = [
  { key: 'complaint_registered',  label: 'Complaint Registered',  desc: 'Your complaint has been received.' },
  { key: 'support_review',        label: 'Support Review',         desc: 'Our team is reviewing your complaint.' },
  { key: 'technician_assigned',   label: 'Technician Assigned',    desc: 'A specialist has been assigned.' },
  { key: 'visit_scheduled',       label: 'Visit Scheduled',        desc: 'Appointment confirmed.' },
  { key: 'diagnosis_completed',   label: 'Diagnosis Completed',    desc: 'Issue has been identified.' },
  { key: 'estimate_approval',     label: 'Estimate Approval',      desc: 'Waiting for your approval.' },
  { key: 'repair_in_progress',    label: 'Repair In Progress',     desc: 'Your device is being repaired.' },
  { key: 'quality_check',         label: 'Quality Check',          desc: 'Final inspection underway.' },
  { key: 'resolved',              label: 'Resolved ✓',             desc: 'Service completed successfully!' },
];

function StepTracker({ currentStage }) {
  const currentIdx = ALL_STAGES.findIndex((s) => s.key === currentStage);
  return (
    <div className="relative">
      {ALL_STAGES.map((stage, idx) => {
        const done   = idx < currentIdx;
        const active = idx === currentIdx;
        return (
          <div key={stage.key} className="flex items-start gap-4 pb-5 last:pb-0">
            <div className="flex flex-col items-center flex-shrink-0">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all ${
                done   ? 'bg-teal-500 border-teal-500' :
                active ? 'bg-white border-teal-500 ring-4 ring-teal-100' :
                         'bg-white border-slate-200'
              }`}>
                {done
                  ? <CheckCircle2 className="w-4 h-4 text-white" />
                  : active
                  ? <span className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse" />
                  : <Circle className="w-4 h-4 text-slate-200" />
                }
              </div>
              {idx < ALL_STAGES.length - 1 && (
                <div className={`w-0.5 mt-1 ${done ? 'bg-teal-400' : 'bg-slate-200'}`} style={{ height: 20 }} />
              )}
            </div>
            <div className="pt-1 pb-1 flex-1">
              <p className={`text-sm font-semibold ${
                done ? 'text-teal-700' : active ? 'text-slate-900' : 'text-slate-400'
              }`}>{stage.label}</p>
              {(done || active) && (
                <p className="text-xs text-slate-500 mt-0.5">{stage.desc}</p>
              )}
              {active && (
                <span className="inline-block mt-1 text-[10px] font-bold bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full">
                  Current Stage
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StarRating({ value, onChange }) {
  const [hovered, setHovered] = useState(0);
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <button key={s} type="button" onClick={() => onChange(s)}
          onMouseEnter={() => setHovered(s)} onMouseLeave={() => setHovered(0)}>
          <Star className={`w-6 h-6 ${(hovered || value) >= s ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}`} />
        </button>
      ))}
    </div>
  );
}

export default function CustomerTracker({ selectedTicketId, onSelectTicket }) {
  const [allTickets, setAllTickets]   = useState([]);  // flat list for dropdown
  const [ticket, setTicket]           = useState(null);
  const [listLoading, setListLoading] = useState(true);
  const [ticketLoading, setTicketLoading] = useState(false);
  const [toast, setToast]             = useState('');
  const [rating, setRating]           = useState(0);
  const [feedback, setFeedback]       = useState('');
  const [submitting, setSubmitting]   = useState(false);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  // Load ticket list for dropdown
  useEffect(() => {
    getMyTickets().then((r) => {
      const data = r.data || {};
      const list = [...(data.active_repairs || []), ...(data.past_services || [])];
      setAllTickets(list);
      if (!selectedTicketId && list.length > 0) onSelectTicket(list[0].id);
    }).catch(console.error).finally(() => setListLoading(false));
  }, []);

  // Load ticket detail whenever selection changes
  useEffect(() => {
    if (!selectedTicketId) return;
    setTicketLoading(true);
    setTicket(null);
    getMyTicket(selectedTicketId)
      .then((r) => setTicket(r.data))
      .catch(console.error)
      .finally(() => setTicketLoading(false));
  }, [selectedTicketId]);

  const handleEstimate = async (approved) => {
    try {
      setSubmitting(true);
      await reviewEstimate(ticket.id, { approved });
      showToast(approved ? '✓ Estimate approved! Repair will begin shortly.' : 'Estimate rejected.');
      const r = await getMyTicket(ticket.id); setTicket(r.data);
    } catch (e) { showToast('Error: ' + (e?.response?.data?.detail || 'Please try again.')); }
    finally { setSubmitting(false); }
  };

  const handlePay = async () => {
    try {
      setSubmitting(true);
      await payInvoice(ticket.id);
      showToast('✓ Payment recorded! Invoice marked as paid.');
      const r = await getMyTicket(ticket.id); setTicket(r.data);
    } catch (e) { showToast('Error: ' + (e?.response?.data?.detail || 'Please try again.')); }
    finally { setSubmitting(false); }
  };

  const handleRate = async () => {
    if (!rating) return;
    try {
      setSubmitting(true);
      await rateService(ticket.id, { rating, feedback });
      showToast('✓ Thank you for your feedback!');
      const r = await getMyTicket(ticket.id); setTicket(r.data);
    } catch (e) { showToast('Error: ' + (e?.response?.data?.detail || 'Please try again.')); }
    finally { setSubmitting(false); }
  };

  if (listLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-sm gap-2">
        <Loader2 className="w-5 h-5 animate-spin text-teal-500" /> Loading repairs...
      </div>
    );
  }

  if (allTickets.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
        <Clock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="font-semibold text-slate-600">No repair tickets found</p>
        <p className="text-sm text-slate-400">Raise a complaint to start tracking.</p>
      </div>
    );
  }

  // Helpers to get ticket detail fields regardless of nested/flat shape
  const productType  = ticket?.product?.type   || ticket?.product_type  || 'Appliance';
  const productModel = ticket?.product?.model  || ticket?.product_model || '';
  const productBrand = ticket?.product?.brand  || ticket?.brand         || '';
  const techName     = ticket?.technician?.name;
  const apptDate     = ticket?.appointment?.scheduled_at;
  const est          = ticket?.estimate;
  const inv          = ticket?.invoice;

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-teal-600 text-white px-4 py-2.5 rounded-xl shadow-lg text-sm font-medium">
          {toast}
        </div>
      )}

      {/* Ticket Selector */}
      <div>
        <label className="block text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Select Ticket</label>
        <div className="relative">
          <select
            value={selectedTicketId || ''}
            onChange={(e) => onSelectTicket(Number(e.target.value))}
            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 appearance-none pr-10 cursor-pointer"
          >
            {allTickets.map((t) => (
              <option key={t.id} value={t.id}>
                {t.ticket_code} — {t.product_type} {t.product_model}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {ticketLoading ? (
        <div className="flex items-center justify-center h-48 text-slate-400 text-sm gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-teal-500" /> Loading ticket...
        </div>
      ) : ticket ? (
        <div className="grid md:grid-cols-5 gap-6">
          {/* Step Tracker */}
          <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 self-start">
            <h3 className="font-bold text-slate-800 mb-5 flex items-center gap-2">
              <Clock className="w-4 h-4 text-teal-500" /> Repair Progress
            </h3>
            <StepTracker currentStage={ticket.stage} />
          </div>

          {/* Details */}
          <div className="md:col-span-3 space-y-4">
            {/* Overview Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <span className="text-xs font-mono font-bold text-teal-600">{ticket.ticket_code}</span>
                  <h2 className="text-lg font-bold text-slate-800 mt-0.5">{productType} — {productModel}</h2>
                  {productBrand && <p className="text-xs text-slate-400">{productBrand}</p>}
                </div>
                <span className={`text-xs font-bold px-2.5 py-1.5 rounded-full whitespace-nowrap ${
                  ticket.stage === 'resolved'           ? 'bg-green-100 text-green-700' :
                  ticket.stage === 'estimate_approval'  ? 'bg-orange-100 text-orange-700' :
                  'bg-teal-100 text-teal-700'
                }`}>
                  {ticket.stage?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              </div>

              <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 rounded-xl p-3">
                {ticket.issue_description}
              </p>

              {techName && (
                <div className="mt-4 flex items-center gap-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
                  <div className="w-9 h-9 bg-blue-200 rounded-full flex items-center justify-center font-bold text-blue-700 text-sm flex-shrink-0">
                    {techName[0]}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-blue-800">{techName}</p>
                    <p className="text-[11px] text-blue-500">{ticket.technician?.specialization || 'Field Technician'}</p>
                  </div>
                </div>
              )}

              {apptDate && (
                <div className="mt-3 flex items-center gap-2 text-sm text-slate-600 bg-indigo-50 rounded-xl p-3 border border-indigo-100">
                  <Calendar className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                  <span>Appointment: <strong>
                    {new Date(apptDate).toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                  </strong></span>
                </div>
              )}
            </div>

            {/* Estimate Approval */}
            {ticket.stage === 'estimate_approval' && est && (
              <div className="bg-orange-50 border border-orange-200 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="w-5 h-5 text-orange-500" />
                  <h4 className="font-bold text-orange-800">Repair Estimate — Action Required</h4>
                </div>
                <div className="bg-white rounded-xl p-4 mb-4 border border-orange-100">
                  <p className="text-sm text-slate-600 mb-3">{est.description || est.diagnosis}</p>
                  <div className="grid grid-cols-3 gap-2 text-sm text-slate-500 mb-3">
                    {est.parts_cost != null && <div>Parts: <strong className="text-slate-800">₹{est.parts_cost}</strong></div>}
                    {est.labor_cost != null && <div>Labour: <strong className="text-slate-800">₹{est.labor_cost}</strong></div>}
                    {est.tax != null && <div>Tax: <strong className="text-slate-800">₹{est.tax}</strong></div>}
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                    <span className="text-sm text-slate-500">Total Estimate</span>
                    <span className="text-xl font-bold text-slate-900">₹{est.total?.toFixed(2) || est.amount?.toFixed(2)}</span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => handleEstimate(true)} disabled={submitting}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-teal-500 hover:bg-teal-400 text-white font-bold text-sm rounded-xl transition disabled:opacity-60">
                    {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ThumbsUp className="w-4 h-4" />} Approve
                  </button>
                  <button onClick={() => handleEstimate(false)} disabled={submitting}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-white hover:bg-rose-50 border border-rose-300 text-rose-600 font-bold text-sm rounded-xl transition disabled:opacity-60">
                    <ThumbsDown className="w-4 h-4" /> Reject
                  </button>
                </div>
              </div>
            )}

            {/* Invoice */}
            {inv && inv.status === 'unpaid' && (
              <div className="bg-white border border-slate-200 rounded-2xl p-5">
                <h4 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-teal-600" /> Invoice
                </h4>
                <div className="flex items-center justify-between mb-4 bg-slate-50 rounded-xl p-4">
                  <div>
                    <p className="text-xs text-slate-500">Invoice #{inv.invoice_number || inv.id}</p>
                    <p className="text-xl font-bold text-slate-900 mt-1">₹{(inv.amount || inv.total_amount)?.toFixed(2)}</p>
                  </div>
                  <span className="text-xs font-bold bg-amber-100 text-amber-700 px-2 py-1 rounded-full">Unpaid</span>
                </div>
                <button onClick={handlePay} disabled={submitting}
                  className="w-full py-2.5 bg-teal-500 hover:bg-teal-400 text-white font-bold text-sm rounded-xl transition disabled:opacity-60 flex items-center justify-center gap-2">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
                  Pay Now (Simulated)
                </button>
              </div>
            )}

            {/* Rate Service */}
            {ticket.stage === 'resolved' && !ticket.rating && (
              <div className="bg-white border border-slate-200 rounded-2xl p-5">
                <h4 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
                  <Star className="w-4 h-4 text-amber-500" /> Rate Your Experience
                </h4>
                <StarRating value={rating} onChange={setRating} />
                <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Tell us about your experience (optional)..." rows={3}
                  className="w-full mt-3 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none" />
                <button onClick={handleRate} disabled={!rating || submitting}
                  className="mt-3 w-full py-2.5 bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold text-sm rounded-xl transition disabled:opacity-50 flex items-center justify-center gap-2">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Star className="w-4 h-4" />} Submit Rating
                </button>
              </div>
            )}

            {ticket.rating && (
              <div className="bg-green-50 border border-green-200 rounded-2xl p-4 flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <div>
                  <p className="text-sm font-semibold text-green-800">Thank you for your feedback!</p>
                  <div className="flex items-center gap-1 mt-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className={`w-4 h-4 ${i < ticket.rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}`} />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Timeline */}
            {ticket.timeline && ticket.timeline.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-2xl p-5">
                <h4 className="font-bold text-slate-800 mb-4">Activity Timeline</h4>
                <div className="space-y-3">
                  {ticket.timeline.slice().reverse().map((ev, i) => (
                    <div key={i} className="flex gap-3 text-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-400 mt-2 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-slate-700 font-medium">{ev.title || ev.note}</p>
                        {(ev.description) && <p className="text-xs text-slate-500 mt-0.5">{ev.description}</p>}
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {new Date(ev.created_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
