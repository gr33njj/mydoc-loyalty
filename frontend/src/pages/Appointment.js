import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  EventAvailable as EventAvailableIcon,
  Person as PersonIcon,
  MedicalServices as MedicalServicesIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  HourglassEmpty as PendingIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  CalendarMonth as CalendarIcon,
  Comment as CommentIcon,
} from '@mui/icons-material';
import axios from 'axios';
import Layout from '../components/Layout';

const API = process.env.REACT_APP_API_URL || '/api';

// Временные слоты
const TIME_SLOTS = [
  '08:00–08:30', '08:30–09:00', '09:00–09:30', '09:30–10:00',
  '10:00–10:30', '10:30–11:00', '11:00–11:30', '11:30–12:00',
  '13:00–13:30', '13:30–14:00', '14:00–14:30', '14:30–15:00',
  '15:00–15:30', '15:30–16:00', '16:00–16:30', '16:30–17:00',
];

const STEPS = ['Специалист / Услуга', 'Дата и время', 'Подтверждение'];

const STATUS_LABELS = {
  pending:   { label: 'Ожидает',    color: 'warning', icon: <PendingIcon fontSize="small" /> },
  confirmed: { label: 'Подтверждена', color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
  cancelled: { label: 'Отменена',   color: 'error',   icon: <CancelIcon fontSize="small" /> },
  completed: { label: 'Выполнена',  color: 'default', icon: <CheckCircleIcon fontSize="small" /> },
};

// Группировка по категориям
function groupBy(arr, key) {
  return arr.reduce((acc, item) => {
    (acc[item[key]] = acc[item[key]] || []).push(item);
    return acc;
  }, {});
}

// Форматирование даты yyyy-mm-dd → dd.mm.yyyy
function fmtDate(iso) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('T')[0].split('-');
  return `${d}.${m}.${y}`;
}

