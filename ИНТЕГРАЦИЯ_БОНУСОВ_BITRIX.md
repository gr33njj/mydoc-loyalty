# 🎁 Интеграция бонусов из Bitrix в "Моя ❤ скидка"

## 📋 Обзор

Эта инструкция описывает интеграцию баланса бонусов из личного кабинета Bitrix (`https://mydoctorarmavir.ru/personal/bonuses/`) в микросервис "Моя ❤ скидка".

## 🎯 Архитектура решения

```
┌──────────────────┐      API       ┌──────────────────┐
│                  │ ────────────>  │                  │
│  Моя ❤ скидка   │  GET bonuses   │  Bitrix CMS      │
│  (it-mydoc.ru)   │ <────────────  │ (mydoctorarmavir)│
│                  │   JSON         │                  │
└──────────────────┘                └──────────────────┘
```

**Преимущества:**
- ✅ Единый источник правды (Bitrix)
- ✅ Актуальные данные в реальном времени
- ✅ Нет необходимости в синхронизации
- ✅ Простая реализация

## 🚀 Шаг 1: Установка PHP API на Bitrix

### 1.1 Создайте файл на сервере Bitrix

**Путь:** `/local/api/get_bonuses.php`  
**URL:** `https://mydoctorarmavir.ru/local/api/get_bonuses.php`

Скопируйте содержимое из файла `bitrix_files/get_bonuses.php`:

```bash
# На сервере Bitrix:
cd /var/www/html/local/api/
nano get_bonuses.php
# Вставьте содержимое из bitrix_files/get_bonuses.php
chmod 644 get_bonuses.php
```

### 1.2 Поле с бонусами

**ДЛЯ ВАШЕГО ПРОЕКТА:** Используется поле `UF_USER__BONUSES_JSON`, которое содержит JSON с историей всех бонусных транзакций (начисления, списания, даты истечения).

API `get_bonuses.php` реплицирует логику из `/personal/bonuses/`:
- Парсит JSON из `UF_USER__BONUSES_JSON`
- Проходит по всем транзакциям (`Receipt` / `Expense`)
- Применяет логику FIFO для списаний
- Обрабатывает сгорания просроченных бонусов
- Возвращает итоговый баланс

**Важно:** Если в вашем Bitrix используется другое поле или логика, обновите `get_bonuses.php` соответственно.

### 1.3 Диагностический скрипт (опционально)

Для диагностики используйте `check_my_bonuses.php`:

```bash
# На сервере Bitrix:
cd /home/bitrix/www/local/api/
wget https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/check_my_bonuses.php

# Откройте в браузере:
https://mydoctorarmavir.ru/local/api/check_my_bonuses.php
```

Скрипт покажет:
- Текущего пользователя и его ID
- Наличие поля `UF_USER__BONUSES_JSON`
- Содержимое JSON с транзакциями
- Готовую команду `curl` для тестирования API

### 1.4 Обновите файл на сервере

Если вы уже установили `get_bonuses.php`, обновите его до последней версии с округлением:

```bash
cd /home/bitrix/www/local/api/ && \
wget -O get_bonuses.php https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/get_bonuses.php
```

### 1.5 Проверьте API

```bash
# Тест 1: Через curl
curl -X POST https://mydoctorarmavir.ru/local/api/get_bonuses.php \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# Ожидаемый ответ (с округлением до 2 знаков):
# {"success":true,"user_id":"1","bonus_balance":73.24}
```

```bash
# Тест 2: Через браузер
https://mydoctorarmavir.ru/local/api/get_bonuses.php?user_id=1
```

---

## 🔧 Шаг 2: Обновление Backend микросервиса

### 2.1 Перезапустите backend

```bash
cd /tmp/mydoc-loyalty
docker-compose restart backend
```

### 2.2 Проверьте новый endpoint

