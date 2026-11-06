import React, { useState, useEffect } from 'react';
import { createTicket, getCustomers } from '../services/api';
import { Send, UserCheck, Search, CheckCircle2, AlertCircle, Cpu } from 'lucide-react';

export default function NewComplaint({ onTicketCreated }) {
  const [customers, setCustomers] = useState([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  
  const [productType, setProductType] = useState('Washing Machine');
  const [model, setModel] = useState('Model X');
  const [brand, setBrand] = useState('Apex Appliances');
  const [issueDescription, setIssueDescription] = useState('');
  const [priority, setPriority] = useState('High');

  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const res = await getCustomers();
      setCustomers(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCustomerSelect = (e) => {
    const cid = e.target.value;
    setSelectedCustomerId(cid);
    if (cid) {
      const found = customers.find(c => c.id === parseInt(cid));
      if (found) {
        setCustomerName(found.name);
        setCustomerPhone(found.phone);
        setCustomerEmail(found.email || '');
      }
    } else {
      setCustomerName('');
      setCustomerPhone('');
      setCustomerEmail('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!issueDescription.trim()) {
      setError('Please provide the complaint details.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const payload = {
        customer_id: selectedCustomerId ? parseInt(selectedCustomerId) : null,
        customer_name: customerName,
        customer_phone: customerPhone,
        customer_email: customerEmail,
        product_type: productType,
        model: model,
        brand: brand,
        issue_description: issueDescription,
        priority: priority
      };

      const res = await createTicket(payload);
      setResult(res.data);
      if (onTicketCreated) {
        onTicketCreated(res.data.id);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to submit ticket. Ensure backend server is running.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="border-b border-slate-100 pb-4 mb-6">
          <h2 className="text-lg font-bold text-slate-900">Capture Customer Complaint</h2>
          <p className="text-xs text-slate-500 mt-1">
            FixLoop validates the record in SQLite and retains the complaint context in Hindsight Experience Memory.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg space-y-2">
            <div className="flex items-center gap-2 font-bold text-sm text-emerald-800">
              <CheckCircle2 className="w-4 h-4" />
              <span>Ticket {result.ticket_code} Created & Retained!</span>
            </div>
            <p className="text-xs text-emerald-700">
              Assigned Status: <span className="font-semibold">{result.status}</span> {result.is_repeat && '(Flagged as Repeat Customer Issue)'}
            </p>
            <div className="text-[11px] font-mono text-emerald-800 bg-emerald-100/60 p-2 rounded flex items-center justify-between">
              <span>Hindsight Retain Operation: {result.hindsight_retain_status || 'Success'}</span>
              <span className="font-sans font-medium text-emerald-900">Ready for AI Repair Advisory</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Quick Select Existing Customer */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Quick Select Existing Demo Customer
            </label>
            <select
              value={selectedCustomerId}
              onChange={handleCustomerSelect}
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-none transition"
            >
              <option value="">-- Create or Enter New Customer --</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.phone})
                </option>
              ))}
            </select>
          </div>

          {/* Customer Details */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Customer Full Name *</label>
              <input
                type="text"
                required
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="e.g. Rahul Sharma"
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Phone Number *</label>
              <input
                type="text"
                required
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                placeholder="+91-98765-43210"
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Email (Optional)</label>
              <input
                type="email"
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                placeholder="customer@example.com"
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Appliance & Model */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Appliance Category</label>
              <select
                value={productType}
                onChange={(e) => setProductType(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              >
                <option value="Washing Machine">Washing Machine</option>
                <option value="Refrigerator">Refrigerator</option>
                <option value="Dishwasher">Dishwasher</option>
                <option value="Microwave Oven">Microwave Oven</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Product Model *</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              >
                <option value="Model X">Model X (Smart Inverter Front Load)</option>
                <option value="Model Y">Model Y (Multi-Door Inverter Refrigerator)</option>
                <option value="Model Pro-Z">Model Pro-Z (Commercial Unit)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Issue Description */}
          <div className="pt-2 border-t border-slate-100">
            <div className="flex justify-between items-center mb-1">
              <label className="block text-xs font-medium text-slate-700">Detailed Complaint Description *</label>
              <button
                type="button"
                onClick={() => setIssueDescription("Drainage error E20 returned after 5 days. Water is stuck in the drum again.")}
                className="text-[11px] text-teal-600 hover:underline font-medium"
              >
                Insert Rahul Demo Repeat Case
              </button>
            </div>
            <textarea
              rows={4}
              required
              value={issueDescription}
              onChange={(e) => setIssueDescription(e.target.value)}
              placeholder="Describe the symptoms reported by the customer (e.g. error codes, unusual sounds, standing water)..."
              className="w-full text-sm border border-slate-300 rounded-lg p-3 focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow transition flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <Cpu className="w-4 h-4 animate-spin" />
                  <span>Saving & Retaining in Hindsight...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit Ticket & Retain Experience</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
