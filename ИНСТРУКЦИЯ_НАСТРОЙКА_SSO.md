# 🚀 Пошаговая инструкция: Настройка SSO с Bitrix

## Что уже готово ✅

- ✅ Новая страница входа на `https://it-mydoc.ru/login`
- ✅ Страница обработки callback
- ✅ Frontend полностью готов

## Что нужно сделать ⚙️

Всего **3 шага** для запуска SSO:

---

## ШАГ 1: Настройка Bitrix CMS (15 минут)

### 1.1 Создайте OAuth-приложение в Bitrix

1. **Войдите в админ-панель Bitrix24:**
   - Откройте: `https://mydoctorarmavir.bitrix24.ru`
   - Зайдите под администратором

2. **Создайте приложение:**
   - Перейдите: **Настройки** → **Разработчикам** → **Другое** → **OAuth-приложения**
   - Или: **Приложения** → **Добавить приложение**

3. **Заполните данные приложения:**
   ```
   Название: Моя ❤ скидка (Программа лояльности)
   Redirect URI: https://it-mydoc.ru/auth/bitrix/callback
   Права доступа (scopes): user, profile
   ```

4. **Сохраните и получите:**
   - `CLIENT_ID` - например: `local.67a1f2b3c4d5e6`
   - `CLIENT_SECRET` - например: `K8xY2mZ9nP4qR7sT3vW1uX6`
   
   ⚠️ **ВАЖНО:** Сохраните эти данные, они понадобятся!

### 1.2 Добавьте кнопку в личный кабинет Bitrix

Найдите файл шаблона личного кабинета (обычно это):
- `/local/templates/your_template/header.php`
- Или компонент профиля пользователя

Добавьте код кнопки:

```html
<!-- Кнопка входа в программу лояльности -->
<a href="https://it-mydoc.ru/auth/bitrix/login" 
   class="loyalty-program-btn"
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
.loyalty-program-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 65, 85, 0.4);
}
</style>
```

Или минимальный вариант:
```html
<a href="https://it-mydoc.ru/auth/bitrix/login">❤️ Моя скидка</a>
```

---

## ШАГ 2: Настройка Backend (20 минут)

### 2.1 Добавьте переменные окружения

Отредактируйте файл `.env` на сервере:

```bash
cd /tmp/mydoc-loyalty
nano .env
```

Добавьте в конец файла:

```env
# Bitrix SSO
BITRIX_CLIENT_ID=local.67a1f2b3c4d5e6
BITRIX_CLIENT_SECRET=K8xY2mZ9nP4qR7sT3vW1uX6
BITRIX_OAUTH_BASE_URL=https://oauth.bitrix.info
BITRIX_REST_API_URL=https://mydoctorarmavir.bitrix24.ru/rest
BASE_URL=https://it-mydoc.ru
```

⚠️ **Замените значения на реальные из Bitrix!**

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### 2.2 Обновите модель User

Файл: `backend/models.py`

Добавьте поле `bitrix_id`:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="patient")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    referral_code_id = Column(Integer, ForeignKey("referral_codes.id"), nullable=True)
    referral_code = relationship("ReferralCode", back_populates="owner", uselist=False)
    
    # Новое поле для Bitrix SSO
    bitrix_id = Column(String, unique=True, index=True, nullable=True)  # ← ДОБАВИТЬ ЭТО

    loyalty_account = relationship("LoyaltyAccount", back_populates="owner", uselist=False)
    certificates = relationship("Certificate", back_populates="owner")
    referral_events = relationship("ReferralEvent", back_populates="referrer")
    audit_logs = relationship("AuditLog", back_populates="user")
```

### 2.3 Обновите config.py

Файл: `backend/config.py`

Добавьте настройки Bitrix:

```python
class Settings(BaseSettings):
    # ... существующие настройки ...
    
    # Bitrix SSO
    bitrix_client_id: str
    bitrix_client_secret: str
    bitrix_oauth_base_url: str = "https://oauth.bitrix.info"
    bitrix_rest_api_url: str = "https://mydoctorarmavir.bitrix24.ru/rest"
    base_url: str = "https://it-mydoc.ru"
    
    model_config = SettingsConfigDict(env_file=".env")
