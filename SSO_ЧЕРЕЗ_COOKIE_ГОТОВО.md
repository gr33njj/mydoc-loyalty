# 🍪 SSO через Cookie/Session - Готовая реализация

## 🎯 Как это работает

1. Пользователь авторизован в Bitrix → нажимает "Моя скидка"
2. JavaScript запрашивает токен у Bitrix
3. Bitrix проверяет сессию и возвращает временный токен (1 минута)
4. Frontend отправляет токен на наш backend
5. Backend проверяет токен, создает пользователя, выдает JWT
6. Пользователь авторизован! ✅

**Преимущества:**
- ✅ Не нужен OAuth
- ✅ Не нужны вебхуки
- ✅ Работает в любой версии Bitrix
- ✅ Настройка за 10 минут

---

## ШАГ 1: Создайте файл на сервере Bitrix

На вашем сервере Bitrix создайте файл:

**Путь:** `/local/api/loyalty_token.php`

```php
<?php
// Разрешаем запросы с нашего домена
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

// Обработка preflight запроса
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

global $USER;

// Проверяем авторизацию
if (!$USER->IsAuthorized()) {
    echo json_encode([
        'success' => false,
        'error' => 'User not authorized'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Получаем данные пользователя
$userId = $USER->GetID();
$userEmail = $USER->GetEmail();
$userName = $USER->GetFirstName();
$userLastName = $USER->GetLastName();
$userLogin = $USER->GetLogin();

// Генерируем одноразовый токен (действует 2 минуты)
$token = md5($userId . time() . 'mydoc_loyalty_secret_2025');

// Сохраняем данные в сессию Bitrix
$_SESSION['LOYALTY_TOKEN_' . $token] = [
    'user_id' => $userId,
    'email' => $userEmail ?: $userLogin . '@mydoc.local',
    'name' => $userName,
    'last_name' => $userLastName,
    'created_at' => time(),
    'expires_at' => time() + 120 // 2 минуты
];

// Возвращаем токен
echo json_encode([
    'success' => true,
    'token' => $token,
    'user_id' => $userId,
    'email' => $userEmail ?: $userLogin . '@mydoc.local'
], JSON_UNESCAPED_UNICODE);
?>
```

**Создайте директорию, если её нет:**
```bash
# На сервере Bitrix:
mkdir -p /path/to/bitrix/local/api
```

---

## ШАГ 2: Создайте файл проверки токена

**Путь:** `/local/api/verify_token.php`

```php
<?php
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require($_SERVER["DOCUMENT_ROOT"] . "/bitrix/modules/main/include/prolog_before.php");

// Получаем токен из POST
$input = json_decode(file_get_contents('php://input'), true);
$token = $input['token'] ?? '';

if (empty($token)) {
    echo json_encode(['success' => false, 'error' => 'Token required'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Проверяем токен в сессии
$sessionKey = 'LOYALTY_TOKEN_' . $token;

if (!isset($_SESSION[$sessionKey])) {
    echo json_encode(['success' => false, 'error' => 'Invalid token'], JSON_UNESCAPED_UNICODE);
    exit;
}

$tokenData = $_SESSION[$sessionKey];

// Проверяем срок действия
if ($tokenData['expires_at'] < time()) {
    unset($_SESSION[$sessionKey]);
    echo json_encode(['success' => false, 'error' => 'Token expired'], JSON_UNESCAPED_UNICODE);
    exit;
}

// Удаляем использованный токен (одноразовый)
unset($_SESSION[$sessionKey]);

// Возвращаем данные пользователя
echo json_encode([
    'success' => true,
    'user' => [
        'bitrix_id' => $tokenData['user_id'],
        'email' => $tokenData['email'],
        'name' => $tokenData['name'],
        'last_name' => $tokenData['last_name']
    ]
], JSON_UNESCAPED_UNICODE);
?>
```

---

## ШАГ 3: Обновите Backend

### 📄 `backend/config.py`

Добавьте:
```python
class Settings(BaseSettings):
    # ... существующие настройки ...
    
    # Bitrix Cookie SSO
    bitrix_domain: str = "https://mydoctorarmavir.ru"
    base_url: str = "https://it-mydoc.ru"
    
    model_config = SettingsConfigDict(env_file=".env")
```

### 📄 `backend/.env`

Добавьте:
```env
BITRIX_DOMAIN=https://mydoctorarmavir.ru
BASE_URL=https://it-mydoc.ru
```

