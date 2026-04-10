"""
Синхронизация сертификатов с 1С:УМЦ через OData API.

Протокол:
  1С → наш сервис: POST /api/integrations/1c/certificate  (вебхук от 1С)
  Наш сервис → 1С: при покупке/погашении сертификата
                   обращаемся к OData API через VPN.

OData-сущность: Catalog_КартыСкидок
  GET  /odata/standard.odata/Catalog_КартыСкидок  — список карт
  POST /odata/standard.odata/Catalog_КартыСкидок  — создать/обновить карту
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Certificate, CertificateRedemption, CertificateStatus, User
from onec_utils import odata_auth, odata_url

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Схемы
# ---------------------------------------------------------------------------

class OneCCertificateWebhook(BaseModel):
    """Тело вебхука от 1С при создании/изменении сертификата."""
    code: str                           # Номер сертификата
    initial_amount: float               # Номинал
    current_amount: float               # Текущий остаток
    status: str                         # active / used / expired / cancelled
    owner_phone: Optional[str] = None   # Телефон владельца в 1С
    owner_external_id: Optional[str] = None  # ID пациента в 1С
    valid_until: Optional[str] = None   # ISO 8601
    document_id: Optional[str] = None  # ID документа-основания в 1С


class OneCRedeemWebhook(BaseModel):
    """Вебхук от 1С при погашении сертификата на кассе."""
    code: str
    amount_used: float
    remaining_amount: float
    document_id: str                    # ID документа «Оказание услуг»
    cashier_comment: Optional[str] = None


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _verify_token(x_webhook_token: Optional[str] = Header(None)):
    if not x_webhook_token:
        raise HTTPException(status_code=401, detail="Токен вебхука отсутствует")
    return x_webhook_token



async def push_certificate_to_1c(cert: Certificate, db: Session) -> bool:
    """
    Создаёт/обновляет запись в Catalog_КартыСкидок в 1С.
    Возвращает True при успехе.
    """
    if not settings.ONEC_API_URL:
        logger.debug("ONEC_API_URL не задан, пропускаем отправку в 1С")
        return False

    owner: User | None = db.get(User, cert.owner_id)
    null_guid = "00000000-0000-0000-0000-000000000000"

    payload = {
        "Description": cert.code,
        "Code": cert.code,
        "ВладелецКарты_Key": owner.external_id if (owner and owner.external_id) else null_guid,
        "СрокДействия": cert.valid_until.strftime("%Y-%m-%dT%H:%M:%S") if cert.valid_until else "0001-01-01T00:00:00",
        "Примечание": f"Сертификат {cert.initial_amount} руб. Источник: loyalty_app",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                odata_url("Catalog_%D0%9A%D0%B0%D1%80%D1%82%D1%8B%D0%A1%D0%BA%D0%B8%D0%B4%D0%BE%D0%BA"),
                json=payload,
                auth=odata_auth(),
                headers={"Content-Type": "application/json"},
                params={"$format": "json"},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                ref_key = data.get("Ref_Key")
                if ref_key:
                    extra = cert.extra_data or {}
                    extra["onec_card_key"] = ref_key
                    cert.extra_data = extra
                    db.commit()
                logger.info(f"Сертификат {cert.code} передан в 1С (key={ref_key})")
                return True
            logger.warning(f"1С вернул {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.warning(f"Ошибка передачи сертификата {cert.code} в 1С: {e}")
        return False


async def sync_certificate_from_1c(code: str, db: Session) -> Certificate | None:
    """
    Ищет Catalog_КартыСкидок по Description=code и обновляет local cert.
    """
    if not settings.ONEC_API_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                odata_url("Catalog_%D0%9A%D0%B0%D1%80%D1%82%D1%8B%D0%A1%D0%BA%D0%B8%D0%B4%D0%BE%D0%BA"),
                params={
                    "$filter": f"Description eq '{code}' and DeletionMark eq false",
                    "$format": "json",
                    "$top": "1",
                },
                auth=odata_auth(),
            )
            resp.raise_for_status()
            vals = resp.json().get("value", [])
            if not vals:
                return None
            data = vals[0]
    except Exception as e:
        logger.warning(f"Не удалось получить сертификат {code} из 1С: {e}")
        return None

    cert = db.query(Certificate).filter(Certificate.code == code).first()
    if not cert:
        return None

    cert.current_amount = data.get("current_amount", cert.current_amount)
    raw_status = data.get("status", cert.status.value)
    try:
        cert.status = CertificateStatus(raw_status)
    except ValueError:
        pass
    db.commit()
    db.refresh(cert)
    return cert


# ---------------------------------------------------------------------------
# Вебхуки от 1С
# ---------------------------------------------------------------------------

@router.post("/certificate", summary="Вебхук: создать/обновить сертификат из 1С")
async def webhook_certificate_from_1c(
    data: OneCCertificateWebhook,
    db: Session = Depends(get_db),
    _token: str = Depends(_verify_token),
):
    """
    1С вызывает этот эндпоинт когда:
    - администратор создал сертификат вручную
    - изменился статус или остаток сертификата
    """
    cert = db.query(Certificate).filter(Certificate.code == data.code).first()

    if cert:
        # Обновляем существующий
        cert.current_amount = data.current_amount
        try:
            cert.status = CertificateStatus(data.status)
        except ValueError:
            pass
        if data.document_id:
            # Сохраняем ID документа-основания в extra_data
            extra = cert.extra_data or {}
            extra["onec_document_id"] = data.document_id
            cert.extra_data = extra
        db.commit()
        logger.info(f"Сертификат {data.code} обновлён из вебхука 1С")
        return {"status": "updated", "code": data.code}

    # Сертификат не найден — создаём. Ищем владельца по телефону или external_id.
    owner: User | None = None
    if data.owner_external_id:
        owner = db.query(User).filter(User.external_id == data.owner_external_id).first()
    if not owner and data.owner_phone:
        owner = db.query(User).filter(User.phone == data.owner_phone).first()

    if not owner:
        # Нет владельца в нашей системе — сохраняем без привязки к пользователю.
        # Когда пациент зарегистрируется, сертификат можно будет привязать.
        logger.warning(
            f"Владелец сертификата {data.code} не найден (phone={data.owner_phone})"
        )
        return {"status": "owner_not_found", "code": data.code}

    from datetime import datetime, timezone
    valid_until = None
    if data.valid_until:
        try:
            valid_until = datetime.fromisoformat(data.valid_until)
        except ValueError:
            pass

    new_cert = Certificate(
        code=data.code,
        initial_amount=data.initial_amount,
        current_amount=data.current_amount,
        status=CertificateStatus(data.status) if data.status in CertificateStatus._value2member_map_ else CertificateStatus.ACTIVE,
        owner_id=owner.id,
        valid_until=valid_until or datetime(datetime.now(timezone.utc).year + 1,
                                            datetime.now(timezone.utc).month,
                                            datetime.now(timezone.utc).day,
                                            tzinfo=timezone.utc),
        extra_data={"onec_document_id": data.document_id} if data.document_id else None,
    )
    db.add(new_cert)
    db.commit()
    logger.info(f"Сертификат {data.code} создан из вебхука 1С для пользователя {owner.id}")
    return {"status": "created", "code": data.code, "owner_id": owner.id}


@router.post("/certificate/redeem", summary="Вебхук: погашение сертификата на кассе 1С")
async def webhook_redeem_from_1c(
    data: OneCRedeemWebhook,
    db: Session = Depends(get_db),
    _token: str = Depends(_verify_token),
):
    """
    1С вызывает этот эндпоинт при добавлении сертификата к документу «Оказание услуг».
    """
    cert = db.query(Certificate).filter(Certificate.code == data.code).first()
    if not cert:
        logger.warning(f"Погашение: сертификат {data.code} не найден")
        return {"status": "not_found"}

    # Проверка идемпотентности — один документ не должен дважды снять деньги
    already = db.query(CertificateRedemption).filter(
        CertificateRedemption.onec_document_id == data.document_id
    ).first()
    if already:
        return {"status": "already_processed", "redemption_id": already.id}

    cert.current_amount = data.remaining_amount
    if data.remaining_amount <= 0:
        cert.status = CertificateStatus.USED

    redemption = CertificateRedemption(
        certificate_id=cert.id,
        amount_used=data.amount_used,
        remaining_amount=data.remaining_amount,
        onec_document_id=data.document_id,
        redeemed_by_id=None,
        notes=data.cashier_comment,
    )
    db.add(redemption)
    db.commit()

    logger.info(
        f"Сертификат {data.code}: списано {data.amount_used} руб., "
        f"остаток {data.remaining_amount} руб. (doc {data.document_id})"
    )
    return {
        "status": "success",
        "code": data.code,
        "amount_used": data.amount_used,
        "remaining_amount": data.remaining_amount,
    }


@router.get("/certificate/sync/{code}", summary="Принудительная синхронизация сертификата из 1С")
async def force_sync_certificate(
    code: str,
    db: Session = Depends(get_db),
):
    """Запросить актуальный остаток сертификата напрямую из 1С."""
    if not settings.ONEC_API_URL:
        raise HTTPException(503, detail="1С интеграция не настроена (ONEC_API_URL пуст)")

    cert = await sync_certificate_from_1c(code, db)
    if not cert:
        raise HTTPException(404, detail="Сертификат не найден")

    return {
        "code": cert.code,
        "current_amount": cert.current_amount,
        "status": cert.status.value,
    }
