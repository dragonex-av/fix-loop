import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = () => api.get('/health');
export const getDashboard = () => api.get('/dashboard');
export const getCustomers = (query = '') => api.get(`/customers${query ? `?query=${encodeURIComponent(query)}` : ''}`);
export const getCustomerHistory = (id) => api.get(`/customers/${id}/history`);
export const getTickets = (params = {}) => api.get('/tickets', { params });
export const getTicketDetail = (id) => api.get(`/tickets/${id}`);
export const createTicket = (data) => api.post('/tickets', data);
export const analyzeTicket = (id) => api.post(`/tickets/${id}/analyze`);
export const recordRepair = (id, data) => api.post(`/tickets/${id}/repairs`, data);
export const getPatterns = () => api.get('/insights/patterns');
export const reviewPattern = (id, data) => api.post(`/insights/patterns/${id}/review`, data);
export const getFollowups = () => api.get('/followups');
export const createFollowup = (data) => api.post('/followups', data);
export const updateFollowup = (id, data) => api.patch(`/followups/${id}`, data);
export const getMemoryEvents = (params = {}) => api.get('/memory/events', { params });

export default api;
