# Интеграция SSO с Bitrix CMS

## Обзор

Интеграция системы лояльности с личным кабинетом Bitrix на сайте https://mydoctorarmavir.ru

## Варианты интеграции

### Вариант 1: OAuth 2.0 через Bitrix REST API (Рекомендуется)

**Преимущества:**
- ✅ Стандартный протокол
- ✅ Высокая безопасность
- ✅ Нативная поддержка в Bitrix
- ✅ Refresh токены

**Схема:**
```
1. Пользователь заходит на mydoctorarmavir.ru → авторизуется в Bitrix
2. Bitrix редиректит на it-mydoc.ru с authorization_code
3. Наш микросервис обменивает code на access_token
4. Получаем данные пользователя из Bitrix REST API
5. Создаем/находим пользователя в нашей БД
6. Выдаем JWT токен для микросервиса
```

### Вариант 2: Webhook от Bitrix (Простой способ)

**Преимущества:**
- ✅ Простая реализация
- ✅ Не требует изменений в Bitrix (только настройка)
- ✅ Работает через API

**Схема:**
```
1. Пользователь авторизуется в Bitrix
2. Bitrix отправляет webhook на наш endpoint с данными пользователя
3. Мы создаем JWT токен и редиректим пользователя в ЛК
```

### Вариант 3: Единая сессия через Cookie (Быстрый способ)

**Преимущества:**
- ✅ Мгновенная авторизация
- ✅ Не требует дополнительных кликов
- ✅ Прозрачно для пользователя

**Схема:**
```
1. Пользователь авторизован в Bitrix (mydoctorarmavir.ru)
2. На странице ЛК добавляем iframe/скрипт, который вызывает наш endpoint
3. Endpoint проверяет сессию Bitrix через REST API
4. Создаем JWT токен и сохраняем в localStorage
```

---

## Рекомендуемая реализация: OAuth 2.0

### 1. Настройка в Bitrix

#### Создание OAuth приложения в Bitrix:

1. Войдите в админ-панель Bitrix: https://mydoctorarmavir.ru/bitrix/admin/
2. Перейдите в **Настройки** → **Настройки продукта** → **OAuth-приложения**
3. Создайте новое приложение:
   - **Название**: Система лояльности MyDoc
   - **Redirect URI**: `https://it-mydoc.ru/auth/bitrix/callback`
   - **Права**: `user` (чтение профиля пользователя)

4. Сохраните:
   - `CLIENT_ID`
   - `CLIENT_SECRET`

#### Добавление ссылки в личный кабинет Bitrix:

В шаблоне личного кабинета (`/local/templates/your_template/header.php`):

```php
<?php
// Кнопка "Моя ❤ скидка" в меню личного кабинета
?>
<a href="https://it-mydoc.ru/auth/bitrix/login" class="loyalty-link">
    <span class="icon">❤️</span> Моя скидка
</a>
```

### 2. Backend: Новые endpoints для SSO

