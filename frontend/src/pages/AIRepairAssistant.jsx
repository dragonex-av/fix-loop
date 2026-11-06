import React, { useState, useEffect } from 'react';
import { getTickets, getTicketDetail, analyzeTicket, recordRepair, createFollowup } from '../services/api';
import { 
  Bot, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  Wrench, 
  FileText, 
  Send, 
  Sparkles,
  Search,
  Clock
} from 'lucide-react';

export default function AIRepairAssistant({ selectedTicketId, onNavigateToCustomer }) {
  const [tickets, setTickets] = useState([]);
  const [currentTicketId, setCurrentTicketId] = useState(selectedTicketId || '');
  const [ticketData, setTicketData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loadingTicket, setLoadingTicket] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  
  // Repair Recording Form
  const [repairAction, setRepairAction] = useState('');
  const [repairOutcome, setRepairOutcome] = useState('successful');
  const [technicianNotes, setTechnicianNotes] = useState('');
  const [confirmedBy, setConfirmedBy] = useState('Vikram Singh (Sr. Tech)');
  const [savingRepair, setSavingRepair] = useState(false);
  const [repairSuccessMsg, setRepairSuccessMsg] = useState(null);

  // Quick Followup Form
  const [showFollowupForm, setShowFollowupForm] = useState(false);
  const [followupDays, setFollowupDays] = useState(5);
  const [followupNotes, setFollowupNotes] = useState('Post-repair verification call to ensure issue did not return.');
  const [followupSaving, setFollowupSaving] = useState(false);
  const [followupSuccessMsg, setFollowupSuccessMsg] = useState(null);

  useEffect(() => {
    loadTicketList();
  }, []);

  useEffect(() => {
    if (selectedTicketId) {
      setCurrentTicketId(selectedTicketId);
    }
  }, [selectedTicketId]);

  useEffect(() => {
    if (currentTicketId) {
      loadTicketDetails(currentTicketId);
    }
  }, [currentTicketId]);

  const loadTicketList = async () => {
    try {
      const res = await getTickets();
      setTickets(res.data);
      if (!currentTicketId && res.data.length > 0) {
        setCurrentTicketId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadTicketDetails = async (id) => {
    try {
      setLoadingTicket(true);
      setAnalysis(null);
      setRepairSuccessMsg(null);
      const res = await getTicketDetail(id);
      setTicketData(res.data);
      // Auto trigger analysis if ticket is loaded
      triggerAnalysis(id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTicket(false);
    }
  };

  const triggerAnalysis = async (id) => {
    try {
      setAnalyzing(true);
      const res = await analyzeTicket(id);
      setAnalysis(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRecordRepair = async (e) => {
    e.preventDefault();
    if (!repairAction.trim()) return;

    try {
      setSavingRepair(true);
      setRepairSuccessMsg(null);
      await recordRepair(currentTicketId, {
        action: repairAction,
        outcome: repairOutcome,
        technician_notes: technicianNotes,
        confirmed_by: confirmedBy
      });
      setRepairSuccessMsg(`Repair action recorded and confirmed outcome retained into Hindsight Cloud!`);
      setRepairAction('');
      setTechnicianNotes('');
      // Reload ticket
      loadTicketDetails(currentTicketId);
    } catch (err) {
      console.error(err);
    } finally {
      setSavingRepair(false);
    }
  };

  const handleCreateFollowup = async (e) => {
    e.preventDefault();
    try {
      setFollowupSaving(true);
      const promisedDate = new Date();
      promisedDate.setDate(promisedDate.getDate() + parseInt(followupDays));

      await createFollowup({
        ticket_id: currentTicketId,
        promised_at: promisedDate.toISOString(),
        owner: confirmedBy,
        notes: followupNotes
      });
      setFollowupSuccessMsg('Proactive follow-up scheduled in Task Center!');
      setShowFollowupForm(false);
    } catch (err) {
      console.error(err);
    } finally {
      setFollowupSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Ticket Selection Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">AI Repair Assistant & Intelligence Copilot</h2>
          <p className="text-xs text-slate-500">Recalls confirmed outcomes from Hindsight to prevent repeat diagnosis mistakes</p>
        </div>

        <div className="w-full sm:w-80">
          <select
            value={currentTicketId}
            onChange={(e) => setCurrentTicketId(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none"
          >
            {tickets.map((t) => (
              <option key={t.id} value={t.id}>
                {t.ticket_code} — {t.customer_name} ({t.issue_category})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadingTicket ? (
        <div className="p-12 text-center text-slate-400 text-sm">Loading ticket details...</div>
      ) : ticketData ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Ticket Info & Human Confirmation Form */}
          <div className="space-y-6">
            {/* Ticket Card */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="font-mono text-sm font-bold text-teal-800 bg-teal-50 px-2.5 py-1 rounded">
                  {ticketData.ticket_code}
                </span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                  ticketData.status === 'Resolved' ? 'bg-emerald-100 text-emerald-800' :
                  ticketData.status === 'Reopened' ? 'bg-amber-100 text-amber-800' :
                  'bg-slate-100 text-slate-800'
                }`}>
                  {ticketData.status}
                </span>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Customer</span>
                <div className="text-sm font-bold text-slate-900 mt-0.5">{ticketData.customer.name}</div>
                <div className="text-xs text-slate-500">{ticketData.customer.phone}</div>
                {onNavigateToCustomer && (
                  <button
                    onClick={() => onNavigateToCustomer(ticketData.customer.id)}
                    className="text-[11px] text-teal-600 hover:underline mt-1 block font-medium"
                  >
                    View Customer 360 Timeline →
                  </button>
                )}
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Appliance</span>
                <div className="text-sm font-medium text-slate-900 mt-0.5">
                  {ticketData.product.brand} {ticketData.product.model}
                </div>
                <div className="text-xs text-slate-500">{ticketData.product.product_type}</div>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Reported Complaint</span>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-xs text-slate-700 mt-1 leading-relaxed">
                  "{ticketData.issue_description}"
                </div>
              </div>
            </div>

            {/* Human Confirmation & Repair Outcome Recording */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-teal-600" />
                  <span>Authorized Staff Repair Confirmation</span>
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Only authorized staff confirm outcomes. Confirmed outcomes are retained into Hindsight experience memory.
                </p>
              </div>

              {repairSuccessMsg && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>{repairSuccessMsg}</span>
                </div>
              )}

              <form onSubmit={handleRecordRepair} className="space-y-3.5">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Repair Action Performed *</label>
                  <input
                    type="text"
                    required
                    value={repairAction}
                    onChange={(e) => setRepairAction(e.target.value)}
                    placeholder="e.g. Replaced internal drain pump & cleaned impeller"
                    className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">Confirmed Outcome *</label>
                    <select
                      value={repairOutcome}
                      onChange={(e) => setRepairOutcome(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-lg p-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none font-semibold"
                    >
                      <option value="successful">Successful (Permanent Fix)</option>
                      <option value="temporary">Temporary (Recurrence Risk)</option>
                      <option value="unsuccessful">Unsuccessful (Failed)</option>
                      <option value="pending">Pending Customer Trial</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">Authorized By</label>
                    <input
                      type="text"
                      value={confirmedBy}
                      onChange={(e) => setConfirmedBy(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">Technician Notes</label>
                  <textarea
                    rows={2}
                    value={technicianNotes}
                    onChange={(e) => setTechnicianNotes(e.target.value)}
                    placeholder="Specific observations, component part numbers, or electrical readings..."
                    className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={savingRepair}
                  className="w-full py-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg shadow transition flex items-center justify-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{savingRepair ? 'Retaining in Hindsight...' : 'Confirm & Retain in Memory'}</span>
                </button>
              </form>

              {/* Proactive Follow-up Shortcut */}
              <div className="pt-3 border-t border-slate-100">
                {!showFollowupForm ? (
                  <button
                    type="button"
                    onClick={() => setShowFollowupForm(true)}
                    className="w-full py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition flex items-center justify-center gap-1.5"
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>+ Schedule Proactive Follow-up</span>
                  </button>
                ) : (
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                    <span className="font-semibold text-slate-900 block">Schedule Proactive Customer Follow-up</span>
                    <div>
                      <label className="text-[11px] text-slate-500">Days from today</label>
                      <input
                        type="number"
                        min="1"
                        max="30"
                        value={followupDays}
                        onChange={(e) => setFollowupDays(e.target.value)}
                        className="w-full text-xs border border-slate-300 rounded p-1.5 mt-0.5"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-500">Follow-up goal</label>
                      <input
                        type="text"
                        value={followupNotes}
                        onChange={(e) => setFollowupNotes(e.target.value)}
                        className="w-full text-xs border border-slate-300 rounded p-1.5 mt-0.5"
                      />
                    </div>
                    <div className="flex gap-2 pt-1">
                      <button
                        type="button"
                        onClick={handleCreateFollowup}
                        disabled={followupSaving}
                        className="flex-1 py-1.5 bg-indigo-600 text-white rounded font-medium text-xs"
                      >
                        Save Commitment
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowFollowupForm(false)}
                        className="px-3 py-1.5 bg-slate-200 text-slate-700 rounded text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right 2 Columns: AI Repair Advisory + Recalled Hindsight Evidence */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">AI Repair Advisory & Memory Synthesis</h3>
                    <p className="text-xs text-slate-500">
                      Reasoned over Hindsight Cloud experience vectors and past technician outcomes
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => triggerAnalysis(currentTicketId)}
                  disabled={analyzing}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5"
                >
                  <Cpu className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin text-teal-600' : ''}`} />
                  <span>{analyzing ? 'Recalling...' : 'Re-analyze Case'}</span>
                </button>
              </div>

              {analyzing ? (
                <div className="py-16 text-center space-y-3">
                  <Cpu className="w-8 h-8 animate-spin mx-auto text-teal-600" />
                  <p className="text-sm font-medium text-slate-700">Recalling Hindsight memories & querying Groq...</p>
                  <p className="text-xs text-slate-400">Comparing prior customer repairs against collective patterns</p>
                </div>
              ) : analysis ? (
                <div className="space-y-6">
                  {/* Repeat Issue Banner */}
                  {analysis.repeat_issue ? (
                    <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-r-xl space-y-2">
                      <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span>Repeat Issue Detected for this Customer</span>
                      </div>
                      <p className="text-xs text-amber-800 leading-relaxed">
                        {analysis.repeat_reason}
                      </p>
                      {analysis.previous_repair_summary && (
                        <div className="text-[11px] bg-amber-100/70 p-2.5 rounded font-mono text-amber-950 space-y-1">
                          <div><strong>Prior Action:</strong> {analysis.previous_repair_summary}</div>
                          <div><strong>Confirmed Outcome:</strong> {analysis.previous_outcome}</div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-xl">
                      <div className="flex items-center gap-2 text-blue-900 font-bold text-sm">
                        <CheckCircle2 className="w-4 h-4 text-blue-600" />
                        <span>First-Time Issue for this Customer Baseline</span>
                      </div>
                      <p className="text-xs text-blue-800 mt-1">
                        No previous repair failures recorded for this customer/product combination. Standard diagnostics recommended.
                      </p>
                    </div>
                  )}

                  {/* Counterfactual Advice / What to Inspect Next */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-teal-600" />
                      <span>Suggested Inspection Areas (Advisory)</span>
                    </h4>
                    <div className="space-y-2">
                      {analysis.suggested_inspection_areas.map((area, idx) => (
                        <div key={idx} className="p-3 bg-teal-50/50 border border-teal-200/70 rounded-lg flex items-start gap-2.5 text-xs text-slate-800">
                          <span className="w-5 h-5 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center flex-shrink-0 text-[10px]">
                            {idx + 1}
                          </span>
                          <span className="font-medium">{area}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Operational Reasoning Explanation */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1.5">
                      Operational Reasoning
                    </h4>
                    <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-lg border border-slate-200/80">
                      {analysis.explanation}
                    </p>
                  </div>

                  {/* Supporting Evidence Citations */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                      Supporting Evidence Citations (Audit Grounding)
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {analysis.supporting_evidence.map((ev, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-900 capitalize text-[11px]">
                              {ev.source.replace('_', ' ')}
                            </span>
                            <span className="font-mono text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded">
                              {ev.reference}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600">{ev.detail}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Safety & Advisory Disclaimers */}
                  <div className="p-3 bg-slate-100 rounded-lg text-[11px] text-slate-500 space-y-1">
                    <div className="font-semibold text-slate-700 flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5" /> AI Safety & Advisory Limitations
                    </div>
                    {analysis.limitations.map((lim, idx) => (
                      <p key={idx}>• {lim}</p>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-400 text-xs">
                  Click 'Re-analyze Case' to generate memory-backed repair intelligence.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
