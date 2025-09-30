from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime


# Перечисления
class TransactionType(str, enum.Enum):
    ACCRUAL = "accrual"  # Начисление
    DEDUCTION = "deduction"  # Списание
    REFUND = "refund"  # Возврат
    EXPIRATION = "expiration"  # Сгорание


class CertificateStatus(str, enum.Enum):
    ACTIVE = "active"  # Активный
    USED = "used"  # Использован
    EXPIRED = "expired"  # Истек
    CANCELLED = "cancelled"  # Отменен


class ReferralEventType(str, enum.Enum):
    REGISTRATION = "registration"  # Регистрация
    FIRST_VISIT = "first_visit"  # Первый визит
    PAID_SERVICE = "paid_service"  # Оплаченная услуга
    REPEAT_VISIT = "repeat_visit"  # Повторный визит


class RewardType(str, enum.Enum):
    FIXED = "fixed"  # Фиксированная сумма
    PERCENTAGE = "percentage"  # Процент
    POINTS = "points"  # Баллы


# === МОДЕЛИ ПОЛЬЗОВАТЕЛЕЙ ===

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=True)  # ID из 1C/Bitrix
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String)
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String, default="patient")  # patient, doctor, cashier, admin
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    loyalty_account = relationship("LoyaltyAccount", back_populates="user", uselist=False)
    certificates_owned = relationship("Certificate", foreign_keys="Certificate.owner_id", back_populates="owner")
    referral_codes = relationship("ReferralCode", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


# === МОДЕЛИ ЛОЯЛЬНОСТИ ===

class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Балансы
    points_balance = Column(Float, default=0.0)  # Бонусные баллы
    cashback_balance = Column(Float, default=0.0)  # Кешбэк в рублях
    
    # Накопительная статистика
    total_points_earned = Column(Float, default=0.0)
    total_points_spent = Column(Float, default=0.0)
    total_cashback_earned = Column(Float, default=0.0)
    total_cashback_spent = Column(Float, default=0.0)
    
    # Карта лояльности
    card_number = Column(String, unique=True, index=True, nullable=True)
    card_tier = Column(String, default="bronze")  # bronze, silver, gold, platinum
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="loyalty_account")
    transactions = relationship("LoyaltyTransaction", back_populates="account")


class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("loyalty_accounts.id"))
    
    transaction_type = Column(Enum(TransactionType))
    amount = Column(Float)  # Сумма баллов/кешбэка
    currency = Column(String, default="points")  # points или cashback
    
    # Связь с источником
    source = Column(String)  # visit, purchase, referral, manual, etc.
    source_id = Column(String, nullable=True)  # ID визита/покупки в 1C
    
    description = Column(Text)
    extra_data = Column(JSON, nullable=True)  # Дополнительные данные
    
    # Идемпотентность
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    
    # Для отмены операций
    is_reversed = Column(Boolean, default=False)
    reversed_by_id = Column(Integer, ForeignKey("loyalty_transactions.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    account = relationship("LoyaltyAccount", back_populates="transactions")


# === МОДЕЛИ СЕРТИФИКАТОВ ===

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Основные данные
    code = Column(String, unique=True, index=True)  # Уникальный код сертификата
    qr_code_path = Column(String, nullable=True)  # Путь к файлу QR-кода
    
    # Финансовые данные
    initial_amount = Column(Float)  # Начальная сумма
    current_amount = Column(Float)  # Текущий баланс
    currency = Column(String, default="RUB")
    
    # Статус
    status = Column(Enum(CertificateStatus), default=CertificateStatus.ACTIVE)
    
    # Владение
    owner_id = Column(Integer, ForeignKey("users.id"))
    issued_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Даты
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Дополнительная информация
    design_template = Column(String, default="default")  # Шаблон дизайна
    message = Column(Text, nullable=True)  # Персональное сообщение
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="certificates_owned")
    transfers = relationship("CertificateTransfer", back_populates="certificate")
    redemptions = relationship("CertificateRedemption", back_populates="certificate")


class CertificateTransfer(Base):
    __tablename__ = "certificate_transfers"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"))
    
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    
    message = Column(Text, nullable=True)
    transferred_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    certificate = relationship("Certificate", back_populates="transfers")


class CertificateRedemption(Base):
    __tablename__ = "certificate_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"))
    
    amount_used = Column(Float)  # Использованная сумма
    remaining_amount = Column(Float)  # Остаток после использования
    
    # Связь с 1C
    onec_document_id = Column(String, nullable=True)  # ID документа в 1C
    
    redeemed_at = Column(DateTime(timezone=True), server_default=func.now())
    redeemed_by_id = Column(Integer, ForeignKey("users.id"))  # Кассир
    
    notes = Column(Text, nullable=True)
    
    # Relationships
    certificate = relationship("Certificate", back_populates="redemptions")


# === МОДЕЛИ РЕФЕРАЛЬНОЙ СИСТЕМЫ ===

class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    code = Column(String, unique=True, index=True)
    
    # Тип реферала
    referrer_type = Column(String)  # patient, doctor
    
    # Статистика
    total_referrals = Column(Integer, default=0)
    successful_referrals = Column(Integer, default=0)  # Завершили первый визит
    total_revenue = Column(Float, default=0.0)  # Общая выручка от рефералов
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="referral_codes")
    events = relationship("ReferralEvent", back_populates="referral_code")


class ReferralEvent(Base):
    __tablename__ = "referral_events"

    id = Column(Integer, primary_key=True, index=True)
    referral_code_id = Column(Integer, ForeignKey("referral_codes.id"))
    
    # Приглашенный пользователь
    referred_user_id = Column(Integer, ForeignKey("users.id"))
    
    event_type = Column(Enum(ReferralEventType))
    
    # Финансовые данные
    transaction_amount = Column(Float, nullable=True)  # Сумма покупки/услуги
    
    # Связь с 1C
    onec_document_id = Column(String, nullable=True)
    
    processed = Column(Boolean, default=False)  # Обработано ли вознаграждение
    
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    referral_code = relationship("ReferralCode", back_populates="events")
    rewards = relationship("ReferralReward", back_populates="event")


class ReferralReward(Base):
    __tablename__ = "referral_rewards"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("referral_events.id"))
    
    # Получатель вознаграждения
    recipient_user_id = Column(Integer, ForeignKey("users.id"))
    
    reward_type = Column(Enum(RewardType))
    reward_amount = Column(Float)
    
    # Уровень реферала (для многоуровневой системы)
    referral_level = Column(Integer, default=1)
    
    # Связь с транзакцией лояльности
    loyalty_transaction_id = Column(Integer, ForeignKey("loyalty_transactions.id"), nullable=True)
    
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    event = relationship("ReferralEvent", back_populates="rewards")


class RewardRule(Base):
    """Правила начисления вознаграждений"""
    __tablename__ = "reward_rules"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String)
    description = Column(Text, nullable=True)
    
    # Условия
    event_type = Column(Enum(ReferralEventType))
    referrer_type = Column(String)  # patient, doctor, any
    
    # Вознаграждение
    reward_type = Column(Enum(RewardType))
    reward_value = Column(Float)  # Сумма или процент
    
    # Многоуровневость
    applies_to_level = Column(Integer, default=1)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# === AUDIT LOG ===

class AuditLog(Base):
    """Аудит всех операций для безопасности и отслеживания"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    action = Column(String)  # create_certificate, transfer, redeem, etc.
    entity_type = Column(String)  # certificate, transaction, referral, etc.
    entity_id = Column(Integer, nullable=True)
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