```bash
# Получите JWT токен (авторизуйтесь через SSO)
# Затем проверьте endpoint:

curl -X GET https://it-mydoc.ru/api/auth/bitrix/bonus-balance \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Ожидаемый ответ:
# {
#   "success": true,
#   "bonus_balance": 150,
#   "source": "bitrix"
# }
```

---

## 🎨 Шаг 3: Обновление Frontend

### 3.1 Перезапустите frontend

```bash
cd /tmp/mydoc-loyalty
docker-compose restart frontend
```

**Что изменилось:**
- `Dashboard.js` теперь запрашивает баланс из `/auth/bitrix/bonus-balance`
- `Loyalty.js` также интегрирован с Bitrix API
- Если пользователь привязан к Bitrix (есть `bitrix_id`), отображается баланс из Bitrix
- Если пользователь не привязан, отображается локальный баланс из `/loyalty/balance`
- Баланс отображается с округлением до 2 знаков: `73.24`

### 3.2 Проверьте UI

После перезапуска откройте:
- **Главная страница:** https://it-mydoc.ru/ - должна показать бонусный баланс из Bitrix
- **Страница "Бонусы":** https://it-mydoc.ru/loyalty - должна показать "Баланс из личного кабинета Мой Доктор"

---

## 🧪 Тестирование

### 1. Проверьте API Bitrix

```bash
curl -X POST https://mydoctorarmavir.ru/local/api/get_bonuses.php \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

**Ожидаемый результат:**
```json
{
  "success": true,
  "user_id": "1",
  "bonus_balance": 150
}
```

**Примечание:** 
- `bonus_balance` - это количество бонусных баллов (без валюты).
- Баланс рассчитывается с учетом всех начислений, списаний и сгораний по **той же логике**, что используется на странице `/personal/bonuses/`.
- **Логика FIFO:** При списании баллы списываются с самых старых начислений (First-In, First-Out).
- **Автоматическое сгорание:** Просроченные бонусы автоматически сгорают при расчете баланса.
- **Округление:** Баланс округляется до 2 знаков после запятой (`73.24000000000001` → `73.24`).

### 2. Проверьте микросервис

1. Авторизуйтесь через SSO: https://it-mydoc.ru/login
2. Откройте главную страницу
3. **Проверьте Console (F12):**
   ```javascript
   // Должны увидеть логи:
   📥 Получение баланса бонусов из Bitrix...
   ✅ Баланс: 150.50 ₽
   ```

4. **Проверьте Network (F12):**
   - Найдите запрос: `GET /api/auth/bitrix/bonus-balance`
   - Статус: `200 OK`
   - Response: `{"success":true,"bonus_balance":150.50,...}`

### 3. Проверьте логи backend

```bash
docker-compose logs backend 2>&1 | grep -E "(💰|📥|✅)" | tail -20
```

**Должны увидеть:**
```
💰 Запрос баланса бонусов для пользователя: bitrix_id=1
📥 Ответ Bitrix: {'success': True, 'bonus_balance': 150.5, ...}
✅ Баланс бонусов получен: 150.5 руб.
```

---

## 📊 Варианты отображения баланса

### Вариант 1: Только Bitrix (Рекомендуемый)
```
┌──────────────────────────────┐
│  Бонусные баллы              │
│  150.50 ₽                    │
│  из личного кабинета         │
└──────────────────────────────┘
```

### Вариант 2: Bitrix + Локальный баланс
```
┌──────────────────────────────┐
│  Бонусные баллы              │
│  📍 Bitrix: 150.50 ₽         │
│  💳 Локально: 50.00 баллов   │
│  ──────────────────────────  │
│  Итого: 200.50               │
└──────────────────────────────┘
```

### Вариант 3: С кнопкой обновления
```
┌──────────────────────────────┐
│  Бонусные баллы       🔄     │
│  150.50 ₽                    │
│  Обновлено: 10:30            │
└──────────────────────────────┘
```

---

## 🔒 Безопасность

### CORS настройки

В `get_bonuses.php` уже настроены CORS:
```php
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
```

### Аутентификация

API использует `bitrix_id` пользователя, который получен через SSO, поэтому дополнительная аутентификация не требуется.

**Однако для повышения безопасности можно добавить:**

```php
// В get_bonuses.php добавьте проверку токена:
$token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
if (empty($token) || !preg_match('/Bearer\s(\S+)/', $token, $matches)) {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'Unauthorized']);
    exit;
}

