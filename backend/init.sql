-- Инициализация БД для Моя ❤ скидка

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание таблиц выполняется SQLAlchemy автоматически

-- Вставка базовых правил вознаграждений для реферальной системы
-- (будет выполнено после создания таблиц SQLAlchemy)

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_loyalty_transactions_account_created 
    ON loyalty_transactions(account_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_certificates_owner_status 
    ON certificates(owner_id, status);

CREATE INDEX IF NOT EXISTS idx_certificates_code 
    ON certificates(code);

CREATE INDEX IF NOT EXISTS idx_referral_codes_code 
    ON referral_codes(code);

CREATE INDEX IF NOT EXISTS idx_referral_events_code_processed 
    ON referral_events(referral_code_id, processed);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity 
    ON audit_logs(entity_type, entity_id, created_at DESC);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_loyalty_accounts_updated_at BEFORE UPDATE ON loyalty_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
