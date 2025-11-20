#!/bin/bash
# Скрипт проверки здоровья системы и автоматического восстановления

LOG_FILE="/var/log/mydoc-health-check.log"
PROJECT_DIR="/tmp/mydoc-loyalty"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_container() {
    local container_name=$1
    local status=$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null)
    
    if [ "$status" != "true" ]; then
        log "❌ $container_name не работает! Перезапуск..."
        cd "$PROJECT_DIR" && docker-compose restart "$container_name"
        sleep 5
        
        status=$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null)
        if [ "$status" == "true" ]; then
            log "✅ $container_name успешно перезапущен"
        else
            log "🚨 КРИТИЧНО: $container_name не удалось перезапустить!"
        fi
        return 1
    fi
    return 0
}

check_api() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" https://it-mydoc.ru/api/health 2>/dev/null)
    
    if [ "$response" != "200" ]; then
        log "❌ API не отвечает (код: $response)! Перезапуск backend..."
        cd "$PROJECT_DIR" && docker-compose restart backend nginx
        sleep 10
        
        response=$(curl -s -o /dev/null -w "%{http_code}" https://it-mydoc.ru/api/health 2>/dev/null)
        if [ "$response" == "200" ]; then
            log "✅ API восстановлен"
        else
            log "🚨 КРИТИЧНО: API не восстановлен!"
        fi
        return 1
    fi
    return 0
}

check_disk_space() {
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 85 ]; then
        log "⚠️ Дисковое пространство заканчивается: ${usage}%"
        
        # Очистка старых логов Docker
        docker system prune -af --filter "until=72h" > /dev/null 2>&1
        log "✅ Очищены старые Docker образы"
        
        # Очистка логов
        find /var/lib/docker/containers/ -name "*.log" -type f -mtime +7 -delete 2>/dev/null
        log "✅ Очищены старые логи контейнеров"
    fi
}

check_ssl_expiry() {
    local days_left=$(openssl x509 -in /etc/letsencrypt/live/it-mydoc.ru/fullchain.pem -noout -checkend 604800 2>/dev/null && echo "OK" || echo "EXPIRING")
    
    if [ "$days_left" == "EXPIRING" ]; then
        log "⚠️ SSL сертификат истекает менее чем через 7 дней! Обновление..."
        certbot renew --force-renewal
        cp /etc/letsencrypt/live/it-mydoc.ru/*.pem "$PROJECT_DIR/nginx/ssl/"
        cd "$PROJECT_DIR" && docker-compose restart nginx
        log "✅ SSL сертификат обновлен"
    fi
}

# Основная проверка
log "🔍 Начало проверки системы"

# Проверка контейнеров
check_container "mydoc_postgres"
check_container "mydoc_redis"
check_container "mydoc_backend"
check_container "mydoc_frontend"
check_container "mydoc_admin"
check_container "mydoc_nginx"

# Проверка API
check_api

# Проверка дискового пространства
check_disk_space

# Проверка SSL (только раз в день в 03:00)
if [ "$(date +%H)" == "03" ]; then
    check_ssl_expiry
fi

log "✅ Проверка завершена"








