import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Snackbar,
  IconButton,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ShareIcon from '@mui/icons-material/Share';
import PeopleIcon from '@mui/icons-material/People';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import Layout from '../components/Layout';
import axios from 'axios';

export default function Referrals() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  useEffect(() => {
    fetchReferralData();
  }, []);

  const fetchReferralData = async () => {
    try {
      // Сначала получаем/создаем код
      const codeResponse = await axios.get('/referrals/my-code');
      // Затем получаем статистику
      const statsResponse = await axios.get('/referrals/stats');
      
      setStats({
        ...statsResponse.data,
        referral_code: codeResponse.data.code
      });
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyReferralLink = () => {
    const link = `https://it-mydoc.ru/login?ref=${stats?.referral_code}`;
    navigator.clipboard.writeText(link);
    setSnackbarMessage('Реферальная ссылка скопирована!');
    setSnackbarOpen(true);
  };

  const shareReferralLink = async () => {
    const link = `https://it-mydoc.ru/login?ref=${stats?.referral_code}`;
    const text = 'Присоединяйтесь к программе лояльности медицинского центра! Получите бонусы при регистрации.';
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Моя ❤ скидка',
          text: text,
          url: link,
        });
      } catch (error) {
        console.error('Ошибка при попытке поделиться:', error);
      }
    } else {
      copyReferralLink();
    }
  };

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  const statCards = [
    {
      title: 'Всего приглашено',
      value: stats?.total_referrals || 0,
      icon: <PeopleIcon />,
      color: '#004155',
    },
    {
      title: 'Успешные рефералы',
      value: stats?.successful_referrals || 0,
      icon: <TrendingUpIcon />,
      color: '#68cdd2',
    },
    {
      title: 'Выручка от рефералов',
      value: `${stats?.total_revenue?.toFixed(0) || 0} ₽`,
      icon: <AttachMoneyIcon />,
      color: '#004155',
    },
    {
      title: 'Заработано бонусов',
      value: stats?.total_rewards?.toFixed(0) || 0,
      icon: <AttachMoneyIcon />,
      color: '#e60a41',
    },
  ];

  return (
    <Layout>
      <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
        Реферальная программа
      </Typography>

      <Alert severity="success" sx={{ mb: 3 }}>
        Приглашайте друзей и получайте бонусы за каждого приведенного пациента!
      </Alert>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Ваш реферальный код
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Поделитесь этой ссылкой с друзьями. Когда они авторизуются через Мой Доктор по вашей ссылке, вы получите бонусы!
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2 }}>
            <TextField
              value={stats?.referral_code || ''}
              InputProps={{
                readOnly: true,
                endAdornment: (
                  <IconButton onClick={copyReferralLink}>
                    <ContentCopyIcon />
                  </IconButton>
                ),
              }}
              fullWidth
            />
            <Button
              variant="contained"
              startIcon={<ShareIcon />}
              onClick={shareReferralLink}
              sx={{ whiteSpace: 'nowrap' }}
            >
              Поделиться
            </Button>
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Реферальная ссылка: https://it-mydoc.ru/register?ref={stats?.referral_code}
          </Typography>
        </CardContent>
      </Card>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    mb: 2,
                  }}
                >
                  <Box
                    sx={{
                      width: 50,
                      height: 50,
                      borderRadius: 2,
                      bgcolor: `${card.color}15`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: card.color,
                    }}
                  >
                    {card.icon}
                  </Box>
                </Box>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                  {card.value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {card.title}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Как это работает?
          </Typography>
          <Box component="ol" sx={{ pl: 2 }}>
            <Typography component="li" variant="body2" paragraph>
              Поделитесь своим реферальным кодом или ссылкой с друзьями
            </Typography>
            <Typography component="li" variant="body2" paragraph>
              Когда друг зарегистрируется по вашей ссылке, он получит приветственный бонус
            </Typography>
            <Typography component="li" variant="body2" paragraph>
              После первого визита друга вы получите бонусные баллы
            </Typography>
            <Typography component="li" variant="body2" paragraph>
              Продолжайте приглашать друзей и зарабатывайте больше!
            </Typography>
          </Box>
          
          {stats?.conversion_rate !== undefined && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Ваша конверсия: {stats.conversion_rate}%
            </Alert>
          )}
        </CardContent>
      </Card>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Layout>
  );
}
