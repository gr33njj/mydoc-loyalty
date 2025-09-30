# Моя ❤ скидка - Система лояльности для медицинского центра

Комплексная микросервисная платформа для управления программой лояльности, подарочными сертификатами и реферальной системой.

## 🏗️ Архитектура

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 18 + TypeScript
- **Admin Panel**: React 18 + TypeScript
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Proxy**: Nginx

## 🚀 Основные функции

### 1. Программа лояльности
- Бонусные баллы и кешбэк
- История транзакций с audit trail
- Синхронизация с 1С:УМЦ
- Личный кабинет пациента

### 2. Подарочные сертификаты
- Электронные сертификаты с QR-кодами
- Передача между клиентами
- Проверка на кассе
- Email/SMS уведомления

### 3. Реферальная CPA-система
- Реферальные коды для пациентов и врачей
- Многоуровневая структура вознаграждений
- Аналитика и статистика
- Автоматическое начисление бонусов

## 📋 Требования

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- SSL сертификат для домена

## 🛠️ Установка и запуск

### 1. Клонирование и настройка

```bash
# Создайте рабочую директорию
mkdir -p /var/www/mydoc-loyalty
cd /var/www/mydoc-loyalty

# Скопируйте файлы проекта
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

### 2. Настройка SSL сертификата

```bash
# Создайте директорию для SSL
mkdir -p nginx/ssl

# Получите Let's Encrypt сертификат (рекомендуется)
certbot certonly --standalone -d it-mydoc.ru
cp /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/it-mydoc.ru/privkey.pem nginx/ssl/

# Или используйте self-signed для разработки
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem
```

### 3. Запуск приложения

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f backend
```

### 4. Инициализация базы данных

```bash
# База данных инициализируется автоматически при первом запуске
# Для создания тестовых данных:
docker-compose exec backend python scripts/seed_data.py
```

## 🌐 Доступ к сервисам

- **Frontend (Личный кабинет)**: https://it-mydoc.ru
- **Admin Panel**: https://it-mydoc.ru/admin
- **API Documentation**: https://it-mydoc.ru/api/docs
- **API Redoc**: https://it-mydoc.ru/api/redoc

## 📚 API Endpoints

### Лояльность
- `GET /api/loyalty/balance/{user_id}` - Баланс пользователя
- `GET /api/loyalty/transactions/{user_id}` - История транзакций
- `POST /api/loyalty/accrue` - Начисление баллов
- `POST /api/loyalty/deduct` - Списание баллов

### Сертификаты
- `POST /api/certificates/create` - Создание сертификата
- `GET /api/certificates/{cert_id}` - Информация о сертификате
- `POST /api/certificates/transfer` - Передача сертификата
- `POST /api/certificates/verify` - Проверка QR-кода
- `POST /api/certificates/redeem` - Использование сертификата

### Рефералы
- `POST /api/referrals/create-code` - Создание реферального кода
- `POST /api/referrals/register-event` - Регистрация события
- `GET /api/referrals/stats/{user_id}` - Статистика рефералов
- `GET /api/referrals/rewards/{user_id}` - История вознаграждений

## 🔐 Безопасность

- JWT авторизация с refresh tokens
- HTTPS only в production
- Rate limiting на API endpoints
- SQL injection защита через ORM
- XSS защита
- CORS настроен для домена
- Шифрование персональных данных

## 🔄 Интеграции

### 1С:УМЦ (Управление Медицинским Центром)
- Webhook endpoints для получения данных о визитах
- REST API для синхронизации балансов
- JSON/XML обмен данными
- Идемпотентность операций

### Bitrix24
- SSO авторизация
- Синхронизация профилей пациентов
- Webhook уведомления

## 📊 Мониторинг

```bash
# Логи всех сервисов
docker-compose logs -f

# Статистика контейнеров
docker stats

# Проверка здоровья
curl https://it-mydoc.ru/api/health
```

## 🔧 Разработка

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

### Admin Panel

```bash
cd admin
npm install
npm start
```

## 📝 Обновление

```bash
# Остановка сервисов
docker-compose down

# Обновление кода
git pull origin main

# Пересборка и запуск
docker-compose up -d --build

# Миграции БД (если нужны)
docker-compose exec backend alembic upgrade head
```

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. Перезапустите сервисы: `docker-compose restart`

## 📄 Лицензия

Proprietary - Все права защищены © 2025
