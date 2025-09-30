from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from models import TransactionType, CertificateStatus, ReferralEventType, RewardType


# === USER SCHEMAS ===

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str


class UserCreate(UserBase):
    password: str
    referral_code: Optional[str] = None  # Реферальный код при регистрации
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    external_id: Optional[str]
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# === LOYALTY SCHEMAS ===

class LoyaltyAccountResponse(BaseModel):
    id: int
    user_id: int
    points_balance: float
    cashback_balance: float
    total_points_earned: float
    total_points_spent: float
    total_cashback_earned: float
    total_cashback_spent: float
    card_number: Optional[str]
    card_tier: str
    
    class Config:
        from_attributes = True


class LoyaltyTransactionCreate(BaseModel):
    account_id: int
    transaction_type: TransactionType
    amount: float
    currency: str = "points"
    source: str
    source_id: Optional[str] = None
    description: str
    metadata: Optional[dict] = None
    idempotency_key: Optional[str] = None


class LoyaltyTransactionResponse(BaseModel):
    id: int
    account_id: int
    transaction_type: TransactionType
    amount: float
    currency: str
    source: str
    source_id: Optional[str]
    description: str
    is_reversed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    points_balance: float
    cashback_balance: float
    card_tier: str
    transactions_count: int


class TransactionHistoryResponse(BaseModel):
    transactions: List[LoyaltyTransactionResponse]
    total: int
    page: int
    page_size: int


# === CERTIFICATE SCHEMAS ===

class CertificateCreate(BaseModel):
    initial_amount: float
    valid_until: Optional[datetime] = None  # Опционально, по умолчанию +1 год
    owner_id: Optional[int] = None  # Опционально, может быть без владельца
    message: Optional[str] = None
    design_template: str = "default"
    
    @validator('initial_amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма должна быть больше нуля')
        return v


class CertificateResponse(BaseModel):
    id: int
    code: str
    initial_amount: float
    current_amount: float
    status: CertificateStatus
    owner_id: int
    issued_at: datetime
    valid_from: datetime
    valid_until: datetime
    used_at: Optional[datetime]
    design_template: str
    message: Optional[str]
    qr_code_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class CertificateTransferCreate(BaseModel):
    certificate_id: int
    to_user_email: str
    message: Optional[str] = None


class CertificateVerifyRequest(BaseModel):
    code: str


class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate: Optional[CertificateResponse]
    message: str


class CertificateRedeemRequest(BaseModel):
    code: str
    amount: float
    cashier_id: int
    onec_document_id: Optional[str] = None
    notes: Optional[str] = None


class CertificateRedeemResponse(BaseModel):
    success: bool
    certificate_id: int
    amount_used: float
    remaining_amount: float
    message: str


# === REFERRAL SCHEMAS ===

class ReferralCodeCreate(BaseModel):
    user_id: int
    referrer_type: str = "patient"
    custom_code: Optional[str] = None


class ReferralCodeResponse(BaseModel):
    id: int
    user_id: int
    code: str
    referrer_type: str
    total_referrals: int
    successful_referrals: int
    total_revenue: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReferralEventCreate(BaseModel):
    referral_code: str
    referred_user_id: int
    event_type: ReferralEventType
    transaction_amount: Optional[float] = None
    onec_document_id: Optional[str] = None
    metadata: Optional[dict] = None


class ReferralEventResponse(BaseModel):
    id: int
    referral_code_id: int
    referred_user_id: int
    event_type: ReferralEventType
    transaction_amount: Optional[float]
    processed: bool
    occurred_at: datetime
    
    class Config:
        from_attributes = True


class ReferralRewardResponse(BaseModel):
    id: int
    event_id: int
    recipient_user_id: int
    reward_type: RewardType
    reward_amount: float
    referral_level: int
    awarded_at: datetime
    
    class Config:
        from_attributes = True


class ReferralStatsResponse(BaseModel):
    total_referrals: int
    successful_referrals: int
    pending_referrals: int
    total_revenue: float
    total_rewards: float
    conversion_rate: float
    referral_code: str


# === ADMIN SCHEMAS ===

class AdminDashboardStats(BaseModel):
    total_users: int
    active_certificates: int
    total_certificates_value: float
    total_loyalty_points: float
    total_loyalty_cashback: float
    active_referral_codes: int
    today_transactions: int


class AdminCertificateList(BaseModel):
    certificates: List[CertificateResponse]
    total: int
    page: int
    page_size: int


class AdminUserList(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


# === INTEGRATION SCHEMAS ===

class OneCWebhookVisit(BaseModel):
    """Webhook от 1С о визите пациента"""
    document_id: str
    patient_external_id: str
    visit_date: datetime
    total_amount: float
    services: List[dict]
    discount_amount: Optional[float] = 0
    points_to_accrue: Optional[float] = 0
    cashback_to_accrue: Optional[float] = 0


class OneCWebhookPayment(BaseModel):
    """Webhook от 1С об оплате"""
    document_id: str
    patient_external_id: str
    payment_date: datetime
    amount: float
    payment_method: str


class BitrixWebhookContact(BaseModel):
    """Webhook от Bitrix о контакте"""
    contact_id: str
    email: str
    phone: Optional[str]
    name: str
    last_name: str
