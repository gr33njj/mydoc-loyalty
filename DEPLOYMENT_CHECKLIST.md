# ✅ Чеклист развертывания - Моя ❤ скидка

## Перед развертыванием

- [ ] Сервер с Ubuntu 20.04+ доступен по IP 85.92.110.173
- [ ] Домен it-mydoc.ru привязан к серверу (A-запись DNS)
- [ ] Открыты порты: 80 (HTTP), 443 (HTTPS), 22 (SSH)
- [ ] Установлен Docker и Docker Compose
- [ ] Доступ root или sudo

## Развертывание

### 1. Подготовка сервера

```bash
# Подключение
ssh root@85.92.110.173

# Обновление системы
apt-get update && apt-get upgrade -y

# Установка необходимых пакетов
apt-get install -y git curl wget nano htop

# Установка Docker (если не установлен)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Установка Docker Compose (если не установлен)
apt-get install -y docker-compose

# Проверка
docker --version
docker-compose --version
```

### 2. Копирование проекта

```bash
# Создание директории
mkdir -p /var/www
cd /var/www

# Копирование проекта (выберите один способ)

# Способ 1: С локального компьютера через rsync
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  /tmp/mydoc-loyalty/ root@85.92.110.173:/var/www/mydoc-loyalty/

# Способ 2: Через Git (если репозиторий настроен)
git clone <your-repo-url> mydoc-loyalty

# Способ 3: Через SCP
scp -r /tmp/mydoc-loyalty root@85.92.110.173:/var/www/
```

### 3. Настройка переменных окружения

```bash
cd /var/www/mydoc-loyalty

# Создание .env файла
cat > .env << 'EOF'
# Database
DB_PASSWORD=MyDoc2025SecurePassword!

# JWT Security
JWT_SECRET=your-random-32-char-secret-key-here-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Domain
DOMAIN=it-mydoc.ru

# Integrations (настроить позже)
BITRIX_API_URL=
BITRIX_WEBHOOK=
ONEC_API_URL=
ONEC_USERNAME=
ONEC_PASSWORD=

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# SMS
SMS_API_KEY=

# App
DEBUG=False
ENVIRONMENT=production
EOF

# Установка прав
chmod 600 .env
```

### 4. SSL Сертификат

```bash
# Установка certbot
apt-get install -y certbot

# Остановка сервисов на порту 80 (если запущены)
docker-compose down

# Получение сертификата Let's Encrypt
certbot certonly --standalone -d it-mydoc.ru --agree-tos --non-interactive --email admin@it-mydoc.ru

# Копирование сертификата
mkdir -p /var/www/mydoc-loyalty/nginx/ssl
cp /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/it-mydoc.ru/privkey.pem nginx/ssl/

# Права на чтение
chmod 644 nginx/ssl/*.pem

# Автообновление сертификата (добавить в cron)
echo "0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/it-mydoc.ru/*.pem /var/www/mydoc-loyalty/nginx/ssl/ && cd /var/www/mydoc-loyalty && docker-compose restart nginx" | crontab -
```

### 5. Запуск приложения

```bash
cd /var/www/mydoc-loyalty

# Создание необходимых директорий
mkdir -p uploads backend/qrcodes nginx/ssl

# Даем права на выполнение
chmod +x deploy.sh

# Запуск
./deploy.sh
```

### 6. Проверка развертывания

```bash
# Проверка контейнеров
docker-compose ps

# Ожидаемый результат: все контейнеры Up

# Проверка логов
docker-compose logs backend | tail -20

# Проверка health endpoint
curl https://it-mydoc.ru/api/health

# Ожидаемый ответ:
# {"status":"healthy","service":"Моя ❤ скидка","version":"1.0.0"}

# Проверка API документации
curl -I https://it-mydoc.ru/api/docs

# Проверка Frontend
curl -I https://it-mydoc.ru
```

### 7. Создание первого администратора

