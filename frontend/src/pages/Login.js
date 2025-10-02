import React, { useState } from 'react';
import {
  Container,
  Box,
  Card,
  CardContent,
  Button,
  Typography,
  Divider,
  Stack,
  CircularProgress,
} from '@mui/material';
import FavoriteIcon from '@mui/icons-material/Favorite';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import axios from 'axios';

export default function Login() {
  const [loading, setLoading] = useState(false);

  const handleBitrixLogin = () => {
    // Редирект на промежуточную страницу Bitrix
    // Она проверит авторизацию, создаст токен и вернет обратно
    window.location.href = 'https://mydoctorarmavir.ru/local/pages/loyalty_redirect.php';
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #004155 0%, #68cdd2 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Декоративные элементы */}
      <Box
        sx={{
          position: 'absolute',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          top: '-100px',
          right: '-100px',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.1)',
          bottom: '-50px',
          left: '-50px',
        }}
      />

      <Container maxWidth="sm" sx={{ position: 'relative', zIndex: 1 }}>
        <Card elevation={8} sx={{ overflow: 'visible' }}>
          <CardContent sx={{ p: { xs: 3, sm: 5 } }}>
            {/* Логотип */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #e60a41 0%, #ff5470 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto',
                  mb: 3,
                  boxShadow: '0 8px 24px rgba(230, 10, 65, 0.3)',
                }}
              >
                <FavoriteIcon sx={{ fontSize: 45, color: 'white' }} />
              </Box>
              
              <Typography 
                variant="h3" 
                component="h1" 
                fontWeight="bold" 
                gutterBottom
                sx={{ 
                  fontSize: { xs: '2rem', sm: '2.5rem' },
                  background: 'linear-gradient(135deg, #004155 0%, #68cdd2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Моя ❤ скидка
              </Typography>
              
              <Typography 
                variant="body1" 
                color="text.secondary" 
                sx={{ fontSize: { xs: '0.95rem', sm: '1.1rem' } }}
              >
                Программа лояльности медицинского центра
              </Typography>
            </Box>

            {/* Основная кнопка SSO */}
            <Stack spacing={2}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleBitrixLogin}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LocalHospitalIcon />}
                sx={{
                  py: 2,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #004155 0%, #68cdd2 100%)',
                  boxShadow: '0 4px 16px rgba(0, 65, 85, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #003344 0%, #57bcc1 100%)',
                    boxShadow: '0 6px 20px rgba(0, 65, 85, 0.4)',
                    transform: 'translateY(-2px)',
                  },
                  '&:disabled': {
                    background: 'linear-gradient(135deg, #004155 0%, #68cdd2 100%)',
                    opacity: 0.7,
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                {loading ? 'Авторизация...' : 'Войти через Мой Доктор'}
              </Button>

              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ textAlign: 'center', mt: 2 }}
              >
                Используйте ваш аккаунт с сайта{' '}
                <strong>mydoctorarmavir.ru</strong>
              </Typography>
            </Stack>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                или
              </Typography>
            </Divider>

            {/* Информация */}
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Нет аккаунта на сайте клиники?
              </Typography>
              <Button
                variant="text"
                size="small"
                href="https://mydoctorarmavir.ru/personal/profile/"
                target="_blank"
                sx={{ textTransform: 'none' }}
              >
                Зарегистрироваться на mydoctorarmavir.ru
              </Button>
            </Box>

            {/* Преимущества */}
            <Box 
              sx={{ 
                mt: 4, 
                p: 2, 
                borderRadius: 2, 
                bgcolor: 'rgba(0, 65, 85, 0.05)',
              }}
            >
              <Typography 
                variant="body2" 
                fontWeight="600" 
                color="primary" 
                gutterBottom
              >
                Возможности программы:
              </Typography>
              <Stack spacing={1} sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  💰 Бонусные баллы и кешбэк
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  🎁 Подарочные сертификаты
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  👥 Реферальная программа
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  📊 История транзакций
                </Typography>
              </Stack>
            </Box>
          </CardContent>
        </Card>

        {/* Футер */}
        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.9)' }}>
            © 2025 Медицинский центр «Мой Доктор»
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}
