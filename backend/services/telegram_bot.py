"""
Telegram Bot Service for Admin KYC Notifications
Free integration using Telegram Bot API - No costs
"""
import asyncio
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import httpx
from config import settings

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Telegram bot for admin notifications and command handling"""
    
    def __init__(self):
        # Get from environment variables
        self.bot_token = settings.__dict__.get('telegram_bot_token', '')
        admin_chat_id_str = settings.__dict__.get('admin_telegram_chat_id', '')
        
        # Support multiple chat IDs (comma-separated)
        if admin_chat_id_str:
            self.admin_chat_ids = [cid.strip() for cid in admin_chat_id_str.split(',') if cid.strip()]
        else:
            self.admin_chat_ids = []
        
        # Check if configured
        self.enabled = bool(self.bot_token and self.admin_chat_ids)
        
        if not self.enabled:
            logger.warning("⚠️ Telegram bot not configured - admin notifications disabled")
            logger.info("   Set TELEGRAM_BOT_TOKEN and ADMIN_TELEGRAM_CHAT_ID to enable")
        else:
            logger.info(f"✅ Telegram bot service initialized ({len(self.admin_chat_ids)} admin(s))")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to all admin chats"""
        if not self.enabled:
            logger.info(f"[MOCK] Telegram: {text[:100]}...")
            return True
        
        success_count = 0
        
        # Send to all admin chat IDs
        for chat_id in self.admin_chat_ids:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        f"{self.base_url}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": text,
                            "parse_mode": parse_mode
                        }
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Telegram message sent to admin {chat_id}")
                        success_count += 1
                    else:
                        logger.error(f"❌ Telegram API error for {chat_id}: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.error(f"❌ Telegram send failed for {chat_id}: {str(e)}")
        
        # Return True if at least one message was sent successfully
        return success_count > 0
    
    async def notify_new_kyc_submission(
        self,
        user_id: str,
        user_data: Dict[str, Any]
    ) -> bool:
        """Notify admin of new KYC submission"""
        
        # Format user data
        full_name = user_data.get('full_name', 'Unknown')
        email = user_data.get('email', 'Unknown')
        dob = user_data.get('dob', 'Not provided')
        phone = user_data.get('phone', 'Not provided')
        occupation = user_data.get('occupation', 'Not provided')
        
        # Fraud detection data
        ip_address = user_data.get('ip_address', 'Unknown')
        is_proxied = user_data.get('is_proxied', False)
        device_fingerprint = user_data.get('device_fingerprint', 'Not captured')
        user_agent = user_data.get('user_agent', 'Unknown')
        screen_info = user_data.get('screen_info', {})
        
        # Format screen info
        screen_text = f"{screen_info.get('width', '?')}x{screen_info.get('height', '?')}" if screen_info else "Unknown"
        
        # Build message
        message = f"""
🚨 <b>NEW KYC SUBMISSION</b> 🚨

👤 <b>User Info:</b>
━━━━━━━━━━━━━━
<b>ID:</b> <code>{user_id}</code>
<b>Name:</b> {full_name}
<b>Email:</b> {email}
<b>DOB:</b> {dob}
<b>Phone:</b> {phone}
<b>Occupation:</b> {occupation}

🔍 <b>Fraud Detection:</b>
━━━━━━━━━━━━━━
<b>IP:</b> <code>{ip_address}</code>
<b>Proxied:</b> {'⚠️ YES' if is_proxied else '✅ NO'}
<b>Fingerprint:</b> <code>{device_fingerprint[:16]}...</code>
<b>Screen:</b> {screen_text}
<b>User-Agent:</b> {user_agent[:50]}...

📄 <b>Submitted Documents:</b>
{len(user_data.get('kyc_docs', []))} file(s) uploaded

━━━━━━━━━━━━━━
<b>⚡ Quick Actions:</b>
<code>/approve {user_id}</code>
<code>/reject {user_id} [reason]</code>
<code>/info {user_id}</code>
        """
        
        return await self.send_message(message)
    
    async def notify_admin_otp(
        self,
        admin_email: str,
        otp_code: str,
        ip_address: str
    ) -> bool:
        """Notify admin of OTP login attempt"""
        
        message = f"""
🔐 <b>ADMIN OTP REQUEST</b>

<b>Email:</b> {admin_email}
<b>OTP Code:</b> <code>{otp_code}</code>
<b>IP Address:</b> <code>{ip_address}</code>
<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

⚠️ <b>Security Note:</b> If you didn't request this, contact security immediately.
        """
        
        return await self.send_message(message)
    
    async def notify_deposit_created(
        self,
        user_id: str,
        user_email: str,
        amount: float,
        currency: str,
        order_id: str,
        payment_id: str
    ) -> bool:
        """Notify admin of new deposit request"""
        
        message = f"""
💰 <b>NEW DEPOSIT CREATED</b>

👤 <b>User Info:</b>
━━━━━━━━━━━━━━
<b>User ID:</b> <code>{user_id}</code>
<b>Email:</b> {user_email}

💵 <b>Deposit Details:</b>
━━━━━━━━━━━━━━
<b>Amount:</b> ${amount:.2f} USD
<b>Pay With:</b> {currency.upper()}
<b>Order ID:</b> <code>{order_id}</code>
<b>Payment ID:</b> <code>{payment_id}</code>

📊 <b>Status:</b> ⏳ Waiting for payment
<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━
Monitor: <code>/deposit_status {order_id}</code>
        """
        
        return await self.send_message(message)
    
    async def notify_deposit_completed(
        self,
        user_id: str,
        user_email: str,
        amount: float,
        currency: str,
        order_id: str,
        payment_id: str,
        new_balance: float
    ) -> bool:
        """Notify admin of completed deposit"""
        
        message = f"""
✅ <b>DEPOSIT COMPLETED</b>

👤 <b>User Info:</b>
━━━━━━━━━━━━━━
<b>User ID:</b> <code>{user_id}</code>
<b>Email:</b> {user_email}

💵 <b>Deposit Details:</b>
━━━━━━━━━━━━━━
<b>Amount Deposited:</b> ${amount:.2f} USD
<b>Paid With:</b> {currency.upper()}
<b>Order ID:</b> <code>{order_id}</code>
<b>Payment ID:</b> <code>{payment_id}</code>

💰 <b>Wallet Update:</b>
<b>New Balance:</b> ${new_balance:.2f} USD

📊 <b>Status:</b> ✅ Completed & Credited
<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━
<b>Action:</b> Funds credited to user wallet
        """
        
        return await self.send_message(message)
    
    async def notify_deposit_failed(
        self,
        user_id: str,
        user_email: str,
        amount: float,
        currency: str,
        order_id: str,
        payment_id: str,
        reason: str
    ) -> bool:
        """Notify admin of failed deposit"""
        
        message = f"""
❌ <b>DEPOSIT FAILED</b>

👤 <b>User Info:</b>
━━━━━━━━━━━━━━
<b>User ID:</b> <code>{user_id}</code>
<b>Email:</b> {user_email}

💵 <b>Deposit Details:</b>
━━━━━━━━━━━━━━
<b>Amount:</b> ${amount:.2f} USD
<b>Currency:</b> {currency.upper()}
<b>Order ID:</b> <code>{order_id}</code>
<b>Payment ID:</b> <code>{payment_id}</code>

⚠️ <b>Failure Reason:</b>
{reason}

📊 <b>Status:</b> ❌ Failed
<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━
<b>Action Required:</b> Check logs and contact user
        """
        
        return await self.send_message(message)
    
    async def notify_withdrawal_requested(
        self,
        user_id: str,
        user_email: str,
        amount: float,
        currency: str,
        address: str,
        withdrawal_id: str
    ) -> bool:
        """Notify admin of withdrawal request"""
        
        message = f"""
💸 <b>WITHDRAWAL REQUESTED</b>

👤 <b>User Info:</b>
━━━━━━━━━━━━━━
<b>User ID:</b> <code>{user_id}</code>
<b>Email:</b> {user_email}

💵 <b>Withdrawal Details:</b>
━━━━━━━━━━━━━━
<b>Amount:</b> {amount:.8f} {currency}
<b>Destination:</b> <code>{address[:20]}...{address[-10:]}</code>
<b>Withdrawal ID:</b> <code>{withdrawal_id}</code>

📊 <b>Status:</b> ⏳ Pending Approval
<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━
<b>⚡ Quick Actions:</b>
<code>/approve_withdrawal {withdrawal_id}</code>
<code>/reject_withdrawal {withdrawal_id} [reason]</code>

⚠️ <b>Security:</b> Verify user and address before approval
        """
        
        return await self.send_message(message)
    
    async def notify_webhook_received(
        self,
        order_id: str,
        payment_status: str,
        payment_id: str
    ) -> bool:
        """Notify admin of webhook received"""
        
        status_emoji = {
            'waiting': '⏳',
            'confirming': '🔄',
            'confirmed': '✅',
            'finished': '✅',
            'failed': '❌',
            'expired': '⏰',
            'partially_paid': '⚠️'
        }
        
        emoji = status_emoji.get(payment_status, '📬')
        
        message = f"""
{emoji} <b>WEBHOOK RECEIVED</b>

<b>Order ID:</b> <code>{order_id}</code>
<b>Payment ID:</b> <code>{payment_id}</code>
<b>Status:</b> {payment_status.upper()}

<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━
Check logs for details: <code>{order_id}</code>
        """
        
        return await self.send_message(message)
    
    async def notify_system_alert(
        self,
        alert_type: str,
        message_text: str,
        severity: str = "warning"
    ) -> bool:
        """Notify admin of system alerts"""
        
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        emoji = severity_emoji.get(severity.lower(), 'ℹ️')
        
        message = f"""
{emoji} <b>SYSTEM ALERT</b>

<b>Type:</b> {alert_type}
<b>Severity:</b> {severity.upper()}

<b>Message:</b>
{message_text}

<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━
Check logs and take action if needed.
        """
        
        return await self.send_message(message)
    
    async def get_updates(self, offset: Optional[int] = None) -> Dict[str, Any]:
        """Get bot updates (for command polling)"""
        if not self.enabled:
            return {"ok": False, "result": []}
        
        try:
            params = {}
            if offset:
                params['offset'] = offset
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/getUpdates",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get updates: {response.status_code}")
                    return {"ok": False, "result": []}
                    
        except Exception as e:
            logger.error(f"Failed to get updates: {str(e)}")
            return {"ok": False, "result": []}
    
    async def handle_command(
        self,
        command: str,
        args: list,
        from_dependencies
    ) -> str:
        """Handle admin commands from Telegram"""
        from database import get_database
        
        try:
            db = from_dependencies.get_db()
        except:
            db = None
        
        if not db:
            return "❌ Database not available"
        
        # Parse commands
        if command == "/approve":
            if not args:
                return "Usage: /approve <user_id>"
            
            user_id = args[0]
            
            try:
                # Update user KYC status
                result = await db.users.update_one(
                    {"id": user_id},
                    {
                        "$set": {
                            "kyc_status": "approved",
                            "kyc_approved_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                if result.modified_count > 0:
                    # Send email notification to user
                    user = await db.users.find_one({"id": user_id})
                    if user:
                        from email_service import email_service
                        from email_templates import kyc_status_update
                        
                        html_content = kyc_status_update(
                            user['name'],
                            'approved',
                            1,
                            'Your identity verification has been approved! You now have full access to all features.'
                        )
                        
                        await email_service.send_email(
                            user['email'],
                            '✅ KYC Approved - Full Access Granted',
                            html_content,
                            f"Your KYC has been approved. Welcome to CryptoVault!"
                        )
                    
                    return f"✅ User {user_id} KYC approved"
                else:
                    return f"❌ User {user_id} not found"
                    
            except Exception as e:
                logger.error(f"Failed to approve KYC: {e}")
                return f"❌ Error: {str(e)}"
        
        elif command == "/reject":
            if len(args) < 1:
                return "Usage: /reject <user_id> [reason]"
            
            user_id = args[0]
            reason = ' '.join(args[1:]) if len(args) > 1 else "KYC verification failed"
            
            try:
                result = await db.users.update_one(
                    {"id": user_id},
                    {
                        "$set": {
                            "kyc_status": "rejected",
                            "kyc_rejected_at": datetime.now(timezone.utc),
                            "kyc_rejection_reason": reason
                        }
                    }
                )
                
                if result.modified_count > 0:
                    # Send email notification to user
                    user = await db.users.find_one({"id": user_id})
                    if user:
                        from email_service import email_service
                        from email_templates import kyc_status_update
                        
                        html_content = kyc_status_update(
                            user['name'],
                            'rejected',
                            1,
                            f'Unfortunately, your KYC verification was not approved. Reason: {reason}. Please resubmit with correct documents.'
                        )
                        
                        await email_service.send_email(
                            user['email'],
                            '❌ KYC Verification Not Approved',
                            html_content,
                            f"Your KYC was not approved: {reason}"
                        )
                    
                    return f"✅ User {user_id} KYC rejected: {reason}"
                else:
                    return f"❌ User {user_id} not found"
                    
            except Exception as e:
                logger.error(f"Failed to reject KYC: {e}")
                return f"❌ Error: {str(e)}"
        
        elif command == "/info":
            if not args:
                return "Usage: /info <user_id>"
            
            user_id = args[0]
            
            try:
                user = await db.users.find_one({"id": user_id})
                
                if user:
                    return f"""
<b>User Info:</b>
ID: <code>{user['id']}</code>
Name: {user.get('name', 'N/A')}
Email: {user.get('email', 'N/A')}
KYC Status: {user.get('kyc_status', 'pending')}
Created: {user.get('created_at', 'N/A')}
                    """
                else:
                    return f"❌ User {user_id} not found"
                    
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        else:
            return f"❌ Unknown command: {command}\n\nAvailable commands:\n/approve <user_id>\n/reject <user_id> [reason]\n/info <user_id>"


# Global service instance
telegram_bot = TelegramBotService()
