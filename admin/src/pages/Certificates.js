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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Autocomplete,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Check as CheckIcon,
  QrCode as QrCodeIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import Layout from '../components/Layout';
import axios from 'axios';
import { format } from 'date-fns';

export default function Certificates() {
  const [certificates, setCertificates] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [verifyDialogOpen, setVerifyDialogOpen] = useState(false);
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [selectedCert, setSelectedCert] = useState(null);
  const [transferEmail, setTransferEmail] = useState('');
  const [verifyCode, setVerifyCode] = useState('');
  const [verifyResult, setVerifyResult] = useState(null);
  const [creatingCert, setCreatingCert] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Форма создания сертификата
  const [newCert, setNewCert] = useState({
    amount: 5000,
    design: 'default',
    message: '',
    recipientEmail: '',
  });

  useEffect(() => {
    fetchCertificates();
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/admin/users', {
        params: { page: 1, page_size: 100 }
      });
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
    }
  };

  const fetchCertificates = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/admin/certificates', {
        params: { page: 1, page_size: 100 }
      });
      setCertificates(response.data.certificates || []);
    } catch (error) {
      console.error('Ошибка загрузки сертификатов:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Ошибка загрузки сертификатов',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCertificate = async () => {
    setCreatingCert(true);
    try {
      const response = await axios.post('/certificates/create', {
        initial_amount: newCert.amount,
        design_template: newCert.design,
        message: newCert.message,
      });

      const certCode = response.data.code;

      // Если указан получатель - переводим сертификат ему
      if (newCert.recipientEmail) {
        try {
          await axios.post('/certificates/transfer', {
            code: certCode,
            recipient_email: newCert.recipientEmail,
          });

          setSnackbar({
            open: true,
            message: `Сертификат ${certCode} создан и отправлен на ${newCert.recipientEmail}`,
            severity: 'success',
          });
        } catch (transferError) {
          console.error('Ошибка передачи сертификата:', transferError);
          const errorMessage = transferError.response?.data?.detail || transferError.message || 'Неизвестная ошибка';
          setSnackbar({
            open: true,
            message: `Сертификат ${certCode} создан, но не удалось отправить: ${errorMessage}`,
            severity: 'warning',
          });
        }
      } else {
        setSnackbar({
          open: true,
          message: `Сертификат ${certCode} успешно создан!`,
          severity: 'success',
        });
      }

      setCreateDialogOpen(false);
      setNewCert({ amount: 5000, design: 'default', message: '', recipientEmail: '' });
      
      // Обновляем список сертификатов
      fetchCertificates();
    } catch (error) {
      console.error('Ошибка создания сертификата:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Ошибка создания сертификата',
        severity: 'error',
      });
    } finally {
      setCreatingCert(false);
    }
  };

  const handleTransferCertificate = async () => {
    try {
      await axios.post('/certificates/transfer', {
        code: selectedCert.code,
        recipient_email: transferEmail,
      });

      setSnackbar({
        open: true,
        message: `Сертификат передан на ${transferEmail}`,
        severity: 'success',
      });

      setTransferDialogOpen(false);
      setTransferEmail('');
      setSelectedCert(null);
      fetchCertificates();
    } catch (error) {
      console.error('Ошибка передачи сертификата:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Ошибка передачи сертификата',
        severity: 'error',
      });
    }
  };

  const handleVerifyCertificate = async () => {
    try {
      const response = await axios.post('/certificates/verify', {
        code: verifyCode,
      });

      setVerifyResult(response.data);
      setSnackbar({
        open: true,
        message: `Сертификат действителен! Баланс: ${response.data.current_amount} ₽`,
        severity: 'success',
      });
    } catch (error) {
      console.error('Ошибка проверки сертификата:', error);
      setVerifyResult(null);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Сертификат недействителен',
        severity: 'error',
      });
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'success',
      used: 'default',
      expired: 'error',
    };
    return colors[status] || 'default';
  };

  const getStatusLabel = (status) => {
    const labels = {
      active: 'Активен',
      used: 'Использован',
      expired: 'Истек',
    };
    return labels[status] || status;
  };

  const getDesignLabel = (design) => {
    const labels = {
      default: 'Классический',
      birthday: 'День рождения',
      holiday: 'Праздничный',
      wellness: 'Здоровье',
    };
    return labels[design] || design;
  };

  const columns = [
    { 
      field: 'code', 
      headerName: 'Код', 
      width: 150,
      renderCell: (params) => (
        <Typography variant="body2" fontFamily="monospace" fontWeight="bold">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'owner_id',
      headerName: 'Владелец',
      width: 150,
      renderCell: (params) => {
        if (!params.value) return 'Не назначен';
        const user = users.find(u => u.id === params.value);
        return user ? user.email : `ID: ${params.value}`;
      },
    },
    {
      field: 'initial_amount',
      headerName: 'Номинал',
      width: 120,
      renderCell: (params) => `${params.value} ₽`,
    },
    {
      field: 'current_amount',
      headerName: 'Баланс',
      width: 120,
      renderCell: (params) => (
        <Typography fontWeight="bold" color="primary">
          {params.value} ₽
        </Typography>
      ),
    },
    {
      field: 'status',
      headerName: 'Статус',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={getStatusLabel(params.value)}
          color={getStatusColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'design_template',
      headerName: 'Дизайн',
      width: 150,
      renderCell: (params) => getDesignLabel(params.value),
    },
    {
      field: 'issued_at',
      headerName: 'Создан',
      width: 120,
      renderCell: (params) => {
        try {
          return format(new Date(params.value), 'dd.MM.yyyy');
        } catch {
          return '—';
        }
      },
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
            startIcon={<QrCodeIcon />}
            onClick={() => {
              if (params.row.qr_code_url) {
                window.open(params.row.qr_code_url, '_blank');
              } else {
                setSnackbar({
                  open: true,
                  message: 'QR-код не доступен',
                  severity: 'warning',
                });
              }
            }}
          >
            QR
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<SendIcon />}
            onClick={() => {
              setSelectedCert(params.row);
              setTransferEmail('');
              setTransferDialogOpen(true);
            }}
            disabled={params.row.status !== 'active'}
          >
            Отправить
          </Button>
        </Box>
      ),
    },
  ];

  const filteredCertificates = certificates.filter((cert) =>
    cert.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const designs = [
    { value: 'default', label: 'Классический' },
    { value: 'birthday', label: 'День рождения' },
    { value: 'holiday', label: 'Праздничный' },
    { value: 'wellness', label: 'Здоровье' },
  ];

  const presetAmounts = [3000, 5000, 10000, 15000, 20000];

  return (
    <Layout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Управление сертификатами
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Всего сертификатов: {certificates.length}
        </Typography>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                placeholder="Поиск по коду сертификата..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchCertificates}
                disabled={loading}
              >
                Обновить
              </Button>
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<CheckIcon />}
                onClick={() => {
                  setVerifyCode('');
                  setVerifyResult(null);
                  setVerifyDialogOpen(true);
                }}
              >
                Проверить
              </Button>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
              >
                Создать сертификат
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <CircularProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Загрузка сертификатов...
            </Typography>
          </CardContent>
        </Card>
      ) : certificates.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" gutterBottom>
              Сертификаты не найдены
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Создайте первый сертификат нажав кнопку "Создать сертификат"
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{ mt: 2 }}
            >
              Создать первый сертификат
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <Box sx={{ height: 600, width: '100%' }}>
              <DataGrid
                rows={filteredCertificates}
                columns={columns}
                pageSize={10}
                rowsPerPageOptions={[10, 25, 50]}
                disableSelectionOnClick
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Диалог создания сертификата */}
      <Dialog open={createDialogOpen} onClose={() => !creatingCert && setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AddIcon />
            Создать подарочный сертификат
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Создайте сертификат и сразу назначьте его получателю, или оставьте без владельца для дальнейшей передачи
            </Alert>

            <Typography variant="subtitle2" gutterBottom>
              Выберите сумму:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
              {presetAmounts.map((amount) => (
                <Button
                  key={amount}
                  variant={newCert.amount === amount ? 'contained' : 'outlined'}
                  onClick={() => setNewCert({ ...newCert, amount })}
                  size="small"
                  disabled={creatingCert}
                >
                  {amount.toLocaleString()} ₽
                </Button>
              ))}
            </Box>

            <TextField
              fullWidth
              type="number"
              label="Или введите свою сумму"
              value={newCert.amount}
              onChange={(e) => setNewCert({ ...newCert, amount: parseInt(e.target.value) || 0 })}
              sx={{ mb: 3 }}
              disabled={creatingCert}
            />

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Дизайн сертификата</InputLabel>
              <Select
                value={newCert.design}
                label="Дизайн сертификата"
                onChange={(e) => setNewCert({ ...newCert, design: e.target.value })}
                disabled={creatingCert}
              >
                {designs.map((design) => (
                  <MenuItem key={design.value} value={design.value}>
                    {design.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Autocomplete
              freeSolo
              options={users}
              getOptionLabel={(option) => typeof option === 'string' ? option : `${option.full_name} (${option.email})`}
              value={newCert.recipientEmail}
              onChange={(e, newValue) => {
                setNewCert({ 
                  ...newCert, 
                  recipientEmail: typeof newValue === 'string' ? newValue : (newValue?.email || '')
                });
              }}
              onInputChange={(e, newInputValue) => {
                setNewCert({ ...newCert, recipientEmail: newInputValue });
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Email получателя (необязательно)"
                  placeholder="Выберите из списка или введите email"
                  helperText="Если не указан, сертификат будет создан без владельца"
                />
              )}
              disabled={creatingCert}
              sx={{ mb: 3 }}
            />

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Поздравительное сообщение (необязательно)"
              value={newCert.message}
              onChange={(e) => setNewCert({ ...newCert, message: e.target.value })}
              placeholder="С Днём Рождения! Желаем здоровья и счастья!"
              disabled={creatingCert}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)} disabled={creatingCert}>
            Отмена
          </Button>
          <Button 
            onClick={handleCreateCertificate} 
            variant="contained" 
            disabled={creatingCert || !newCert.amount}
            startIcon={creatingCert ? <CircularProgress size={20} /> : <AddIcon />}
          >
            {creatingCert ? 'Создание...' : `Создать на ${newCert.amount.toLocaleString()} ₽`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог передачи сертификата */}
      <Dialog open={transferDialogOpen} onClose={() => setTransferDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Отправить сертификат</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Сертификат: <strong>{selectedCert?.code}</strong>
              <br />
              Баланс: <strong>{selectedCert?.current_amount} ₽</strong>
            </Alert>

            <Autocomplete
              freeSolo
              options={users}
              getOptionLabel={(option) => typeof option === 'string' ? option : `${option.full_name} (${option.email})`}
              value={transferEmail}
              onChange={(e, newValue) => {
                setTransferEmail(typeof newValue === 'string' ? newValue : (newValue?.email || ''));
              }}
              onInputChange={(e, newInputValue) => {
                setTransferEmail(newInputValue);
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Email получателя"
                  placeholder="Выберите из списка или введите email"
                />
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTransferDialogOpen(false)}>Отмена</Button>
          <Button
            onClick={handleTransferCertificate}
            variant="contained"
            disabled={!transferEmail}
            startIcon={<SendIcon />}
          >
            Отправить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог проверки сертификата */}
      <Dialog open={verifyDialogOpen} onClose={() => setVerifyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Проверить сертификат</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Введите код сертификата для проверки его действительности
            </Alert>

            <TextField
              fullWidth
              label="Код сертификата"
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.toUpperCase())}
              placeholder="CERT-XXXXXXXX"
              sx={{ mb: 2 }}
            />

            {verifyResult && (
              <Alert severity="success">
                <Typography variant="subtitle2">Сертификат действителен!</Typography>
                <Typography variant="body2">
                  Код: <strong>{verifyResult.code}</strong>
                </Typography>
                <Typography variant="body2">
                  Баланс: <strong>{verifyResult.current_amount} ₽</strong>
                </Typography>
                <Typography variant="body2">
                  Статус: <strong>{getStatusLabel(verifyResult.status)}</strong>
                </Typography>
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setVerifyDialogOpen(false);
            setVerifyCode('');
            setVerifyResult(null);
          }}>
            Закрыть
          </Button>
          <Button
            onClick={handleVerifyCertificate}
            variant="contained"
            disabled={!verifyCode}
          >
            Проверить
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Layout>
  );
}