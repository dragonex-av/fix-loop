import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

// JWT interceptor — attach token from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fixloop_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Auth ────────────────────────────────────────────────────────────────────
export const register   = (data)       => api.post('/auth/register', data);
export const login      = (data)       => api.post('/auth/login', data);
export const getMe      = ()           => api.get('/auth/me');
export const updateMe   = (data)       => api.put('/auth/me', data);

// ─── Customer Portal ─────────────────────────────────────────────────────────
export const getMyTickets    = ()           => api.get('/portal/my-tickets');
export const getMyTicket     = (id)         => api.get(`/portal/tickets/${id}`);
export const raiseComplaint  = (data)       => api.post('/portal/tickets', data);
export const reviewEstimate  = (id, data)   => api.post(`/portal/tickets/${id}/estimate`, data);
export const rescheduleAppt  = (id, data)   => api.post(`/portal/tickets/${id}/appointment/reschedule`, data);
export const payInvoice      = (id)         => api.post(`/portal/tickets/${id}/pay`);
export const rateService     = (id, data)   => api.post(`/portal/tickets/${id}/rate`, data);
export const reopenTicket    = (id)         => api.post(`/portal/tickets/${id}/reopen`);
export const getCustomerChat = (ticketId)   => api.get('/portal/chat', { params: { ticket_id: ticketId } });
export const sendCustomerChat= (ticketId, msg) => api.post('/portal/chat', { ticket_id: ticketId, message: msg });

// ─── Operations ──────────────────────────────────────────────────────────────
export const getTechnicians    = ()           => api.get('/operations/technicians');
export const assignTechnician  = (id, data)   => api.post(`/operations/tickets/${id}/assign-technician`, data);
export const createAppointment = (id, data)   => api.post(`/operations/tickets/${id}/appointments`, data);
export const updateTicketStage = (id, data)   => api.post(`/operations/tickets/${id}/stage`, data);
export const createEstimate    = (id, data)   => api.post(`/operations/tickets/${id}/estimate`, data);
export const getOpsAnalytics   = ()           => api.get('/operations/analytics');

// ─── Existing Ops Endpoints ──────────────────────────────────────────────────
export const getDashboard       = ()           => api.get('/dashboard');
export const getCustomers       = (q = '')     => api.get(`/customers${q ? `?query=${encodeURIComponent(q)}` : ''}`);
export const getCustomerHistory = (id)         => api.get(`/customers/${id}/history`);
export const getTickets         = (params = {}) => api.get('/tickets', { params });
export const getTicketDetail    = (id)         => api.get(`/tickets/${id}`);
export const createTicket       = (data)       => api.post('/tickets', data);
export const analyzeTicket      = (id)         => api.post(`/tickets/${id}/analyze`);
export const recordRepair       = (id, data)   => api.post(`/tickets/${id}/repairs`, data);
export const getPatterns        = ()           => api.get('/insights/patterns');
export const reviewPattern      = (id, data)   => api.post(`/insights/patterns/${id}/review`, data);
export const getFollowups       = ()           => api.get('/followups');
export const createFollowup     = (data)       => api.post('/followups', data);
export const updateFollowup     = (id, data)   => api.patch(`/followups/${id}`, data);
export const getMemoryEvents    = (params = {}) => api.get('/memory/events', { params });
export const getHealth          = ()           => api.get('/health');

export default api;
