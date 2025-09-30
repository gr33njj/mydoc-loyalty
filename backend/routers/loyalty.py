from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from database import get_db
from models import User, LoyaltyAccount, LoyaltyTransaction, TransactionType, AuditLog
from schemas import (
    LoyaltyAccountResponse, 
    LoyaltyTransactionCreate, 
    LoyaltyTransactionResponse,
    BalanceResponse,
    TransactionHistoryResponse
)
from routers.auth import get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def create_audit_log(db: Session, user_id: int, action: str, entity_type: str, entity_id: int, 
                     old_values: dict = None, new_values: dict = None):
    """Создание записи аудита"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values
    )
    db.add(audit)


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение баланса текущего пользователя"""
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    transactions_count = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.account_id == account.id
    ).count()
    
    return BalanceResponse(
        points_balance=account.points_balance,
        cashback_balance=account.cashback_balance,
        card_tier=account.card_tier,
        transactions_count=transactions_count
    )


@router.get("/balance/{user_id}", response_model=BalanceResponse)
def get_user_balance(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение баланса пользователя (для админов и кассиров)"""
    
    if current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    transactions_count = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.account_id == account.id
    ).count()
    
    return BalanceResponse(
        points_balance=account.points_balance,
        cashback_balance=account.cashback_balance,
        card_tier=account.card_tier,
        transactions_count=transactions_count
    )


@router.get("/transactions", response_model=TransactionHistoryResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение истории транзакций текущего пользователя"""
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    # Подсчет общего количества
    total = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.account_id == account.id
    ).count()
    
    # Получение транзакций с пагинацией
    transactions = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.account_id == account.id
    ).order_by(desc(LoyaltyTransaction.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return TransactionHistoryResponse(
        transactions=[LoyaltyTransactionResponse.from_orm(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/accrue", response_model=LoyaltyTransactionResponse, status_code=status.HTTP_201_CREATED)
def accrue_points(
    transaction: LoyaltyTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Начисление баллов/кешбэка (только для админов и системы)"""
    
    if current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для начисления баллов"
        )
    
    # Проверка идемпотентности
    if transaction.idempotency_key:
        existing = db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.idempotency_key == transaction.idempotency_key
        ).first()
        if existing:
            logger.info(f"Транзакция с ключом {transaction.idempotency_key} уже существует")
            return LoyaltyTransactionResponse.from_orm(existing)
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.id == transaction.account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    # Сохранение старого баланса для аудита
    old_balance = {
        "points": account.points_balance,
        "cashback": account.cashback_balance
    }
    
    # Обновление баланса
    if transaction.currency == "points":
        account.points_balance += transaction.amount
        account.total_points_earned += transaction.amount
    elif transaction.currency == "cashback":
        account.cashback_balance += transaction.amount
        account.total_cashback_earned += transaction.amount
    
    # Создание транзакции
    new_transaction = LoyaltyTransaction(
        account_id=account.id,
        transaction_type=TransactionType.ACCRUAL,
        amount=transaction.amount,
        currency=transaction.currency,
        source=transaction.source,
        source_id=transaction.source_id,
        description=transaction.description,
        metadata=transaction.metadata,
        idempotency_key=transaction.idempotency_key,
        created_by=current_user.id
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    # Аудит
    new_balance = {
        "points": account.points_balance,
        "cashback": account.cashback_balance
    }
    create_audit_log(db, current_user.id, "accrue_points", "loyalty_transaction", 
                     new_transaction.id, old_balance, new_balance)
    db.commit()
    
    logger.info(f"Начислено {transaction.amount} {transaction.currency} на аккаунт {account.id}")
    
    return LoyaltyTransactionResponse.from_orm(new_transaction)


@router.post("/deduct", response_model=LoyaltyTransactionResponse, status_code=status.HTTP_201_CREATED)
def deduct_points(
    transaction: LoyaltyTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Списание баллов/кешбэка"""
    
    if current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для списания баллов"
        )
    
    # Проверка идемпотентности
    if transaction.idempotency_key:
        existing = db.query(LoyaltyTransaction).filter(
            LoyaltyTransaction.idempotency_key == transaction.idempotency_key
        ).first()
        if existing:
            logger.info(f"Транзакция с ключом {transaction.idempotency_key} уже существует")
            return LoyaltyTransactionResponse.from_orm(existing)
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.id == transaction.account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    # Проверка достаточности средств
    if transaction.currency == "points":
        if account.points_balance < transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно баллов. Доступно: {account.points_balance}"
            )
    elif transaction.currency == "cashback":
        if account.cashback_balance < transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно кешбэка. Доступно: {account.cashback_balance}"
            )
    
    # Сохранение старого баланса для аудита
    old_balance = {
        "points": account.points_balance,
        "cashback": account.cashback_balance
    }
    
    # Обновление баланса
    if transaction.currency == "points":
        account.points_balance -= transaction.amount
        account.total_points_spent += transaction.amount
    elif transaction.currency == "cashback":
        account.cashback_balance -= transaction.amount
        account.total_cashback_spent += transaction.amount
    
    # Создание транзакции
    new_transaction = LoyaltyTransaction(
        account_id=account.id,
        transaction_type=TransactionType.DEDUCTION,
        amount=transaction.amount,
        currency=transaction.currency,
        source=transaction.source,
        source_id=transaction.source_id,
        description=transaction.description,
        metadata=transaction.metadata,
        idempotency_key=transaction.idempotency_key,
        created_by=current_user.id
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    # Аудит
    new_balance = {
        "points": account.points_balance,
        "cashback": account.cashback_balance
    }
    create_audit_log(db, current_user.id, "deduct_points", "loyalty_transaction", 
                     new_transaction.id, old_balance, new_balance)
    db.commit()
    
    logger.info(f"Списано {transaction.amount} {transaction.currency} с аккаунта {account.id}")
    
    return LoyaltyTransactionResponse.from_orm(new_transaction)


@router.get("/account", response_model=LoyaltyAccountResponse)
def get_loyalty_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение полной информации об аккаунте лояльности"""
    
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аккаунт лояльности не найден"
        )
    
    return LoyaltyAccountResponse.from_orm(account)
