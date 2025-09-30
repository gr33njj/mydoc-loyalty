#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных в БД
"""

import sys
import os
from datetime import datetime, timedelta

# Добавление родительской директории в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Base, engine
from models import (
    User, LoyaltyAccount, LoyaltyTransaction, TransactionType,
    Certificate, CertificateStatus,
    ReferralCode, ReferralEvent, ReferralEventType, RewardRule, RewardType
)
from routers.auth import get_password_hash
import random


def create_tables():
    """Создание всех таблиц"""
    print("📊 Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")


def seed_reward_rules(db):
    """Создание правил вознаграждений"""
    print("📋 Создание правил вознаграждений...")
    
    rules = [
        RewardRule(
            name="Регистрация пациента",
            description="Бонус за регистрацию приглашенного пациента",
            event_type=ReferralEventType.REGISTRATION,
            referrer_type="any",
            reward_type=RewardType.POINTS,
            reward_value=100,
            applies_to_level=1,
            is_active=True
        ),
        RewardRule(
            name="Первый визит пациента",
            description="Бонус за первый визит приглашенного пациента",
            event_type=ReferralEventType.FIRST_VISIT,
            referrer_type="any",
            reward_type=RewardType.POINTS,
            reward_value=500,
            applies_to_level=1,
            is_active=True
        ),
        RewardRule(
            name="Оплаченная услуга - процент для пациента",
            description="Процент от суммы оплаченной услуги приглашенным",
            event_type=ReferralEventType.PAID_SERVICE,
            referrer_type="patient",
            reward_type=RewardType.PERCENTAGE,
            reward_value=5.0,  # 5%
            applies_to_level=1,
            is_active=True
        ),
        RewardRule(
            name="Оплаченная услуга - процент для врача",
            description="Процент от суммы для врача-рекомендателя",
            event_type=ReferralEventType.PAID_SERVICE,
            referrer_type="doctor",
            reward_type=RewardType.PERCENTAGE,
            reward_value=10.0,  # 10%
            applies_to_level=1,
            is_active=True
        ),
    ]
    
    for rule in rules:
        db.add(rule)
    
    db.commit()
    print(f"✅ Создано {len(rules)} правил вознаграждений")


def seed_test_users(db):
    """Создание тестовых пользователей"""
    print("👥 Создание тестовых пользователей...")
    
    users_data = [
        {
            "email": "admin@it-mydoc.ru",
            "phone": "+79991234567",
            "full_name": "Администратор Системы",
            "password": "admin123",
            "role": "admin",
            "tier": "platinum"
        },
        {
            "email": "cashier@it-mydoc.ru",
            "phone": "+79991234568",
            "full_name": "Кассир Мария",
            "password": "cashier123",
            "role": "cashier",
            "tier": "gold"
        },
        {
            "email": "doctor@it-mydoc.ru",
            "phone": "+79991234569",
            "full_name": "Доктор Иванов",
            "password": "doctor123",
            "role": "doctor",
            "tier": "gold"
        },
        {
            "email": "patient@it-mydoc.ru",
            "phone": "+79991234570",
            "full_name": "Пациент Петров",
            "password": "patient123",
            "role": "patient",
            "tier": "silver"
        },
    ]
    
    created_users = []
    
    for user_data in users_data:
        # Проверка существования
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"⏭️  Пользователь {user_data['email']} уже существует")
            created_users.append(existing)
            continue
        
        user = User(
            email=user_data["email"],
            phone=user_data["phone"],
            full_name=user_data["full_name"],
            password_hash=get_password_hash(user_data["password"]),
            role=user_data["role"],
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.flush()
        
        # Создание аккаунта лояльности
        card_number = f"ML{random.randint(10000000, 99999999)}"
        loyalty = LoyaltyAccount(
            user_id=user.id,
            card_number=card_number,
            card_tier=user_data["tier"],
            points_balance=random.randint(0, 5000),
            cashback_balance=random.uniform(0, 1000)
        )
        db.add(loyalty)
        
        # Создание реферального кода для пациентов и врачей
        if user_data["role"] in ["patient", "doctor"]:
            ref_code = ReferralCode(
                user_id=user.id,
                code=f"REF-{user_data['role'][:3].upper()}-{random.randint(1000, 9999)}",
                referrer_type=user_data["role"]
            )
            db.add(ref_code)
        
        created_users.append(user)
        print(f"✅ Создан пользователь: {user_data['email']} (пароль: {user_data['password']})")
    
    db.commit()
    return created_users


def seed_test_transactions(db, users):
    """Создание тестовых транзакций"""
    print("💳 Создание тестовых транзакций...")
    
    patient = next((u for u in users if u.role == "patient"), None)
    if not patient:
        print("⚠️  Пациент не найден, пропуск создания транзакций")
        return
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == patient.id).first()
    if not account:
        print("⚠️  Аккаунт лояльности не найден")
        return
    
    transactions = [
        {
            "type": TransactionType.ACCRUAL,
            "amount": 500,
            "currency": "points",
            "description": "Бонус за регистрацию",
            "source": "registration"
        },
        {
            "type": TransactionType.ACCRUAL,
            "amount": 1000,
            "currency": "points",
            "description": "Бонус за первый визит",
            "source": "visit"
        },
        {
            "type": TransactionType.ACCRUAL,
            "amount": 250.50,
            "currency": "cashback",
            "description": "Кешбэк за услугу УЗИ",
            "source": "purchase"
        },
        {
            "type": TransactionType.DEDUCTION,
            "amount": 300,
            "currency": "points",
            "description": "Списание баллов на приеме",
            "source": "manual"
        },
    ]
    
    for trans_data in transactions:
        trans = LoyaltyTransaction(
            account_id=account.id,
            transaction_type=trans_data["type"],
            amount=trans_data["amount"],
            currency=trans_data["currency"],
            description=trans_data["description"],
            source=trans_data["source"]
        )
        db.add(trans)
    
    db.commit()
    print(f"✅ Создано {len(transactions)} тестовых транзакций")


def seed_test_certificates(db, users):
    """Создание тестовых сертификатов"""
    print("🎁 Создание тестовых сертификатов...")
    
    patient = next((u for u in users if u.role == "patient"), None)
    admin = next((u for u in users if u.role == "admin"), None)
    
    if not patient or not admin:
        print("⚠️  Пользователи не найдены, пропуск создания сертификатов")
        return
    
    certificates = [
        {
            "code": f"CERT-TEST-{random.randint(10000, 99999)}",
            "initial_amount": 5000,
            "current_amount": 5000,
            "owner_id": patient.id,
            "issued_by_id": admin.id,
            "valid_until": datetime.utcnow() + timedelta(days=365),
            "design_template": "default",
            "message": "Поздравляем! Этот сертификат на 5000 рублей для вас!"
        },
        {
            "code": f"CERT-TEST-{random.randint(10000, 99999)}",
            "initial_amount": 3000,
            "current_amount": 1500,
            "owner_id": patient.id,
            "issued_by_id": admin.id,
            "valid_until": datetime.utcnow() + timedelta(days=180),
            "design_template": "birthday",
            "message": "С Днем Рождения!"
        },
    ]
    
    for cert_data in certificates:
        cert = Certificate(**cert_data, status=CertificateStatus.ACTIVE)
        db.add(cert)
    
    db.commit()
    print(f"✅ Создано {len(certificates)} тестовых сертификатов")


def main():
    """Главная функция"""
    print("=" * 60)
    print("🌱 Инициализация базы данных - Моя ❤ скидка")
    print("=" * 60)
    
    # Создание таблиц
    create_tables()
    
    # Создание сессии БД
    db = SessionLocal()
    
    try:
        # Создание правил вознаграждений
        seed_reward_rules(db)
        
        # Создание тестовых пользователей
        users = seed_test_users(db)
        
        # Создание тестовых транзакций
        seed_test_transactions(db, users)
        
        # Создание тестовых сертификатов
        seed_test_certificates(db, users)
        
        print("=" * 60)
        print("✅ Инициализация завершена успешно!")
        print("=" * 60)
        print("\n📝 Тестовые учетные данные:")
        print("\nАдминистратор:")
        print("  Email: admin@it-mydoc.ru")
        print("  Пароль: admin123")
        print("\nКассир:")
        print("  Email: cashier@it-mydoc.ru")
        print("  Пароль: cashier123")
        print("\nДоктор:")
        print("  Email: doctor@it-mydoc.ru")
        print("  Пароль: doctor123")
        print("\nПациент:")
        print("  Email: patient@it-mydoc.ru")
        print("  Пароль: patient123")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ошибка при инициализации: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()