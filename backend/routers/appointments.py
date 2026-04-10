"""
Роутер онлайн-записи к врачам.

Архитектура:
  - Список врачей и услуг: сначала возвращаем статические данные,
    после подключения VPN+1С они будут подтягиваться из 1С REST API.
  - Заявка сохраняется локально в БД.
  - После подключения к 1С заявка пробрасывается туда же.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import AppointmentRequest, AppointmentStatus, User
from routers.auth import get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Схемы
# ---------------------------------------------------------------------------

class DoctorOut(BaseModel):
    id: str
    name: str
    specialty: str
    photo_url: Optional[str] = None


class ServiceOut(BaseModel):
    id: str
    name: str
    category: str
    duration_min: int


class AppointmentCreate(BaseModel):
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    preferred_date: Optional[datetime] = None
    preferred_time_slot: Optional[str] = None
    comment: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    doctor_name: Optional[str]
    service_name: Optional[str]
    preferred_date: Optional[datetime]
    preferred_time_slot: Optional[str]
    comment: Optional[str]
    status: str
    onec_document_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Статические данные (заглушка до подключения 1С)
# ---------------------------------------------------------------------------

STATIC_DOCTORS: list[dict] = [
    {"id": "doc_001", "name": "Иванова Мария Петровна",   "specialty": "Терапевт",       "photo_url": None},
    {"id": "doc_002", "name": "Петров Андрей Сергеевич",  "specialty": "Хирург",         "photo_url": None},
    {"id": "doc_003", "name": "Сидорова Елена Викторовна","specialty": "Педиатр",        "photo_url": None},
    {"id": "doc_004", "name": "Козлов Дмитрий Алексеевич","specialty": "Кардиолог",      "photo_url": None},
    {"id": "doc_005", "name": "Новикова Ольга Ивановна",  "specialty": "Гинеколог",      "photo_url": None},
    {"id": "doc_006", "name": "Волков Игорь Николаевич",  "specialty": "Невролог",       "photo_url": None},
    {"id": "doc_007", "name": "Морозова Анна Дмитриевна", "specialty": "Дерматолог",     "photo_url": None},
    {"id": "doc_008", "name": "Зайцев Павел Геннадьевич", "specialty": "Офтальмолог",    "photo_url": None},
    {"id": "doc_009", "name": "Лебедева Светлана Юрьевна","specialty": "Эндокринолог",   "photo_url": None},
    {"id": "doc_010", "name": "Орлов Максим Владимирович","specialty": "Ортопед",        "photo_url": None},
]

STATIC_SERVICES: list[dict] = [
    # Терапия
    {"id": "svc_001", "name": "Первичный приём терапевта",          "category": "Терапия",       "duration_min": 30},
    {"id": "svc_002", "name": "Повторный приём терапевта",           "category": "Терапия",       "duration_min": 20},
    # Хирургия
    {"id": "svc_003", "name": "Первичный приём хирурга",             "category": "Хирургия",      "duration_min": 30},
    {"id": "svc_004", "name": "Перевязка",                           "category": "Хирургия",      "duration_min": 20},
    # Педиатрия
    {"id": "svc_005", "name": "Осмотр педиатра",                     "category": "Педиатрия",     "duration_min": 30},
    # Кардиология
    {"id": "svc_006", "name": "Первичный приём кардиолога",          "category": "Кардиология",   "duration_min": 40},
    {"id": "svc_007", "name": "ЭКГ с расшифровкой",                  "category": "Кардиология",   "duration_min": 20},
    # Гинекология
    {"id": "svc_008", "name": "Приём гинеколога",                    "category": "Гинекология",   "duration_min": 30},
    {"id": "svc_009", "name": "УЗИ органов малого таза",             "category": "Гинекология",   "duration_min": 30},
    # Неврология
    {"id": "svc_010", "name": "Приём невролога",                     "category": "Неврология",    "duration_min": 40},
    # Дерматология
    {"id": "svc_011", "name": "Приём дерматолога",                   "category": "Дерматология",  "duration_min": 30},
    # Офтальмология
    {"id": "svc_012", "name": "Осмотр офтальмолога",                 "category": "Офтальмология", "duration_min": 30},
    # Эндокринология
    {"id": "svc_013", "name": "Приём эндокринолога",                 "category": "Эндокринология","duration_min": 40},
    # Ортопедия
    {"id": "svc_014", "name": "Приём ортопеда",                      "category": "Ортопедия",     "duration_min": 40},
    {"id": "svc_015", "name": "Рентгенография (1 проекция)",         "category": "Диагностика",   "duration_min": 15},
    {"id": "svc_016", "name": "УЗИ брюшной полости",                 "category": "Диагностика",   "duration_min": 30},
    {"id": "svc_017", "name": "Общий анализ крови",                  "category": "Лабораторные",  "duration_min": 10},
    {"id": "svc_018", "name": "Биохимический анализ крови",          "category": "Лабораторные",  "duration_min": 10},
]


async def _fetch_doctors_from_1c() -> list[dict] | None:
    """Пытается получить список врачей из 1С. Возвращает None если недоступен."""
    if not settings.ONEC_API_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.ONEC_API_URL}/hs/loyalty/v1/doctors",
                auth=(settings.ONEC_USERNAME, settings.ONEC_PASSWORD),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"Не удалось получить врачей из 1С: {e}")
        return None


async def _fetch_services_from_1c() -> list[dict] | None:
    """Пытается получить список услуг из 1С. Возвращает None если недоступен."""
    if not settings.ONEC_API_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.ONEC_API_URL}/hs/loyalty/v1/services",
                auth=(settings.ONEC_USERNAME, settings.ONEC_PASSWORD),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"Не удалось получить услуги из 1С: {e}")
        return None


async def _push_appointment_to_1c(appt: AppointmentRequest, user: User) -> str | None:
    """Отправляет заявку в 1С и возвращает ID документа. None если недоступен."""
    if not settings.ONEC_API_URL:
        return None
    try:
        payload = {
            "patient_external_id": user.external_id or str(user.id),
            "patient_name": user.full_name,
            "patient_phone": user.phone,
            "doctor_id": appt.doctor_id,
            "doctor_name": appt.doctor_name,
            "service_id": appt.service_id,
            "service_name": appt.service_name,
            "preferred_date": appt.preferred_date.isoformat() if appt.preferred_date else None,
            "preferred_time_slot": appt.preferred_time_slot,
            "comment": appt.comment,
            "source": "loyalty_app",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.ONEC_API_URL}/hs/loyalty/v1/appointments",
                json=payload,
                auth=(settings.ONEC_USERNAME, settings.ONEC_PASSWORD),
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("document_id")
    except Exception as e:
        logger.warning(f"Не удалось передать заявку в 1С: {e}")
        return None


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@router.get("/doctors", response_model=List[DoctorOut])
async def get_doctors():
    """Список врачей. Берётся из 1С если доступна, иначе — статика."""
    data = await _fetch_doctors_from_1c()
    if data:
        return data
    return STATIC_DOCTORS


@router.get("/services", response_model=List[ServiceOut])
async def get_services():
    """Список услуг. Берётся из 1С если доступна, иначе — статика."""
    data = await _fetch_services_from_1c()
    if data:
        return data
    return STATIC_SERVICES


@router.post("/request", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создать заявку на запись. Сохраняется локально + пробрасывается в 1С."""
    if not body.doctor_id and not body.service_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите врача или услугу",
        )

    appt = AppointmentRequest(
        user_id=current_user.id,
        doctor_id=body.doctor_id,
        doctor_name=body.doctor_name,
        service_id=body.service_id,
        service_name=body.service_name,
        preferred_date=body.preferred_date,
        preferred_time_slot=body.preferred_time_slot,
        comment=body.comment,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # Попытка передачи в 1С (не блокирует если 1С недоступна)
    onec_id = await _push_appointment_to_1c(appt, current_user)
    if onec_id:
        appt.onec_document_id = onec_id
        appt.status = AppointmentStatus.CONFIRMED
        db.commit()
        db.refresh(appt)
        logger.info(f"Заявка {appt.id} передана в 1С: {onec_id}")
    else:
        logger.info(f"Заявка {appt.id} сохранена локально (1С недоступна)")

    return appt


@router.get("/my", response_model=List[AppointmentOut])
async def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """История заявок текущего пользователя."""
    appts = (
        db.query(AppointmentRequest)
        .filter(AppointmentRequest.user_id == current_user.id)
        .order_by(AppointmentRequest.created_at.desc())
        .all()
    )
    return appts


@router.delete("/request/{appointment_id}", status_code=204)
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отменить заявку."""
    appt = db.query(AppointmentRequest).filter(
        AppointmentRequest.id == appointment_id,
        AppointmentRequest.user_id == current_user.id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if appt.status == AppointmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Выполненную заявку нельзя отменить")
    appt.status = AppointmentStatus.CANCELLED
    db.commit()
