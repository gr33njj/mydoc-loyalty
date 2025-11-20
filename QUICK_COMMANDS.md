# ⚡ Быстрые команды для управления mydoc-loyalty

## 🚀 Основные команды

### Статус системы
```bash
cd /tmp/mydoc-loyalty && docker-compose ps
```

### Просмотр логов
```bash
# Все логи в реальном времени
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# Последние 50 строк
docker-compose logs --tail=50 backend
```

### Перезапуск сервисов
```bash
# Все сервисы
docker-compose restart

# Конкретный сервис
docker-compose restart backend
docker-compose restart nginx
```

### Обновление из GitHub
```bash
cd /tmp/mydoc-loyalty
git pull origin main
docker-compose up -d --build
```

---

## 🔍 Мониторинг

### Проверка здоровья
```bash
/tmp/mydoc-loyalty/health-check.sh
tail -f /var/log/mydoc-health-check.log
```

### Метрики системы
```bash
tail -20 /var/log/mydoc-metrics.log
```

### Проверка API
```bash
curl https://it-mydoc.ru/api/health
```

### Использование ресурсов
```bash
docker stats --no-stream
```

---

## 💾 Резервное копирование

### Создать бэкап вручную
```bash
/tmp/mydoc-loyalty/backup.sh
```

### Просмотр бэкапов
```bash
ls -lah /var/backups/mydoc-loyalty/
```

### Восстановление из бэкапа
```bash
# База данных
gunzip < /var/backups/mydoc-loyalty/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i mydoc_postgres psql -U mydoc_user mydoc_loyalty
```

---

## 🔐 SSL Сертификат

### Проверка срока действия
```bash
openssl x509 -in /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem -noout -dates
```

### Обновить вручную
```bash
certbot renew --force-renewal
cp /etc/letsencrypt/live/it-mydoc.ru/*.pem /tmp/mydoc-loyalty/nginx/ssl/
docker-compose restart nginx
```

---

## 🧹 Очистка

### Очистить Docker
```bash
docker system prune -a
```

### Очистить логи
```bash
truncate -s 0 /var/log/mydoc-*.log
```

---

## 🔧 Проблемы и решения

### API не отвечает
```bash
docker-compose restart backend nginx
docker-compose logs backend | tail -50
```

### База данных не доступна
```bash
docker-compose restart postgres
docker exec mydoc_postgres psql -U mydoc_user -d mydoc_loyalty -c "SELECT 1"
```

### Нет места на диске
```bash
df -h
docker system prune -af
find /var/lib/docker/containers/ -name "*.log" -type f -mtime +7 -delete
```

### Контейнер постоянно перезапускается
```bash
docker-compose logs <container_name> --tail=100
docker inspect <container_name>
```

---

## 📊 Полезная информация

### Автоматические задачи (Cron)
- **Каждые 5 минут:** Проверка здоровья системы
- **Каждые 15 минут:** Сбор метрик
- **Каждые 12 часов:** Обновление SSL
- **Ежедневно в 02:00:** Резервное копирование
- **Еженедельно (воскресенье 03:00):** Очистка Docker
- **Еженедельно (понедельник 04:00):** Перезапуск контейнеров

### Порты
- **80:** HTTP (редирект на HTTPS)
- **443:** HTTPS (основной)
- **3000:** Frontend (внутренний)
- **3001:** Admin (внутренний)
- **8000:** Backend API (внутренний)
- **5432:** PostgreSQL (внутренний)
- **6379:** Redis (внутренний)

### Логи
- `/var/log/mydoc-health-check.log` - Проверка здоровья
- `/var/log/mydoc-metrics.log` - Метрики системы
- `/var/log/mydoc-backup.log` - Резервное копирование
- `/var/log/certbot-renew.log` - Обновление SSL
- `/var/log/docker-cleanup.log` - Очистка Docker

### Файлы конфигурации
- `/tmp/mydoc-loyalty/.env` - Переменные окружения
- `/tmp/mydoc-loyalty/docker-compose.yml` - Docker композиция
- `/tmp/mydoc-loyalty/nginx/nginx.conf` - Конфигурация Nginx
- `/etc/cron.d/mydoc-loyalty` - Автоматические задачи

---

## 📖 Полная документация

Полная документация в файле: `/tmp/mydoc-loyalty/AUTOMATION.md`








