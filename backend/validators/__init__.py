"""
Centralized Validation Schemas
All Pydantic models for request/response validation
"""

from .auth_validators import *
from .user_validators import *
from .portfolio_validators import *
from .trading_validators import *
from .wallet_validators import *
from .alert_validators import *
from .transfer_validators import *

__all__ = [
    # Auth
    'SignupRequest', 'LoginRequest', 'EmailVerificationRequest',
    'ForgotPasswordRequest', 'ResetPasswordRequest', 'ChangePasswordRequest',
    'TwoFactorSetupRequest', 'TwoFactorVerifyRequest',
    
    # User
    'UserProfileUpdate', 'UserPreferencesUpdate',
    
    # Portfolio
    'AddHoldingRequest', 'UpdateHoldingRequest',
    
    # Trading
    'PlaceOrderRequest', 'CancelOrderRequest',
    
    # Wallet
    'DepositRequest', 'WithdrawRequest', 'TransferRequest',
    
    # Alerts
    'CreateAlertRequest', 'UpdateAlertRequest',
    
    # Transfers
    'P2PTransferRequest',
]
