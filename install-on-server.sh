#!/bin/bash
#
# Скрипт для запуска НЕПОСРЕДСТВЕННО НА СЕРВЕРЕ 85.92.110.173
# Сначала скопируйте проект, затем запустите этот скрипт на сервере
#

set -e

PROJECT_DIR="/var/www/mydoc-loyalty"
DOMAIN="it-mydoc.ru"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     УСТАНОВКА 'МОЯ ❤ СКИДКА' НА СЕРВЕРЕ                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Переход в директорию проекта
cd $PROJECT_DIR

# 1. Установка Docker и Docker Compose
echo ""
echo "📦 Установка Docker и Docker Compose..."
if ! command -v docker &> /dev/null; then
    echo "   Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "   ✅ Docker установлен"
else
    echo "   ✅ Docker уже установлен: $(docker --version)"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "   Установка Docker Compose..."
    apt-get update -qq
    apt-get install -y docker-compose
    echo "   ✅ Docker Compose установлен"
else
    echo "   ✅ Docker Compose уже установлен: $(docker-compose --version)"
fi

# 2. Установка certbot
echo ""
echo "🔐 Установка certbot..."
if ! command -v certbot &> /dev/null; then
    apt-get update -qq
    apt-get install -y certbot
    echo "   ✅ Certbot установлен"
else
    echo "   ✅ Certbot уже установлен"
fi

# 3. Создание директорий
echo ""
echo "📁 Создание необходимых директорий..."
mkdir -p nginx/ssl uploads backend/qrcodes
echo "   ✅ Директории созданы"

# 4. SSL сертификат
echo ""
echo "🔐 Настройка SSL сертификата..."
if [ ! -f "nginx/ssl/fullchain.pem" ]; then
    docker-compose down 2>/dev/null || true
    
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        echo "   Копирование существующего сертификата..."
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
        cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
        echo "   ✅ Сертификат скопирован"
    else
        echo "   Получение Let's Encrypt сертификата..."
        certbot certonly --standalone -d $DOMAIN --agree-tos --non-interactive --email admin@$DOMAIN || {
            echo "   ⚠️  Let's Encrypt не удался, создаю self-signed..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout nginx/ssl/privkey.pem \
                -out nginx/ssl/fullchain.pem \
                -subj "/C=RU/ST=Moscow/L=Moscow/O=MyDoc/CN=$DOMAIN"
            echo "   ✅ Self-signed сертификат создан"
        }
        
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
            cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
            echo "   ✅ Let's Encrypt сертификат получен"
        fi
    fi
else
    echo "   ✅ SSL сертификаты уже существуют"
fi

# 5. Создание .env
echo ""
echo "⚙️  Создание .env файла..."
if [ ! -f ".env" ]; then
    DB_PASSWORD="MyDoc2025Secure!$(openssl rand -hex 4)"
    JWT_SECRET=$(openssl rand -hex 32)
    
    cat > .env << EOF
DB_PASSWORD=$DB_PASSWORD
JWT_SECRET=$JWT_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DOMAIN=$DOMAIN
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
    echo "   ✅ .env создан с безопасными паролями"
else
    echo "   ✅ .env уже существует"
fi

# 6. Права доступа
echo ""
echo "🔧 Установка прав..."
chmod +x deploy.sh backend/scripts/seed_data.py 2>/dev/null || true
echo "   ✅ Права установлены"

# 7. Запуск Docker
echo ""
echo "🚀 Запуск Docker контейнеров..."
docker-compose down 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

# 8. Ожидание
echo ""
echo "⏳ Ожидание запуска сервисов..."
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# 9. Статус
echo ""
echo "🔍 Статус контейнеров:"
docker-compose ps

# 10. Инициализация БД
echo ""
echo "📊 Инициализация базы данных с тестовыми данными..."
sleep 5
docker-compose exec -T backend python scripts/seed_data.py 2>/dev/null || {
    echo "   Повторная попытка через 10 секунд..."
    sleep 10
    docker-compose exec -T backend python scripts/seed_data.py
}

# 11. Cron jobs
echo ""
echo "🔄 Настройка автоматических задач..."

# SSL автообновление
CRON_SSL="0 0 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/*.pem $PROJECT_DIR/nginx/ssl/ && cd $PROJECT_DIR && docker-compose restart nginx"
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_SSL") | crontab - 2>/dev/null || true

# Backup БД
mkdir -p /var/backups/mydoc-loyalty
cat > /usr/local/bin/backup-mydoc.sh << 'BEOF'
#!/bin/bash
BACKUP_DIR="/var/backups/mydoc-loyalty"
DATE=$(date +%Y%m%d_%H%M%S)
cd /var/www/mydoc-loyalty
docker-compose exec -T postgres pg_dump -U mydoc_user mydoc_loyalty | gzip > $BACKUP_DIR/db_$DATE.sql.gz
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
BEOF

chmod +x /usr/local/bin/backup-mydoc.sh
CRON_BACKUP="0 3 * * * /usr/local/bin/backup-mydoc.sh >> /var/log/mydoc-backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup-mydoc"; echo "$CRON_BACKUP") | crontab - 2>/dev/null || true

echo "   ✅ Автозадачи настроены"

# 12. Финальная проверка
echo ""
echo "🔍 Проверка API..."
sleep 3
if curl -k -s https://localhost/api/health | grep -q "healthy"; then
    echo "   ✅ API работает!"
else
    echo "   ⚠️  API еще запускается..."
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                ✅ УСТАНОВКА ЗАВЕРШЕНА!                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Сервисы доступны:"
echo "   • Frontend:  https://$DOMAIN"
echo "   • Admin:     https://$DOMAIN/admin"
echo "   • API Docs:  https://$DOMAIN/api/docs"
echo "   • Health:    https://$DOMAIN/api/health"
echo ""
echo "🔑 Тестовые данные:"
echo "   Администратор: admin@it-mydoc.ru / admin123"
echo "   Кассир:        cashier@it-mydoc.ru / cashier123"
echo "   Пациент:       patient@it-mydoc.ru / patient123"
echo ""
echo "⚠️  ВАЖНО: Смените пароли после первого входа!"
echo ""
echo "📝 Полезные команды:"
echo "   docker-compose logs -f backend   # Логи"
echo "   docker-compose ps                # Статус"
echo "   docker-compose restart           # Перезапуск"
echo ""
