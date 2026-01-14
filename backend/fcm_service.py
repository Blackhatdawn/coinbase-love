"""
Firebase Cloud Messaging (FCM) Service
Push notifications for price alerts, order confirmations, etc.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Firebase Admin SDK
firebase_initialized = False
firebase_app = None

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global firebase_initialized, firebase_app
    
    if firebase_initialized:
        return True
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Try to get credentials from environment
        creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        
        if creds_json:
            # Parse JSON from environment variable
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
        elif creds_path and os.path.exists(creds_path):
            # Load from file
            cred = credentials.Certificate(creds_path)
        else:
            logger.warning("⚠️ Firebase credentials not found - FCM disabled")
            return False
        
        firebase_app = firebase_admin.initialize_app(cred)
        firebase_initialized = True
        logger.info("✅ Firebase Admin SDK initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        return False


class FCMService:
    """Firebase Cloud Messaging service for push notifications"""
    
    def __init__(self):
        self.initialized = initialize_firebase()
    
    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a single device
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Image URL for rich notification
        """
        if not self.initialized:
            logger.warning("FCM not initialized, skipping notification")
            return {"success": False, "error": "FCM not initialized"}
        
        try:
            from firebase_admin import messaging
            
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                token=token,
                data=data or {},
                # Android specific config
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        icon="ic_notification",
                        color="#F59E0B",
                        sound="default",
                        click_action="OPEN_APP"
                    )
                ),
                # Web push config
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon="/logo.svg",
                        badge="/logo.svg",
                        vibrate=[200, 100, 200]
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link="https://cryptovault.financial"
                    )
                )
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"✅ FCM notification sent: {response}")
            
            return {
                "success": True,
                "message_id": response
            }
            
        except Exception as e:
            logger.error(f"❌ FCM send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send notification to multiple devices"""
        if not self.initialized:
            return {"success": False, "error": "FCM not initialized"}
        
        try:
            from firebase_admin import messaging
            
            notification = messaging.Notification(title=title, body=body)
            
            message = messaging.MulticastMessage(
                notification=notification,
                tokens=tokens,
                data=data or {},
                android=messaging.AndroidConfig(priority="high"),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon="/logo.svg"
                    )
                )
            )
            
            response = messaging.send_multicast(message)
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
            
        except Exception as e:
            logger.error(f"FCM multicast error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_price_alert(
        self,
        token: str,
        symbol: str,
        current_price: float,
        target_price: float,
        condition: str
    ) -> Dict[str, Any]:
        """Send price alert notification"""
        direction = "above" if condition == "above" else "below"
        emoji = "🚀" if condition == "above" else "📉"
        
        title = f"{emoji} {symbol} Price Alert!"
        body = f"{symbol} is now ${current_price:,.2f} – {direction} your target of ${target_price:,.2f}"
        
        return await self.send_notification(
            token=token,
            title=title,
            body=body,
            data={
                "type": "price_alert",
                "symbol": symbol,
                "price": str(current_price),
                "target": str(target_price),
                "condition": condition
            }
        )
    
    async def send_order_confirmation(
        self,
        token: str,
        order_type: str,
        symbol: str,
        amount: float,
        price: float,
        order_id: str
    ) -> Dict[str, Any]:
        """Send order confirmation notification"""
        emoji = "✅" if order_type == "buy" else "💰"
        action = "bought" if order_type == "buy" else "sold"
        
        title = f"{emoji} Order Filled!"
        body = f"You {action} {amount:.6f} {symbol} at ${price:,.2f}"
        
        return await self.send_notification(
            token=token,
            title=title,
            body=body,
            data={
                "type": "order_confirmation",
                "order_id": order_id,
                "order_type": order_type,
                "symbol": symbol,
                "amount": str(amount),
                "price": str(price)
            }
        )
    
    async def send_deposit_confirmation(
        self,
        token: str,
        amount: float,
        currency: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """Send deposit confirmation notification"""
        title = "💰 Deposit Received!"
        body = f"Your deposit of ${amount:,.2f} has been credited to your account"
        
        return await self.send_notification(
            token=token,
            title=title,
            body=body,
            data={
                "type": "deposit_confirmation",
                "amount": str(amount),
                "currency": currency,
                "payment_id": payment_id
            }
        )
    
    async def send_referral_notification(
        self,
        token: str,
        referee_name: str,
        reward_amount: float
    ) -> Dict[str, Any]:
        """Send referral reward notification"""
        title = "🎉 Referral Reward!"
        body = f"{referee_name} joined via your link! You earned ${reward_amount:.2f}"
        
        return await self.send_notification(
            token=token,
            title=title,
            body=body,
            data={
                "type": "referral_reward",
                "referee": referee_name,
                "reward": str(reward_amount)
            }
        )


# Global service instance
fcm_service = FCMService()
