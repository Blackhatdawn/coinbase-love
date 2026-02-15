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
        # Get from validated settings
        self.feature_enabled = bool(settings.telegram_enabled)
        self.bot_token = (settings.telegram_bot_token or '').strip()
        admin_chat_id_str = (settings.admin_telegram_chat_id or '').strip()

        # Support multiple chat IDs (comma-separated)
        self.admin_chat_ids = [cid.strip() for cid in admin_chat_id_str.split(',') if cid.strip()] if admin_chat_id_str else []

        # Check if configured
        self.enabled = self.feature_enabled and bool(self.bot_token and self.admin_chat_ids)

        if not self.feature_enabled:
            logger.warning("⚠️ Telegram explicitly disabled via TELEGRAM_ENABLED=false")
        elif not self.bot_token or not self.admin_chat_ids:
            logger.warning("⚠️ Telegram bot partially configured - notifications disabled")
            logger.info("   Set TELEGRAM_BOT_TOKEN and ADMIN_TELEGRAM_CHAT_ID to enable")
        else:
            logger.info(f"✅ Telegram bot service initialized ({len(self.admin_chat_ids)} admin(s))")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ""
        self._polling_task: Optional[asyncio.Task] = None
        self._last_update_id: Optional[int] = None
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to all admin chats"""
        if not self.enabled:
            logger.info("Telegram notification skipped (bot disabled or not fully configured)")
            return False
        
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
    

    async def get_health_status(self) -> Dict[str, Any]:
        """Validate Telegram connectivity and return service health metadata."""
        status: Dict[str, Any] = {
            "feature_enabled": self.feature_enabled,
            "enabled": self.enabled,
            "configured_admin_count": len(self.admin_chat_ids),
            "api_reachable": False,
            "bot_username": None,
        }

        if not self.enabled:
            return status

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/getMe")
            if response.status_code != 200:
                logger.error("❌ Telegram getMe failed: %s - %s", response.status_code, response.text)
                return status

            payload = response.json()
            if payload.get("ok") and payload.get("result"):
                status["api_reachable"] = True
                status["bot_username"] = payload["result"].get("username")
            else:
                logger.error("❌ Telegram getMe unexpected payload: %s", payload)
        except Exception as exc:
            logger.error("❌ Telegram connectivity check failed: %s", exc)

        return status


    async def start_command_polling(self) -> None:
        """Start Telegram command polling loop if bot is enabled."""
        if not self.enabled:
            logger.info("Telegram command polling not started (bot disabled or not fully configured)")
            return
        if self._polling_task and not self._polling_task.done():
            return

        self._polling_task = asyncio.create_task(self._poll_commands_loop())
        logger.info("✅ Telegram command polling started")

    async def stop_command_polling(self) -> None:
        """Stop Telegram command polling loop gracefully."""
        if not self._polling_task:
            return

        self._polling_task.cancel()
        try:
            await self._polling_task
        except asyncio.CancelledError:
            pass
        finally:
            self._polling_task = None

    async def _poll_commands_loop(self) -> None:
        """Poll Telegram updates and execute supported admin commands."""
        import dependencies

        while True:
            try:
                updates = await self.get_updates(offset=self._last_update_id)
                for update in updates.get("result", []):
                    update_id = update.get("update_id")
                    if isinstance(update_id, int):
                        self._last_update_id = update_id + 1

                    message = update.get("message") or {}
                    text = (message.get("text") or "").strip()
                    if not text.startswith("/"):
                        continue

                    chat_id = str((message.get("chat") or {}).get("id", "")).strip()
                    if chat_id not in self.admin_chat_ids:
                        logger.warning("⚠️ Ignoring Telegram command from unauthorized chat_id=%s", chat_id)
                        continue

                    pieces = text.split()
                    command, args = pieces[0], pieces[1:]
                    result_text = await self.handle_command(command, args, dependencies)

                    await self.send_message(
                        f"<b>Command:</b> <code>{command}</code>\n"
                        f"<b>Result:</b> {result_text}"
                    )
            except asyncio.CancelledError:
                logger.info("Telegram command polling stopped")
                raise
            except Exception as exc:
                logger.error("Telegram command polling loop error: %s", exc)

            await asyncio.sleep(2)

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
        
        elif command == "/deposit_status":
            if not args:
                return "Usage: /deposit_status <order_id>"
            
            order_id = args[0]
            
            try:
                deposit = await db.get_collection("deposits").find_one({"order_id": order_id})
                
                if deposit:
                    user = await db.get_collection("users").find_one({"id": deposit['user_id']})
                    user_email = user.get('email', 'N/A') if user else 'N/A'
                    
                    return f"""
