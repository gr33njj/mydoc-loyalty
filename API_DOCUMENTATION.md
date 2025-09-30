# 📚 API Документация - Моя ❤ скидка

## Базовый URL

```
Production: https://it-mydoc.ru/api
Development: http://localhost:8000/api
```

## Авторизация

Все защищенные endpoints требуют JWT токен в заголовке:

```
Authorization: Bearer <access_token>
```

---

## 🔐 Авторизация

### POST /auth/register

Регистрация нового пользователя

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "full_name": "Иванов Иван Иванович",
  "phone": "+79991234567",
  "password": "secure_password"
}
```

**Ответ (201):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Иванов Иван Иванович",
    "phone": "+79991234567",
    "role": "patient",
    "is_active": true,
    "created_at": "2025-09-30T12:00:00Z"
  }
}
```

### POST /auth/login

Вход в систему

**Тело запроса (Form Data):**
```
username=user@example.com
password=secure_password
```

**Ответ (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": { ... }
}
```

### POST /auth/refresh

Обновление access токена

**Параметры:**
- `refresh_token` (query) - Refresh token

**Ответ (200):**
```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer"
}
```

### GET /auth/me

Получение данных текущего пользователя

**Заголовки:** `Authorization: Bearer <token>`

**Ответ (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Иванов Иван",
  "role": "patient",
  ...
}
```

---

## 💳 Программа лояльности

### GET /loyalty/balance

Получение баланса текущего пользователя

**Ответ (200):**
```json
{
  "points_balance": 1250.0,
  "cashback_balance": 350.50,
  "card_tier": "gold",
  "transactions_count": 42
}
```

### GET /loyalty/transactions

История транзакций

**Параметры:**
- `page` (query, default: 1) - Номер страницы
- `page_size` (query, default: 20) - Размер страницы

