import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_API_URL || 'https://it-mydoc.ru/api';

// Configure axios
axios.defaults.baseURL = API_URL;

// Axios interceptor для автоматической установки токена
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Axios interceptor для обработки ошибок авторизации
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_access_token');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Проверка наличия токена при загрузке
    const token = localStorage.getItem('admin_access_token');
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get('/auth/me');
      const userData = response.data;
      
      // Проверяем что это админ или кассир
      if (userData.role === 'admin' || userData.role === 'cashier') {
        setUser(userData);
      } else {
        // Обычный пользователь - не может использовать админку
        localStorage.removeItem('admin_access_token');
        setUser(null);
      }
    } catch (error) {
      console.error('Ошибка получения данных пользователя:', error);
      localStorage.removeItem('admin_access_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await axios.post('/auth/login', formData);
      const { access_token, user: userData } = response.data;

      // Проверяем роль
      if (userData.role !== 'admin' && userData.role !== 'cashier') {
        return {
          success: false,
          error: 'Доступ запрещен. Требуется роль администратора или кассира.'
        };
      }

      localStorage.setItem('admin_access_token', access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Ошибка входа:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Ошибка входа'
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('admin_access_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};