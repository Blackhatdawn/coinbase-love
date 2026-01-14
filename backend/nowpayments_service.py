"""
NOWPayments Integration Service
Handles crypto payment processing for deposits
Supports MOCK mode when no API key is provided
"""
import os
import hmac
import hashlib
import httpx
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class NOWPaymentsService:
    """NOWPayments API integration for crypto deposits (with mock fallback)"""
    
    def __init__(self):
        self.api_key = os.environ.get("NOWPAYMENTS_API_KEY", "")
        self.ipn_secret = os.environ.get("NOWPAYMENTS_IPN_SECRET", "")
        self.sandbox = os.environ.get("NOWPAYMENTS_SANDBOX", "true").lower() == "true"
        
        # Enable mock mode if no API key
        self.mock_mode = not self.api_key or self.api_key.strip() == ""
        
        # Use sandbox or production URL
        self.base_url = (
            "https://api-sandbox.nowpayments.io/v1" 
            if self.sandbox 
            else "https://api.nowpayments.io/v1"
        )
        
        if self.mock_mode:
            logger.info("📦 NOWPayments initialized in MOCK mode (no API key)")
        else:
            logger.info(f"📦 NOWPayments initialized (sandbox={self.sandbox})")
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Check API status"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/status",
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"NOWPayments status check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_available_currencies(self) -> list:
        """Get list of available cryptocurrencies"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/currencies",
                    headers=self.headers
                )
                data = response.json()
                return data.get("currencies", [])
        except Exception as e:
            logger.error(f"Failed to get currencies: {e}")
            return ["btc", "eth", "usdt", "usdc", "ltc", "bnb", "sol"]
    
    async def get_min_amount(self, currency_from: str, currency_to: str = "usd") -> float:
        """Get minimum payment amount"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/min-amount",
                    headers=self.headers,
                    params={
                        "currency_from": currency_from,
                        "currency_to": currency_to
                    }
                )
                data = response.json()
                return float(data.get("min_amount", 10))
        except Exception as e:
            logger.error(f"Failed to get min amount: {e}")
            return 10.0
    
    async def get_estimated_price(
        self, 
        amount: float, 
        currency_from: str, 
        currency_to: str = "usd"
    ) -> Dict[str, Any]:
        """Get estimated price for conversion"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/estimate",
                    headers=self.headers,
                    params={
                        "amount": amount,
                        "currency_from": currency_from,
                        "currency_to": currency_to
                    }
                )
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get estimate: {e}")
            return {"error": str(e)}
    
    async def create_payment(
        self,
        price_amount: float,
        price_currency: str,
        pay_currency: str,
        order_id: str,
        order_description: str,
        ipn_callback_url: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment invoice
        
        Args:
            price_amount: Amount in price_currency (e.g., 100 USD)
            price_currency: Fiat currency (usd, eur, etc.)
            pay_currency: Crypto to pay with (btc, eth, etc.)
            order_id: Unique order identifier
            order_description: Description for the order
            ipn_callback_url: Webhook URL for payment notifications
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            customer_email: Customer email for receipt
        """
        # MOCK MODE: Return simulated payment data
        if self.mock_mode:
            mock_address = self._generate_mock_address(pay_currency)
            mock_payment_id = f"mock-{str(uuid.uuid4())[:8]}"
            
            # Simulate crypto amount based on current rough prices
            mock_rates = {"btc": 95000, "eth": 3300, "usdt": 1, "usdc": 1, "ltc": 100, "sol": 145}
            rate = mock_rates.get(pay_currency.lower(), 100)
            pay_amount = round(price_amount / rate, 8)
            
            logger.info(f"📦 [MOCK] Payment created: {mock_payment_id} for ${price_amount}")
            
            return {
                "success": True,
                "mock": True,
                "payment_id": mock_payment_id,
                "payment_status": "waiting",
                "pay_address": mock_address,
                "pay_amount": pay_amount,
                "pay_currency": pay_currency.upper(),
                "price_amount": price_amount,
                "price_currency": price_currency.upper(),
                "order_id": order_id,
                "expiration_estimate_date": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?data={mock_address}&size=200x200"
            }
        
        try:
            payload = {
                "price_amount": price_amount,
                "price_currency": price_currency,
                "pay_currency": pay_currency,
                "order_id": order_id,
                "order_description": order_description,
                "ipn_callback_url": ipn_callback_url,
                "is_fixed_rate": True,
                "is_fee_paid_by_user": False
            }
            
            if success_url:
                payload["success_url"] = success_url
            if cancel_url:
                payload["cancel_url"] = cancel_url
            if customer_email:
                payload["customer_email"] = customer_email
            
            logger.info(f"Creating NOWPayments invoice: {order_id} - ${price_amount}")
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/payment",
                    headers=self.headers,
                    json=payload
                )
                
                data = response.json()
                
                if response.status_code == 201 or response.status_code == 200:
                    logger.info(f"✅ Payment created: {data.get('payment_id')}")
                    return {
                        "success": True,
                        "payment_id": data.get("payment_id"),
                        "payment_status": data.get("payment_status"),
                        "pay_address": data.get("pay_address"),
                        "pay_amount": data.get("pay_amount"),
                        "pay_currency": data.get("pay_currency"),
                        "price_amount": data.get("price_amount"),
                        "price_currency": data.get("price_currency"),
                        "order_id": data.get("order_id"),
                        "expiration_estimate_date": data.get("expiration_estimate_date"),
                        "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?data={data.get('pay_address')}&size=200x200"
                    }
                else:
                    logger.error(f"Payment creation failed: {data}")
                    return {
                        "success": False,
                        "error": data.get("message", "Payment creation failed")
                    }
                    
        except Exception as e:
            logger.error(f"NOWPayments create_payment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_invoice(
        self,
        price_amount: float,
        price_currency: str,
        order_id: str,
        order_description: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        ipn_callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a hosted invoice (redirect to NOWPayments checkout page)
        User can choose which crypto to pay with
        """
        try:
            payload = {
                "price_amount": price_amount,
                "price_currency": price_currency,
                "order_id": order_id,
                "order_description": order_description,
                "is_fixed_rate": True,
                "is_fee_paid_by_user": False
            }
            
            if success_url:
                payload["success_url"] = success_url
            if cancel_url:
                payload["cancel_url"] = cancel_url
            if ipn_callback_url:
                payload["ipn_callback_url"] = ipn_callback_url
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/invoice",
                    headers=self.headers,
                    json=payload
                )
                
                data = response.json()
                
                if response.status_code in [200, 201]:
                    return {
                        "success": True,
                        "invoice_id": data.get("id"),
                        "invoice_url": data.get("invoice_url"),
                        "order_id": data.get("order_id"),
                        "price_amount": price_amount,
                        "price_currency": price_currency
                    }
                else:
                    return {"success": False, "error": data.get("message", "Invoice creation failed")}
                    
        except Exception as e:
            logger.error(f"NOWPayments create_invoice error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status by ID"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/payment/{payment_id}",
                    headers=self.headers
                )
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get payment status: {e}")
            return {"error": str(e)}
    
    def verify_ipn_signature(self, request_body: bytes, signature: str) -> bool:
        """
        Verify IPN webhook signature
        
        NOWPayments sends HMAC-SHA512 signature in x-nowpayments-sig header
        """
        if not self.ipn_secret:
            logger.warning("IPN secret not configured, skipping verification")
            return True
        
        try:
            # Sort JSON keys and compute HMAC
            import json
            data = json.loads(request_body)
            sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
            
            expected_sig = hmac.new(
                self.ipn_secret.encode('utf-8'),
                sorted_data.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            is_valid = hmac.compare_digest(expected_sig, signature)
            
            if not is_valid:
                logger.warning(f"IPN signature mismatch")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"IPN signature verification error: {e}")
            return False


# Payment status constants
class PaymentStatus:
    WAITING = "waiting"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    SENDING = "sending"
    PARTIALLY_PAID = "partially_paid"
    FINISHED = "finished"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    
    # Statuses that mean payment is complete
    SUCCESS_STATUSES = [FINISHED, CONFIRMED]
    
    # Statuses that mean payment is pending
    PENDING_STATUSES = [WAITING, CONFIRMING, SENDING, PARTIALLY_PAID]
    
    # Statuses that mean payment failed
    FAILED_STATUSES = [FAILED, REFUNDED, EXPIRED]


# Global service instance
nowpayments_service = NOWPaymentsService()
