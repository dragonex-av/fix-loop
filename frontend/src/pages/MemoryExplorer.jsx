import React, { useState, useEffect } from 'react';
import { getMemoryEvents } from '../services/api';
import { Cpu, Database, CheckCircle2, AlertCircle, Search, RefreshCw, Key, Code } from 'lucide-react';

export default function MemoryExplorer() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterOp, setFilterOp] = useState('');
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => {
    loadEvents();
  }, [filterOp]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterOp) params.operation = filterOp;
      const res = await getMemoryEvents(params);
      setEvents(res.data);
      if (res.data.length > 0) {
        setSelectedEvent(res.data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 text-white rounded-xl p-6 shadow-md border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 mb-2">
              <Cpu className="w-3.5 h-3.5" /> Hackathon Evaluation & Trust Proof
            </div>
            <h2 className="text-xl md:text-2xl font-bold tracking-tight">Hindsight Cloud Memory Explorer</h2>
            <p className="text-slate-300 text-xs md:text-sm mt-1 max-w-2xl">
              Inspect actual Hindsight <code>retain</code> and <code>recall</code> events, vector memory references, payloads, and timestamps.
              Proves memory persistence and transparent separation between SQLite records and Hindsight experience memories.
            </p>
          </div>

          <button
            onClick={loadEvents}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-lg shadow transition flex items-center gap-2 self-start md:self-center"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Audit Log</span>
          </button>
        </div>
      </div>

      {/* Comparison Explainer Pill */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="p-2 bg-blue-50 text-blue-700 rounded-lg">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">SQLite Layer (Structured Truth)</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Source of truth for operational relational entities: customers, tickets, repair dates, status flags, and staff ownership.
            </p>
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="p-2 bg-cyan-50 text-cyan-700 rounded-lg">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">Hindsight Layer (Experience Memory)</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Persistent semantic experience memory. Retains confirmed repair outcomes and recalls them during future diagnostics.
            </p>
          </div>
        </div>
      </div>

      {/* Main Events Audit Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Events List */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[560px]">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Memory Events ({events.length})</span>
            <div className="flex gap-1">
              <button
                onClick={() => setFilterOp('')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                  filterOp === '' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterOp('retain')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                  filterOp === 'retain' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Retain
              </button>
              <button
                onClick={() => setFilterOp('recall')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                  filterOp === 'recall' ? 'bg-cyan-600 text-white' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Recall
              </button>
            </div>
          </div>

          <div className="divide-y divide-slate-100 overflow-y-auto flex-1 font-mono text-xs">
            {events.length === 0 ? (
              <div className="p-8 text-center text-slate-400 font-sans text-xs">
                No events found. Trigger a complaint or repair to record an event.
              </div>
            ) : (
              events.map((ev) => {
                const isSelected = selectedEvent?.id === ev.id;
                return (
                  <div
                    key={ev.id}
                    onClick={() => setSelectedEvent(ev)}
                    className={`p-3.5 cursor-pointer transition flex items-start justify-between gap-3 ${
                      isSelected ? 'bg-cyan-50/70 border-l-4 border-cyan-600' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="truncate">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 rounded uppercase font-bold text-[10px] ${
                          ev.operation === 'retain' ? 'bg-indigo-100 text-indigo-800' : 'bg-cyan-100 text-cyan-800'
                        }`}>
                          {ev.operation}
                        </span>
                        <span className="text-slate-800 font-semibold truncate text-xs">
                          {ev.entity_type} #{ev.entity_id || 'query'}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 truncate font-sans">
                        {ev.query_or_content}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1 font-sans">
                        {new Date(ev.created_at).toLocaleTimeString()}
                      </div>
                    </div>

                    <span className={`text-[10px] font-sans px-2 py-0.5 rounded-full font-bold uppercase ${
                      ev.status === 'success' ? 'bg-emerald-100 text-emerald-800' :
                      ev.status === 'empty' ? 'bg-amber-100 text-amber-800' :
                      ev.status === 'unconfigured' ? 'bg-slate-100 text-slate-600' :
                      'bg-rose-100 text-rose-800'
                    }`}>
                      {ev.status}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Selected Event Deep Inspector */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6 flex flex-col h-[560px] overflow-y-auto">
          {selectedEvent ? (
            <>
              <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                      selectedEvent.operation === 'retain' ? 'bg-indigo-100 text-indigo-800' : 'bg-cyan-100 text-cyan-800'
                    }`}>
                      {selectedEvent.operation} Event
                    </span>
                    <span className="font-mono text-xs text-slate-500">ID: #{selectedEvent.id}</span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mt-1">
                    Hindsight Memory Provider Transaction
                  </h3>
                </div>

                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Logged at</span>
                  <span className="text-xs font-mono font-semibold text-slate-700">
                    {new Date(selectedEvent.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Event Attributes */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                  <span className="text-slate-400 uppercase tracking-wider font-semibold text-[10px] block">
                    Provider Reference / Memory ID
                  </span>
                  <span className="font-mono font-bold text-slate-900 mt-0.5 block truncate">
                    {selectedEvent.provider_ref || 'Local transaction reference'}
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                  <span className="text-slate-400 uppercase tracking-wider font-semibold text-[10px] block">
                    Operation Status
                  </span>
                  <span className="font-semibold text-emerald-700 mt-0.5 block uppercase">
                    {selectedEvent.status}
                  </span>
                </div>
              </div>

              {/* Payload / Query Content */}
              <div>
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1.5 flex items-center gap-1.5">
                  <Code className="w-3.5 h-3.5 text-teal-600" />
                  <span>Outbound Query / Experience Content</span>
                </span>
                <pre className="p-3.5 bg-slate-900 text-teal-300 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
                  {selectedEvent.query_or_content}
                </pre>
              </div>

              {/* Raw Provider Response */}
              <div>
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-1.5 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-600" />
                  <span>Provider Response Payload (JSON)</span>
                </span>
                <pre className="p-3.5 bg-slate-900 text-slate-200 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
                  {selectedEvent.raw_response || (selectedEvent.error_summary ? `Error: ${selectedEvent.error_summary}` : '{"status": "recorded"}')}
                </pre>
              </div>
            </>
          ) : (
            <div className="py-24 text-center text-slate-400 text-xs">
              Select an event on the left to inspect its Hindsight memory payload.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
