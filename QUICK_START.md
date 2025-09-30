# 🚀 Быстрый старт - Моя ❤ скидка

## Развертывание на сервере 85.92.110.173

### Шаг 1: Подключение к серверу

```bash
ssh root@85.92.110.173
```

### Шаг 2: Установка Docker и Docker Compose (если еще не установлены)

```bash
# Обновление системы
apt-get update && apt-get upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt-get install docker-compose -y

# Проверка установки
docker --version
docker-compose --version
```

### Шаг 3: Копирование проекта на сервер

```bash
# На вашем локальном компьютере
cd /tmp/mydoc-loyalty
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  ./ root@85.92.110.173:/var/www/mydoc-loyalty/
```

Или используйте Git:

```bash
# На сервере
cd /var/www
git clone <your-repo-url> mydoc-loyalty
cd mydoc-loyalty
```

### Шаг 4: Настройка переменных окружения

```bash
cd /var/www/mydoc-loyalty

# Создайте .env файл
nano .env
```

Скопируйте и отредактируйте:

```env
# Database Configuration
DB_PASSWORD=MyDoc2025Loyalty!Strong

# JWT Configuration
JWT_SECRET=your-very-secret-jwt-key-change-this-to-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Domain Configuration
DOMAIN=it-mydoc.ru

# Bitrix Integration (опционально)
BITRIX_API_URL=
BITRIX_WEBHOOK=

# 1C Integration (настройте позже)
ONEC_API_URL=
ONEC_USERNAME=
ONEC_PASSWORD=

# Email Configuration (настройте для отправки сертификатов)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# SMS Configuration (опционально)
SMS_API_KEY=

# Application Settings
DEBUG=False
ENVIRONMENT=production
```

### Шаг 5: Настройка SSL сертификата (Let's Encrypt)

```bash
# Установка certbot
apt-get install certbot -y

# Получение сертификата
certbot certonly --standalone -d it-mydoc.ru

# Копирование сертификата
mkdir -p /var/www/mydoc-loyalty/nginx/ssl
cp /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem /var/www/mydoc-loyalty/nginx/ssl/
cp /etc/letsencrypt/live/it-mydoc.ru/privkey.pem /var/www/mydoc-loyalty/nginx/ssl/

# Настройка автообновления (каждые 80 дней)
echo "0 0 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/it-mydoc.ru/*.pem /var/www/mydoc-loyalty/nginx/ssl/ && docker-compose -f /var/www/mydoc-loyalty/docker-compose.yml restart nginx" | crontab -
```

### Шаг 6: Запуск приложения

```bash
cd /var/www/mydoc-loyalty

# Даем права на выполнение скрипта
chmod +x deploy.sh

# Запускаем развертывание
./deploy.sh
```

### Шаг 7: Проверка работы

```bash
# Проверка статуса контейнеров
docker-compose ps

# Должны быть запущены:
# - mydoc_postgres
# - mydoc_redis
# - mydoc_backend
# - mydoc_frontend
# - mydoc_admin
# - mydoc_nginx

# Просмотр логов
docker-compose logs -f backend

# Проверка health endpoint
curl https://it-mydoc.ru/api/health
```

### Шаг 8: Создание первого админа

```bash
# Подключаемся к контейнеру backend
docker-compose exec backend python

# В Python консоли:
from database import SessionLocal
from models import User, LoyaltyAccount
from routers.auth import get_password_hash

db = SessionLocal()

# Создание админа
admin = User(
    email="admin@it-mydoc.ru",
    phone="+79999999999",
    full_name="Администратор",
    password_hash=get_password_hash("admin123"),
    role="admin",
    is_active=True,
    is_verified=True
)
db.add(admin)
db.commit()
db.refresh(admin)

# Создание аккаунта лояльности для админа
loyalty = LoyaltyAccount(
    user_id=admin.id,
    card_number="ML00000001",
    card_tier="platinum"
)
db.add(loyalty)
db.commit()

print(f"Админ создан: {admin.email}")
exit()
```

## 🎉 Готово!

Теперь сервис доступен по адресам:

- **Личный кабинет**: https://it-mydoc.ru
- **Админ-панель**: https://it-mydoc.ru/admin
- **API документация**: https://it-mydoc.ru/api/docs
- **API Redoc**: https://it-mydoc.ru/api/redoc

### Тестовые данные для входа:

**Админ:**
- Email: admin@it-mydoc.ru
- Пароль: admin123

## 📊 Мониторинг и обслуживание

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Последние 100 строк
docker-compose logs --tail=100 backend
```

### Перезапуск сервисов

```bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск только backend
docker-compose restart backend

# Полная пересборка и перезапуск
docker-compose down
docker-compose up -d --build
```

### Обновление приложения

```bash
cd /var/www/mydoc-loyalty

# Получение обновлений
git pull origin main

# Пересборка и перезапуск
docker-compose down
docker-compose up -d --build

# Применение миграций БД (если есть)
docker-compose exec backend alembic upgrade head
```

### Резервное копирование БД

```bash
# Создание backup
docker-compose exec postgres pg_dump -U mydoc_user mydoc_loyalty > backup_$(date +%Y%m%d).sql

# Восстановление из backup
docker-compose exec -T postgres psql -U mydoc_user mydoc_loyalty < backup_20250101.sql
```

## 🔧 Настройка интеграций

### 1С:УМЦ Интеграция

1. В .env файле укажите:
   ```
   ONEC_API_URL=http://your-1c-server:port/api
   ONEC_USERNAME=integration_user
   ONEC_PASSWORD=strong_password
   ```

2. Настройте webhook в 1С для отправки событий о визитах:
   - URL: https://it-mydoc.ru/api/integrations/1c/visit
   - Метод: POST
   - Headers: Authorization: Bearer <ваш_токен>

### Bitrix24 Интеграция

1. В .env файле укажите:
   ```
   BITRIX_API_URL=https://your-company.bitrix24.ru/rest
   BITRIX_WEBHOOK=your_webhook_key
   ```

2. Настройте webhook в Bitrix24:
   - URL: https://it-mydoc.ru/api/integrations/bitrix/patient
   - События: создание/обновление контакта

### Email/SMS уведомления

1. Для Gmail:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```
   
   Создайте App Password в настройках Google аккаунта.

2. Для SMS (SMS.RU):
   ```
   SMS_API_KEY=your-sms-ru-api-key
   ```

## 🆘 Решение проблем

### Контейнер не запускается

```bash
# Проверка логов
docker-compose logs backend

# Проверка конфигурации
docker-compose config

# Пересборка без кеша
docker-compose build --no-cache
```

### Ошибка подключения к БД

```bash
# Проверка статуса Postgres
docker-compose exec postgres pg_isready

# Проверка подключения
docker-compose exec postgres psql -U mydoc_user -d mydoc_loyalty -c "SELECT 1;"
```

### Проблемы с SSL

```bash
# Проверка сертификата
openssl s_client -connect it-mydoc.ru:443 -servername it-mydoc.ru

# Обновление сертификата
certbot renew --force-renewal
```

## 📞 Поддержка

При возникновении проблем проверьте:
1. Логи всех сервисов: `docker-compose logs -f`
2. Статус контейнеров: `docker-compose ps`
3. Доступность портов: `netstat -tulpn | grep -E '(80|443|5432|6379|8000)'`
4. Конфигурацию Nginx: `docker-compose exec nginx nginx -t`