export default function Appointment() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [tab, setTab] = useState(0);          // 0 = Новая запись, 1 = Мои записи
  const [step, setStep] = useState(0);

  // Справочники
  const [doctors, setDoctors] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Форма
  const [selectionMode, setSelectionMode] = useState('doctor'); // 'doctor' | 'service'
  const [form, setForm] = useState({
    doctor_id: '',
    doctor_name: '',
    service_id: '',
    service_name: '',
    preferred_date: '',
    preferred_time_slot: '',
    comment: '',
  });

  // История
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Состояние отправки
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  // Отмена
  const [cancelDialog, setCancelDialog] = useState(null);

  // Загрузка справочников
  useEffect(() => {
    Promise.all([
      axios.get(`${API}/appointments/doctors`),
      axios.get(`${API}/appointments/services`),
    ])
      .then(([dRes, sRes]) => {
        setDoctors(dRes.data);
        setServices(sRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Загрузка истории при переключении вкладки
  useEffect(() => {
    if (tab === 1) {
      setHistoryLoading(true);
      axios.get(`${API}/appointments/my`)
        .then(r => setHistory(r.data))
        .catch(() => {})
        .finally(() => setHistoryLoading(false));
    }
  }, [tab]);

  // --- Выбор врача / услуги ---
  const handleSelectDoctor = (doc) => {
    setForm(f => ({
      ...f,
      doctor_id: doc.id,
      doctor_name: doc.name,
      service_id: '',
      service_name: '',
    }));
  };

  const handleSelectService = (svc) => {
    setForm(f => ({
      ...f,
      service_id: svc.id,
      service_name: svc.name,
      doctor_id: '',
      doctor_name: '',
    }));
  };

  // --- Переходы по шагам ---
  const canNextStep1 = selectionMode === 'doctor'
    ? Boolean(form.doctor_id)
    : Boolean(form.service_id);

  const canNextStep2 = Boolean(form.preferred_date) && Boolean(form.preferred_time_slot);

  const handleNext = () => setStep(s => s + 1);
  const handleBack = () => setStep(s => s - 1);

  // --- Отправка ---
  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      await axios.post(`${API}/appointments/request`, {
        doctor_id: form.doctor_id || undefined,
        doctor_name: form.doctor_name || undefined,
        service_id: form.service_id || undefined,
        service_name: form.service_name || undefined,
        preferred_date: form.preferred_date
          ? new Date(form.preferred_date).toISOString()
          : undefined,
        preferred_time_slot: form.preferred_time_slot,
        comment: form.comment || undefined,
      });
      setSuccess(true);
    } catch (e) {
      setError(e.response?.data?.detail || 'Ошибка при отправке заявки');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setStep(0);
    setSuccess(false);
    setError('');
    setForm({
      doctor_id: '', doctor_name: '',
      service_id: '', service_name: '',
      preferred_date: '', preferred_time_slot: '', comment: '',
    });
  };

  // --- Отмена заявки ---
  const handleCancel = async (id) => {
    try {
      await axios.delete(`${API}/appointments/request/${id}`);
      setHistory(h => h.map(a => a.id === id ? { ...a, status: 'cancelled' } : a));
    } catch {}
    setCancelDialog(null);
  };

  // --- Минимальная допустимая дата (завтра) ---
  const minDate = new Date();
  minDate.setDate(minDate.getDate() + 1);
  const minDateStr = minDate.toISOString().split('T')[0];

  const groupedServices = useMemo(() => groupBy(services, 'category'), [services]);

  // ==================== РЕНДЕР ====================

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700} color="primary" gutterBottom>
          <EventAvailableIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Онлайн-запись
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Запишитесь к специалисту — мы свяжемся для подтверждения времени
        </Typography>
      </Box>

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{ mb: 3 }}
        textColor="primary"
        indicatorColor="primary"
      >
        <Tab label="Новая запись" />
        <Tab label="Мои записи" />
      </Tabs>

      {/* ===================== ВКЛАДКА: НОВАЯ ЗАПИСЬ ===================== */}
      {tab === 0 && (
        <Card>
          <CardContent sx={{ p: isMobile ? 2 : 3 }}>
            {success ? (
              <SuccessScreen onReset={handleReset} onHistory={() => setTab(1)} />
            ) : (
              <>
                <Stepper
                  activeStep={step}
                  alternativeLabel={isMobile}
                  sx={{ mb: 3 }}
                >
                  {STEPS.map(label => (
                    <Step key={label}>
                      <StepLabel>{label}</StepLabel>
                    </Step>
                  ))}
                </Stepper>

                {error && (
                  <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                    {error}
                  </Alert>
                )}

                {/* === ШАГ 0: Выбор врача / услуги === */}
                {step === 0 && (
                  <Step0
                    selectionMode={selectionMode}
                    setSelectionMode={setSelectionMode}
                    doctors={doctors}
                    groupedServices={groupedServices}
                    form={form}
                    onSelectDoctor={handleSelectDoctor}
                    onSelectService={handleSelectService}
                  />
                )}

                {/* === ШАГ 1: Дата и время === */}
                {step === 1 && (
                  <Step1
                    form={form}
                    setForm={setForm}
                    minDate={minDateStr}
                  />
                )}

                {/* === ШАГ 2: Подтверждение === */}
                {step === 2 && (
                  <Step2
                    form={form}
                    setForm={setForm}
                    selectionMode={selectionMode}
                  />
                )}

                {/* Кнопки навигации */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                  <Button
                    startIcon={<ArrowBackIcon />}
                    onClick={handleBack}
                    disabled={step === 0}
                    variant="outlined"
                  >
                    Назад
                  </Button>

                  {step < 2 ? (
                    <Button
                      endIcon={<ArrowForwardIcon />}
                      onClick={handleNext}
                      disabled={step === 0 ? !canNextStep1 : !canNextStep2}
                      variant="contained"
                    >
                      Далее
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleSubmit}
                      disabled={submitting}
                      startIcon={submitting ? <CircularProgress size={18} color="inherit" /> : <CheckCircleIcon />}
                    >
                      {submitting ? 'Отправка...' : 'Записаться'}
                    </Button>
                  )}
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* ===================== ВКЛАДКА: МОИ ЗАПИСИ ===================== */}
      {tab === 1 && (
        <Card>
          <CardContent>
            {historyLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : history.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <EventAvailableIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">
                  У вас пока нет записей
                </Typography>
                <Button
                  variant="contained"
                  sx={{ mt: 2 }}
                  onClick={() => setTab(0)}
                >
                  Записаться
                </Button>
              </Box>
            ) : (
              <List disablePadding>
                {history.map((appt, idx) => {
                  const st = STATUS_LABELS[appt.status] || STATUS_LABELS.pending;
                  return (
                    <React.Fragment key={appt.id}>
                      {idx > 0 && <Divider />}
                      <ListItem
                        alignItems="flex-start"
                        secondaryAction={
                          appt.status === 'pending' && (
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => setCancelDialog(appt.id)}
                              title="Отменить"
                            >
                              <CancelIcon fontSize="small" />
                            </IconButton>
                          )
                        }
                      >
                        <ListItemIcon sx={{ mt: 1, minWidth: 36 }}>
                          {appt.doctor_name
                            ? <PersonIcon color="primary" />
                            : <MedicalServicesIcon color="secondary" />
                          }
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                              <Typography variant="body1" fontWeight={600}>
                                {appt.doctor_name || appt.service_name || 'Запись'}
                              </Typography>
                              <Chip
                                size="small"
                                icon={st.icon}
                                label={st.label}
                                color={st.color}
                                variant="outlined"
                              />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              {appt.preferred_date && (
                                <Typography variant="body2" color="text.secondary">
                                  <CalendarIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                                  {fmtDate(appt.preferred_date)}
                                  {appt.preferred_time_slot && ` · ${appt.preferred_time_slot}`}
                                </Typography>
                              )}
                              {appt.comment && (
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.3 }}>
                                  <CommentIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                                  {appt.comment}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    </React.Fragment>
                  );
                })}
              </List>
            )}
          </CardContent>
        </Card>
      )}

      {/* Диалог подтверждения отмены */}
      <Dialog open={Boolean(cancelDialog)} onClose={() => setCancelDialog(null)}>
        <DialogTitle>Отменить запись?</DialogTitle>
        <DialogContent>
          <Typography>Вы уверены, что хотите отменить эту запись?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialog(null)}>Нет</Button>
          <Button color="error" onClick={() => handleCancel(cancelDialog)}>
            Да, отменить
          </Button>
        </DialogActions>
      </Dialog>
    </Layout>
  );
}


