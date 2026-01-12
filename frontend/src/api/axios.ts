import axios from 'axios';

// Base URL from Vite env (create .env in frontend root)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // Sends cookies (tokens + CSRF)
  timeout: 10000,
});

// Auto-add CSRF token from cookie to header
axiosInstance.interceptors.request.use(
  (config) => {
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];

    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 (expired token) – redirect to login
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';  // Adjust to your login route
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
