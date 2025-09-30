# 🚀 Руководство по развертыванию

## Требования к серверу

- **ОС**: Ubuntu 20.04+ или CentOS 8+
- **RAM**: Минимум 4GB
- **Диск**: 20GB свободного места
- **Процессор**: 2 ядра
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## IP адрес и домен

- **IP**: 85.92.110.173
- **Домен**: it-mydoc.ru

## Быстрый старт

### 1. Подключение к серверу

```bash
ssh root@85.92.110.173
```

### 2. Установка Docker (если не установлен)

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка зависимостей
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление репозитория Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

# Установка Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

### 3. Настройка DNS

Убедитесь, что домен `it-mydoc.ru` указывает на IP `85.92.110.173`:

```bash
# A-запись
it-mydoc.ru      IN A    85.92.110.173
www.it-mydoc.ru  IN A    85.92.110.173
```

### 4. Развертывание приложения

```bash
# Создание рабочей директории
mkdir -p /var/www/mydoc-loyalty
cd /var/www/mydoc-loyalty

# Загрузка файлов проекта (скопируйте все файлы из /tmp/mydoc-loyalty)
# Или клонируйте из репозитория

# Настройка окружения
cp .env.example .env
nano .env
```

Отредактируйте `.env` файл:

```env
# База данных - задайте сложный пароль
DB_PASSWORD=your_strong_password_here

# JWT Secret - сгенерируйте случайную строку
JWT_SECRET=$(openssl rand -hex 32)

# 1C Integration
ONEC_API_URL=http://your-1c-server:port/base/hs/api
ONEC_USERNAME=webservice_user
ONEC_PASSWORD=webservice_password

# Bitrix Integration
BITRIX_API_URL=https://your-bitrix.ru/rest
BITRIX_WEBHOOK=your_webhook_token

# Email (SMTP) - например, для Gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS Gateway (SMS.RU или другой)
SMS_API_KEY=your-sms-api-key
```

### 5. Получение SSL сертификата (Let's Encrypt)

```bash
# Установка Certbot
apt install -y certbot

# Остановка Nginx (если запущен)
docker-compose down

# Получение сертификата
certbot certonly --standalone -d it-mydoc.ru -d www.it-mydoc.ru

# Копирование сертификатов
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/it-mydoc.ru/privkey.pem nginx/ssl/

# Настройка автообновления
echo "0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/it-mydoc.ru/*.pem /var/www/mydoc-loyalty/nginx/ssl/ && docker-compose restart nginx" | crontab -
```

### 6. Запуск приложения

```bash
# Сделать скрипт исполняемым
chmod +x deploy.sh

# Запуск развертывания
./deploy.sh
```

Или вручную:

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### 7. Инициализация данных

```bash
# Создание тестовых пользователей и настроек
docker-compose exec backend python scripts/seed_data.py
```

## Проверка работоспособности

### Проверка сервисов

```bash
# Статус контейнеров
docker-compose ps

# Логи backend
docker-compose logs backend

# Логи базы данных
docker-compose logs postgres

# Проверка доступности API
curl https://it-mydoc.ru/api/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "service": "Моя ❤ скидка",
  "version": "1.0.0"
}
```

### Доступ к приложению

- **Личный кабинет пациента**: https://it-mydoc.ru
- **Админ-панель**: https://it-mydoc.ru/admin
- **API документация**: https://it-mydoc.ru/api/docs
- **ReDoc**: https://it-mydoc.ru/api/redoc

### Тестовые учетные данные

**Администратор:**
- Email: `admin@it-mydoc.ru`
- Пароль: `admin123`

**Кассир:**
- Email: `cashier@it-mydoc.ru`
- Пароль: `cashier123`

**Пациент:**
- Email: `patient1@example.com`
- Пароль: `patient123`

## Настройка firewall

```bash
# UFW Firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Проверка
ufw status
```

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Последние 100 строк
docker-compose logs --tail=100
```

### Резервное копирование БД

```bash
# Создание backup
docker-compose exec postgres pg_dump -U mydoc_user mydoc_loyalty > backup_$(date +%Y%m%d).sql

# Восстановление
docker-compose exec -T postgres psql -U mydoc_user mydoc_loyalty < backup_20250930.sql
```

### Обновление приложения

```bash
cd /var/www/mydoc-loyalty

# Загрузка новой версии
git pull origin main  # или скопируйте новые файлы

# Пересборка и перезапуск
docker-compose down
docker-compose up -d --build

# Миграции БД (если есть)
docker-compose exec backend alembic upgrade head
```

### Очистка и перезапуск

```bash
# Полная остановка
docker-compose down

# Остановка с удалением volumes (ВНИМАНИЕ: удалит данные)
docker-compose down -v

# Очистка неиспользуемых образов
docker system prune -a
```

## Настройка интеграций

### 1С:Управление Медицинским Центром

1. Создайте HTTP-сервис в 1С
2. Настройте webhook endpoints:
   - `/api/integrations/1c/visit` - уведомления о визитах
   - `/api/integrations/1c/payment` - уведомления об оплате

3. Добавьте заголовок авторизации: `X-Webhook-Token: your_token`

### Bitrix24

1. Создайте входящий webhook в Bitrix24
2. Настройте webhook для синхронизации контактов:
   - URL: `/api/integrations/bitrix/contact`
   
3. Обновите `.env` с учетными данными Bitrix

## Производительность

### Рекомендуемые настройки для production

**PostgreSQL** (`docker-compose.yml`):
```yaml
environment:
  POSTGRES_MAX_CONNECTIONS: 100
  POSTGRES_SHARED_BUFFERS: 256MB
```

**Backend workers** (`docker-compose.yml`):
```yaml
command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Масштабирование

Для увеличения нагрузки можно:

1. Увеличить количество workers backend
2. Добавить реплики PostgreSQL
3. Настроить Redis Cluster
4. Использовать Load Balancer

## Безопасность

### Рекомендации

1. ✅ Используйте сложные пароли в `.env`
2. ✅ Регулярно обновляйте SSL сертификаты
3. ✅ Настройте firewall (UFW)
4. ✅ Ограничьте доступ к админ-панели по IP
5. ✅ Регулярно создавайте backup БД
6. ✅ Мониторьте логи на подозрительную активность

### Ограничение доступа к админке по IP

В `nginx/nginx.conf` добавьте:

```nginx
location /admin {
    allow 192.168.1.0/24;  # Ваша локальная сеть
    allow 85.92.110.173;   # IP сервера
    deny all;
    
    proxy_pass http://admin:80;
    ...
}
```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. Проверьте `.env` файл
4. Перезапустите сервисы: `docker-compose restart`

## Дополнительные ресурсы

- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация PostgreSQL](https://www.postgresql.org/docs/)
- [Документация Docker](https://docs.docker.com/)
- [Документация React](https://react.dev/)
