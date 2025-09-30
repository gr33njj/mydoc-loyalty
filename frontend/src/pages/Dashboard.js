import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Button,
} from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import CardGiftcardIcon from '@mui/icons-material/CardGiftcard';
import PeopleIcon from '@mui/icons-material/People';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import Layout from '../components/Layout';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [balance, setBalance] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [balanceRes, statsRes] = await Promise.all([
        axios.get('/loyalty/balance'),
        axios.get('/referrals/stats'),
      ]);
      
      setBalance(balanceRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
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
      title: 'Бонусные баллы',
      value: balance?.points_balance?.toFixed(0) || '0',
      icon: <AccountBalanceWalletIcon sx={{ fontSize: 40 }} />,
      color: '#004155',
      action: () => navigate('/loyalty'),
    },
    {
      title: 'Кешбэк',
      value: `${balance?.cashback_balance?.toFixed(2) || '0'} ₽`,
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      color: '#68cdd2',
      action: () => navigate('/loyalty'),
    },
    {
      title: 'Сертификаты',
      value: '0', // TODO: Add certificates count
      icon: <CardGiftcardIcon sx={{ fontSize: 40 }} />,
      color: '#e60a41',
      action: () => navigate('/certificates'),
    },
    {
      title: 'Приглашено друзей',
      value: stats?.total_referrals || '0',
      icon: <PeopleIcon sx={{ fontSize: 40 }} />,
      color: '#004155',
      action: () => navigate('/referrals'),
    },
  ];

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Добро пожаловать!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Ваш уровень: <strong>{balance?.card_tier || 'Bronze'}</strong>
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 8px 24px rgba(0,65,85,0.15)',
                },
              }}
              onClick={card.action}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 2,
                  }}
                >
                  <Box
                    sx={{
                      width: 60,
                      height: 60,
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
                <Typography variant="h4" component="div" fontWeight="bold" gutterBottom>
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

      <Box sx={{ mt: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              Программа лояльности
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Получайте баллы за каждый визит и покупку, используйте их для оплаты услуг.
              Приглашайте друзей и получайте дополнительные бонусы!
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button variant="contained" onClick={() => navigate('/loyalty')}>
                Мои бонусы
              </Button>
              <Button variant="outlined" onClick={() => navigate('/referrals')}>
                Пригласить друга
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Layout>
  );
}
