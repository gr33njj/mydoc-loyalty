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

### 1.2 Определите название поля с бонусами

**ВАЖНО!** Вам нужно узнать, в каком поле Bitrix хранит баланс бонусов:

1. **Откройте БД Bitrix:**
   ```sql
   SELECT * FROM b_user WHERE ID = 1;
   ```

2. **Найдите поле с бонусами:**
   Возможные варианты:
   - `UF_BONUS_BALANCE`
   - `UF_BONUS_POINTS`
   - `UF_LOYALTY_BALANCE`
   - `UF_BONUSES`

3. **Обновите `get_bonuses.php`:**
   Замените в коде:
   ```php
   if (isset($user['UF_BONUS_BALANCE'])) {  // ← Укажите правильное название!
       $bonusBalance = floatval($user['UF_BONUS_BALANCE']);
   }
   ```

### 1.3 Альтернатива: Бонусы в модуле Sale

Если бонусы хранятся в модуле Sale (счет покупателя), раскомментируйте в `get_bonuses.php`:

```php
$accounts = \Bitrix\Sale\Internals\UserAccountTable::getList([
    'filter' => [
        'USER_ID' => $userId,
        'CURRENCY' => 'RUB'
    ]
])->fetch();

if ($accounts) {
    $bonusBalance = floatval($accounts['CURRENT_BUDGET']);
}
```

### 1.4 Проверьте API

```bash
# Тест 1: Через curl
curl -X POST https://mydoctorarmavir.ru/local/api/get_bonuses.php \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# Ожидаемый ответ:
# {"success":true,"user_id":"1","bonus_balance":150.50,"currency":"RUB"}
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
#   "bonus_balance": 150.50,
#   "currency": "RUB",
#   "source": "bitrix"
# }
```

---

## 🎨 Шаг 3: Обновление Frontend

### 3.1 Модифицируйте Dashboard

Откройте `frontend/src/pages/Dashboard.js` и добавьте запрос баланса из Bitrix:

```javascript
const [bitrixBalance, setBitrixBalance] = useState(null);
const [loadingBitrix, setLoadingBitrix] = useState(true);

useEffect(() => {
  const fetchBitrixBalance = async () => {
    try {
      const response = await axios.get('/auth/bitrix/bonus-balance');
      if (response.data.success) {
        setBitrixBalance(response.data.bonus_balance);
      }
    } catch (error) {
      console.error('Ошибка получения баланса из Bitrix:', error);
    } finally {
      setLoadingBitrix(false);
    }
  };

  fetchBitrixBalance();
}, []);
```

### 3.2 Отобразите баланс из Bitrix

```javascript
<Card>
  <CardContent>
    <Box display="flex" alignItems="center" mb={2}>
      <AccountBalanceWalletIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
      <Box>
        <Typography variant="h6" color="text.secondary">
          Бонусные баллы
        </Typography>
        <Typography variant="h4" fontWeight="bold" color="primary.main">
          {loadingBitrix ? (
            <CircularProgress size={24} />
          ) : (
            `${bitrixBalance?.toFixed(2) || '0.00'} ₽`
          )}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          из личного кабинета Мой Доктор
        </Typography>
      </Box>
    </Box>
  </CardContent>
</Card>
```

### 3.3 Модифицируйте страницу Loyalty

Аналогично обновите `frontend/src/pages/Loyalty.js`:

```javascript
// В компоненте fetchLoyaltyData:
const bitrixResponse = await axios.get('/auth/bitrix/bonus-balance');
if (bitrixResponse.data.success) {
  setLoyaltyData(prev => ({
    ...prev,
    balance: bitrixResponse.data.bonus_balance,
    source: 'bitrix'
  }));
}
```

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
  "bonus_balance": 150.50,
  "currency": "RUB"
}
```

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

