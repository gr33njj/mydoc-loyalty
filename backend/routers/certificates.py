from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List
import qrcode
import secrets
import os

from database import get_db
from models import User, Certificate, CertificateTransfer, CertificateRedemption, CertificateStatus, AuditLog
from schemas import (
    CertificateCreate,
    CertificateResponse,
    CertificateTransferCreate,
    CertificateVerifyRequest,
    CertificateVerifyResponse,
    CertificateRedeemRequest,
    CertificateRedeemResponse
)
from routers.auth import get_current_active_user
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_certificate_code() -> str:
    """Генерация уникального кода сертификата"""
    return f"CERT-{secrets.token_hex(8).upper()}"


def generate_qr_code(certificate_code: str) -> str:
    """Генерация QR-кода для сертификата"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"https://{settings.DOMAIN}/verify/{certificate_code}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохранение QR-кода
    os.makedirs(settings.QR_CODE_DIR, exist_ok=True)
    qr_path = os.path.join(settings.QR_CODE_DIR, f"{certificate_code}.png")
    img.save(qr_path)
    
    return qr_path


@router.post("/create", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def create_certificate(
    cert_data: CertificateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создание нового подарочного сертификата"""
    
    if current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания сертификата"
        )
    
    # Генерация уникального кода
    code = generate_certificate_code()
    
    # Автоматическая генерация valid_until если не указано (по умолчанию +1 год)
    valid_until = cert_data.valid_until
    if valid_until is None:
        valid_until = datetime.utcnow() + timedelta(days=365)
    
    # Создание сертификата
    certificate = Certificate(
        code=code,
        initial_amount=cert_data.initial_amount,
        current_amount=cert_data.initial_amount,
        owner_id=cert_data.owner_id,  # Может быть None
        issued_by_id=current_user.id,
        valid_until=valid_until,
        design_template=cert_data.design_template,
        message=cert_data.message,
        status=CertificateStatus.ACTIVE
    )
    
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    
    # Генерация QR-кода
    try:
        qr_path = generate_qr_code(code)
        certificate.qr_code_path = qr_path
        db.commit()
    except Exception as e:
        logger.error(f"Ошибка генерации QR-кода: {e}")
    
    # Аудит
    audit = AuditLog(
        user_id=current_user.id,
        action="create_certificate",
        entity_type="certificate",
        entity_id=certificate.id,
        new_values={"code": code, "amount": cert_data.initial_amount}
    )
    db.add(audit)
    db.commit()
    
    logger.info(f"Создан сертификат {code} на сумму {cert_data.initial_amount}")
    
    # TODO: Отправка email/SMS владельцу
    
    response = CertificateResponse.from_orm(certificate)
    response.qr_code_url = f"https://{settings.DOMAIN}/qrcodes/{code}.png"
    
    return response


@router.get("/my", response_model=List[CertificateResponse])
def get_my_certificates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение списка сертификатов текущего пользователя"""
    
    certificates = db.query(Certificate).filter(
        Certificate.owner_id == current_user.id
    ).order_by(Certificate.issued_at.desc()).all()
    
    responses = []
    for cert in certificates:
        response = CertificateResponse.from_orm(cert)
        if cert.qr_code_path:
            response.qr_code_url = f"https://{settings.DOMAIN}/qrcodes/{cert.code}.png"
        responses.append(response)
    
    return responses


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение информации о сертификате"""
    
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сертификат не найден"
        )
    
    # Проверка прав доступа
    if certificate.owner_id != current_user.id and current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому сертификату"
        )
    
    response = CertificateResponse.from_orm(certificate)
    if certificate.qr_code_path:
        response.qr_code_url = f"https://{settings.DOMAIN}/qrcodes/{certificate.code}.png"
    
    return response