### 📄 `backend/routers/bitrix_sso.py`

Создайте или замените:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import secrets

from database import get_db
from config import settings
from models import User
from routers.auth import create_access_token, get_password_hash

router = APIRouter()

class TokenVerifyRequest(BaseModel):
    token: str

@router.post("/verify-token")
async def verify_bitrix_token(
    request: TokenVerifyRequest,
    db: Session = Depends(get_db)
):
    """Проверяет токен от Bitrix и авторизует пользователя"""
    
    try:
        # Проверяем токен у Bitrix
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.bitrix_domain}/local/api/verify_token.php",
                json={"token": request.token},
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('error', 'Invalid token')
            )
        
        user_data = result['user']
        bitrix_id = str(user_data['bitrix_id'])
        email = user_data['email']
        
        # Ищем или создаем пользователя
        user = db.query(User).filter(User.bitrix_id == bitrix_id).first()
        
        if not user:
            # Проверяем по email
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Привязываем существующего пользователя
                user.bitrix_id = bitrix_id
            else:
                # Создаем нового пользователя
                user = User(
                    email=email,
                    hashed_password=get_password_hash(secrets.token_urlsafe(16)),
                    bitrix_id=bitrix_id,
                    role="patient"
                )
            
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Генерируем JWT токен
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "success": True,
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка связи с Bitrix: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {str(e)}"
        )
```

### 📄 `backend/main.py`

Добавьте роутер (если ещё нет):

```python
from routers import bitrix_sso