<b>Deposit Status:</b>
━━━━━━━━━━━━━━
<b>Order ID:</b> <code>{deposit['order_id']}</code>
<b>User:</b> {user_email}
<b>Amount:</b> ${deposit['amount']:.2f} USD
<b>Currency:</b> {deposit['pay_currency']}
<b>Status:</b> {deposit['status'].upper()}
<b>Created:</b> {deposit['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}
<b>Payment ID:</b> <code>{deposit.get('payment_id', 'N/A')}</code>
                    """
                else:
                    return f"❌ Deposit {order_id} not found"
                    
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        elif command == "/approve_withdrawal":
            if not args:
                return "Usage: /approve_withdrawal <withdrawal_id>"
            
            withdrawal_id = args[0]
            
            try:
                # Update withdrawal status to processing
                result = await db.get_collection("withdrawals").update_one(
                    {"id": withdrawal_id, "status": "pending"},
                    {
                        "$set": {
                            "status": "processing",
                            "processed_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                if result.modified_count > 0:
                    return f"✅ Withdrawal {withdrawal_id} approved and set to processing"
                else:
                    return f"❌ Withdrawal {withdrawal_id} not found or already processed"
                    
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        elif command == "/reject_withdrawal":
            if len(args) < 1:
                return "Usage: /reject_withdrawal <withdrawal_id> [reason]"
            
            withdrawal_id = args[0]
            reason = ' '.join(args[1:]) if len(args) > 1 else "Rejected by admin"
            
            try:
                # Get withdrawal to refund amount
                withdrawal = await db.get_collection("withdrawals").find_one({"id": withdrawal_id})
                
                if not withdrawal:
                    return f"❌ Withdrawal {withdrawal_id} not found"
                
                if withdrawal['status'] != 'pending':
                    return f"❌ Withdrawal {withdrawal_id} is not pending (status: {withdrawal['status']})"
                
                # Update withdrawal status
                await db.get_collection("withdrawals").update_one(
                    {"id": withdrawal_id},
                    {
                        "$set": {
                            "status": "cancelled",
                            "notes": reason,
                            "processed_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Refund amount to wallet
                total_amount = withdrawal['total_amount']
                currency = withdrawal['currency']
                user_id = withdrawal['user_id']
                
                wallet = await db.get_collection("wallets").find_one({"user_id": user_id})
                if wallet:
                    current_balance = wallet.get('balances', {}).get(currency, 0)
                    await db.get_collection("wallets").update_one(
                        {"user_id": user_id},
                        {
                            "$set": {
                                f"balances.{currency}": current_balance + total_amount,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                
                return f"✅ Withdrawal {withdrawal_id} rejected and amount refunded: {reason}"
                    
            except Exception as e:
                logger.error(f"Failed to reject withdrawal: {e}")
                return f"❌ Error: {str(e)}"
        
        elif command == "/stats":
            """Get platform statistics"""
            try:
                # Get total users
                total_users = await db.get_collection("users").count_documents({})
                
                # Get pending deposits
                pending_deposits = await db.get_collection("deposits").count_documents({"status": "pending"})
                
                # Get pending withdrawals
                pending_withdrawals = await db.get_collection("withdrawals").count_documents({"status": "pending"})
                
                # Get total deposits today
                from datetime import timedelta
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                today_deposits = await db.get_collection("deposits").count_documents({
                    "created_at": {"$gte": today_start},
                    "status": "finished"
                })
                
                return f"""
<b>Platform Statistics:</b>
━━━━━━━━━━━━━━
<b>Total Users:</b> {total_users}
<b>Pending Deposits:</b> {pending_deposits}
<b>Pending Withdrawals:</b> {pending_withdrawals}
<b>Completed Deposits Today:</b> {today_deposits}

<b>Time:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                """
                    
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        else:
            return f"""❌ Unknown command: {command}

<b>Available commands:</b>
━━━━━━━━━━━━━━
<b>KYC Management:</b>
/approve &lt;user_id&gt; - Approve KYC
/reject &lt;user_id&gt; [reason] - Reject KYC
/info &lt;user_id&gt; - Get user info

<b>Deposit Management:</b>
/deposit_status &lt;order_id&gt; - Check deposit

<b>Withdrawal Management:</b>
/approve_withdrawal &lt;withdrawal_id&gt;
/reject_withdrawal &lt;withdrawal_id&gt; [reason]

<b>Platform:</b>
/stats - Get platform statistics
            """


# Global service instance
telegram_bot = TelegramBotService()
