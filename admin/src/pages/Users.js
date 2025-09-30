import React from 'react';
import { Container, Typography } from '@mui/material';

export default function Users() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Управление пользователями
      </Typography>
      <Typography color="text.secondary">
        Здесь будет список пользователей системы
      </Typography>
    </Container>
  );
}