```bash
cd /var/www/mydoc-loyalty

# Запуск скрипта инициализации
docker-compose exec backend python scripts/seed_data.py

# Тестовые данные созданы!
```

## После развертывания

### Тестирование

- [ ] Открыть https://it-mydoc.ru - должна загрузиться страница входа
- [ ] Войти с тестовыми данными: admin@it-mydoc.ru / admin123
- [ ] Проверить Dashboard - должны отображаться балансы
- [ ] Открыть https://it-mydoc.ru/api/docs - должна быть доступна документация API
- [ ] Проверить https://it-mydoc.ru/admin - админ-панель

### Безопасность

- [ ] Изменить пароль администратора по умолчанию
- [ ] Настроить firewall (UFW):
  ```bash
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw enable
  ```
- [ ] Настроить автоматические обновления безопасности
- [ ] Регулярные backup базы данных
- [ ] Мониторинг логов

### Интеграции

- [ ] Настроить интеграцию с 1С:УМЦ
- [ ] Настроить интеграцию с Bitrix24
- [ ] Настроить Email (SMTP)
- [ ] Настроить SMS-уведомления
- [ ] Протестировать webhooks

### Мониторинг

```bash
# Установка мониторинга (опционально)
# Prometheus + Grafana или simple monitoring

# Простой мониторинг через cron
cat > /usr/local/bin/monitor-mydoc.sh << 'EOF'
#!/bin/bash
cd /var/www/mydoc-loyalty
if ! docker-compose ps | grep -q "Up"; then
    echo "$(date): Сервис не запущен! Перезапуск..." >> /var/log/mydoc-monitor.log
    docker-compose up -d
fi
EOF

chmod +x /usr/local/bin/monitor-mydoc.sh
echo "*/5 * * * * /usr/local/bin/monitor-mydoc.sh" | crontab -
```

### Backup

```bash
# Настройка автоматического backup БД
cat > /usr/local/bin/backup-mydoc.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/mydoc-loyalty"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

cd /var/www/mydoc-loyalty

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump -U mydoc_user mydoc_loyalty | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "$(date): Backup завершен - $BACKUP_DIR/db_$DATE.sql.gz"
EOF

chmod +x /usr/local/bin/backup-mydoc.sh

# Запуск каждый день в 3:00
echo "0 3 * * * /usr/local/bin/backup-mydoc.sh >> /var/log/mydoc-backup.log 2>&1" | crontab -
```

## Полезные команды

### Управление

```bash
# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Запуск
docker-compose up -d

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Обслуживание БД

```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U mydoc_user -d mydoc_loyalty

# Backup
docker-compose exec postgres pg_dump -U mydoc_user mydoc_loyalty > backup.sql

# Restore
docker-compose exec -T postgres psql -U mydoc_user mydoc_loyalty < backup.sql

# Очистка логов транзакций (старше 90 дней)
docker-compose exec backend python -c "
from database import SessionLocal
from models import LoyaltyTransaction
from datetime import datetime, timedelta

db = SessionLocal()
cutoff = datetime.utcnow() - timedelta(days=90)
deleted = db.query(LoyaltyTransaction).filter(LoyaltyTransaction.created_at < cutoff).delete()
db.commit()
print(f'Удалено {deleted} старых транзакций')
"
```

### Отладка

```bash
# Подключение к контейнеру
docker-compose exec backend bash
docker-compose exec frontend sh

# Просмотр переменных окружения
docker-compose exec backend env

# Проверка подключения к БД
docker-compose exec backend python -c "from database import engine; print(engine.connect())"

# Проверка подключения к Redis
docker-compose exec redis redis-cli ping
```

## Контакты и поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте документацию: `/tmp/mydoc-loyalty/README.md`
3. См. Quick Start: `/tmp/mydoc-loyalty/QUICK_START.md`

---

**Дата развертывания:** _____________

**Ответственный:** _____________

**Версия:** 1.0.0

