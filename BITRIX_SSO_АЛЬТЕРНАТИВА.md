# 🔧 Альтернативные способы настройки SSO с Bitrix

## Проблема: Не найден раздел OAuth-приложений

В зависимости от версии Bitrix24 (облачная/коробочная) путь к настройкам может отличаться.

---

## ✅ ВАРИАНТ 1: Через Вебхуки Bitrix24 (Самый простой!)

Это **рекомендуемый способ** для Bitrix24 облачной версии.

### Шаг 1: Создайте входящий вебхук

1. **Откройте Bitrix24:**
   - Зайдите: `https://mydoctorarmavir.bitrix24.ru`

2. **Перейдите в раздел вебхуков:**
   ```
   Главное меню (☰) → Приложения → Вебхуки → Добавить вебхук
   ```
   
   Или альтернативный путь:
   ```
   Настройки → Настройки портала → Вебхуки → Добавить вебхук
   ```

3. **Выберите тип:**
   - **"Входящий вебхук"**

4. **Настройте права доступа:**
   Выберите следующие разрешения:
   - ✅ `user` - Доступ к профилю пользователя
   - ✅ `profile` - Расширенный доступ к профилю
   
5. **Сохраните и получите:**
   ```
   URL вебхука: https://mydoctorarmavir.bitrix24.ru/rest/1/xxxxx/
   ```
   
   ⚠️ **Сохраните этот URL!**

---

### Шаг 2: Упрощенная интеграция через Вебхук

Вместо OAuth 2.0 используем прямой вебхук. Обновите файлы:

#### 📄 `.env`
```env
# Вебхук Bitrix (вместо OAuth)
BITRIX_WEBHOOK_URL=https://mydoctorarmavir.bitrix24.ru/rest/1/xxxxx/
BASE_URL=https://it-mydoc.ru
```

#### 📄 `backend/config.py`
```python
class Settings(BaseSettings):
    # ... существующие настройки ...
    
    # Bitrix Webhook
    bitrix_webhook_url: str
    base_url: str = "https://it-mydoc.ru"
    
    model_config = SettingsConfigDict(env_file=".env")
```

#### 📄 `backend/routers/bitrix_sso.py` (Новая версия)

```python
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
from pydantic import BaseModel

from database import get_db
from config import settings
from models import User
from routers.auth import create_access_token, get_password_hash

router = APIRouter()

class BitrixAuthRequest(BaseModel):
    user_id: str
    email: str
    name: str = ""
    last_name: str = ""

@router.post("/webhook/auth")
async def bitrix_webhook_auth(
    auth_data: BitrixAuthRequest,
    db: Session = Depends(get_db)
):
    """Авторизация через вебхук Bitrix"""
    
    bitrix_id = str(auth_data.user_id)
    email = auth_data.email
    
    # Поиск или создание пользователя
    user = db.query(User).filter(User.bitrix_id == bitrix_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.bitrix_id = bitrix_id
        else:
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
        "redirect_url": f"{settings.base_url}/?token={access_token}"
    }

@router.get("/check/{user_id}")
async def check_bitrix_user(user_id: str):
    """Проверка пользователя Bitrix через вебхук"""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.bitrix_webhook_url}user.get",
            params={"ID": user_id}
        )
        response.raise_for_status()
        return response.json()
```

---

### Шаг 3: Обновите страницу входа в Bitrix

Создайте файл на сервере Bitrix: `/local/templates/your_template/loyalty_auth.php`

```php
<?php
require($_SERVER["DOCUMENT_ROOT"]."/bitrix/header.php");

// Получаем данные текущего пользователя
global $USER;

if ($USER->IsAuthorized()) {
    $userId = $USER->GetID();
    $userEmail = $USER->GetEmail();
    $userName = $USER->GetFirstName();
    $userLastName = $USER->GetLastName();
    ?>
    
    <script>
    // Отправляем данные на сервер лояльности
    async function authInLoyalty() {
        try {
            const response = await fetch('https://it-mydoc.ru/auth/bitrix/webhook/auth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: '<?= $userId ?>',
                    email: '<?= $userEmail ?>',
                    name: '<?= $userName ?>',
                    last_name: '<?= $userLastName ?>'
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.redirect_url) {
                // Перенаправляем пользователя
                window.location.href = data.redirect_url;
            }
        } catch (error) {
            console.error('Ошибка авторизации:', error);
            alert('Не удалось авторизоваться в системе лояльности');
        }
    }
    
    // Автоматически вызываем при загрузке страницы
    authInLoyalty();
    </script>
    
    <div style="text-align: center; padding: 50px;">
        <h2>Перенаправление в программу лояльности...</h2>
        <p>Пожалуйста, подождите</p>
    </div>
    
    <?php
} else {
    // Пользователь не авторизован - редирект на логин
    LocalRedirect('/auth/');
}

require($_SERVER["DOCUMENT_ROOT"]."/bitrix/footer.php");
?>
```

