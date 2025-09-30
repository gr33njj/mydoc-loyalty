from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import httpx
from typing import Optional

from database import get_db
from models import User, LoyaltyAccount, LoyaltyTransaction, TransactionType, ReferralEvent, ReferralEventType
from schemas import OneCWebhookVisit, OneCWebhookPayment, BitrixWebhookContact
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_webhook_token(x_webhook_token: Optional[str] = Header(None)):
    """Проверка токена webhook (простая проверка для безопасности)"""
    if not x_webhook_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен webhook отсутствует"
        )
    # В production здесь должна быть реальная проверка токена
    return x_webhook_token


# === 1C Integration ===

@router.post("/1c/visit")
async def handle_1c_visit(
    visit_data: OneCWebhookVisit,
    db: Session = Depends(get_db),
    token: str = Depends(verify_webhook_token)
):
    """Webhook от 1С о визите пациента - начисление баллов/кешбэка"""
    
    logger.info(f"Получен webhook от 1С о визите: {visit_data.document_id}")
    
    # Поиск пользователя по external_id
    user = db.query(User).filter(User.external_id == visit_data.patient_external_id).first()
    
    if not user:
        logger.warning(f"Пользователь с external_id {visit_data.patient_external_id} не найден")
        return {"status": "user_not_found", "message": "Пользователь не найден в системе"}
    
    # Поиск аккаунта лояльности
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user.id).first()
    
    if not account:
        logger.warning(f"Аккаунт лояльности не найден для пользователя {user.id}")
        return {"status": "account_not_found", "message": "Аккаунт лояльности не найден"}
    
    # Начисление баллов (если указано)
    if visit_data.points_to_accrue and visit_data.points_to_accrue > 0:
        transaction = LoyaltyTransaction(
            account_id=account.id,
            transaction_type=TransactionType.ACCRUAL,
            amount=visit_data.points_to_accrue,
            currency="points",
            source="1c_visit",
            source_id=visit_data.document_id,
            description=f"Начисление баллов за визит от {visit_data.visit_date.strftime('%d.%m.%Y')}",
            idempotency_key=f"1c_visit_{visit_data.document_id}_points"
        )
        
        account.points_balance += visit_data.points_to_accrue
        account.total_points_earned += visit_data.points_to_accrue
        
        db.add(transaction)
        logger.info(f"Начислено {visit_data.points_to_accrue} баллов пользователю {user.email}")
    
    # Начисление кешбэка (если указано)
    if visit_data.cashback_to_accrue and visit_data.cashback_to_accrue > 0:
        transaction = LoyaltyTransaction(
            account_id=account.id,
            transaction_type=TransactionType.ACCRUAL,
            amount=visit_data.cashback_to_accrue,
            currency="cashback",
            source="1c_visit",
            source_id=visit_data.document_id,
            description=f"Начисление кешбэка за визит от {visit_data.visit_date.strftime('%d.%m.%Y')}",
            idempotency_key=f"1c_visit_{visit_data.document_id}_cashback"
        )
        
        account.cashback_balance += visit_data.cashback_to_accrue
        account.total_cashback_earned += visit_data.cashback_to_accrue
        
        db.add(transaction)
        logger.info(f"Начислено {visit_data.cashback_to_accrue} руб. кешбэка пользователю {user.email}")
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Баллы успешно начислены",
        "user_id": user.id,
        "points_accrued": visit_data.points_to_accrue or 0,
        "cashback_accrued": visit_data.cashback_to_accrue or 0
    }


@router.post("/1c/payment")
async def handle_1c_payment(
    payment_data: OneCWebhookPayment,
    db: Session = Depends(get_db),
    token: str = Depends(verify_webhook_token)
):
    """Webhook от 1С об оплате"""
    
    logger.info(f"Получен webhook от 1С об оплате: {payment_data.document_id}")
    
    # Здесь может быть логика обработки оплаты
    # Например, проверка использования сертификатов или баллов
    
    return {"status": "success", "message": "Оплата зарегистрирована"}


