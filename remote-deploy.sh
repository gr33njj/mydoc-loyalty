#!/bin/bash
#
# Скрипт автоматического развертывания на сервере 85.92.110.173
#

set -e

SERVER_IP="85.92.110.173"
SERVER_USER="root"
DOMAIN="it-mydoc.ru"
PROJECT_DIR="/var/www/mydoc-loyalty"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     РАЗВЕРТЫВАНИЕ МИКРОСЕРВИСА 'МОЯ ❤ СКИДКА'              ║"
echo "║     Сервер: $SERVER_IP                              ║"
echo "║     Домен: $DOMAIN                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Проверка подключения к серверу
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Ошибка: Не удается подключиться к серверу $SERVER_IP"
    echo "   Убедитесь, что:"
    echo "   1. Сервер доступен"
    echo "   2. SSH работает на порту 22"
    echo "   3. У вас есть SSH-ключ или пароль для подключения"
    exit 1
fi
echo "✅ Подключение к серверу успешно"
echo ""

# Копирование проекта на сервер
echo "📦 Копирование проекта на сервер..."
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '*.pyc' \
    --exclude '.env' \
    ./ $SERVER_USER@$SERVER_IP:$PROJECT_DIR/

echo "✅ Проект скопирован"
echo ""

# Выполнение команд на сервере
echo "🚀 Запуск установки на сервере..."

ssh $SERVER_USER@$SERVER_IP "bash -s" << 'ENDSSH'
set -e

PROJECT_DIR="/var/www/mydoc-loyalty"
DOMAIN="it-mydoc.ru"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     УСТАНОВКА НА СЕРВЕРЕ                                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

cd $PROJECT_DIR

# 1. Установка Docker и Docker Compose (если не установлены)
echo ""
echo "📦 Проверка Docker..."
if ! command -v docker &> /dev/null; then
    echo "   Docker не найден. Установка..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "   ✅ Docker установлен"
else
    echo "   ✅ Docker уже установлен: $(docker --version)"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "   Docker Compose не найден. Установка..."
    apt-get update
    apt-get install -y docker-compose
    echo "   ✅ Docker Compose установлен"
else
    echo "   ✅ Docker Compose уже установлен: $(docker-compose --version)"
fi

# 2. Установка certbot (если не установлен)
echo ""
echo "🔐 Проверка certbot..."
if ! command -v certbot &> /dev/null; then
    echo "   Certbot не найден. Установка..."
    apt-get update
    apt-get install -y certbot
    echo "   ✅ Certbot установлен"
else
    echo "   ✅ Certbot уже установлен"
fi

# 3. Создание необходимых директорий
echo ""
echo "📁 Создание директорий..."
mkdir -p nginx/ssl uploads backend/qrcodes
echo "   ✅ Директории созданы"

# 4. Проверка и получение SSL сертификата
echo ""
echo "🔐 Проверка SSL сертификата..."
if [ ! -f "nginx/ssl/fullchain.pem" ] || [ ! -f "nginx/ssl/privkey.pem" ]; then
    echo "   SSL сертификаты не найдены"
    
    # Остановка всех контейнеров, чтобы освободить порт 80
    docker-compose down 2>/dev/null || true
    
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        echo "   Найден существующий сертификат Let's Encrypt, копирование..."
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
        cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
        echo "   ✅ Сертификат скопирован"
    else
        echo "   Получение нового сертификата Let's Encrypt..."
        echo "   ⚠️  Убедитесь, что домен $DOMAIN указывает на этот сервер!"
        
        certbot certonly --standalone -d $DOMAIN \
            --agree-tos \
            --non-interactive \
            --email admin@$DOMAIN \
            --preferred-challenges http || {
            
            echo "   ⚠️  Не удалось получить сертификат Let's Encrypt"
            echo "   Создание self-signed сертификата для тестирования..."
            
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout nginx/ssl/privkey.pem \
                -out nginx/ssl/fullchain.pem \
                -subj "/C=RU/ST=Moscow/L=Moscow/O=MyDoc/CN=$DOMAIN"
            
            echo "   ✅ Self-signed сертификат создан"
            echo "   ⚠️  Для production получите настоящий SSL сертификат!"
        }
        
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
            cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
            echo "   ✅ Let's Encrypt сертификат получен и скопирован"
        fi
    fi
else
    echo "   ✅ SSL сертификаты уже существуют"
fi

# 5. Создание .env файла (если не существует)
echo ""
echo "⚙️  Проверка .env файла..."
if [ ! -f ".env" ]; then
    echo "   Создание .env файла..."
    cat > .env << 'EOF'
