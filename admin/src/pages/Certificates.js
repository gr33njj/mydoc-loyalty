import React from 'react';
import { Container, Typography } from '@mui/material';

export default function Certificates() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Управление сертификатами
      </Typography>
      <Typography color="text.secondary">
        Здесь будет список и управление сертификатами
      </Typography>
    </Container>
  );
}
