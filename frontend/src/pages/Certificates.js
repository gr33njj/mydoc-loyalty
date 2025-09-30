import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  IconButton,
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  CircularProgress,
} from '@mui/material';
import CardGiftcardIcon from '@mui/icons-material/CardGiftcard';
import SendIcon from '@mui/icons-material/Send';
import QrCode2Icon from '@mui/icons-material/QrCode2';
import AddIcon from '@mui/icons-material/Add';
import ShareIcon from '@mui/icons-material/Share';
import Layout from '../components/Layout';
import axios from 'axios';

export default function Certificates() {
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [buyDialogOpen, setBuyDialogOpen] = useState(false);
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [tabValue, setTabValue] = useState(0);

  // Форма покупки
  const [buyForm, setBuyForm] = useState({
    amount: 5000,
    design: 'default',
    message: ''
  });

  // Форма передачи
  const [transferForm, setTransferForm] = useState({
    email: '',
    message: ''
  });

  // Доступные дизайны
  const designs = [
    { value: 'default', label: 'Классический', color: '#004155' },
    { value: 'birthday', label: 'День рождения', color: '#e60a41' },
    { value: 'holiday', label: 'Праздничный', color: '#68cdd2' },
    { value: 'wellness', label: 'Здоровье', color: '#00a896' },
  ];

  // Предустановленные суммы
  const presetAmounts = [3000, 5000, 10000, 15000, 20000];

  useEffect(() => {
    fetchCertificates();
  }, []);

  const fetchCertificates = async () => {
    try {
      // TODO: Реализовать API endpoint для получения сертификатов пользователя
      // const response = await axios.get('/certificates/my');
      // setCertificates(response.data);
      setCertificates([]);
    } catch (error) {
      console.error('Ошибка загрузки сертификатов:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBuyCertificate = async () => {
    try {
      await axios.post('/certificates/create', {
        initial_amount: buyForm.amount,
        design_template: buyForm.design,
        message: buyForm.message,
        // owner_id будет определен на сервере из текущего пользователя
      });
      
      setSnackbarMessage('Сертификат успешно создан!');
      setSnackbarOpen(true);
      setBuyDialogOpen(false);
      fetchCertificates();
    } catch (error) {
      console.error('Ошибка создания сертификата:', error);
      setSnackbarMessage('Ошибка создания сертификата');
      setSnackbarOpen(true);
    }
  };

  const handleTransfer = async () => {
    try {
      await axios.post('/certificates/transfer', {
        certificate_id: selectedCertificate.id,
        to_user_email: transferForm.email,
        message: transferForm.message
      });
      
      setSnackbarMessage('Сертификат успешно передан!');
      setSnackbarOpen(true);
      setTransferDialogOpen(false);
      fetchCertificates();
    } catch (error) {
      console.error('Ошибка передачи сертификата:', error);
      setSnackbarMessage('Ошибка передачи сертификата');
      setSnackbarOpen(true);
    }
  };

  const openTransferDialog = (certificate) => {
    setSelectedCertificate(certificate);
    setTransferForm({ email: '', message: '' });
    setTransferDialogOpen(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'used': return 'default';
      case 'expired': return 'error';
      default: return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'active': return 'Активен';
      case 'used': return 'Использован';
      case 'expired': return 'Истек';
      default: return status;
    }
  };

  return (
    <Layout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Подарочные сертификаты
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setBuyDialogOpen(true)}
        >
          Купить сертификат
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Подарочные сертификаты - отличный подарок для ваших близких! Вы можете выбрать дизайн и сумму сертификата.
      </Alert>

      <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 3 }}>
        <Tab label="Мои сертификаты" />
        <Tab label="Как это работает" />
      </Tabs>

      {tabValue === 0 && (
        <>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          ) : certificates.length === 0 ? (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <CardGiftcardIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  У вас пока нет сертификатов
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Купите сертификат для себя или в подарок
                </Typography>
                <Button 
                  variant="contained" 
                  sx={{ mt: 2 }}
                  onClick={() => setBuyDialogOpen(true)}
                >
                  Купить сертификат
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Grid container spacing={3}>
              {certificates.map((cert) => (
                <Grid item xs={12} md={6} key={cert.id}>
                  <Card sx={{ 
                    position: 'relative',
                    background: `linear-gradient(135deg, ${designs.find(d => d.value === cert.design_template)?.color || '#004155'}15 0%, ${designs.find(d => d.value === cert.design_template)?.color || '#004155'}30 100%)`
                  }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Typography variant="h6" fontWeight="bold">
                          Сертификат #{cert.code}
                        </Typography>
                        <Chip 
                          label={getStatusLabel(cert.status)} 
                          color={getStatusColor(cert.status)}
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
                        {cert.current_amount.toFixed(0)} ₽
                      </Typography>
                      
                      {cert.initial_amount !== cert.current_amount && (
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Начальная сумма: {cert.initial_amount.toFixed(0)} ₽
                        </Typography>
                      )}
                      
                      {cert.message && (
                        <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
                          {cert.message}
                        </Alert>
                      )}
                      
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
                        Действителен до: {new Date(cert.valid_until).toLocaleDateString()}
                      </Typography>
                      
                      {cert.status === 'active' && (
                        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<QrCode2Icon />}
                            onClick={() => window.open(cert.qr_code_url, '_blank')}
                          >
                            QR-код
                          </Button>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<SendIcon />}
                            onClick={() => openTransferDialog(cert)}
                          >
                            Передать
                          </Button>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}

      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Как использовать сертификаты?
            </Typography>
            <Box component="ol" sx={{ pl: 2 }}>
              <Typography component="li" variant="body2" paragraph>
                <strong>Покупка:</strong> Выберите сумму и дизайн сертификата. Оплатите через безопасную форму.
              </Typography>
              <Typography component="li" variant="body2" paragraph>
                <strong>Получение:</strong> Сертификат появится в вашем личном кабинете с уникальным QR-кодом.
              </Typography>
              <Typography component="li" variant="body2" paragraph>
                <strong>Передача:</strong> Вы можете передать сертификат другому пользователю по email.
              </Typography>
              <Typography component="li" variant="body2" paragraph>
                <strong>Использование:</strong> Покажите QR-код на кассе клиники для оплаты услуг.
              </Typography>
              <Typography component="li" variant="body2" paragraph>
                <strong>Частичное использование:</strong> Сертификат можно использовать несколько раз, пока не закончится баланс.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Диалог покупки сертификата */}
      <Dialog open={buyDialogOpen} onClose={() => setBuyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Купить подарочный сертификат</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Выберите сумму:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
              {presetAmounts.map((amount) => (
                <Button
                  key={amount}
                  variant={buyForm.amount === amount ? 'contained' : 'outlined'}
                  onClick={() => setBuyForm({ ...buyForm, amount })}
                  size="small"
                >
                  {amount.toLocaleString()} ₽
                </Button>
              ))}
            </Box>

            <TextField
              fullWidth
              type="number"
              label="Или введите свою сумму"
              value={buyForm.amount}
              onChange={(e) => setBuyForm({ ...buyForm, amount: parseInt(e.target.value) || 0 })}
              sx={{ mb: 3 }}
              InputProps={{
                endAdornment: <Typography>₽</Typography>
              }}
            />

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Дизайн сертификата</InputLabel>
              <Select
                value={buyForm.design}
                label="Дизайн сертификата"
                onChange={(e) => setBuyForm({ ...buyForm, design: e.target.value })}
              >
                {designs.map((design) => (
                  <MenuItem key={design.value} value={design.value}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 20, height: 20, bgcolor: design.color, borderRadius: 1 }} />
                      {design.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Поздравительное сообщение (необязательно)"
              value={buyForm.message}
              onChange={(e) => setBuyForm({ ...buyForm, message: e.target.value })}
              placeholder="Напишите пожелание получателю..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBuyDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleBuyCertificate} variant="contained">
            Купить за {buyForm.amount.toLocaleString()} ₽
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог передачи сертификата */}
      <Dialog open={transferDialogOpen} onClose={() => setTransferDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Передать сертификат</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Сертификат будет передан пользователю с указанным email
            </Alert>

            <TextField
              fullWidth
              type="email"
              label="Email получателя"
              value={transferForm.email}
              onChange={(e) => setTransferForm({ ...transferForm, email: e.target.value })}
              sx={{ mb: 3 }}
            />

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Сообщение получателю (необязательно)"
              value={transferForm.message}
              onChange={(e) => setTransferForm({ ...transferForm, message: e.target.value })}
              placeholder="Поздравление или пожелание..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTransferDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleTransfer} variant="contained" startIcon={<SendIcon />}>
            Передать
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Layout>
  );
}