// =====================================================================
// Шаг 0 — Выбор специалиста или услуги
// =====================================================================
function Step0({ selectionMode, setSelectionMode, doctors, groupedServices, form, onSelectDoctor, onSelectService }) {
  return (
    <Box>
      <Tabs
        value={selectionMode}
        onChange={(_, v) => setSelectionMode(v)}
        sx={{ mb: 2 }}
        variant="fullWidth"
      >
        <Tab value="doctor" label="По врачу" icon={<PersonIcon />} iconPosition="start" />
        <Tab value="service" label="По услуге" icon={<MedicalServicesIcon />} iconPosition="start" />
      </Tabs>

      {selectionMode === 'doctor' ? (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
          {doctors.map(doc => {
            const selected = form.doctor_id === doc.id;
            return (
              <Card
                key={doc.id}
                onClick={() => onSelectDoctor(doc)}
                sx={{
                  width: { xs: '100%', sm: 'calc(50% - 6px)', md: 'calc(33% - 8px)' },
                  cursor: 'pointer',
                  border: '2px solid',
                  borderColor: selected ? 'primary.main' : 'transparent',
                  bgcolor: selected ? 'primary.light' + '18' : 'background.paper',
                  transition: 'all 0.2s',
                  '&:hover': { borderColor: 'primary.light', boxShadow: 3 },
                }}
                elevation={selected ? 3 : 1}
              >
                <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon color={selected ? 'primary' : 'action'} />
                    <Box>
                      <Typography variant="body2" fontWeight={600} lineHeight={1.2}>
                        {doc.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {doc.specialty}
                      </Typography>
                    </Box>
                    {selected && (
                      <CheckCircleIcon color="primary" sx={{ ml: 'auto', flexShrink: 0 }} />
                    )}
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      ) : (
        <Box>
          {Object.entries(groupedServices).map(([category, items]) => (
            <Box key={category} sx={{ mb: 2 }}>
              <Typography
                variant="subtitle2"
                fontWeight={700}
                color="primary"
                sx={{ mb: 0.5, ml: 0.5 }}
              >
                {category}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {items.map(svc => {
                  const selected = form.service_id === svc.id;
                  return (
                    <Chip
                      key={svc.id}
                      label={`${svc.name} · ${svc.duration_min} мин`}
                      onClick={() => onSelectService(svc)}
                      color={selected ? 'primary' : 'default'}
                      variant={selected ? 'filled' : 'outlined'}
                      icon={selected ? <CheckCircleIcon /> : undefined}
                      sx={{ cursor: 'pointer', height: 'auto', py: 0.5,
                        '& .MuiChip-label': { whiteSpace: 'normal' } }}
                    />
                  );
                })}
              </Box>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}


// =====================================================================
// Шаг 1 — Дата и время
// =====================================================================
function Step1({ form, setForm, minDate }) {
  return (
    <Box>
      <TextField
        label="Желаемая дата"
        type="date"
        fullWidth
        value={form.preferred_date}
        onChange={e => setForm(f => ({ ...f, preferred_date: e.target.value, preferred_time_slot: '' }))}
        InputLabelProps={{ shrink: true }}
        inputProps={{ min: minDate }}
        sx={{ mb: 3 }}
      />

      {form.preferred_date && (
        <>
          <Typography variant="subtitle2" gutterBottom>
            <AccessTimeIcon sx={{ mr: 0.5, fontSize: 16, verticalAlign: 'middle' }} />
            Выберите время
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {TIME_SLOTS.map(slot => (
              <Chip
                key={slot}
                label={slot}
                onClick={() => setForm(f => ({ ...f, preferred_time_slot: slot }))}
                color={form.preferred_time_slot === slot ? 'primary' : 'default'}
                variant={form.preferred_time_slot === slot ? 'filled' : 'outlined'}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </>
      )}
    </Box>
  );
}


// =====================================================================
// Шаг 2 — Подтверждение
// =====================================================================
function Step2({ form, setForm, selectionMode }) {
  return (
    <Box>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        Проверьте данные заявки
      </Typography>
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <InfoRow
            icon={<PersonIcon color="primary" fontSize="small" />}
            label={selectionMode === 'doctor' ? 'Врач' : 'Услуга'}
            value={form.doctor_name || form.service_name || '—'}
          />
          <Divider sx={{ my: 1 }} />
          <InfoRow
            icon={<CalendarIcon color="primary" fontSize="small" />}
            label="Дата"
            value={form.preferred_date
              ? new Date(form.preferred_date).toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })
              : '—'
            }
          />
          <Divider sx={{ my: 1 }} />
          <InfoRow
            icon={<AccessTimeIcon color="primary" fontSize="small" />}
            label="Время"
            value={form.preferred_time_slot || '—'}
          />
        </CardContent>
      </Card>

      <TextField
        label="Комментарий (необязательно)"
        multiline
        rows={3}
        fullWidth
        value={form.comment}
        onChange={e => setForm(f => ({ ...f, comment: e.target.value }))}
        placeholder="Опишите жалобы или пожелания..."
        inputProps={{ maxLength: 500 }}
      />

      <Alert severity="info" sx={{ mt: 2 }}>
        После отправки заявки администратор свяжется с вами для подтверждения удобного времени.
      </Alert>
    </Box>
  );
}

function InfoRow({ icon, label, value }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {icon}
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
        {label}:
      </Typography>
      <Typography variant="body2" fontWeight={600}>
        {value}
      </Typography>
    </Box>
  );
}


// =====================================================================
// Экран успеха
// =====================================================================
function SuccessScreen({ onReset, onHistory }) {
  return (
    <Box sx={{ textAlign: 'center', py: 3 }}>
      <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
      <Typography variant="h6" fontWeight={700} gutterBottom>
        Заявка отправлена!
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Мы рассмотрим вашу заявку и свяжемся с вами для подтверждения записи.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button variant="outlined" onClick={onHistory}>
          Мои записи
        </Button>
        <Button variant="contained" onClick={onReset}>
          Новая запись
        </Button>
      </Box>
    </Box>
  );
}