@router.post("/transfer", status_code=status.HTTP_200_OK)
def transfer_certificate(
    request_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Передача сертификата другому пользователю (по коду или ID)"""
    
    # Поддержка двух вариантов: по коду (для админки) или по ID (старый формат)
    code = request_data.get('code')
    recipient_email = request_data.get('recipient_email')
    message = request_data.get('message')
    
    if code:
        # Новый формат - передача по коду (для админки при создании)
        certificate = db.query(Certificate).filter(Certificate.code == code).first()
        to_email = recipient_email
    elif 'certificate_id' in request_data:
        # Старый формат - передача по ID
        certificate = db.query(Certificate).filter(
            Certificate.id == request_data['certificate_id']
        ).first()
        to_email = request_data.get('to_user_email')
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать код сертификата (code) или ID (certificate_id)"
        )
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сертификат не найден"
        )
    
    # Проверка владения - пропускаем для админов и кассиров, или если сертификат без владельца
    if current_user.role not in ["admin", "cashier"]:
        if certificate.owner_id and certificate.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь владельцем этого сертификата"
            )
    
    # Проверка статуса
    if certificate.status != CertificateStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Сертификат имеет статус {certificate.status} и не может быть передан"
        )
    
    # Поиск получателя
    recipient = db.query(User).filter(User.email == to_email).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Получатель с email {to_email} не найден"
        )
    
    # Запись передачи
    transfer = CertificateTransfer(
        certificate_id=certificate.id,
        from_user_id=certificate.owner_id or current_user.id,
        to_user_id=recipient.id,
        message=message
    )
    db.add(transfer)
    
    # Смена владельца
    old_owner_id = certificate.owner_id
    certificate.owner_id = recipient.id
    
    # Аудит
    audit = AuditLog(
        user_id=current_user.id,
        action="transfer_certificate",
        entity_type="certificate",
        entity_id=certificate.id,
        old_values={"owner_id": old_owner_id},
        new_values={"owner_id": recipient.id}
    )
    db.add(audit)
    
    db.commit()
    
    logger.info(f"Сертификат {certificate.code} передан к {recipient.email}")
    
    # TODO: Отправка уведомления получателю
    
    return {"message": "Сертификат успешно передан", "recipient_email": recipient.email}


@router.post("/verify", response_model=CertificateVerifyResponse)
def verify_certificate(
    verify_data: CertificateVerifyRequest,
    db: Session = Depends(get_db)
):
    """Проверка действительности сертификата (публичный endpoint)"""
    
    certificate = db.query(Certificate).filter(Certificate.code == verify_data.code).first()
    
    if not certificate:
        return CertificateVerifyResponse(
            valid=False,
            certificate=None,
            message="Сертификат не найден"
        )
    
    # Проверка срока действия
    now = datetime.now(timezone.utc)
    valid_until = certificate.valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)
    
    if now > valid_until:
        certificate.status = CertificateStatus.EXPIRED
        db.commit()
        return CertificateVerifyResponse(
            valid=False,
            certificate=CertificateResponse.from_orm(certificate),
            message="Срок действия сертификата истек"
        )
    
    # Проверка статуса
    if certificate.status != CertificateStatus.ACTIVE:
        return CertificateVerifyResponse(
            valid=False,
            certificate=CertificateResponse.from_orm(certificate),
            message=f"Сертификат имеет статус: {certificate.status}"
        )
    
    # Проверка баланса
    if certificate.current_amount <= 0:
        certificate.status = CertificateStatus.USED
        db.commit()
        return CertificateVerifyResponse(
            valid=False,
            certificate=CertificateResponse.from_orm(certificate),
            message="Сертификат полностью использован"
        )
    
    response = CertificateResponse.from_orm(certificate)
    if certificate.qr_code_path:
        response.qr_code_url = f"https://{settings.DOMAIN}/qrcodes/{certificate.code}.png"
    
    return CertificateVerifyResponse(
        valid=True,
        certificate=response,
        message=f"Сертификат действителен. Доступно: {certificate.current_amount} руб."
    )


@router.post("/redeem", response_model=CertificateRedeemResponse)
def redeem_certificate(
    redeem_data: CertificateRedeemRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Использование (погашение) сертификата на кассе"""
    
    if current_user.role not in ["admin", "cashier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для погашения сертификата"
        )
    
    certificate = db.query(Certificate).filter(Certificate.code == redeem_data.code).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сертификат не найден"
        )
    
    # Проверка статуса
    if certificate.status != CertificateStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Сертификат не может быть использован. Статус: {certificate.status}"
        )
    
    # Проверка срока действия
    now = datetime.now(timezone.utc)
    valid_until = certificate.valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=timezone.utc)
    
    if now > valid_until:
        certificate.status = CertificateStatus.EXPIRED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Срок действия сертификата истек"
        )
    
    # Проверка суммы
    if redeem_data.amount > certificate.current_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недостаточно средств на сертификате. Доступно: {certificate.current_amount}"
        )
    
    # Списание суммы
    old_amount = certificate.current_amount
    certificate.current_amount -= redeem_data.amount
    remaining_amount = certificate.current_amount
    
    # Если сертификат использован полностью
    if certificate.current_amount <= 0:
        certificate.status = CertificateStatus.USED
        certificate.used_at = datetime.utcnow()
    
    # Создание записи о погашении
    redemption = CertificateRedemption(
        certificate_id=certificate.id,
        amount_used=redeem_data.amount,
        remaining_amount=remaining_amount,
        onec_document_id=redeem_data.onec_document_id,
        redeemed_by_id=current_user.id,
        notes=redeem_data.notes
    )
    db.add(redemption)
    
    # Аудит
    audit = AuditLog(
        user_id=current_user.id,
        action="redeem_certificate",
        entity_type="certificate",
        entity_id=certificate.id,
        old_values={"amount": old_amount, "status": "active"},
        new_values={"amount": remaining_amount, "status": certificate.status}
    )
    db.add(audit)
    
    db.commit()
    
    logger.info(f"Сертификат {certificate.code} использован на сумму {redeem_data.amount}. Остаток: {remaining_amount}")
    
    return CertificateRedeemResponse(
        success=True,
        certificate_id=certificate.id,
        amount_used=redeem_data.amount,
        remaining_amount=remaining_amount,
        message=f"Сертификат успешно использован. Остаток: {remaining_amount} руб."
    )
