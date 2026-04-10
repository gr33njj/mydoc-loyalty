"""
Роутер онлайн-записи к врачам.

Архитектура:
  - Список врачей: из Catalog_Сотрудники (1С OData), fallback — статика
  - Список услуг: из Catalog_Номенклатура (1С OData), fallback — статика
  - Создание заявки: POST в Document_Заявка (1С OData) + сохранение в БД
  - Клиент в 1С ищется по Catalog_Клиенты.phone
  - ONEC_API_URL формат: http://192.168.100.234/BITtest
                          (базовая часть без /odata/...)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import AppointmentRequest, AppointmentStatus, User
from onec_utils import odata_auth, odata_url
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
    """Список врачей из Catalog_Сотрудники (1С OData)."""
    if not settings.ONEC_API_URL:
        return None
    try:
        params = {
            "$filter": "IsFolder eq false and DeletionMark eq false",
            "$select": "Ref_Key,Description",
            "$format": "json",
            "$orderby": "Description",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                odata_url("Catalog_%D0%A1%D0%BE%D1%82%D1%80%D1%83%D0%B4%D0%BD%D0%B8%D0%BA%D0%B8"),
                params=params,
                auth=odata_auth(),
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            {
                "id": v["Ref_Key"],
                "name": v.get("Description", ""),
                "specialty": "",   # Специализация требует отдельного запроса
                "photo_url": None,
            }
            for v in data.get("value", [])
            if v.get("Description", "").strip()
        ]
    except Exception as e:
        logger.warning(f"Не удалось получить врачей из 1С: {e}")
        return None


async def _fetch_services_from_1c() -> list[dict] | None:
    """Список услуг из Catalog_Номенклатура (1С OData)."""
    if not settings.ONEC_API_URL:
        return None
    try:
        params = {
            "$filter": "IsFolder eq false and DeletionMark eq false",
            "$select": "Ref_Key,Description",
            "$format": "json",
            "$top": "200",
            "$orderby": "Description",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                odata_url("Catalog_%D0%9D%D0%BE%D0%BC%D0%B5%D0%BD%D0%BA%D0%BB%D0%B0%D1%82%D1%83%D1%80%D0%B0"),
                params=params,
                auth=odata_auth(),
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            {
                "id": v["Ref_Key"],
                "name": v.get("Description", ""),
                "category": "Услуги",
                "duration_min": 30,
            }
            for v in data.get("value", [])
            if v.get("Description", "").strip()
        ]
    except Exception as e:
        logger.warning(f"Не удалось получить услуги из 1С: {e}")
        return None


async def _find_client_in_1c(user: User) -> str | None:
    """Ищет клиента в Catalog_Клиенты по external_id и ФИО параллельно."""
    if not settings.ONEC_API_URL:
        return None

    async def _lookup(client: httpx.AsyncClient, filter_expr: str) -> str | None:
        try:
            resp = await client.get(
                odata_url("Catalog_%D0%9A%D0%BB%D0%B8%D0%B5%D0%BD%D1%82%D1%8B"),
                params={"$filter": filter_expr, "$select": "Ref_Key", "$format": "json", "$top": "1"},
                auth=odata_auth(),
            )
            if resp.status_code == 200:
                vals = resp.json().get("value", [])
                return vals[0]["Ref_Key"] if vals else None
        except Exception:
            pass
        return None

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            filters = []
            if user.external_id:
                filters.append(f"Code eq '{user.external_id}'")
            if user.full_name:
                filters.append(f"Description eq '{user.full_name}' and DeletionMark eq false")
            if not filters:
                return None
            results = await asyncio.gather(*[_lookup(client, f) for f in filters])
            return next((r for r in results if r), None)
    except Exception as e:
        logger.warning(f"Ошибка поиска клиента в 1С: {e}")
    return None


async def _push_appointment_to_1c(appt: AppointmentRequest, user: User) -> str | None:
    """
    Создаёт Document_Заявка в 1С через OData POST.
    Возвращает Ref_Key созданного документа.
    """
    if not settings.ONEC_API_URL:
        return None
    try:
        # Находим клиента в 1С
        client_key = await _find_client_in_1c(user)
        null_guid = "00000000-0000-0000-0000-000000000000"

        # Формируем дату/время начала
        dt_start = appt.preferred_date or datetime.now()
        if appt.preferred_time_slot:
            # "09:00–09:30" → берём начало
            time_part = appt.preferred_time_slot.split("–")[0].split("-")[0].strip()
            try:
                h, m = map(int, time_part.split(":"))
                dt_start = dt_start.replace(hour=h, minute=m, second=0, microsecond=0)
            except Exception:
                pass
        dt_end = dt_start + timedelta(minutes=30)

        payload = {
            "Клиент_Key": client_key or null_guid,
            "Сотрудник_Key": appt.doctor_id if appt.doctor_id and len(appt.doctor_id) == 36 else null_guid,
            "ДатаНачала": dt_start.strftime("%Y-%m-%dT%H:%M:%S"),
            "ДатаОкончания": dt_end.strftime("%Y-%m-%dT%H:%M:%S"),
            "ВремяНачала": f"0001-01-01T{dt_start.strftime('%H:%M:%S')}",
            "ВремяОкончания": f"0001-01-01T{dt_end.strftime('%H:%M:%S')}",
            "КомментарийКлиента": appt.comment or "",
            "Примечание": f"Запись через приложение Моя скидка. "
                          f"Услуга: {appt.service_name or '—'}. "
                          f"Пациент: {user.full_name or user.email}",
            "СайтНомерЗаявки": "0",
            "НесколькоСотрудников": False,
        }

        # Если выбрана услуга — добавляем в табличную часть Работы
        if appt.service_id and len(appt.service_id) == 36:
            payload["Работы"] = [{
                "Номенклатура_Key": appt.service_id,
                "ДатаНачала": dt_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "ДатаОкончания": dt_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "Продолжительность": f"0001-01-01T{dt_end.strftime('%H:%M:%S')}",
                "Сотрудник_Key": payload["Сотрудник_Key"],
                "Оборудование1_Key": null_guid,
                "Оборудование2_Key": null_guid,
                "Оборудование3_Key": null_guid,
                "ПродолжительностьИзмененаВручную": False,
            }]

        async with httpx.AsyncClient(timeout=15.0) as http:
            resp = await http.post(
                odata_url("Document_%D0%97%D0%B0%D1%8F%D0%B2%D0%BA%D0%B0"),
                json=payload,
                auth=odata_auth(),
                headers={"Content-Type": "application/json"},
                params={"$format": "json"},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                ref_key = data.get("Ref_Key") or data.get("value", {}).get("Ref_Key")
                logger.info(f"Заявка создана в 1С: {ref_key}")
                return ref_key
            else:
                logger.warning(f"1С вернул {resp.status_code}: {resp.text[:300]}")
                return None
    except Exception as e:
        logger.warning(f"Не удалось создать заявку в 1С: {e}")
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
