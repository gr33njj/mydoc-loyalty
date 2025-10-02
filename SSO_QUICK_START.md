# 🚀 SSO - Быстрый старт

> ⚠️ **КРИТИЧНО!** Обязательно используйте последние версии файлов!  
> **Изменение:** Токены теперь хранятся в ФАЙЛАХ вместо сессий (межсерверные запросы не имеют доступа к $_SESSION).  
> **Требуется:** Директория `/upload/loyalty_tokens/` с правами на запись.

## ✅ Что уже сделано

- ✅ Frontend с кнопкой "Войти через Мой Доктор"
- ✅ Backend API для проверки токенов
- ✅ Редирект-based SSO (без проблем с CORS)
- ✅ Исправлена работа PHP сессий (session_start)

## 📁 Файлы для установки на Bitrix

Нужно установить **2 файла** на сервер Bitrix:

### 1. Главный файл (обязательно!)

**`loyalty_redirect.php`** → `/local/pages/loyalty_redirect.php`

Скачать: [bitrix_files/loyalty_redirect.php](bitrix_files/loyalty_redirect.php)

### 2. Вспомогательный файл

**`verify_token.php`** → `/local/api/verify_token.php`

Скачать: [bitrix_files/verify_token.php](bitrix_files/verify_token.php)

---

## 🔧 Установка (1 минута)

### Вариант 1: Через wget (рекомендуется)

```bash
# На сервере Bitrix:

# 1. Создайте директории
mkdir -p /var/www/html/local/pages
mkdir -p /var/www/html/local/api
mkdir -p /var/www/html/upload/loyalty_tokens

# 2. Скачайте файлы с GitHub
cd /var/www/html/local/pages/
wget -O loyalty_redirect.php https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/loyalty_redirect.php

cd /var/www/html/local/api/
wget -O verify_token.php https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/verify_token.php

# 3. Установите права
chmod 644 /var/www/html/local/pages/loyalty_redirect.php
chmod 644 /var/www/html/local/api/verify_token.php
chmod 777 /var/www/html/upload/loyalty_tokens
```

### Вариант 2: Скачать вручную

Скачайте файлы по прямым ссылкам:

1. **loyalty_redirect.php:**  
   https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/loyalty_redirect.php  
   → Сохранить в `/var/www/html/local/pages/`

2. **verify_token.php:**  
   https://raw.githubusercontent.com/gr33njj/mydoc-loyalty/main/bitrix_files/verify_token.php  
   → Сохранить в `/var/www/html/local/api/`

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
    ↓ (Сохраняет в ФАЙЛ /upload/loyalty_tokens/XXX.json)
    ↓
it-mydoc.ru/auth/sso?token=XXX
    ↓ (Frontend отправляет токен на backend)
    ↓
Backend → POST mydoctorarmavir.ru/verify_token.php
    ↓ (Читает токен из ФАЙЛА)
    ↓ (Возвращает данные пользователя)
    ↓
Backend создает JWT токен
    ↓
Frontend сохраняет JWT
    ↓
it-mydoc.ru/ ✅ АВТОРИЗОВАН!
```

**Важно:** Токены хранятся в файлах, т.к. `verify_token.php` получает запрос от другого сервера без cookies Bitrix.

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

