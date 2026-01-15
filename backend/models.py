from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    email_verified: bool = False
    email_verification_token: Optional[str] = None
    email_verification_code: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    backup_codes: List[str] = Field(default_factory=list)
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    createdAt: str


class VerifyEmailRequest(BaseModel):
    token: str  # Can be 6-digit code or UUID token


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# Cryptocurrency Models
class Cryptocurrency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    name: str
    price: float
    market_cap: float
    volume_24h: float
    change_24h: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# Portfolio Models
class Holding(BaseModel):
    symbol: str
    name: str
    amount: float
    value: float
    allocation: float
    change: Optional[float] = None


class Portfolio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    holdings: List[Holding] = Field(default_factory=list)
    total_balance: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HoldingCreate(BaseModel):
    symbol: str
    name: str
    amount: float


# Order Models
class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    trading_pair: str
    order_type: str  # market, limit
    side: str  # buy, sell
    amount: float
    price: float
    status: str = "pending"  # pending, filled, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None


class OrderCreate(BaseModel):
    trading_pair: str
    order_type: str
    side: str
    amount: float
    price: float


# Transaction Models
class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # deposit, withdrawal, trade, fee
    amount: float
    symbol: Optional[str] = None
    description: Optional[str] = None
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionCreate(BaseModel):
    type: str
    amount: float
    symbol: Optional[str] = None
    description: Optional[str] = None


# Audit Log Models
class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    resource: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Alias for backward compatibility with endpoints expecting 'timestamp'
    @property
    def timestamp(self) -> datetime:
        return self.created_at


# Token Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# 2FA Models
class TwoFactorSetup(BaseModel):
    secret: str
    qr_code_url: str


class TwoFactorVerify(BaseModel):
    code: str


class BackupCodes(BaseModel):
    codes: List[str]


# Wallet Models
class Wallet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    balances: dict = Field(default_factory=dict)  # {"USD": 1000.0, "BTC": 0.5}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Deposit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    order_id: str
    payment_id: Optional[str] = None
    amount: float
    currency: str  # USD
    pay_currency: str  # BTC, ETH, etc.
    pay_amount: Optional[float] = None
    pay_address: Optional[str] = None
    status: str = "pending"  # pending, confirming, confirmed, finished, failed
    mock: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Withdrawal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    currency: str
    address: str
    status: str = "pending"  # pending, processing, completed, failed, cancelled
    fee: float = 0.0
    net_amount: float
    transaction_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Price Alert Models
class PriceAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    symbol: str  # BTC, ETH, etc.
    target_price: float
    condition: str  # "above" or "below"
    is_active: bool = True
    notify_email: bool = True
    notify_push: bool = False
    triggered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PriceAlertCreate(BaseModel):
    symbol: str
    target_price: float = Field(gt=0)
    condition: str  # "above" or "below"
    notify_email: bool = True
    notify_push: bool = False


class PriceAlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    target_price: Optional[float] = Field(default=None, gt=0)
    condition: Optional[str] = None
    notify_email: Optional[bool] = None
    notify_push: Optional[bool] = None


# Notification Models
class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: str  # info, success, warning, error, alert
    read: bool = False
    link: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"
    link: Optional[str] = None


# Session Models
class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)

