#!/bin/bash
# Скрипт автоматического резервного копирования базы данных

BACKUP_DIR="/var/backups/mydoc-loyalty"
PROJECT_DIR="/tmp/mydoc-loyalty"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Создаем директорию для бэкапов
mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🔄 Начало резервного копирования..."

# Бэкап PostgreSQL
log "📦 Создание бэкапа базы данных..."
docker exec mydoc_postgres pg_dump -U mydoc_user mydoc_loyalty | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

if [ $? -eq 0 ]; then
    log "✅ Бэкап базы данных создан: db_backup_$DATE.sql.gz"
    
    # Размер бэкапа
    SIZE=$(du -h "$BACKUP_DIR/db_backup_$DATE.sql.gz" | cut -f1)
    log "📊 Размер бэкапа: $SIZE"
else
    log "❌ Ошибка создания бэкапа базы данных!"
    exit 1
fi

# Бэкап файлов uploads
if [ -d "$PROJECT_DIR/uploads" ] && [ "$(ls -A $PROJECT_DIR/uploads)" ]; then
    log "📦 Создание бэкапа загруженных файлов..."
    tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" -C "$PROJECT_DIR" uploads
    
    if [ $? -eq 0 ]; then
        SIZE=$(du -h "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" | cut -f1)
        log "✅ Бэкап файлов создан: uploads_backup_$DATE.tar.gz (Размер: $SIZE)"
    fi
fi

# Удаление старых бэкапов (старше RETENTION_DAYS дней)
log "🗑️ Удаление бэкапов старше $RETENTION_DAYS дней..."
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "uploads_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Статистика бэкапов
TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "📊 Всего бэкапов: $TOTAL_BACKUPS, Общий размер: $TOTAL_SIZE"

log "✅ Резервное копирование завершено"








