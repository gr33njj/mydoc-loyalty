from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import secrets

from database import get_db
from config import settings
from models import User
from routers.auth import create_access_token, get_password_hash

router = APIRouter()

class TokenVerifyRequest(BaseModel):
    token: str

@router.post("/verify-token")
async def verify_bitrix_token(
    request: TokenVerifyRequest,
    db: Session = Depends(get_db)
):
    """Проверяет токен от Bitrix и авторизует пользователя"""
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔄 Проверка токена Bitrix: {request.token[:20]}...")
        
        # Проверяем токен у Bitrix
        async with httpx.AsyncClient() as client:
            logger.info(f"📡 Отправка запроса на {settings.bitrix_domain}/local/api/verify_token.php")
            response = await client.post(
                f"{settings.bitrix_domain}/local/api/verify_token.php",
                json={"token": request.token},
                timeout=10.0
            )
            logger.info(f"📥 Статус ответа: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            logger.info(f"📋 Ответ Bitrix: {result}")
        
        if not result.get('success'):
            logger.error(f"❌ Bitrix вернул ошибку: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('error', 'Invalid token')
            )
        
        user_data = result['user']
        bitrix_id = str(user_data['bitrix_id'])
        email = user_data['email']
        
        # Ищем или создаем пользователя
        user = db.query(User).filter(User.bitrix_id == bitrix_id).first()
        
        if not user:
            # Проверяем по email
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Привязываем существующего пользователя
                user.bitrix_id = bitrix_id
            else:
                # Создаем нового пользователя
                user = User(
                    email=email,
                    password_hash=get_password_hash(secrets.token_urlsafe(16)),
                    bitrix_id=bitrix_id,
                    role="patient"
                )
            
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Генерируем JWT токен
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "success": True,
            "token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка связи с Bitrix: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {str(e)}"
        )

