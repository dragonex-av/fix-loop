import React, { useState } from 'react';
import { raiseComplaint } from '../../services/api';
import { PlusCircle, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

const CATEGORIES = ['Washing Machine', 'Refrigerator', 'Air Conditioner', 'Microwave', 'Dishwasher', 'Television', 'Laptop', 'Smartphone', 'Other'];
const PRIORITIES  = ['low', 'medium', 'high'];

export default function CustomerRaiseComplaint({ onCreated }) {
  const [form, setForm] = useState({
    product_type: '',
    brand: '',
    model: '',
    serial_number: '',
    issue_description: '',
    priority: 'medium',
    customer_address: '',
  });
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(null);
  const [error, setError]       = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.product_type || !form.issue_description) {
      setError('Product type and issue description are required.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await raiseComplaint(form);
      setSuccess(res.data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit complaint. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-lg mx-auto text-center">
        <div className="bg-white rounded-2xl border border-slate-200 p-10 shadow-sm">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-xl font-bold text-slate-800">Complaint Submitted!</h2>
          <p className="text-slate-500 mt-2 text-sm">Your complaint has been registered successfully.</p>

          <div className="mt-6 bg-teal-50 border border-teal-200 rounded-xl p-4">
            <p className="text-xs text-teal-600 font-semibold uppercase tracking-wider mb-1">Your Ticket ID</p>
            <p className="text-2xl font-mono font-bold text-teal-700">{success.ticket_code}</p>
          </div>

          <div className="mt-4 text-left bg-slate-50 rounded-xl p-4 text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Product</span>
              <span className="font-medium text-slate-800">{success.product_type} — {success.model}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Priority</span>
              <span className={`font-semibold capitalize ${
                success.priority === 'high' ? 'text-rose-600' :
                success.priority === 'medium' ? 'text-amber-600' : 'text-green-600'
              }`}>{success.priority}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Status</span>
              <span className="font-semibold text-teal-600">Registered</span>
            </div>
          </div>

          <p className="text-xs text-slate-400 mt-4">Our support team will review your complaint and assign a technician shortly.</p>

          <button
            onClick={() => onCreated(success.id)}
            className="mt-6 w-full flex items-center justify-center gap-2 py-3 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm rounded-xl transition"
          >
            Track Repair Status <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <PlusCircle className="w-5 h-5 text-teal-600" /> Raise a Complaint
        </h2>
        <p className="text-sm text-slate-500 mt-1">Describe your issue and we'll assign the right specialist.</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
        {/* Product Details */}
        <div>
          <h3 className="text-sm font-bold text-slate-700 mb-3 pb-2 border-b border-slate-100">Product Information</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Product Category *</label>
              <select
                name="product_type"
                value={form.product_type}
                onChange={handleChange}
                required
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
              >
                <option value="">Select category...</option>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Brand</label>
              <input
                type="text"
                name="brand"
                value={form.brand}
                onChange={handleChange}
                placeholder="e.g. Samsung, LG, Bosch"
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Model Number</label>
              <input
                type="text"
                name="model"
                value={form.model}
                onChange={handleChange}
                placeholder="e.g. WM-1200X"
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Serial Number</label>
              <input
                type="text"
                name="serial_number"
                value={form.serial_number}
                onChange={handleChange}
                placeholder="Optional"
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>
        </div>

        {/* Issue */}
        <div>
          <h3 className="text-sm font-bold text-slate-700 mb-3 pb-2 border-b border-slate-100">Issue Details</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Describe the Problem *</label>
              <textarea
                name="issue_description"
                value={form.issue_description}
                onChange={handleChange}
                required
                rows={4}
                placeholder="Please describe the issue in detail — when it started, what happens, any error codes..."
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Priority</label>
              <div className="flex gap-3">
                {PRIORITIES.map((p) => (
                  <label key={p} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="priority"
                      value={p}
                      checked={form.priority === p}
                      onChange={handleChange}
                      className="accent-teal-500"
                    />
                    <span className={`text-xs font-semibold capitalize ${
                      p === 'high' ? 'text-rose-600' :
                      p === 'medium' ? 'text-amber-600' : 'text-green-600'
                    }`}>{p}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Address */}
        <div>
          <h3 className="text-sm font-bold text-slate-700 mb-3 pb-2 border-b border-slate-100">Service Address</h3>
          <input
            type="text"
            name="customer_address"
            value={form.customer_address}
            onChange={handleChange}
            placeholder="Enter your full address for technician visit"
            className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-3 bg-teal-500 hover:bg-teal-400 disabled:opacity-60 text-slate-950 font-bold text-sm rounded-xl transition"
        >
          {loading
            ? <><Loader2 className="w-4 h-4 animate-spin" /> Submitting...</>
            : <><PlusCircle className="w-4 h-4" /> Submit Complaint</>
          }
        </button>
      </form>
    </div>
  );
}