**Ответ (200):**
```json
{
  "transactions": [
    {
      "id": 123,
      "account_id": 1,
      "transaction_type": "accrual",
      "amount": 100.0,
      "currency": "points",
      "source": "visit",
      "description": "Начисление за визит",
      "created_at": "2025-09-30T10:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

### POST /loyalty/accrue

Начисление баллов (только admin/cashier)

**Тело запроса:**
```json
{
  "account_id": 1,
  "transaction_type": "accrual",
  "amount": 100.0,
  "currency": "points",
  "source": "visit",
  "source_id": "DOC-12345",
  "description": "Начисление за визит",
  "idempotency_key": "unique-key-123"
}
```

**Ответ (201):**
```json
{
  "id": 124,
  "account_id": 1,
  "amount": 100.0,
  ...
}
```

### POST /loyalty/deduct

Списание баллов (только admin/cashier)

Аналогично `/loyalty/accrue`

---

## 🎁 Подарочные сертификаты

### POST /certificates/create

Создание сертификата (только admin/cashier)

**Тело запроса:**
```json
{
  "initial_amount": 5000.0,
  "valid_until": "2026-12-31T23:59:59Z",
  "owner_id": 1,
  "message": "С днем рождения!",
  "design_template": "birthday"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "code": "CERT-A1B2C3D4E5F6G7H8",
  "initial_amount": 5000.0,
  "current_amount": 5000.0,
  "status": "active",
  "owner_id": 1,
  "qr_code_url": "https://it-mydoc.ru/qrcodes/CERT-A1B2C3D4E5F6G7H8.png",
  "issued_at": "2025-09-30T12:00:00Z",
  "valid_until": "2026-12-31T23:59:59Z"
}
```

### GET /certificates/{certificate_id}

Получение информации о сертификате

**Ответ (200):**
```json
{
  "id": 1,
  "code": "CERT-...",
  "initial_amount": 5000.0,
  "current_amount": 3500.0,
  "status": "active",
  ...
}
```

### POST /certificates/transfer

Передача сертификата

**Тело запроса:**
```json
{
  "certificate_id": 1,
  "to_user_email": "friend@example.com",
  "message": "Это для тебя!"
}
```

**Ответ (200):**
```json
{
  "message": "Сертификат успешно передан",
  "recipient_email": "friend@example.com"
}
```

### POST /certificates/verify

Проверка действительности сертификата (публичный)

**Тело запроса:**
```json
{
  "code": "CERT-A1B2C3D4E5F6G7H8"
}
```

**Ответ (200):**
```json
{
  "valid": true,
  "certificate": { ... },
  "message": "Сертификат действителен. Доступно: 3500 руб."
}
```

### POST /certificates/redeem

Использование сертификата (только admin/cashier)

**Тело запроса:**
```json
{
  "code": "CERT-A1B2C3D4E5F6G7H8",
  "amount": 1500.0,
  "cashier_id": 2,
  "onec_document_id": "DOC-12345",
  "notes": "Оплата консультации"
}
```

**Ответ (200):**
```json
{
  "success": true,
  "certificate_id": 1,
  "amount_used": 1500.0,
  "remaining_amount": 2000.0,
  "message": "Сертификат успешно использован"
}
```

---

## 👥 Реферальная программа

### POST /referrals/create-code

Создание реферального кода

**Тело запроса:**
```json
{
  "user_id": 1,
  "referrer_type": "patient"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "code": "REF-ABC12345",
  "referrer_type": "patient",
  "total_referrals": 0,
  "successful_referrals": 0,
  "is_active": true
}
```

### GET /referrals/my-code

Получение своего реферального кода

**Ответ (200):**
```json
{
  "id": 1,
  "code": "REF-ABC12345",
  "total_referrals": 5,
  "successful_referrals": 3,
  "total_revenue": 15000.0
}
```

### POST /referrals/register-event

Регистрация реферального события (только admin/cashier)

**Тело запроса:**
```json
{
  "referral_code": "REF-ABC12345",
  "referred_user_id": 10,
  "event_type": "first_visit",
  "transaction_amount": 3000.0,
  "onec_document_id": "DOC-67890"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "referral_code_id": 1,
  "referred_user_id": 10,
  "event_type": "first_visit",
  "processed": true,
  "occurred_at": "2025-09-30T14:00:00Z"
}
```

### GET /referrals/stats

Статистика по рефералам

**Ответ (200):**
```json
{
  "total_referrals": 5,
  "successful_referrals": 3,
  "pending_referrals": 2,
  "total_revenue": 15000.0,
  "total_rewards": 1500.0,
  "conversion_rate": 60.0,
  "referral_code": "REF-ABC12345"
}
```

### GET /referrals/rewards

История вознаграждений

**Ответ (200):**
```json
[
  {
    "id": 1,
    "event_id": 1,
    "recipient_user_id": 1,
    "reward_type": "points",
    "reward_amount": 500.0,
    "awarded_at": "2025-09-30T14:00:00Z"
  }
]
```

---

## 🛡️ Администрирование

### GET /admin/dashboard

Статистика дашборда (только admin)

**Ответ (200):**
```json
{
  "total_users": 1250,
  "active_certificates": 45,
  "total_certificates_value": 225000.0,
  "total_loyalty_points": 500000.0,
  "total_loyalty_cashback": 75000.0,
  "active_referral_codes": 320,
  "today_transactions": 87
}
```

### GET /admin/users

Список пользователей (только admin)

**Параметры:**
- `page` (query)
- `page_size` (query)
- `role` (query) - Фильтр по роли

**Ответ (200):**
```json
{
  "users": [ ... ],
  "total": 1250,
  "page": 1,
  "page_size": 20
}
```

### GET /admin/certificates

Список сертификатов (только admin)

Аналогично `/admin/users`

### GET /admin/audit-log

Журнал аудита (только admin)

**Параметры:**
- `page`, `page_size`
- `entity_type` - Тип сущности
- `action` - Действие
- `user_id` - ID пользователя

---

## 🔌 Интеграции

### POST /integrations/1c/visit

Webhook от 1С о визите пациента

**Заголовки:** `X-Webhook-Token: your_token`

**Тело запроса:**
```json
{
  "document_id": "DOC-12345",
  "patient_external_id": "1C-PATIENT-001",
  "visit_date": "2025-09-30T10:00:00Z",
  "total_amount": 3000.0,
  "services": [...],
  "points_to_accrue": 150.0,
  "cashback_to_accrue": 90.0
}
```

### POST /integrations/bitrix/contact

Webhook от Bitrix о контакте

**Заголовки:** `X-Webhook-Token: your_token`

**Тело запроса:**
```json
{
  "contact_id": "123",
  "email": "user@example.com",
  "phone": "+79991234567",
  "name": "Иван",
  "last_name": "Иванов"
}
```

---

## Коды ошибок

- `200` - OK
- `201` - Created
- `400` - Bad Request (неверные данные)
- `401` - Unauthorized (не авторизован)
- `403` - Forbidden (недостаточно прав)
- `404` - Not Found (не найдено)
- `500` - Internal Server Error

## Rate Limiting

- Обычные API endpoints: 10 запросов/секунду
- Авторизация: 5 запросов/минуту

## Интерактивная документация

- Swagger UI: https://it-mydoc.ru/api/docs
- ReDoc: https://it-mydoc.ru/api/redoc
