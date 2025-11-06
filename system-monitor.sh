#!/bin/bash
# Скрипт мониторинга системных метрик

METRICS_FILE="/var/log/mydoc-metrics.log"

log_metric() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$METRICS_FILE"
}

# CPU использование
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
log_metric "CPU: ${CPU_USAGE}%"

# RAM использование
MEM_TOTAL=$(free -m | awk 'NR==2{print $2}')
MEM_USED=$(free -m | awk 'NR==2{print $3}')
MEM_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($MEM_USED/$MEM_TOTAL)*100}")
log_metric "RAM: ${MEM_USED}MB / ${MEM_TOTAL}MB (${MEM_PERCENT}%)"

# Дисковое пространство
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
DISK_AVAILABLE=$(df -h / | awk 'NR==2 {print $4}')
log_metric "DISK: Used ${DISK_USAGE}, Available ${DISK_AVAILABLE}"

# Docker контейнеры
CONTAINERS_RUNNING=$(docker ps -q | wc -l)
CONTAINERS_TOTAL=$(docker ps -aq | wc -l)
log_metric "CONTAINERS: ${CONTAINERS_RUNNING}/${CONTAINERS_TOTAL} running"

# Статистика контейнеров
for container in mydoc_backend mydoc_frontend mydoc_admin mydoc_postgres mydoc_redis mydoc_nginx; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        # CPU и Memory для контейнера
        STATS=$(docker stats $container --no-stream --format "CPU: {{.CPUPerc}}, MEM: {{.MemUsage}}" 2>/dev/null)
        log_metric "$container - $STATS"
    fi
done

# Количество активных подключений к nginx
NGINX_CONNECTIONS=$(docker exec mydoc_nginx nginx -T 2>/dev/null | grep -c "server {" || echo "N/A")
log_metric "NGINX: ${NGINX_CONNECTIONS} server blocks configured"

# Размер базы данных
DB_SIZE=$(docker exec mydoc_postgres psql -U mydoc_user -d mydoc_loyalty -t -c "SELECT pg_size_pretty(pg_database_size('mydoc_loyalty'));" 2>/dev/null | xargs)
log_metric "DB_SIZE: ${DB_SIZE}"

# Количество записей в основных таблицах
USERS_COUNT=$(docker exec mydoc_postgres psql -U mydoc_user -d mydoc_loyalty -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
log_metric "USERS: ${USERS_COUNT}"

# Проверка ошибок в логах за последний час
BACKEND_ERRORS=$(docker logs mydoc_backend --since 1h 2>&1 | grep -i "error" | wc -l)
if [ "$BACKEND_ERRORS" -gt 10 ]; then
    log_metric "⚠️ BACKEND_ERRORS: ${BACKEND_ERRORS} errors in last hour"
else
    log_metric "BACKEND_ERRORS: ${BACKEND_ERRORS}"
fi