@router.get("/1c/sync-patient/{external_id}")
async def sync_patient_from_1c(
    external_id: str,
    db: Session = Depends(get_db)
):
    """Синхронизация данных пациента из 1С"""
    
    if not settings.ONEC_API_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="1С интеграция не настроена"
        )
    
    try:
        # Запрос к 1С API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ONEC_API_URL}/patients/{external_id}",
                auth=(settings.ONEC_USERNAME, settings.ONEC_PASSWORD),
                timeout=10.0
            )
            response.raise_for_status()
            patient_data = response.json()
        
        # Обновление или создание пользователя
        user = db.query(User).filter(User.external_id == external_id).first()
        
        if user:
            user.full_name = patient_data.get("full_name", user.full_name)
            user.phone = patient_data.get("phone", user.phone)
            user.email = patient_data.get("email", user.email)
            logger.info(f"Обновлены данные пользователя {external_id}")
        else:
            # Создание нового пользователя
            logger.info(f"Создание нового пользователя из 1С: {external_id}")
            # Здесь должна быть логика создания пользователя
        
        db.commit()
        
        return {"status": "success", "message": "Данные синхронизированы"}
        
    except httpx.HTTPError as e:
        logger.error(f"Ошибка синхронизации с 1С: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка связи с 1С: {str(e)}"
        )


# === Bitrix Integration ===

@router.post("/bitrix/contact")
async def handle_bitrix_contact(
    contact_data: BitrixWebhookContact,
    db: Session = Depends(get_db),
    token: str = Depends(verify_webhook_token)
):
    """Webhook от Bitrix о создании/обновлении контакта"""
    
    logger.info(f"Получен webhook от Bitrix о контакте: {contact_data.contact_id}")
    
    # Поиск или создание пользователя
    user = db.query(User).filter(User.email == contact_data.email).first()
    
    if user:
        # Обновление данных
        user.phone = contact_data.phone or user.phone
        user.full_name = f"{contact_data.name} {contact_data.last_name}"
        if not user.external_id:
            user.external_id = contact_data.contact_id
        logger.info(f"Обновлены данные пользователя из Bitrix: {user.email}")
    else:
        # Создание нового пользователя
        user = User(
            email=contact_data.email,
            phone=contact_data.phone,
            full_name=f"{contact_data.name} {contact_data.last_name}",
            external_id=contact_data.contact_id,
            is_active=True,
            role="patient"
        )
        db.add(user)
        db.flush()
        
        # Создание аккаунта лояльности
        import random
        card_number = f"ML{random.randint(10000000, 99999999)}"
        loyalty_account = LoyaltyAccount(
            user_id=user.id,
            card_number=card_number
        )
        db.add(loyalty_account)
        
        logger.info(f"Создан новый пользователь из Bitrix: {user.email}")
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Контакт синхронизирован",
        "user_id": user.id
    }


@router.get("/bitrix/push-balance/{user_id}")
async def push_balance_to_bitrix(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Отправка баланса пользователя в Bitrix"""
    
    if not settings.BITRIX_API_URL or not settings.BITRIX_WEBHOOK:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bitrix интеграция не настроена"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    try:
        # Отправка в Bitrix
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.BITRIX_API_URL}/{settings.BITRIX_WEBHOOK}/crm.contact.update",
                json={
                    "id": user.external_id,
                    "fields": {
                        "UF_LOYALTY_POINTS": account.points_balance,
                        "UF_LOYALTY_CASHBACK": account.cashback_balance,
                        "UF_LOYALTY_TIER": account.card_tier
                    }
                },
                timeout=10.0
            )
            response.raise_for_status()
        
        logger.info(f"Баланс пользователя {user_id} отправлен в Bitrix")
        
        return {"status": "success", "message": "Баланс отправлен в Bitrix"}
        
    except httpx.HTTPError as e:
        logger.error(f"Ошибка отправки в Bitrix: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка связи с Bitrix: {str(e)}"
        )