```

### 2.4 Создайте роутер Bitrix SSO

Создайте новый файл: `backend/routers/bitrix_sso.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import secrets

from database import get_db
from config import settings
from models import User
from routers.auth import create_access_token, get_password_hash

router = APIRouter()

# Временное хранилище для state (CSRF-защита)
oauth_states = {}

@router.get("/login")
async def bitrix_login(request: Request):
    """Инициирует процесс авторизации через Bitrix OAuth"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True
    
    auth_url = (
        f"{settings.bitrix_oauth_base_url}/oauth/authorize/"
        f"?client_id={settings.bitrix_client_id}"
        f"&response_type=code"
        f"&redirect_uri={settings.base_url}/auth/bitrix/callback"
        f"&scope=user,profile"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)

@router.get("/callback")
async def bitrix_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Обрабатывает callback от Bitrix после авторизации"""
    
    # Проверка state (CSRF-защита)
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный state параметр"
        )
    del oauth_states[state]
    
    # Обмен code на access_token
    token_url = f"{settings.bitrix_oauth_base_url}/oauth/token/"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.bitrix_client_id,
        "client_secret": settings.bitrix_client_secret,
        "code": code,
        "redirect_uri": f"{settings.base_url}/auth/bitrix/callback"
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_response.raise_for_status()
        bitrix_tokens = token_response.json()
    
    access_token = bitrix_tokens["access_token"]
    
    # Получение данных пользователя из Bitrix
    user_info_url = f"{settings.bitrix_rest_api_url}/user.current"
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            user_info_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info_response.raise_for_status()
        bitrix_user_data = user_info_response.json()["result"]
    
    bitrix_id = str(bitrix_user_data["ID"])
    email = bitrix_user_data.get("EMAIL") or f"bitrix_user_{bitrix_id}@it-mydoc.ru"
    
    # Поиск или создание пользователя
    user = db.query(User).filter(User.bitrix_id == bitrix_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.bitrix_id = bitrix_id
            db.add(user)
            db.commit()
            db.refresh(user)
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
    access_token_jwt = create_access_token(data={"sub": user.email})
    
    # Редирект на frontend с токеном
    return RedirectResponse(
        url=f"{settings.base_url}/?token={access_token_jwt}",
        status_code=status.HTTP_302_FOUND
    )
```

### 2.5 Подключите роутер в main.py

Файл: `backend/main.py`

```python
# ... существующие импорты ...
from routers import loyalty, certificates, referrals, auth, admin, integrations
from routers import bitrix_sso  # ← ДОБАВИТЬ

# ... существующий код ...

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(bitrix_sso.router, prefix="/auth/bitrix", tags=["Bitrix SSO"])  # ← ДОБАВИТЬ
app.include_router(loyalty.router, prefix="/loyalty", tags=["Loyalty"])
# ... остальные роутеры ...
```

### 2.6 Создайте миграцию БД

```bash
cd /tmp/mydoc-loyalty/backend

# Создать миграцию
docker-compose exec backend alembic revision -m "add bitrix_id to users"

# Отредактировать файл миграции (он будет в backend/alembic/versions/)
# Добавить в функцию upgrade():
#   op.add_column('users', sa.Column('bitrix_id', sa.String(), nullable=True))
#   op.create_index(op.f('ix_users_bitrix_id'), 'users', ['bitrix_id'], unique=True)
#
# И в downgrade():
#   op.drop_index(op.f('ix_users_bitrix_id'), table_name='users')
#   op.drop_column('users', 'bitrix_id')

# Применить миграцию
docker-compose exec backend alembic upgrade head
```

Или выполните миграцию вручную в БД:

```sql
ALTER TABLE users ADD COLUMN bitrix_id VARCHAR(255) UNIQUE;
CREATE INDEX ix_users_bitrix_id ON users(bitrix_id);
```

### 2.7 Перезапустите контейнеры

```bash
cd /tmp/mydoc-loyalty
docker-compose restart backend
```

---

## ШАГ 3: Тестирование (5 минут)

### 3.1 Очистите кеш браузера
- Нажмите: `Ctrl+Shift+Delete`
- Выберите: "Изображения и файлы в кеше"
- Очистите

### 3.2 Проверьте страницу входа

1. Откройте: `https://it-mydoc.ru/login`
2. Должны увидеть красивую страницу с кнопкой "Войти через Мой Доктор"

### 3.3 Протестируйте SSO

1. **Нажмите** кнопку "Войти через Мой Доктор"
2. **Должно произойти:**
   - Редирект на Bitrix OAuth
   - Автоматическая авторизация (если уже залогинены в Bitrix)
   - Редирект обратно на `it-mydoc.ru`
   - Вход в личный кабинет лояльности ✅

### 3.4 Проверьте из Bitrix

1. Войдите в личный кабинет на `mydoctorarmavir.ru`
2. Найдите кнопку "❤️ Моя скидка"
3. Нажмите на неё
4. → Должны автоматически войти в систему лояльности

---

## 🔧 Устранение неполадок

### Ошибка: "CLIENT_ID not found"
- Проверьте файл `.env`
- Перезапустите backend: `docker-compose restart backend`

### Ошибка: "Invalid redirect_uri"
- В Bitrix OAuth-приложении должен быть указан: `https://it-mydoc.ru/auth/bitrix/callback`

### Ошибка: "User not authenticated"
- Проверьте, что пользователь авторизован в Bitrix
- Проверьте права доступа (scopes) в OAuth-приложении

### Страница не открывается
- Очистите кеш браузера
- Проверьте логи: `docker logs mydoc_backend`
- Проверьте логи: `docker logs mydoc_frontend`

---

## 📊 Проверка работы

### Проверьте логи backend:
```bash
docker logs mydoc_backend --tail 50
```

Должны увидеть:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Проверьте переменные окружения:
```bash
docker-compose exec backend env | grep BITRIX
```

Должны увидеть:
```
BITRIX_CLIENT_ID=local.67a1f2b3c4d5e6
BITRIX_CLIENT_SECRET=K8xY2mZ9nP4qR7sT3vW1uX6
```

### Проверьте базу данных:
```bash
docker-compose exec postgres psql -U postgres -d mydoc_loyalty -c "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='bitrix_id';"
```

Должна вернуть: `bitrix_id`

---

## 🎯 Итоговый чек-лист

Перед запуском убедитесь:

- [ ] Создано OAuth-приложение в Bitrix
- [ ] Получены CLIENT_ID и CLIENT_SECRET
- [ ] Добавлена кнопка в личный кабинет Bitrix
- [ ] Обновлен файл `.env` с данными Bitrix
- [ ] Добавлено поле `bitrix_id` в модель User
- [ ] Обновлен `config.py`
- [ ] Создан роутер `bitrix_sso.py`
- [ ] Роутер подключен в `main.py`
- [ ] Выполнена миграция БД
- [ ] Перезапущен backend
- [ ] Очищен кеш браузера
- [ ] Проверена страница `/login`
- [ ] Протестирован вход через SSO

---

## 📞 Помощь

Если что-то не работает:

1. **Проверьте документацию:** `ИНТЕГРАЦИЯ_SSO_BITRIX.md`
2. **Посмотрите логи:** `docker logs mydoc_backend`
3. **Проверьте .env:** Все переменные заполнены?
4. **Проверьте Bitrix:** OAuth-приложение создано?

---

## ✅ После успешной настройки

Пользователи смогут:
- 🏥 Войти в систему лояльности с сайта клиники
- ❤️ Использовать один аккаунт для обоих сайтов
- 🚀 Авторизоваться одним кликом

**Удачи с настройкой!** 🎉

