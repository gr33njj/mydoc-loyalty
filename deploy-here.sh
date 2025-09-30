#!/bin/bash
#
# Скрипт установки из ТЕКУЩЕЙ директории
#

set -e

CURRENT_DIR=$(pwd)
DOMAIN="it-mydoc.ru"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     УСТАНОВКА 'МОЯ ❤ СКИДКА' НА СЕРВЕРЕ                     ║"
echo "║     Директория: $CURRENT_DIR"
echo "╚═══════════════════════════════════════════════════════════════╝"

# 1. Установка Docker
echo ""
echo "📦 Проверка и установка Docker..."
if ! command -v docker &> /dev/null; then
    echo "   Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
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

# 2. Certbot
echo ""
echo "🔐 Установка certbot..."
if ! command -v certbot &> /dev/null; then
    apt-get update -qq
    apt-get install -y certbot openssl
    echo "   ✅ Certbot установлен"
else
    echo "   ✅ Certbot уже установлен"
fi

# 3. Создание директорий
echo ""
echo "📁 Создание директорий..."
mkdir -p nginx/ssl uploads backend/qrcodes
chmod 755 nginx/ssl uploads backend/qrcodes
echo "   ✅ Директории созданы"

# 4. SSL сертификат
echo ""
echo "🔐 Настройка SSL..."
if [ ! -f "nginx/ssl/fullchain.pem" ]; then
    echo "   Остановка контейнеров для освобождения порта 80..."
    docker-compose down 2>/dev/null || true
    
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        echo "   Копирование существующего Let's Encrypt сертификата..."
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
        cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
        echo "   ✅ Сертификат скопирован"
    else
        echo "   Попытка получить Let's Encrypt сертификат..."
        echo "   (Убедитесь что домен $DOMAIN указывает на этот сервер)"
        
        certbot certonly --standalone -d $DOMAIN \
            --agree-tos \
            --non-interactive \
            --email admin@$DOMAIN \
            --preferred-challenges http 2>&1 | tee /tmp/certbot.log || {
            
            echo "   ⚠️  Let's Encrypt не удалось получить"
            echo "   Создаю самоподписанный сертификат для тестирования..."
            
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout nginx/ssl/privkey.pem \
                -out nginx/ssl/fullchain.pem \
                -subj "/C=RU/ST=Moscow/L=Moscow/O=MyDoc/CN=$DOMAIN" 2>&1
            
            echo "   ✅ Самоподписанный сертификат создан"
            echo "   ⚠️  Для production получите настоящий SSL!"
        }
        
        # Попробуем скопировать если Let's Encrypt успешен
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
            cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
            echo "   ✅ Let's Encrypt сертификат получен!"
        fi
    fi
    chmod 644 nginx/ssl/*.pem
else
    echo "   ✅ SSL сертификаты уже существуют"
fi

# 5. Создание .env
echo ""
echo "⚙️  Создание .env файла..."
if [ ! -f ".env" ]; then
    DB_PASSWORD="MyDocSecure$(openssl rand -hex 8)"
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
    echo "   DB Password: $DB_PASSWORD"
    echo "   (сохраните эти данные!)"
else
    echo "   ✅ .env уже существует"
fi

# 6. Установка прав
echo ""
echo "🔧 Установка прав доступа..."
chmod +x deploy.sh 2>/dev/null || true
chmod +x backend/scripts/seed_data.py 2>/dev/null || true
echo "   ✅ Права установлены"

# 7. Запуск Docker
echo ""
echo "🚀 Сборка и запуск Docker контейнеров..."
echo "   Остановка старых контейнеров..."
docker-compose down 2>/dev/null || true

echo "   Сборка образов (это может занять несколько минут)..."
docker-compose build --no-cache

echo "   Запуск контейнеров..."
docker-compose up -d

# 8. Ожидание запуска
echo ""
echo "⏳ Ожидание запуска сервисов (40 секунд)..."
for i in {1..40}; do
    echo -n "."
    sleep 1
    if [ $((i % 10)) -eq 0 ]; then
        echo -n " ${i}s "
    fi
done
echo ""

# 9. Статус
echo ""
echo "🔍 Статус контейнеров:"
docker-compose ps

# 10. Инициализация БД
echo ""
echo "📊 Инициализация базы данных с тестовыми данными..."
echo "   Ожидание готовности PostgreSQL..."
sleep 10

# Несколько попыток инициализации
for attempt in 1 2 3; do
    echo "   Попытка $attempt из 3..."
    if docker-compose exec -T backend python scripts/seed_data.py 2>&1; then
        echo "   ✅ База данных инициализирована!"
        break
    else
        if [ $attempt -lt 3 ]; then
            echo "   Ожидание 10 секунд перед повтором..."
            sleep 10
        else
            echo "   ⚠️  Не удалось инициализировать БД автоматически"
            echo "   Попробуйте вручную: docker-compose exec backend python scripts/seed_data.py"
        fi
    fi
done

# 11. Проверка API
echo ""
echo "🔍 Проверка доступности API..."
sleep 5
for attempt in 1 2 3; do
    if curl -k -s https://localhost/api/health 2>/dev/null | grep -q "healthy"; then
        echo "   ✅ API работает!"
        break
    else
        if [ $attempt -lt 3 ]; then
            echo "   Ожидание... попытка $attempt из 3"
            sleep 5
        else
            echo "   ⚠️  API еще запускается, проверьте позже"
        fi
    fi
done

# 12. Настройка автозадач
echo ""
echo "🔄 Настройка автоматических задач..."

# Backup
mkdir -p /var/backups/mydoc-loyalty
cat > /usr/local/bin/backup-mydoc.sh << 'BEOF'
#!/bin/bash
BACKUP_DIR="/var/backups/mydoc-loyalty"
DATE=$(date +%Y%m%d_%H%M%S)
cd /tmp/mydoc-loyalty
docker-compose exec -T postgres pg_dump -U mydoc_user mydoc_loyalty | gzip > $BACKUP_DIR/db_$DATE.sql.gz
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
echo "$(date): Backup completed - $BACKUP_DIR/db_$DATE.sql.gz"
BEOF

chmod +x /usr/local/bin/backup-mydoc.sh

# Добавляем в cron (ежедневно в 3:00)
(crontab -l 2>/dev/null | grep -v "backup-mydoc"; echo "0 3 * * * /usr/local/bin/backup-mydoc.sh >> /var/log/mydoc-backup.log 2>&1") | crontab - 2>/dev/null || true

echo "   ✅ Автоматический backup настроен (каждый день в 3:00)"

# SSL автообновление
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    (crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 0 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/*.pem $CURRENT_DIR/nginx/ssl/ && cd $CURRENT_DIR && docker-compose restart nginx") | crontab - 2>/dev/null || true
    echo "   ✅ SSL автообновление настроено"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                ✅ УСТАНОВКА ЗАВЕРШЕНА!                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Сервисы доступны по адресам:"
echo "   • Frontend:       https://$DOMAIN"
echo "   • Admin Panel:    https://$DOMAIN/admin"
echo "   • API Docs:       https://$DOMAIN/api/docs"
echo "   • Health Check:   https://$DOMAIN/api/health"
echo ""
echo "🔑 Тестовые данные для входа:"
echo ""
echo "   Администратор:"
echo "     Email:    admin@it-mydoc.ru"
echo "     Пароль:   admin123"
echo ""
echo "   Кассир:"
echo "     Email:    cashier@it-mydoc.ru"
echo "     Пароль:   cashier123"
echo ""
echo "   Доктор:"
echo "     Email:    doctor@it-mydoc.ru"
echo "     Пароль:   doctor123"
echo ""
echo "   Пациент:"
echo "     Email:    patient@it-mydoc.ru"
echo "     Пароль:   patient123"
echo ""
echo "⚠️  ВАЖНО: Смените все пароли после первого входа!"
echo ""
echo "📝 Полезные команды:"
echo "   docker-compose ps                # Статус контейнеров"
echo "   docker-compose logs -f backend   # Логи backend"
echo "   docker-compose restart           # Перезапуск"
echo "   docker-compose down              # Остановка"
echo "   docker-compose up -d             # Запуск"
echo ""
echo "📁 Проект расположен в: $CURRENT_DIR"
echo ""
echo "🎉 Откройте https://$DOMAIN в браузере!"
echo ""
