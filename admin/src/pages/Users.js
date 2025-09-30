import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import Layout from '../components/Layout';
import axios from 'axios';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [pointsDialogOpen, setPointsDialogOpen] = useState(false);
  const [pointsAmount, setPointsAmount] = useState('');
  const [pointsAction, setPointsAction] = useState('accrue'); // accrue or deduct
  const [pointsReason, setPointsReason] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      // Для демонстрации используем тестовые данные
      // В продакшене здесь будет реальный API запрос
      const mockUsers = [
        {
          id: 1,
          email: 'admin@it-mydoc.ru',
          full_name: 'Администратор Системы',
          phone: '+79991234567',
          role: 'admin',
          is_active: true,
          created_at: '2025-09-30T07:41:51Z',
          points_balance: 0,
          cashback_balance: 0,
        },
        {
          id: 2,
          email: 'cashier@it-mydoc.ru',
          full_name: 'Кассир Мария',
          phone: '+79991234568',
          role: 'cashier',
          is_active: true,
          created_at: '2025-09-30T07:41:51Z',
          points_balance: 1200,
          cashback_balance: 350.50,
        },
        {
          id: 3,
          email: 'doctor@it-mydoc.ru',
          full_name: 'Доктор Иванов',
          phone: '+79991234569',
          role: 'doctor',
          is_active: true,
          created_at: '2025-09-30T07:41:51Z',
          points_balance: 2800,
          cashback_balance: 750.00,
        },
        {
          id: 4,
          email: 'patient@it-mydoc.ru',
          full_name: 'Пациент Петров',
          phone: '+79991234570',
          role: 'patient',
          is_active: true,
          created_at: '2025-09-30T07:41:51Z',
          points_balance: 2500,
          cashback_balance: 1050.75,
        },
      ];
      setUsers(mockUsers);
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
      setSnackbar({ open: true, message: 'Ошибка загрузки пользователей', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handlePointsDialog = (user, action) => {
    setSelectedUser(user);
    setPointsAction(action);
    setPointsDialogOpen(true);
  };

  const handlePointsSubmit = async () => {
    try {
      const endpoint = pointsAction === 'accrue' ? '/loyalty/accrue' : '/loyalty/deduct';
      
      await axios.post(endpoint, {
        user_id: selectedUser.id,
        points: parseFloat(pointsAmount),
        description: pointsReason,
        idempotency_key: `admin-${Date.now()}`,
      });

      setSnackbar({
        open: true,
        message: `Баллы успешно ${pointsAction === 'accrue' ? 'начислены' : 'списаны'}`,
        severity: 'success',
      });

      setPointsDialogOpen(false);
      setPointsAmount('');
      setPointsReason('');
      fetchUsers();
    } catch (error) {
      console.error('Ошибка операции с баллами:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Ошибка операции',
        severity: 'error',
      });
    }
  };

  const getRoleLabel = (role) => {
    const roles = {
      admin: 'Администратор',
      cashier: 'Кассир',
      doctor: 'Врач',
      patient: 'Пациент',
    };
    return roles[role] || role;
  };

  const getRoleColor = (role) => {
    const colors = {
      admin: 'error',
      cashier: 'warning',
      doctor: 'info',
      patient: 'success',
    };
    return colors[role] || 'default';
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    {
      field: 'full_name',
      headerName: 'Имя',
      width: 200,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="bold">
            {params.row.full_name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.email}
          </Typography>
        </Box>
      ),
    },
    { field: 'phone', headerName: 'Телефон', width: 150 },
    {
      field: 'role',
      headerName: 'Роль',
      width: 130,
      renderCell: (params) => (
        <Chip
          label={getRoleLabel(params.value)}
          color={getRoleColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'points_balance',
      headerName: 'Баллы',
      width: 100,
      renderCell: (params) => (
        <Typography fontWeight="bold" color="primary">
          {params.value?.toFixed(0) || 0}
        </Typography>
      ),
    },
    {
      field: 'cashback_balance',
      headerName: 'Кешбэк',
      width: 100,
      renderCell: (params) => (
        <Typography fontWeight="bold" color="secondary">
          {params.value?.toFixed(2) || 0} ₽
        </Typography>
      ),
    },
    {
      field: 'is_active',
      headerName: 'Статус',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Активен' : 'Неактивен'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Действия',
      width: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            color="success"
            onClick={() => handlePointsDialog(params.row, 'accrue')}
          >
            +
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={() => handlePointsDialog(params.row, 'deduct')}
          >
            −
          </Button>
        </Box>
      ),
    },
  ];

  const filteredUsers = users.filter(
    (user) =>
      user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.phone.includes(searchTerm)
  );

  return (
    <Layout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Управление пользователями
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Всего пользователей: {users.length}
        </Typography>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                placeholder="Поиск по имени, email или телефону..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                disabled
              >
                Добавить пользователя
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Box sx={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={filteredUsers}
              columns={columns}
              pageSize={10}
              rowsPerPageOptions={[10, 25, 50]}
              disableSelectionOnClick
              loading={loading}
              sx={{
                '& .MuiDataGrid-cell': {
                  padding: '8px',
                },
              }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Диалог начисления/списания баллов */}
      <Dialog open={pointsDialogOpen} onClose={() => setPointsDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {pointsAction === 'accrue' ? 'Начислить баллы' : 'Списать баллы'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Пользователь: <strong>{selectedUser?.full_name}</strong>
              <br />
              Текущий баланс: <strong>{selectedUser?.points_balance?.toFixed(0) || 0} баллов</strong>
            </Alert>

            <TextField
              fullWidth
              label="Количество баллов"
              type="number"
              value={pointsAmount}
              onChange={(e) => setPointsAmount(e.target.value)}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Причина"
              multiline
              rows={3}
              value={pointsReason}
              onChange={(e) => setPointsReason(e.target.value)}
              placeholder="Укажите причину операции..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPointsDialogOpen(false)}>Отмена</Button>
          <Button
            onClick={handlePointsSubmit}
            variant="contained"
            disabled={!pointsAmount || !pointsReason}
          >
            {pointsAction === 'accrue' ? 'Начислить' : 'Списать'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Layout>
  );
}