Создаем файл `backend/routers/bitrix_sso.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
from datetime import datetime, timedelta

from database import get_db
from models import User
from routers.auth import create_access_token, get_password_hash
from config import settings

router = APIRouter(prefix="/auth/bitrix", tags=["Bitrix SSO"])

# Конфигурация Bitrix OAuth
BITRIX_DOMAIN = "https://mydoctorarmavir.ru"
BITRIX_CLIENT_ID = settings.bitrix_client_id  # Из .env
BITRIX_CLIENT_SECRET = settings.bitrix_client_secret  # Из .env
BITRIX_REDIRECT_URI = "https://it-mydoc.ru/auth/bitrix/callback"

# Временное хранилище для state (в продакшене использовать Redis)
oauth_states = {}


@router.get("/login")
async def bitrix_login():
    """Редирект на авторизацию Bitrix"""
    
    # Генерируем уникальный state для защиты от CSRF
    state = secrets.token_urlsafe(32)
    oauth_states[state] = datetime.utcnow()
    
    # URL авторизации Bitrix
    auth_url = (
        f"{BITRIX_DOMAIN}/oauth/authorize/"
        f"?client_id={BITRIX_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={BITRIX_REDIRECT_URI}"
        f"&state={state}"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def bitrix_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Обработка callback от Bitrix OAuth"""
    
    # Проверяем state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Удаляем использованный state
    del oauth_states[state]
    
    # Обмениваем code на access_token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            f"{BITRIX_DOMAIN}/oauth/token/",
            data={
                "grant_type": "authorization_code",
                "client_id": BITRIX_CLIENT_ID,
                "client_secret": BITRIX_CLIENT_SECRET,
                "code": code,
                "redirect_uri": BITRIX_REDIRECT_URI,
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        token_data = token_response.json()
        access_token = token_data["access_token"]
        
        # Получаем данные пользователя из Bitrix
        user_response = await client.get(
            f"{BITRIX_DOMAIN}/rest/user.current.json",
            params={"auth": access_token}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )
        
        bitrix_user = user_response.json()["result"]
    
    # Ищем или создаем пользователя в нашей БД
    user = db.query(User).filter(
        User.email == bitrix_user["EMAIL"]
    ).first()
    
    if not user:
        # Создаем нового пользователя
        user = User(
            email=bitrix_user["EMAIL"],
            full_name=f'{bitrix_user.get("NAME", "")} {bitrix_user.get("LAST_NAME", "")}'.strip(),
            phone=bitrix_user.get("PERSONAL_PHONE", ""),
            password_hash=get_password_hash(secrets.token_urlsafe(32)),  # Случайный пароль
            role="patient",
            bitrix_id=bitrix_user["ID"]  # Добавим поле bitrix_id в модель
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Создаем JWT токен для нашего микросервиса
    jwt_token = create_access_token(data={"sub": str(user.id)})
    
    # Редиректим в ЛК с токеном
    redirect_url = f"https://it-mydoc.ru/?token={jwt_token}"
    
    return RedirectResponse(url=redirect_url)


@router.post("/webhook")
async def bitrix_webhook(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """Webhook для получения данных пользователя из Bitrix"""
    
    # Проверяем подпись запроса (опционально)
    # signature = request.headers.get("X-Bitrix-Signature")
    # verify_signature(signature, user_data)
    
    email = user_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Ищем или создаем пользователя
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        user = User(
            email=email,
            full_name=user_data.get("full_name", ""),
            phone=user_data.get("phone", ""),
            password_hash=get_password_hash(secrets.token_urlsafe(32)),
            role="patient",
            bitrix_id=user_data.get("bitrix_id")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Создаем JWT токен
    jwt_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "success": True,
        "token": jwt_token,
        "user_id": user.id
    }
```

### 3. Обновление модели User

Добавляем поле `bitrix_id` в `backend/models.py`:

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)
    bitrix_id = Column(String, unique=True, index=True, nullable=True)  # НОВОЕ!
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 4. Обновление конфигурации

Добавляем в `backend/config.py`:

```python
class Settings(BaseSettings):
    # ... существующие настройки ...
    
    # Bitrix OAuth
    bitrix_client_id: str
    bitrix_client_secret: str
    
    class Config:
        env_file = ".env"
```

Добавляем в `.env`:

```env
BITRIX_CLIENT_ID=your_client_id_from_bitrix
BITRIX_CLIENT_SECRET=your_client_secret_from_bitrix
```

### 5. Регистрация роутера

В `backend/main.py`:

```python
from routers import loyalty, certificates, referrals, auth, admin, integrations, bitrix_sso

# ...

app.include_router(bitrix_sso.router)
```

### 6. Frontend: Обработка SSO токена

Обновляем `frontend/src/context/AuthContext.js`:

```javascript
useEffect(() => {
  // Проверяем токен из URL (SSO редирект)
  const urlParams = new URLSearchParams(window.location.search);
  const ssoToken = urlParams.get('token');
  
  if (ssoToken) {
    // Сохраняем токен
    localStorage.setItem('token', ssoToken);
    setToken(ssoToken);
    
    // Очищаем URL от токена
    window.history.replaceState({}, document.title, '/');
    
    // Загружаем данные пользователя
    fetchCurrentUser();
  } else {
    // Обычная проверка токена
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      fetchCurrentUser();
    }
  }
}, []);
```