# Database
DB_PASSWORD=MyDoc2025SecurePassword!$(openssl rand -hex 8)

# JWT Security
JWT_SECRET=$(openssl rand -hex 32)
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
    
    # Генерация случайных секретов
    DB_PASSWORD="MyDoc2025SecurePassword!$(openssl rand -hex 8)"
    JWT_SECRET=$(openssl rand -hex 32)
    
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|g" .env
    sed -i "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|g" .env
    
    chmod 600 .env
    echo "   ✅ .env файл создан с безопасными паролями"
    echo "   ⚠️  Отредактируйте .env для настройки интеграций"
else
    echo "   ✅ .env файл уже существует"
fi

# 6. Даем права на выполнение
echo ""
echo "🔧 Установка прав доступа..."
chmod +x deploy.sh
chmod +x backend/scripts/seed_data.py
echo "   ✅ Права установлены"

# 7. Запуск сервисов
echo ""
echo "🚀 Запуск Docker контейнеров..."
docker-compose down
docker-compose build
docker-compose up -d

# 8. Ожидание запуска сервисов
echo ""
echo "⏳ Ожидание запуска сервисов (30 секунд)..."
sleep 30

# 9. Проверка статуса
echo ""
echo "🔍 Проверка статуса контейнеров..."
docker-compose ps

# 10. Инициализация БД тестовыми данными
echo ""
echo "📊 Инициализация базы данных..."
docker-compose exec -T backend python scripts/seed_data.py || {
    echo "   ⚠️  Первая попытка не удалась, пробуем еще раз через 10 секунд..."
    sleep 10
    docker-compose exec -T backend python scripts/seed_data.py
}

# 11. Настройка автообновления SSL
echo ""
echo "🔄 Настройка автообновления SSL сертификата..."
CRON_CMD="0 0 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/*.pem $PROJECT_DIR/nginx/ssl/ && cd $PROJECT_DIR && docker-compose restart nginx"
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_CMD") | crontab -
echo "   ✅ Автообновление настроено"

# 12. Настройка автоматического backup
echo ""
echo "💾 Настройка автоматического backup БД..."
mkdir -p /var/backups/mydoc-loyalty

cat > /usr/local/bin/backup-mydoc.sh << 'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/var/backups/mydoc-loyalty"
DATE=$(date +%Y%m%d_%H%M%S)
cd /var/www/mydoc-loyalty
docker-compose exec -T postgres pg_dump -U mydoc_user mydoc_loyalty | gzip > $BACKUP_DIR/db_$DATE.sql.gz
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
BACKUPEOF

chmod +x /usr/local/bin/backup-mydoc.sh

BACKUP_CRON="0 3 * * * /usr/local/bin/backup-mydoc.sh >> /var/log/mydoc-backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup-mydoc"; echo "$BACKUP_CRON") | crontab -
echo "   ✅ Автоматический backup настроен (каждый день в 3:00)"

# 13. Проверка доступности API
echo ""
echo "🔍 Проверка доступности API..."
sleep 5
if curl -k -s https://localhost/api/health > /dev/null 2>&1; then
    echo "   ✅ API доступен"
else
    echo "   ⚠️  API пока не отвечает, может потребоваться время"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     ✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Сервисы доступны по адресам:"
echo "   • Frontend: https://$DOMAIN"
echo "   • Admin Panel: https://$DOMAIN/admin"
echo "   • API Docs: https://$DOMAIN/api/docs"
echo "   • Health Check: https://$DOMAIN/api/health"
echo ""
echo "🔑 Тестовые данные для входа:"
echo "   Администратор:"
echo "     Email: admin@it-mydoc.ru"
echo "     Пароль: admin123"
echo ""
echo "   Кассир:"
echo "     Email: cashier@it-mydoc.ru"
echo "     Пароль: cashier123"
echo ""
echo "   Пациент:"
echo "     Email: patient@it-mydoc.ru"
echo "     Пароль: patient123"
echo ""
echo "⚠️  ВАЖНО: Смените пароли после первого входа!"
echo ""
echo "📝 Полезные команды:"
echo "   Просмотр логов: docker-compose logs -f backend"
echo "   Статус: docker-compose ps"
echo "   Перезапуск: docker-compose restart"
echo ""
echo "📚 Документация находится в: $PROJECT_DIR/"
echo ""

ENDSSH

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     🎉 ДЕПЛОЙ ЗАВЕРШЕН!                                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Откройте в браузере: https://$DOMAIN"
echo ""
