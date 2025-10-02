# 🚀 SSO - Быстрый старт

## ✅ Что уже сделано

- ✅ Frontend с кнопкой "Войти через Мой Доктор"
- ✅ Backend API для проверки токенов
- ✅ Редирект-based SSO (без проблем с CORS)

## 📁 Файлы для установки на Bitrix

Нужно установить **2 файла** на сервер Bitrix:

### 1. Главный файл (обязательно!)

**`loyalty_redirect.php`** → `/local/pages/loyalty_redirect.php`

Скачать: [bitrix_files/loyalty_redirect.php](bitrix_files/loyalty_redirect.php)

### 2. Вспомогательный файл

**`verify_token.php`** → `/local/api/verify_token.php`

Скачать: [bitrix_files/verify_token.php](bitrix_files/verify_token.php)

---

## 🔧 Установка (3 минуты)

### На сервере Bitrix:

```bash
# 1. Создайте директории
mkdir -p /var/www/html/local/pages
mkdir -p /var/www/html/local/api

# 2. Скопируйте файлы
# loyalty_redirect.php → /var/www/html/local/pages/
# verify_token.php     → /var/www/html/local/api/

# 3. Установите права
chmod 644 /var/www/html/local/pages/loyalty_redirect.php
chmod 644 /var/www/html/local/api/verify_token.php
chown www-data:www-data /var/www/html/local/pages/*.php
chown www-data:www-data /var/www/html/local/api/*.php
```

---

## 🧪 Тестирование

### Вариант 1: Прямой редирект

1. Авторизуйтесь в Bitrix: https://mydoctorarmavir.ru
2. **В этой же вкладке** откройте:  
   https://mydoctorarmavir.ru/local/pages/loyalty_redirect.php
3. Должен произойти редирект на it-mydoc.ru с авторизацией ✅

### Вариант 2: Через кнопку

1. Откройте: https://it-mydoc.ru/login
2. Нажмите "Войти через Мой Доктор"
3. Авторизация должна пройти автоматически ✅

---

## 🎯 Как это работает

```
Пользователь
    ↓
it-mydoc.ru/login (нажимает кнопку)
    ↓
mydoctorarmavir.ru/local/pages/loyalty_redirect.php
    ↓ (Bitrix проверяет авторизацию)
    ↓ (Создает токен)
    ↓
it-mydoc.ru/auth/sso?token=XXX
    ↓ (Frontend проверяет токен)
    ↓ (Получает JWT)
    ↓
it-mydoc.ru/ ✅ АВТОРИЗОВАН!
```

---

## 🐛 Отладка

Если не работает:

1. Откройте консоль браузера (F12 → Console)
2. Попробуйте войти
3. Проверьте логи:
   - `🔄 Проверка токена от Bitrix: XXX`
   - `📥 Ответ от backend: {...}`
   - `✅ JWT токен сохранен`

### Частые проблемы:

**"Not Found"** → Проверьте что файлы установлены:
- `/local/pages/loyalty_redirect.php` ✅
- `/local/api/verify_token.php` ✅

**"User not authorized"** → Сначала авторизуйтесь в Bitrix, потом пробуйте SSO

**"Token expired"** → Токен действует 5 минут, попробуйте снова

---

## 📊 Статус

- ✅ Frontend готов
- ✅ Backend готов  
- ⏳ Нужно установить 2 файла на Bitrix
- ⏳ Протестировать

---

## 📞 Нужна помощь?

1. Проверьте логи в консоли браузера (F12)
2. Проверьте что файлы на месте
3. Отправьте скриншот консоли если есть ошибки

