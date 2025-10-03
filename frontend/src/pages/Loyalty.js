import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Pagination,
} from '@mui/material';
import Layout from '../components/Layout';
import axios from 'axios';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export default function Loyalty() {
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchLoyaltyData();
  }, [page]);

  const fetchLoyaltyData = async () => {
    try {
      const [balanceRes, transactionsRes, bitrixBalanceRes] = await Promise.all([
        axios.get('/loyalty/balance').catch(err => {
          console.log('Локальный баланс не найден (нормально для SSO пользователей)');
          return { data: { points_balance: 0, cashback_balance: 0, card_tier: 'Bronze', transactions_count: 0 } };
        }),
        axios.get(`/loyalty/transactions?page=${page}&page_size=10`).catch(err => {
          console.log('Транзакции не найдены');
          return { data: { transactions: [], total: 0 } };
        }),
        axios.get('/auth/bitrix/bonus-balance').catch(err => {
          console.log('Не удалось получить баланс из Bitrix:', err.response?.data?.error);
          return { data: { success: false, bonus_balance: 0 } };
        }),
      ]);
      
      const balanceData = balanceRes.data;
      
      // Если есть баланс из Bitrix, используем его для бонусных баллов
      if (bitrixBalanceRes.data.success) {
        balanceData.points_balance = bitrixBalanceRes.data.bonus_balance;
        console.log('✅ Баланс из Bitrix:', balanceData.points_balance);
      }
      
      setBalance(balanceData);
      setTransactions(transactionsRes.data.transactions || []);
      setTotalPages(Math.ceil((transactionsRes.data.total || 0) / 10));
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'accrual':
        return 'success';
      case 'deduction':
        return 'error';
      case 'refund':
        return 'info';
      default:
        return 'default';
    }
  };

  const getTransactionLabel = (type) => {
    switch (type) {
      case 'accrual':
        return 'Начисление';
      case 'deduction':
        return 'Списание';
      case 'refund':
        return 'Возврат';
      case 'expiration':
        return 'Сгорание';
      default:
        return type;
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

  return (
    <Layout>
      <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
        Программа лояльности
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Бонусные баллы
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="primary">
                {balance?.points_balance?.toFixed(2) || '0'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Баланс из личного кабинета Мой Доктор
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Кешбэк
              </Typography>
              <Typography variant="h3" fontWeight="bold" sx={{ color: '#68cdd2' }}>
                {balance?.cashback_balance?.toFixed(2) || '0'} ₽
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Всего заработано: {balance?.cashback_balance?.toFixed(2) || '0'} ₽
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Уровень карты
              </Typography>
              <Typography variant="h3" fontWeight="bold" sx={{ textTransform: 'capitalize' }}>
                {balance?.card_tier || 'Bronze'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Транзакций: {balance?.transactions_count || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            История транзакций
          </Typography>
          
          {transactions.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                У вас пока нет транзакций
              </Typography>
            </Box>
          ) : (
            <>
              <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Дата</TableCell>
                      <TableCell>Тип</TableCell>
                      <TableCell>Описание</TableCell>
                      <TableCell>Валюта</TableCell>
                      <TableCell align="right">Сумма</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {transactions.map((transaction) => (
                      <TableRow key={transaction.id}>
                        <TableCell>
                          {format(new Date(transaction.created_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={getTransactionLabel(transaction.transaction_type)}
                            color={getTransactionColor(transaction.transaction_type)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{transaction.description}</TableCell>
                        <TableCell>
                          <Chip
                            label={transaction.currency === 'points' ? 'Баллы' : 'Кешбэк'}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            fontWeight="bold"
                            color={transaction.transaction_type === 'accrual' ? 'success.main' : 'error.main'}
                          >
                            {transaction.transaction_type === 'accrual' ? '+' : '-'}
                            {transaction.amount.toFixed(2)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {totalPages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Pagination
                    count={totalPages}
                    page={page}
                    onChange={(e, value) => setPage(value)}
                    color="primary"
                  />
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Layout>
  );
}
