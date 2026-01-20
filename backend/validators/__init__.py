"""
Centralized Validation Schemas
All Pydantic models for request/response validation
"""

from .auth_validators import (
    SignupRequest, LoginRequest, EmailVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    TwoFactorSetupRequest, TwoFactorVerifyRequest, RefreshTokenRequest
)
from .user_validators import (
    UserProfileUpdate, UserPreferencesUpdate, UserSecurityUpdate
)
from .portfolio_validators import (
    AddHoldingRequest, UpdateHoldingRequest, RemoveHoldingRequest
)
from .trading_validators import (
    PlaceOrderRequest, CancelOrderRequest, ModifyOrderRequest
)
from .wallet_validators import (
    DepositRequest, WithdrawRequest, InternalTransferRequest
)
from .alert_validators import (
    CreateAlertRequest, UpdateAlertRequest, DeleteAlertRequest
)
from .transfer_validators import (
    P2PTransferRequest, AcceptTransferRequest, RejectTransferRequest, FeeEstimateRequest
)

__all__ = [
    # Auth
    'SignupRequest', 'LoginRequest', 'EmailVerificationRequest',
    'ForgotPasswordRequest', 'ResetPasswordRequest', 'ChangePasswordRequest',
    'TwoFactorSetupRequest', 'TwoFactorVerifyRequest', 'RefreshTokenRequest',
    
    # User
    'UserProfileUpdate', 'UserPreferencesUpdate', 'UserSecurityUpdate',
    
    # Portfolio
    'AddHoldingRequest', 'UpdateHoldingRequest', 'RemoveHoldingRequest',
    
    # Trading
    'PlaceOrderRequest', 'CancelOrderRequest', 'ModifyOrderRequest',
    
    # Wallet
    'DepositRequest', 'WithdrawRequest', 'InternalTransferRequest',
    
    # Alerts
    'CreateAlertRequest', 'UpdateAlertRequest', 'DeleteAlertRequest',
    
    # Transfers
    'P2PTransferRequest', 'AcceptTransferRequest', 'RejectTransferRequest', 'FeeEstimateRequest',
]
