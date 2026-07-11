import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim() || (import.meta.env.DEV ? 'http://localhost:8000' : '/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const exceptionsApi = {
  getExceptions: async (params = {}) => {
    const response = await api.get('/exceptions', { params });
    return response.data;
  },

  getExceptionDetail: async (id) => {
    const response = await api.get(`/exceptions/${id}`);
    return response.data;
  },

  updateExceptionStatus: async (id, status) => {
    const response = await api.patch(`/exceptions/${id}`, { status });
    return response.data;
  },
};

export const dashboardApi = {
  getSummary: async () => {
    const response = await api.get('/dashboard/summary');
    return response.data;
  },
};

export default api;
