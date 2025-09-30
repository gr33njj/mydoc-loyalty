from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import secrets
import string

from database import get_db
from models import (
    User, ReferralCode, ReferralEvent, ReferralReward, RewardRule, 
    LoyaltyAccount, LoyaltyTransaction, TransactionType, ReferralEventType, RewardType
)
from schemas import (
    ReferralCodeCreate,
    ReferralCodeResponse,
    ReferralEventCreate,
    ReferralEventResponse,
    ReferralRewardResponse,
    ReferralStatsResponse
)
from routers.auth import get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_referral_code(prefix: str = "REF") -> str:
    """Генерация уникального реферального кода"""
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"{prefix}-{random_part}"


def process_referral_rewards(db: Session, event: ReferralEvent, referral_code: ReferralCode):
    """Обработка вознаграждений за реферальное событие"""
    
    # Получение правил вознаграждений
    rules = db.query(RewardRule).filter(
        RewardRule.event_type == event.event_type,
        RewardRule.is_active == True
    ).all()
    
    for rule in rules:
        # Проверка типа реферера
        if rule.referrer_type != "any" and rule.referrer_type != referral_code.referrer_type:
            continue
        
        # Расчет суммы вознаграждения
        if rule.reward_type == RewardType.FIXED:
            reward_amount = rule.reward_value
        elif rule.reward_type == RewardType.PERCENTAGE:
            if event.transaction_amount:
                reward_amount = event.transaction_amount * (rule.reward_value / 100)
            else:
                continue
        elif rule.reward_type == RewardType.POINTS:
            reward_amount = rule.reward_value
        else:
            continue
        
        # Получение аккаунта лояльности реферера
        referrer_account = db.query(LoyaltyAccount).filter(
            LoyaltyAccount.user_id == referral_code.user_id
        ).first()
        
        if not referrer_account:
            logger.warning(f"Аккаунт лояльности не найден для пользователя {referral_code.user_id}")
            continue
        
        # Создание транзакции лояльности
        loyalty_transaction = LoyaltyTransaction(
            account_id=referrer_account.id,
            transaction_type=TransactionType.ACCRUAL,
            amount=reward_amount,
            currency="points" if rule.reward_type == RewardType.POINTS else "cashback",
            source="referral",
            source_id=str(event.id),
            description=f"Вознаграждение за реферала: {event.event_type}"
        )
        db.add(loyalty_transaction)
        db.flush()
        
        # Обновление баланса
        if rule.reward_type == RewardType.POINTS:
            referrer_account.points_balance += reward_amount
            referrer_account.total_points_earned += reward_amount
        else:
            referrer_account.cashback_balance += reward_amount
            referrer_account.total_cashback_earned += reward_amount
        
        # Создание записи о вознаграждении
        reward = ReferralReward(
            event_id=event.id,
            recipient_user_id=referral_code.user_id,
            reward_type=rule.reward_type,
            reward_amount=reward_amount,
            referral_level=rule.applies_to_level,
            loyalty_transaction_id=loyalty_transaction.id
        )
        db.add(reward)
        
        logger.info(f"Начислено вознаграждение {reward_amount} пользователю {referral_code.user_id} за событие {event.event_type}")


@router.post("/create-code", response_model=ReferralCodeResponse, status_code=status.HTTP_201_CREATED)
def create_referral_code(
    code_data: ReferralCodeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создание реферального кода"""
    
    # Проверка прав (пользователь может создать код только для себя, кроме админов)
    if code_data.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Проверка существования активного кода
    existing_code = db.query(ReferralCode).filter(
        ReferralCode.user_id == code_data.user_id,
        ReferralCode.is_active == True
    ).first()
    
    if existing_code:
        return ReferralCodeResponse.from_orm(existing_code)
    
    # Генерация кода
    if code_data.custom_code:
        # Проверка уникальности
        if db.query(ReferralCode).filter(ReferralCode.code == code_data.custom_code).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Код уже используется"
            )
        code = code_data.custom_code
    else:
        code = generate_referral_code()
    
    # Создание реферального кода
    referral_code = ReferralCode(
        user_id=code_data.user_id,
        code=code,
        referrer_type=code_data.referrer_type,
        is_active=True
    )
    
    db.add(referral_code)
    db.commit()
    db.refresh(referral_code)
    
    logger.info(f"Создан реферальный код {code} для пользователя {code_data.user_id}")
    
    return ReferralCodeResponse.from_orm(referral_code)


@router.get("/my-code", response_model=ReferralCodeResponse)
def get_my_referral_code(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение реферального кода текущего пользователя"""
    
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.user_id == current_user.id,
        ReferralCode.is_active == True
    ).first()
    
    if not referral_code:
        # Автоматическое создание кода
        code = generate_referral_code()
        referral_code = ReferralCode(
            user_id=current_user.id,
            code=code,
            referrer_type="patient",
            is_active=True
        )
        db.add(referral_code)
        db.commit()
        db.refresh(referral_code)
    
    return ReferralCodeResponse.from_orm(referral_code)


