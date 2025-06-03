import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and not already retrying
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        const response = await axios.post('/api/auth/refresh', { 
          refresh_token: refreshToken 
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  getCurrentUser: () => api.get('/auth/me'),
  updateUser: (userData) => api.put('/auth/me', userData),
};

// Task API
export const taskAPI = {
  getTasks: (params) => api.get('/tasks', { params }),
  getTask: (taskId) => api.get(`/tasks/${taskId}`),
  createTask: (taskData) => api.post('/tasks', taskData),
  updateTask: (taskId, taskData) => api.put(`/tasks/${taskId}`, taskData),
  cancelTask: (taskId) => api.post(`/tasks/${taskId}/cancel`),
};

// Provider API
export const providerAPI = {
  getProviders: () => api.get('/providers'),
  getProvider: (providerId) => api.get(`/providers/${providerId}`),
  getProviderStatus: (providerId) => api.get(`/providers/${providerId}/status`),
  testProvider: (providerId) => api.post(`/providers/${providerId}/test`),
};

// Content API
export const contentAPI = {
  getContent: (params) => api.get('/content', { params }),
  getContentItem: (contentId) => api.get(`/content/${contentId}`),
  updateContent: (contentId, contentData) => api.put(`/content/${contentId}`, contentData),
  exportContent: (contentId, format) => api.post(`/content/${contentId}/export`, { format }),
  shareContent: (contentId, shareData) => api.post(`/content/${contentId}/share`, shareData),
};

// Admin API
export const adminAPI = {
  getUsers: (params) => api.get('/admin/users', { params }),
  getStats: () => api.get('/admin/stats'),
  getLogs: (params) => api.get('/admin/logs', { params }),
  updateSettings: (settings) => api.post('/admin/settings', settings),
};

export default api;
