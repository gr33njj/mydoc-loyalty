from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

from database import get_db
from models import (
    User, LoyaltyAccount, Certificate, ReferralCode, 
    LoyaltyTransaction, CertificateStatus, AuditLog
)
from schemas import (
    AdminDashboardStats,
    AdminCertificateList,
    AdminUserList,
    CertificateResponse,
    UserResponse
)
from routers.auth import get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_active_user)):
    """Проверка прав администратора"""
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user


@router.get("/dashboard", response_model=AdminDashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Получение общей статистики для дашборда"""
    
    # Подсчет пользователей
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # Активные сертификаты
    active_certificates = db.query(Certificate).filter(
        Certificate.status == CertificateStatus.ACTIVE
    ).count()
    
    # Общая стоимость активных сертификатов
    total_certificates_value = db.query(
        func.sum(Certificate.current_amount)
    ).filter(
        Certificate.status == CertificateStatus.ACTIVE
    ).scalar() or 0.0
    
    # Общий баланс баллов лояльности
    total_loyalty_points = db.query(
        func.sum(LoyaltyAccount.points_balance)
    ).scalar() or 0.0
    
    # Общий баланс кешбэка
    total_loyalty_cashback = db.query(
        func.sum(LoyaltyAccount.cashback_balance)
    ).scalar() or 0.0
    
    # Активные реферальные коды
    active_referral_codes = db.query(ReferralCode).filter(
        ReferralCode.is_active == True
    ).count()
    
    # Транзакции за сегодня
    today = datetime.utcnow().date()
    today_transactions = db.query(LoyaltyTransaction).filter(
        func.date(LoyaltyTransaction.created_at) == today
    ).count()
    
    return AdminDashboardStats(
        total_users=total_users,
        active_certificates=active_certificates,
        total_certificates_value=total_certificates_value,
        total_loyalty_points=total_loyalty_points,
        total_loyalty_cashback=total_loyalty_cashback,
        active_referral_codes=active_referral_codes,
        today_transactions=today_transactions
    )


@router.get("/certificates", response_model=AdminCertificateList)
def list_certificates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Список всех сертификатов с фильтрацией"""
    
    query = db.query(Certificate)
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Certificate.status == status)
    
    # Подсчет общего количества
    total = query.count()
    
    # Пагинация
    certificates = query.order_by(
        desc(Certificate.issued_at)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return AdminCertificateList(
        certificates=[CertificateResponse.from_orm(c) for c in certificates],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users", response_model=AdminUserList)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Список всех пользователей с фильтрацией"""
    
    query = db.query(User)
    
    # Фильтрация по роли
    if role:
        query = query.filter(User.role == role)
    
    # Подсчет общего количества
    total = query.count()
    
    # Пагинация
    users = query.order_by(
        desc(User.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return AdminUserList(
        users=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/audit-log")
def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: str = Query(None),
    action: str = Query(None),
    user_id: int = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Получение логов аудита"""
    
    query = db.query(AuditLog)
    
    # Фильтры
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Подсчет общего количества
    total = query.count()
    
    # Пагинация
    logs = query.order_by(
        desc(AuditLog.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Деактивация пользователя"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = False
    
    # Аудит
    audit = AuditLog(
        user_id=current_user.id,
        action="deactivate_user",
        entity_type="user",
        entity_id=user.id,
        old_values={"is_active": True},
        new_values={"is_active": False}
    )
    db.add(audit)
    
    db.commit()
    
    logger.info(f"Пользователь {user.email} деактивирован администратором {current_user.email}")
    
    return {"message": "Пользователь деактивирован", "user_id": user_id}


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Активация пользователя"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = True
    
    # Аудит
    audit = AuditLog(
        user_id=current_user.id,
        action="activate_user",
        entity_type="user",
        entity_id=user.id,
        old_values={"is_active": False},
        new_values={"is_active": True}
    )
    db.add(audit)
    
    db.commit()
    
    logger.info(f"Пользователь {user.email} активирован администратором {current_user.email}")
    
    return {"message": "Пользователь активирован", "user_id": user_id}


@router.get("/reports/loyalty")
def loyalty_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Отчет по программе лояльности за период"""
    
    # Транзакции за период
    transactions = db.query(LoyaltyTransaction).filter(
        and_(
            LoyaltyTransaction.created_at >= start_date,
            LoyaltyTransaction.created_at <= end_date
        )
    ).all()
    
    # Агрегация
    total_accrued_points = sum(
        t.amount for t in transactions 
        if t.transaction_type == "accrual" and t.currency == "points"
    )
    total_spent_points = sum(
        t.amount for t in transactions 
        if t.transaction_type == "deduction" and t.currency == "points"
    )
    total_accrued_cashback = sum(
        t.amount for t in transactions 
        if t.transaction_type == "accrual" and t.currency == "cashback"
    )
    total_spent_cashback = sum(
        t.amount for t in transactions 
        if t.transaction_type == "deduction" and t.currency == "cashback"
    )
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "transactions_count": len(transactions),
        "points": {
            "accrued": total_accrued_points,
            "spent": total_spent_points,
            "net": total_accrued_points - total_spent_points
        },
        "cashback": {
            "accrued": total_accrued_cashback,
            "spent": total_spent_cashback,
            "net": total_accrued_cashback - total_spent_cashback
        }
    }
