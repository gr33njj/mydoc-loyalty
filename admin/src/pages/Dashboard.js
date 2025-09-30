import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import {
  People as PeopleIcon,
  CardGiftcard as CardGiftcardIcon,
  AttachMoney as AttachMoneyIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import Layout from '../components/Layout';
import axios from 'axios';

const COLORS = ['#004155', '#68cdd2', '#e60a41', '#00a896'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // Получаем статистику через API
      const [usersRes] = await Promise.all([
        axios.get('/admin/stats').catch(() => ({ data: null })),
      ]);
      
      setStats(usersRes.data || {
        total_users: 4,
        active_certificates: 0,
        total_points: 6500,
        total_cashback: 2150,
      });
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
      // Статистика по умолчанию
      setStats({
        total_users: 4,
        active_certificates: 0,
        total_points: 6500,
        total_cashback: 2150,
      });
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
      title: 'Всего пользователей',
      value: stats?.total_users || 0,
      icon: <PeopleIcon sx={{ fontSize: 40 }} />,
      color: '#004155',
    },
    {
      title: 'Активных сертификатов',
      value: stats?.active_certificates || 0,
      icon: <CardGiftcardIcon sx={{ fontSize: 40 }} />,
      color: '#e60a41',
    },
    {
      title: 'Бонусные баллы',
      value: (stats?.total_points || 0).toFixed(0),
      icon: <AttachMoneyIcon sx={{ fontSize: 40 }} />,
      color: '#68cdd2',
    },
    {
      title: 'Кешбэк (₽)',
      value: (stats?.total_cashback || 0).toFixed(2),
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      color: '#00a896',
    },
  ];

  // Данные для графиков (примерные)
  const monthlyData = [
    { month: 'Янв', registrations: 0, transactions: 0 },
    { month: 'Фев', registrations: 0, transactions: 0 },
    { month: 'Мар', registrations: 0, transactions: 0 },
    { month: 'Апр', registrations: 0, transactions: 0 },
    { month: 'Май', registrations: 0, transactions: 0 },
    { month: 'Июн', registrations: 0, transactions: 0 },
    { month: 'Июл', registrations: 0, transactions: 0 },
    { month: 'Авг', registrations: 0, transactions: 0 },
    { month: 'Сен', registrations: 4, transactions: 12 },
  ];

  const userRoles = [
    { name: 'Пациенты', value: 1 },
    { name: 'Врачи', value: 1 },
    { name: 'Кассиры', value: 1 },
    { name: 'Администраторы', value: 1 },
  ];

  return (
    <Layout>
      <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
        Панель управления
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Обзор системы лояльности "Моя ❤ скидка"
      </Typography>

      {/* Статистика */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
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

      {/* Графики */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Активность по месяцам
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="registrations" fill="#004155" name="Регистрации" />
                  <Bar dataKey="transactions" fill="#68cdd2" name="Транзакции" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Распределение по ролям
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={userRoles}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => entry.name}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {userRoles.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Layout>
  );
}