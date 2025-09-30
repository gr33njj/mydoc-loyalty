#!/bin/bash

# Скрипт развертывания для Моя ❤ скидка

set -e

echo "🚀 Развертывание Моя ❤ скидка"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Копирование из .env.example..."
    cp .env.example .env
    echo "⚠️  Пожалуйста, отредактируйте .env файл и запустите скрипт снова"
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p nginx/ssl uploads backend/qrcodes

# Проверка SSL сертификатов
if [ ! -f nginx/ssl/fullchain.pem ] || [ ! -f nginx/ssl/privkey.pem ]; then
    echo "⚠️  SSL сертификаты не найдены"
    echo "Создание self-signed сертификата для разработки..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/privkey.pem \
        -out nginx/ssl/fullchain.pem \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=MyDoc/CN=it-mydoc.ru"
    echo "✅ Self-signed сертификат создан"
    echo "ℹ️  Для production используйте Let's Encrypt!"
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker-compose build

# Запуск сервисов
echo "🚀 Запуск сервисов..."
docker-compose up -d

# Ожидание запуска БД
echo "⏳ Ожидание запуска PostgreSQL..."
sleep 10

# Инициализация БД тестовыми данными
echo "📊 Инициализация базы данных..."
docker-compose exec -T backend python scripts/seed_data.py

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Развертывание завершено!"
echo ""
echo "📍 Доступные сервисы:"
echo "   • Frontend: https://it-mydoc.ru"
echo "   • Admin Panel: https://it-mydoc.ru/admin"
echo "   • API Docs: https://it-mydoc.ru/api/docs"
echo ""
echo "🔍 Проверка статуса:"
echo "   docker-compose ps"
echo ""
echo "📝 Просмотр логов:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Остановка:"
echo "   docker-compose down"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