@router.post("/register-event", response_model=ReferralEventResponse, status_code=status.HTTP_201_CREATED)
def register_referral_event(
    event_data: ReferralEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Регистрация реферального события"""
    
    if current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    # Поиск реферального кода
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.code == event_data.referral_code,
        ReferralCode.is_active == True
    ).first()
    
    if not referral_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Реферальный код не найден или неактивен"
        )
    
    # Проверка, что пользователь не использует свой собственный код
    if referral_code.user_id == event_data.referred_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя использовать собственный реферальный код"
        )
    
    # Создание события
    event = ReferralEvent(
        referral_code_id=referral_code.id,
        referred_user_id=event_data.referred_user_id,
        event_type=event_data.event_type,
        transaction_amount=event_data.transaction_amount,
        onec_document_id=event_data.onec_document_id,
        metadata=event_data.metadata,
        processed=False
    )
    
    db.add(event)
    db.flush()
    
    # Обработка вознаграждений
    try:
        process_referral_rewards(db, event, referral_code)
        event.processed = True
        
        # Обновление статистики реферального кода
        referral_code.total_referrals += 1
        if event_data.event_type == ReferralEventType.FIRST_VISIT:
            referral_code.successful_referrals += 1
        if event_data.transaction_amount:
            referral_code.total_revenue += event_data.transaction_amount
        
    except Exception as e:
        logger.error(f"Ошибка обработки вознаграждений: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки вознаграждений: {str(e)}"
        )
    
    db.commit()
    db.refresh(event)
    
    logger.info(f"Зарегистрировано реферальное событие {event_data.event_type} для кода {event_data.referral_code}")
    
    return ReferralEventResponse.from_orm(event)


@router.get("/stats", response_model=ReferralStatsResponse)
def get_referral_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение статистики по рефералам текущего пользователя"""
    
    referral_code = db.query(ReferralCode).filter(
        ReferralCode.user_id == current_user.id,
        ReferralCode.is_active == True
    ).first()
    
    if not referral_code:
        return ReferralStatsResponse(
            total_referrals=0,
            successful_referrals=0,
            pending_referrals=0,
            total_revenue=0.0,
            total_rewards=0.0,
            conversion_rate=0.0,
            referral_code=""
        )
    
    # Подсчет общей суммы вознаграждений
    total_rewards = db.query(func.sum(ReferralReward.reward_amount)).join(
        ReferralEvent
    ).filter(
        ReferralEvent.referral_code_id == referral_code.id
    ).scalar() or 0.0
    
    # Подсчет pending рефералов (зарегистрировались, но не совершили первый визит)
    pending = db.query(ReferralEvent).filter(
        ReferralEvent.referral_code_id == referral_code.id,
        ReferralEvent.event_type == ReferralEventType.REGISTRATION
    ).count()
    
    first_visits = db.query(ReferralEvent).filter(
        ReferralEvent.referral_code_id == referral_code.id,
        ReferralEvent.event_type == ReferralEventType.FIRST_VISIT
    ).count()
    
    pending_referrals = pending - first_visits
    
    # Конверсия
    conversion_rate = (referral_code.successful_referrals / referral_code.total_referrals * 100) if referral_code.total_referrals > 0 else 0.0
    
    return ReferralStatsResponse(
        total_referrals=referral_code.total_referrals,
        successful_referrals=referral_code.successful_referrals,
        pending_referrals=max(0, pending_referrals),
        total_revenue=referral_code.total_revenue,
        total_rewards=total_rewards,
        conversion_rate=round(conversion_rate, 2),
        referral_code=referral_code.code
    )


@router.get("/rewards", response_model=list[ReferralRewardResponse])
def get_my_rewards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение истории вознаграждений"""
    
    rewards = db.query(ReferralReward).filter(
        ReferralReward.recipient_user_id == current_user.id
    ).order_by(ReferralReward.awarded_at.desc()).all()
    
    return [ReferralRewardResponse.from_orm(r) for r in rewards]
