import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { Box, Button, Alert, CircularProgress } from '@mui/material';
import { CameraAlt, Stop } from '@mui/icons-material';

export default function QRScanner({ onScanSuccess, onClose }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [cameraId, setCameraId] = useState(null);
  const scannerRef = useRef(null);
  const html5QrCodeRef = useRef(null);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      stopScanning();
    };
  }, []);

  const getCameras = async () => {
    try {
      const devices = await Html5Qrcode.getCameras();
      if (devices && devices.length > 0) {
        // Предпочитаем заднюю камеру
        const backCamera = devices.find(device => 
          device.label.toLowerCase().includes('back') || 
          device.label.toLowerCase().includes('rear')
        );
        return backCamera ? backCamera.id : devices[0].id;
      } else {
        throw new Error('Камеры не найдены');
      }
    } catch (err) {
      console.error('Ошибка получения камер:', err);
      throw new Error('Не удалось получить доступ к камере');
    }
  };

  const startScanning = async () => {
    try {
      setError(null);
      setScanning(true);

      const camId = await getCameras();
      setCameraId(camId);

      html5QrCodeRef.current = new Html5Qrcode("qr-reader");

      await html5QrCodeRef.current.start(
        camId,
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
          aspectRatio: 1.0,
        },
        (decodedText) => {
          console.log('QR-код отсканирован:', decodedText);
          stopScanning();
          onScanSuccess(decodedText);
        },
        (errorMessage) => {
          // Игнорируем ошибки сканирования (они постоянны)
        }
      );
    } catch (err) {
      console.error('Ошибка запуска сканера:', err);
      setError(err.message || 'Не удалось запустить камеру');
      setScanning(false);
    }
  };

  const stopScanning = async () => {
    try {
      if (html5QrCodeRef.current && scanning) {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current.clear();
      }
    } catch (err) {
      console.error('Ошибка остановки сканера:', err);
    } finally {
      setScanning(false);
      html5QrCodeRef.current = null;
    }
  };

  return (
    <Box sx={{ textAlign: 'center' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box
        id="qr-reader"
        ref={scannerRef}
        sx={{
          width: '100%',
          maxWidth: '500px',
          margin: '0 auto',
          borderRadius: 2,
          overflow: 'hidden',
          bgcolor: '#000',
          minHeight: scanning ? '300px' : '0',
        }}
      />

      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
        {!scanning ? (
          <Button
            variant="contained"
            color="primary"
            startIcon={<CameraAlt />}
            onClick={startScanning}
            size="large"
          >
            Включить камеру
          </Button>
        ) : (
          <Button
            variant="contained"
            color="error"
            startIcon={<Stop />}
            onClick={stopScanning}
            size="large"
          >
            Остановить сканирование
          </Button>
        )}
        
        <Button onClick={onClose} variant="outlined" size="large">
          Отмена
        </Button>
      </Box>

      {scanning && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Наведите камеру на QR-код сертификата
        </Alert>
      )}
    </Box>
  );
}