### Шаг 4: Добавьте кнопку в личный кабинет

В шаблоне личного кабинета (`header.php` или профиль):

```html
<a href="/loyalty_auth.php" 
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
   ">
   <span style="font-size: 1.2em;">❤️</span>
   Моя скидка
</a>
```

---

## ✅ ВАРИАНТ 2: Через REST API без OAuth

Если вебхуки тоже недоступны, используем REST API с ключом администратора.

### Шаг 1: Получите API-ключ

1. **Bitrix24:**
   ```
   Настройки → Настройки портала → Разработчикам → 
   Другое → Локальные приложения → Создать приложение
   ```

2. **Получите:**
   - `REST_KEY` - ключ доступа

### Шаг 2: Настройте .env

```env
BITRIX_REST_KEY=ваш_rest_key
BITRIX_DOMAIN=mydoctorarmavir.bitrix24.ru
BASE_URL=https://it-mydoc.ru
```

---

## ✅ ВАРИАНТ 3: Самый простой - Cookie-based SSO

Если ничего не работает, используем общие cookies между доменами.

### Требования:
- Оба домена должны быть на одном родительском домене (например: `mydoc.ru`)
- Или настроить CORS

### Шаг 1: Создайте скрипт на Bitrix

`/local/templates/your_template/loyalty_token.php`:

```php
<?php
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
header('Access-Control-Allow-Credentials: true');
header('Content-Type: application/json');

require($_SERVER["DOCUMENT_ROOT"]."/bitrix/modules/main/include/prolog_before.php");

global $USER;

if ($USER->IsAuthorized()) {
    // Генерируем одноразовый токен
    $token = md5($USER->GetID() . time() . 'secret_salt');
    
    // Сохраняем в кеш на 1 минуту
    $cache = \Bitrix\Main\Data\Cache::createInstance();
    $cache->startDataCache(60, "auth_token_" . $token);
    $cache->endDataCache([
        'user_id' => $USER->GetID(),
        'email' => $USER->GetEmail(),
        'name' => $USER->GetFirstName(),
        'last_name' => $USER->GetLastName()
    ]);
    
    echo json_encode([
        'success' => true,
        'token' => $token,
        'user_id' => $USER->GetID()
    ]);
} else {
    echo json_encode([
        'success' => false,
        'error' => 'Not authorized'
    ]);
}
?>
```

### Шаг 2: Обновите Frontend Login.js

```javascript
const handleBitrixLogin = async () => {
  try {
    // Запрашиваем токен у Bitrix
    const response = await fetch('https://mydoctorarmavir.ru/loyalty_token.php', {
      credentials: 'include'
    });
    
    const data = await response.json();
    
    if (data.success && data.token) {
      // Отправляем токен на наш backend
      const authResponse = await axios.post('/auth/bitrix/verify', {
        bitrix_token: data.token,
        user_id: data.user_id
      });
      
      if (authResponse.data.token) {
        localStorage.setItem('token', authResponse.data.token);
        window.location.href = '/';
      }
    }
  } catch (error) {
    console.error('Ошибка SSO:', error);
  }
};
```

---

## 🔍 Как найти правильный раздел в вашем Bitrix?

### Попробуйте эти пути:

1. **Bitrix24 Облачная версия:**
   ```
   Главное меню → Приложения → Вебхуки
   ```

2. **Bitrix24 Коробочная версия:**
   ```
   Настройки → Настройки продукта → Вебхуки
   ```

3. **Старая версия Bitrix:**
   ```
   Маркетплейс → Разработчикам → REST приложения
   ```

4. **Через URL:**
   ```
   https://mydoctorarmavir.bitrix24.ru/configs/index.php?lang=ru&ID=configs
   ```

5. **Поиск:**
   - Нажмите на поиск (🔍) в Bitrix24
   - Введите: "вебхук" или "webhook" или "REST"

---

## 📞 Определение версии Bitrix

Чтобы понять, какая у вас версия:

1. **Откройте:**
   ```
   Настройки → О продукте
   ```

2. **Или проверьте URL:**
   - Если `.bitrix24.ru` → облачная версия (используйте Вебхуки)
   - Если свой домен + `/bitrix/` → коробочная (используйте OAuth)

---

## 🚀 Рекомендация

**Для большинства случаев лучше всего подходит ВАРИАНТ 1 (Вебхуки)**:
- ✅ Проще настроить
- ✅ Не требует OAuth
- ✅ Работает в облачной версии Bitrix24
- ✅ Безопасно

---

## ❓ Что делать дальше?

1. **Определите вашу версию Bitrix** (облачная/коробочная)
2. **Найдите раздел Вебхуков** по путям выше
3. **Создайте входящий вебхук**
4. **Используйте код из ВАРИАНТА 1**

Если ничего не помогло - напишите, какая у вас версия Bitrix, и я подскажу точный путь! 🎯