app.include_router(bitrix_sso.router, prefix="/auth/bitrix", tags=["Bitrix SSO"])
```

---

## ШАГ 4: Обновите Frontend

### 📄 `frontend/src/pages/Login.js`

Замените функцию `handleBitrixLogin`:

```javascript
const handleBitrixLogin = async () => {
  try {
    setLoading(true);
    
    // 1. Запрашиваем токен у Bitrix
    const response = await fetch('https://mydoctorarmavir.ru/local/api/loyalty_token.php', {
      method: 'GET',
      credentials: 'include', // Важно! Отправляем cookies
      headers: {
        'Accept': 'application/json',
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Не удалось получить токен от Bitrix');
    }
    
    // 2. Проверяем токен на нашем backend
    const authResponse = await axios.post('/auth/bitrix/verify-token', {
      token: data.token
    });
    
    if (authResponse.data.success && authResponse.data.token) {
      // 3. Сохраняем JWT токен
      localStorage.setItem('token', authResponse.data.token);
      
      // 4. Перенаправляем в личный кабинет
      window.location.href = '/';
    } else {
      throw new Error('Не удалось авторизоваться');
    }
    
  } catch (error) {
    console.error('Ошибка SSO:', error);
    
    let errorMessage = 'Ошибка авторизации';
    
    if (error.message.includes('CORS')) {
      errorMessage = 'Пожалуйста, авторизуйтесь сначала на сайте клиники';
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    alert(errorMessage);
  } finally {
    setLoading(false);
  }
};
```

И обновите состояние loading:

```javascript
export default function Login() {
  const [loading, setLoading] = useState(false);

  const handleBitrixLogin = async () => {
    // ... код выше
  };

  return (
    // ... остальной код
    <Button
      fullWidth
      variant="contained"
      size="large"
      onClick={handleBitrixLogin}
      disabled={loading}
      startIcon={<LocalHospitalIcon />}
      sx={{ /* ... стили */ }}
    >
      {loading ? 'Авторизация...' : 'Войти через Мой Доктор'}
    </Button>
    // ...
  );
}
```

---

## ШАГ 5: Добавьте кнопку в Bitrix

В шаблоне личного кабинета Bitrix (например, `header.php`):

```html
<!-- Кнопка программы лояльности -->
<a href="https://it-mydoc.ru/login" 
   target="_blank"
   class="loyalty-btn"
   style="
     display: inline-flex;
     align-items: center;
     gap: 8px;
     padding: 12px 24px;
     background: linear-gradient(135deg, #004155 0%, #68cdd2 100%);
     color: white;
     text-decoration: none;
     border-radius: 12px;
     font-weight: 600;
     transition: all 0.3s ease;
   ">
   <span style="font-size: 1.2em;">❤️</span>
   Моя скидка
</a>

<style>
.loyalty-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 65, 85, 0.4);
}
</style>
```

---

## ШАГ 6: Примените изменения

### 6.1 Добавьте поле bitrix_id (если ещё нет)

```bash
cd /tmp/mydoc-loyalty

# Вариант 1: Через миграцию
docker-compose exec backend alembic revision -m "add bitrix_id to users"
# Отредактируйте файл миграции в backend/alembic/versions/
# Добавьте: op.add_column('users', sa.Column('bitrix_id', sa.String(), nullable=True))
docker-compose exec backend alembic upgrade head

# Вариант 2: Вручную в БД
docker-compose exec postgres psql -U postgres -d mydoc_loyalty -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS bitrix_id VARCHAR(255) UNIQUE;"
```

### 6.2 Пересоберите и перезапустите

```bash
cd /tmp/mydoc-loyalty

# Пересобрать frontend с обновленным Login.js
docker-compose stop frontend
docker-compose rm -f frontend
docker-compose up -d --build frontend

# Перезапустить backend
docker-compose restart backend

# Проверить статус
docker-compose ps
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Шаг 1: Проверьте файлы на Bitrix

Откройте в браузере:
```
https://mydoctorarmavir.ru/local/api/loyalty_token.php
```

**Должны увидеть:**
- Если авторизованы: `{"success":true,"token":"...","user_id":123,...}`
- Если нет: `{"success":false,"error":"User not authorized"}`

### Шаг 2: Проверьте авторизацию

1. **Авторизуйтесь в Bitrix:** `https://mydoctorarmavir.ru`
2. **Откройте систему лояльности:** `https://it-mydoc.ru/login`
3. **Нажмите:** "Войти через Мой Доктор"
4. **Результат:** Должны автоматически войти в ЛК! ✅

### Шаг 3: Проверьте БД

```bash
docker-compose exec postgres psql -U postgres -d mydoc_loyalty -c "SELECT id, email, bitrix_id FROM users WHERE bitrix_id IS NOT NULL;"
```

Должны увидеть пользователя с заполненным `bitrix_id`.

---

## 🔧 Устранение неполадок

### Ошибка CORS

**Симптом:** `Access to fetch has been blocked by CORS policy`

**Решение:** Проверьте заголовки в `loyalty_token.php`:
```php
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
```

### Ошибка "User not authorized"

**Причина:** Пользователь не авторизован в Bitrix

**Решение:**
1. Откройте `https://mydoctorarmavir.ru`
2. Авторизуйтесь
3. Затем откройте `https://it-mydoc.ru/login`

### Токен не проверяется

**Проверьте:**
```bash
# Логи backend
docker logs mydoc_backend --tail 50

# Проверьте .env
docker-compose exec backend env | grep BITRIX
```

### Файлы не создаются на Bitrix

**На сервере Bitrix:**
```bash
# Создайте директорию
mkdir -p /var/www/html/local/api

# Дайте права
chmod 755 /var/www/html/local/api
chmod 644 /var/www/html/local/api/*.php

# Проверьте владельца
chown www-data:www-data /var/www/html/local/api/*.php
```

---

## ✅ Проверочный чек-лист

Перед тестированием убедитесь:

- [ ] Созданы файлы на Bitrix:
  - [ ] `/local/api/loyalty_token.php`
  - [ ] `/local/api/verify_token.php`
- [ ] Файлы доступны по URL (проверить в браузере)
- [ ] Обновлен `backend/routers/bitrix_sso.py`
- [ ] Роутер подключен в `backend/main.py`
- [ ] Обновлен `frontend/src/pages/Login.js`
- [ ] Добавлено поле `bitrix_id` в БД
- [ ] Пересобран frontend
- [ ] Перезапущен backend
- [ ] Добавлена кнопка в личный кабинет Bitrix

---

## 🎉 Готово!

Теперь SSO работает через Cookie/Session:

1. Пользователь авторизован в Bitrix
2. Нажимает кнопку → автоматически входит в систему лояльности
3. Никаких OAuth, вебхуков, дополнительных настроек!

**Просто, быстро, работает!** ✅

---

## 📞 Поддержка

Если что-то не работает:
1. Проверьте файлы на Bitrix (откройте в браузере)
2. Посмотрите логи: `docker logs mydoc_backend`
3. Проверьте консоль браузера (F12)
4. Убедитесь, что авторизованы в Bitrix