---

## Миграция БД

Создаем миграцию для добавления `bitrix_id`:

```bash
cd /tmp/mydoc-loyalty/backend
alembic revision -m "add bitrix_id to users"
```

В созданном файле миграции:

```python
def upgrade():
    op.add_column('users', sa.Column('bitrix_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_bitrix_id'), 'users', ['bitrix_id'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_users_bitrix_id'), table_name='users')
    op.drop_column('users', 'bitrix_id')
```

Применяем миграцию:

```bash
docker exec -it mydoc_backend alembic upgrade head
```

---

## Схема интеграции (Итоговая)

```
┌─────────────────────────────────────────────────────────────┐
│                  mydoctorarmavir.ru                         │
│                    (Bitrix CMS)                             │
│                                                             │
│  Личный кабинет пациента                                   │
│  ┌──────────────────────────────────────────┐              │
│  │  👤 Иван Иванов                          │              │
│  │  📧 ivan@example.com                     │              │
│  │                                          │              │
│  │  [❤️ Моя скидка] ← Ссылка на SSO        │              │
│  └──────────────────────────────────────────┘              │
│                      ↓ (клик)                               │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         it-mydoc.ru/auth/bitrix/login                       │
│         (Наш микросервис)                                   │
│                                                             │
│  Генерирует state и редиректит на Bitrix OAuth             │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│    mydoctorarmavir.ru/oauth/authorize                       │
│                                                             │
│  Пользователь уже авторизован → автоматически              │
│  редиректит с authorization_code                           │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│    it-mydoc.ru/auth/bitrix/callback?code=XXX&state=YYY      │
│                                                             │
│  1. Проверяет state                                         │
│  2. Обменивает code на access_token                         │
│  3. Получает данные пользователя из Bitrix REST API         │
│  4. Создает/находит пользователя в БД                       │
│  5. Генерирует JWT токен                                    │
│  6. Редиректит в ЛК: it-mydoc.ru/?token=JWT_TOKEN          │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              it-mydoc.ru (Личный кабинет)                   │
│                                                             │
│  1. Извлекает токен из URL                                  │
│  2. Сохраняет в localStorage                                │
│  3. Загружает данные пользователя                           │
│  4. Показывает дашборд с бонусами и сертификатами          │
└─────────────────────────────────────────────────────────────┘
```

---

## Тестирование

### 1. Локальное тестирование (через ngrok):

```bash
# Запускаем ngrok для локальной разработки
ngrok http 8000

# Используем URL из ngrok как redirect_uri в настройках Bitrix
```

### 2. Проверка интеграции:

1. Зайдите на https://mydoctorarmavir.ru
2. Авторизуйтесь в личном кабинете
3. Нажмите "Моя ❤ скидка"
4. Должно перенаправить на it-mydoc.ru с автоматической авторизацией

---

## Дополнительная безопасность

### 1. PKCE (для мобильных приложений):

```python
import hashlib
import base64

# Генерация code_verifier и code_challenge
code_verifier = secrets.token_urlsafe(32)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')
```

### 2. Проверка подписи webhook:

```python
import hmac

def verify_bitrix_signature(signature: str, data: dict, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

---

## Преимущества реализации

✅ **Единая авторизация** - пользователь авторизуется один раз  
✅ **Безопасность** - используется стандартный OAuth 2.0  
✅ **Автоматическая синхронизация** - данные пользователя из Bitrix  
✅ **Прозрачность** - пользователь не замечает перехода между системами  
✅ **Масштабируемость** - легко добавить другие сервисы  

---

## Следующие шаги

1. Получите `CLIENT_ID` и `CLIENT_SECRET` из Bitrix
2. Создайте файл `backend/routers/bitrix_sso.py`
3. Добавьте поле `bitrix_id` в модель User
4. Примените миграцию БД
5. Добавьте обработку токена из URL во frontend
6. Настройте кнопку в личном кабинете Bitrix

Готово к внедрению! 🚀

