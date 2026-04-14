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
        
        // Проверяем наличие сохраненного реферального кода
        const pendingReferralCode = localStorage.getItem('pending_referral_code');
        if (pendingReferralCode) {
          console.log('🎯 Найден реферальный код для применения:', pendingReferralCode);
        }
        
        const response = await axios.post('/auth/bitrix/verify-token', {
          token: token,
          referral_code: pendingReferralCode || undefined
        });

        console.log('📥 Ответ от backend:', response.data);

        if (response.data.success && response.data.token) {
          // Удаляем использованный реферальный код
          if (pendingReferralCode) {
            localStorage.removeItem('pending_referral_code');
            console.log('🗑️ Реферальный код использован и удален');
          }
          
          // Сохраняем JWT токен (как access_token для AuthContext)
          localStorage.setItem('access_token', response.data.token);
          console.log('✅ JWT токен сохранен:', response.data.token.substring(0, 50) + '...');
          
          // ВАЖНО: Даем время localStorage сохранить данные (async)
          // и только потом перезагружаем страницу
          await new Promise(resolve => setTimeout(resolve, 100));
          
          console.log('🔄 Перезагрузка страницы...');
          window.location.href = '/';
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
        Авторизация через МД-ID
      </Typography>
      <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
        Подождите, мы проверяем ваши данные
      </Typography>
    </Box>
  );
}

