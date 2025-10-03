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
  useMediaQuery,
  useTheme,
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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  useEffect(() => {
    fetchLoyaltyData();
  }, [page]);

  const fetchLoyaltyData = async () => {
    try {
      const [balanceRes, bitrixBalanceRes, bitrixHistoryRes] = await Promise.all([
        axios.get('/loyalty/balance').catch(err => {
          console.log('Локальный баланс не найден (нормально для SSO пользователей)');
          return { data: { points_balance: 0, cashback_balance: 0, card_tier: 'Bronze', transactions_count: 0 } };
        }),
        axios.get('/auth/bitrix/bonus-balance').catch(err => {
          console.log('Не удалось получить баланс из Bitrix:', err.response?.data?.error);
          return { data: { success: false, bonus_balance: 0 } };
        }),
        axios.get('/auth/bitrix/bonus-history', { params: { limit: 50 } }).catch(err => {
          console.log('Не удалось получить историю из Bitrix:', err.response?.data?.error);
          return { data: { success: false, transactions: [], total: 0 } };
        }),
      ]);
      
      const balanceData = balanceRes.data;
      
      // Если есть баланс из Bitrix, используем его для бонусных баллов
      if (bitrixBalanceRes.data.success) {
        balanceData.points_balance = bitrixBalanceRes.data.bonus_balance;
        console.log('✅ Баланс из Bitrix:', balanceData.points_balance);
      }
      
      // Если есть история из Bitrix, используем её
      let transactionsData = [];
      let totalTransactions = 0;
      
      if (bitrixHistoryRes.data.success && bitrixHistoryRes.data.transactions.length > 0) {
        // Преобразуем транзакции из Bitrix в формат, ожидаемый frontend
        transactionsData = bitrixHistoryRes.data.transactions.map(tx => ({
          id: tx.date, // используем дату как ID
          created_at: tx.date,
          transaction_type: tx.type,
          currency: 'points',
          amount: tx.amount,
          description: tx.description,
          balance_after: tx.balance,
          expires_at: tx.expires_at,
          valid_days: tx.valid_days
        }));
        totalTransactions = bitrixHistoryRes.data.total;
        console.log('✅ История из Bitrix:', transactionsData.length, 'транзакций');
      } else {
        // Fallback на локальные транзакции
        const localTransactions = await axios.get(`/loyalty/transactions?page=${page}&page_size=10`).catch(err => {
          return { data: { transactions: [], total: 0 } };
        });
        transactionsData = localTransactions.data.transactions || [];
        totalTransactions = localTransactions.data.total || 0;
      }
      
      setBalance(balanceData);
      setTransactions(transactionsData);
      setTotalPages(Math.ceil(totalTransactions / 10));
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
      case 'expiration':
        return 'warning';
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
      case 'expiration':
        return 'Сгорание';
      case 'refund':
        return 'Возврат';
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
              {/* Мобильная версия - карточки */}
              {isMobile ? (
                <Box sx={{ mt: 2 }}>
                  {transactions.map((transaction) => (
                    <Card key={transaction.id} variant="outlined" sx={{ mb: 2 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                          <Chip
                            label={getTransactionLabel(transaction.transaction_type)}
                            color={getTransactionColor(transaction.transaction_type)}
                            size="small"
                          />
                          <Typography
                            fontWeight="bold"
                            fontSize="1.2rem"
                            color={transaction.transaction_type === 'accrual' ? 'success.main' : 'error.main'}
                          >
                            {transaction.transaction_type === 'accrual' ? '+' : '-'}
                            {transaction.amount.toFixed(2)}
                          </Typography>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {transaction.description}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(transaction.created_at), 'dd MMM yyyy, HH:mm', { locale: ru })}
                          </Typography>
                          <Chip
                            label={transaction.currency === 'points' ? 'Баллы' : 'Кешбэк'}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                        
                        {transaction.balance_after !== undefined && (
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                            Баланс: {transaction.balance_after.toFixed(2)}
                          </Typography>
                        )}
                        
                        {transaction.expires_at && (
                          <Typography variant="caption" color="warning.main" display="block" sx={{ mt: 0.5 }}>
                            Действительны до {format(new Date(transaction.expires_at), 'dd MMM yyyy', { locale: ru })}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              ) : (
                /* Десктопная версия - таблица */
                <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Дата</TableCell>
                        <TableCell>Тип</TableCell>
                        <TableCell>Описание</TableCell>
                        <TableCell>Валюта</TableCell>
                        <TableCell align="right">Сумма</TableCell>
                        <TableCell align="right">Баланс</TableCell>
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
                          <TableCell>
                            {transaction.description}
                            {transaction.expires_at && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                до {format(new Date(transaction.expires_at), 'dd MMM yyyy', { locale: ru })}
                              </Typography>
                            )}
                          </TableCell>
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
                          <TableCell align="right">
                            <Typography variant="body2" color="text.secondary">
                              {transaction.balance_after !== undefined ? transaction.balance_after.toFixed(2) : '-'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

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
