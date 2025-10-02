import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { useAuth } from '../context/AuthContext';

export default function SSOCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken, fetchCurrentUser } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(errorParam);
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    if (token) {
      // Сохраняем токен
      localStorage.setItem('token', token);
      setToken(token);
      
      // Загружаем данные пользователя
      fetchCurrentUser().then(() => {
        navigate('/');
      }).catch((err) => {
        console.error('Ошибка загрузки пользователя:', err);
        setError('Не удалось загрузить данные пользователя');
        setTimeout(() => navigate('/login'), 3000);
      });
    } else {
      setError('Токен авторизации не получен');
      setTimeout(() => navigate('/login'), 3000);
    }
  }, [searchParams, navigate, setToken, fetchCurrentUser]);

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #004155 0%, #68cdd2 100%)',
        }}
      >
        <Alert severity="error" sx={{ maxWidth: 500 }}>
          <Typography variant="h6" gutterBottom>
            Ошибка авторизации
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Перенаправление на страницу входа...
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #004155 0%, #68cdd2 100%)',
      }}
    >
      <CircularProgress size={60} sx={{ color: 'white', mb: 3 }} />
      <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
        Авторизация...
      </Typography>
      <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
        Подождите, мы проверяем ваши данные
      </Typography>
    </Box>
  );
}

