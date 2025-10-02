import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import axios from 'axios';

export default function SSORedirect() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setError('Токен не получен');
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    // Проверяем токен на backend
    const verifyToken = async () => {
      try {
        console.log('🔄 Проверка токена от Bitrix:', token);
        
        const response = await axios.post('/api/auth/bitrix/verify-token', {
          token: token
        });

        console.log('📥 Ответ от backend:', response.data);

        if (response.data.success && response.data.token) {
          // Сохраняем JWT токен
          localStorage.setItem('token', response.data.token);
          console.log('✅ JWT токен сохранен, редирект в ЛК');
          
          // Редирект в личный кабинет
          navigate('/');
        } else {
          throw new Error('Не удалось получить JWT токен');
        }
      } catch (err) {
        console.error('❌ Ошибка проверки токена:', err);
        setError(err.response?.data?.detail || err.message || 'Ошибка авторизации');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    verifyToken();
  }, [searchParams, navigate]);

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
        Авторизация через Bitrix...
      </Typography>
      <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
        Подождите, мы проверяем ваши данные
      </Typography>
    </Box>
  );
}

