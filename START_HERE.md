# 🚀 НАЧНИТЕ ЗДЕСЬ - Моя ❤ скидка

## 📍 Быстрый старт для деплоя на сервер 85.92.110.173

Этот проект готов к запуску! Следуйте простым шагам ниже.

---

## 🎯 Что это?

**Моя ❤ скидка** — полноценный микросервис для сети клиник, включающий:

✅ **Программу лояльности** - бонусы и кешбэк  
✅ **Электронные сертификаты** - с QR-кодами  
✅ **Реферальную CPA-систему** - вознаграждения за рефералов  
✅ **Интеграции** - 1С:УМЦ, Bitrix24, Email/SMS  
✅ **Админ-панель** - управление всем функционалом  

---

## 🚀 Развертывание за 5 минут

### 1️⃣ Подключитесь к серверу

```bash
ssh root@85.92.110.173
```

### 2️⃣ Скопируйте проект на сервер

**С вашего компьютера:**

```bash
cd /tmp/mydoc-loyalty
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  ./ root@85.92.110.173:/var/www/mydoc-loyalty/
```

### 3️⃣ На сервере: Установите Docker (если нужно)

```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose

# Проверка
docker --version
```

### 4️⃣ Настройте SSL сертификат

```bash
# Установка certbot
apt-get install -y certbot

# Получение сертификата
certbot certonly --standalone -d it-mydoc.ru \
  --agree-tos --non-interactive --email admin@it-mydoc.ru

# Копирование
mkdir -p /var/www/mydoc-loyalty/nginx/ssl
cp /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem /var/www/mydoc-loyalty/nginx/ssl/
cp /etc/letsencrypt/live/it-mydoc.ru/privkey.pem /var/www/mydoc-loyalty/nginx/ssl/
```

### 5️⃣ Создайте .env файл

```bash
cd /var/www/mydoc-loyalty

cat > .env << 'EOF'
DB_PASSWORD=MyDoc2025SecurePassword!
JWT_SECRET=change-this-to-random-32-char-string
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DOMAIN=it-mydoc.ru
BITRIX_API_URL=
BITRIX_WEBHOOK=
ONEC_API_URL=
ONEC_USERNAME=
ONEC_PASSWORD=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMS_API_KEY=
DEBUG=False
ENVIRONMENT=production
EOF

chmod 600 .env
```

### 6️⃣ Запустите приложение!

```bash
cd /var/www/mydoc-loyalty
chmod +x deploy.sh
./deploy.sh
```

### 7️⃣ Готово! 🎉

Откройте в браузере:

- **Личный кабинет:** https://it-mydoc.ru
- **Админ-панель:** https://it-mydoc.ru/admin  
- **API документация:** https://it-mydoc.ru/api/docs

---

## 🔐 Тестовые данные для входа

После запуска `./deploy.sh` автоматически создаются:

**Администратор:**
- Email: `admin@it-mydoc.ru`
- Пароль: `admin123`

**Кассир:**
- Email: `cashier@it-mydoc.ru`
- Пароль: `cashier123`

**Доктор:**
- Email: `doctor@it-mydoc.ru`
- Пароль: `doctor123`

**Пациент:**
- Email: `patient@it-mydoc.ru`
- Пароль: `patient123`

> ⚠️ **Важно:** Смените пароли после первого входа!

---

## 📚 Дополнительная документация

Для подробной информации смотрите:

1. **[QUICK_START.md](./QUICK_START.md)** - Детальная инструкция по развертыванию
2. **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Чеклист развертывания
3. **[README.md](./README.md)** - Общая документация проекта
4. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Документация API
5. **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Инструкции по деплою

---

## 🔧 Управление сервисом

### Просмотр статуса

```bash
docker-compose ps
```

### Просмотр логов

```bash
docker-compose logs -f backend
```

### Перезапуск

```bash
docker-compose restart
```

### Остановка

```bash
docker-compose down
```

### Backup БД

```bash
docker-compose exec postgres pg_dump -U mydoc_user mydoc_loyalty > backup_$(date +%Y%m%d).sql
```

---

## 🎨 Фирменный стиль

Проект использует фирменные цвета клиники:

- **Основной:** #004155 (темно-бирюзовый)
- **Вторичный:** #68cdd2 (светло-бирюзовый)
- **Акцент:** #e60a41 (красный, для логотипа ❤ и важных кнопок)
- **Фон:** #e5eef2

Дизайн минималистичный, медицинский, с округлыми углами и мягкими градиентами.

---

## ⚙️ Настройка интеграций

### 1С:УМЦ

В `.env` файле укажите:
```
ONEC_API_URL=http://your-1c-server:port/api
ONEC_USERNAME=integration_user
ONEC_PASSWORD=strong_password
```

Webhook URL для 1С: `https://it-mydoc.ru/api/integrations/1c/visit`

### Bitrix24

В `.env` файле укажите:
```
BITRIX_API_URL=https://your-company.bitrix24.ru/rest
BITRIX_WEBHOOK=your_webhook_key
```

### Email уведомления

Для Gmail создайте App Password и укажите в `.env`:
```
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### SMS уведомления

Для SMS.RU получите API ключ и укажите:
```
SMS_API_KEY=your-api-key
```

---

## 🆘 Проблемы?

### Контейнер не запускается

```bash
docker-compose logs backend
docker-compose build --no-cache
```

### Ошибка SSL

```bash
certbot renew --force-renewal
cp /etc/letsencrypt/live/it-mydoc.ru/*.pem /var/www/mydoc-loyalty/nginx/ssl/
docker-compose restart nginx
```

### БД не доступна

```bash
docker-compose exec postgres pg_isready
docker-compose restart postgres
```

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. См. документацию в папке проекта

---

## ✅ Что дальше?

После успешного запуска:

1. ✅ Войдите в админ-панель: https://it-mydoc.ru/admin
2. ✅ Смените пароли администраторов
3. ✅ Настройте интеграции (1С, Bitrix)
4. ✅ Настройте Email/SMS уведомления
5. ✅ Создайте правила начисления бонусов
6. ✅ Запустите тестовую программу лояльности

---

**Версия:** 1.0.0  
**Дата:** Сентябрь 2025  
**Домен:** it-mydoc.ru  
**Сервер:** 85.92.110.173

🚀 **Удачного запуска!**

