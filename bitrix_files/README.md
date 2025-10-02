# 📁 Файлы для установки на сервер Bitrix

Эти файлы нужно установить на сервере Bitrix для работы SSO через Cookie.

## 📋 Инструкция по установке

### 1. Создайте директорию на сервере Bitrix

```bash
# На сервере Bitrix (обычно /var/www/html или путь к Bitrix)
mkdir -p /path/to/bitrix/local/api
```

### 2. Скопируйте файлы

**Скопируйте 2 файла в директорию `/local/api/`:**

- `loyalty_token.php` → `/local/api/loyalty_token.php`
- `verify_token.php` → `/local/api/verify_token.php`

```bash
# На сервере Bitrix:
cd /path/to/bitrix/local/api

# Создайте файлы и скопируйте содержимое
nano loyalty_token.php
# Вставьте содержимое из loyalty_token.php

nano verify_token.php  
# Вставьте содержимое из verify_token.php
```

### 3. Установите права доступа

```bash
# На сервере Bitrix:
chmod 644 /path/to/bitrix/local/api/*.php
chown www-data:www-data /path/to/bitrix/local/api/*.php
```

### 4. Проверьте доступность

Откройте в браузере (авторизуйтесь в Bitrix перед этим):

```
https://mydoctorarmavir.ru/local/api/loyalty_token.php
```

**Должны увидеть JSON:**
```json
{
  "success": true,
  "token": "abc123...",
  "user_id": 123,
  "email": "user@example.com"
}
```

---

## 🔧 Настройка кнопки в личном кабинете

Добавьте кнопку в шаблон личного кабинета Bitrix:

**Файл:** `/local/templates/your_template/header.php` (или в компоненте профиля)

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

## 🧪 Тестирование

### Шаг 1: Проверьте файлы

1. Авторизуйтесь в Bitrix: `https://mydoctorarmavir.ru`
2. Откройте: `https://mydoctorarmavir.ru/local/api/loyalty_token.php`
3. Должны получить токен

### Шаг 2: Проверьте SSO

1. Авторизуйтесь в Bitrix
2. Откройте: `https://it-mydoc.ru/login`
3. Нажмите "Войти через Мой Доктор"
4. Должны автоматически войти в систему лояльности ✅

---

## ❓ Возможные проблемы

### Ошибка 404 при открытии файлов

**Решение:** Проверьте путь установки файлов:
```bash
ls -la /path/to/bitrix/local/api/
```

### Ошибка CORS

**Решение:** Убедитесь, что в начале файлов `loyalty_token.php` и `verify_token.php` указан правильный домен:
```php
header('Access-Control-Allow-Origin: https://it-mydoc.ru');
```

### "User not authorized"

**Решение:** Сначала авторизуйтесь в Bitrix, затем откройте систему лояльности.

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте права доступа к файлам
2. Проверьте логи Bitrix
3. Откройте консоль браузера (F12) для просмотра ошибок

---

## ✅ Готово!

После установки файлов SSO через Cookie будет работать! 🎉