// Проверьте токен (опционально)
```

---

## 🚨 Troubleshooting

### Проблема: `{"success":false,"bonus_balance":0}`

**Причина:** Неправильное название поля с бонусами.

**Решение:**
1. Проверьте БД Bitrix:
   ```sql
   SHOW COLUMNS FROM b_user LIKE 'UF_%';
   ```
2. Найдите поле с бонусами
3. Обновите `get_bonuses.php`

---

### Проблема: CORS ошибка

**Причина:** Неправильные CORS заголовки.

**Решение:** Убедитесь что в `get_bonuses.php`:
```php
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
```

---

### Проблема: Битрикс возвращает `"bonus_balance":0` для всех

**Причина:** Бонусы хранятся не в пользовательских полях.

**Решение:** Раскомментируйте блок с модулем Sale в `get_bonuses.php`:
```php
$accounts = \Bitrix\Sale\Internals\UserAccountTable::getList([
    'filter' => ['USER_ID' => $userId, 'CURRENCY' => 'RUB']
])->fetch();
```

---

## 📝 Дополнительные возможности

### 1. Кэширование в Redis

Добавьте кэширование для уменьшения нагрузки на Bitrix:

```python
# В backend/routers/bitrix_sso.py
import redis

redis_client = redis.from_url(settings.REDIS_URL)

@router.get("/bonus-balance")
async def get_bitrix_bonus_balance(...):
    # Проверяем кэш
    cache_key = f"bitrix:bonus:{current_user.bitrix_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Получаем из Bitrix...
    result = {...}
    
    # Кэшируем на 5 минут
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
```

### 2. Webhook при изменении баланса

Настройте в Bitrix отправку webhook при изменении баланса:

```php
// В обработчике изменения бонусов:
$ch = curl_init('https://it-mydoc.ru/api/integrations/bitrix-bonus-changed');
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
    'user_id' => $userId,
    'new_balance' => $newBalance
]));
curl_exec($ch);
```

### 3. История изменений баланса

Получайте историю транзакций из Bitrix:

```php
// /local/api/get_bonus_history.php
$history = \Bitrix\Sale\Internals\AccountTransactionTable::getList([
    'filter' => ['USER_ID' => $userId],
    'order' => ['TIMESTAMP_X' => 'DESC'],
    'limit' => 10
]);
```

---

## ✅ Checklist внедрения

- [ ] Создан файл `/local/api/get_bonuses.php` на Bitrix
- [ ] Определено правильное название поля с бонусами
- [ ] API протестирован через curl
- [ ] Backend микросервиса перезапущен
- [ ] Endpoint `/api/auth/bitrix/bonus-balance` работает
- [ ] Frontend обновлен (Dashboard + Loyalty)
- [ ] Тестирование пройдено
- [ ] CORS настроен правильно
- [ ] Логи показывают успешные запросы
- [ ] Баланс отображается корректно в UI

---

## 🎉 Результат

После внедрения:

✅ **Dashboard** показывает актуальный баланс из Bitrix  
✅ **Страница "Бонусы"** отображает данные из личного кабинета  
✅ **Автоматическое обновление** при каждой загрузке страницы  
✅ **Единый источник правды** - Bitrix  
✅ **Нет рассинхронизации** между системами  

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи backend: `docker-compose logs backend | tail -50`
2. Проверьте Console в браузере (F12)
3. Убедитесь что API Bitrix отвечает: `curl ...`
4. Проверьте название поля с бонусами в БД

