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
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    backup_codes: List[str] = Field(default_factory=list)


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
