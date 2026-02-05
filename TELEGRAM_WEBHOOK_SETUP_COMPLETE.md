# 🚀 CryptoVault Telegram Bot & Webhook - Complete Setup Guide

**Date:** February 5, 2025  
**Status:** ✅ Enhanced & Production-Ready

---

## 📋 Overview

This guide covers the complete setup of:
1. Telegram Bot for admin notifications
2. NOWPayments webhook configuration
3. End-to-end testing
4. Production deployment

---

## 🤖 Telegram Bot Enhancements

### New Features Added

#### 1. **Deposit Notifications** 💰
- New deposit created notification
- Deposit completed notification (with balance update)
- Deposit failed notification

#### 2. **Withdrawal Management** 💸
- Withdrawal request notifications
- Admin approval commands
- Refund on rejection

#### 3. **Webhook Monitoring** 📬
- Real-time webhook status updates
- Payment status tracking

#### 4. **System Alerts** 🚨
- Critical system notifications
- Error alerts
- Warning messages

#### 5. **Enhanced Commands** ⚡
New admin commands:
- `/deposit_status <order_id>` - Check deposit status
- `/approve_withdrawal <withdrawal_id>` - Approve withdrawal
- `/reject_withdrawal <withdrawal_id> [reason]` - Reject and refund
- `/stats` - Get platform statistics

---

## 🔧 Telegram Bot Setup

### Step 1: Create Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` command
3. Choose a name: `CryptoVault Admin Bot`
4. Choose a username: `cryptovault_admin_bot` (must be unique)
5. Copy the **bot token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

1. Message **@userinfobot** on Telegram
2. It will reply with your chat ID (e.g., `123456789`)
3. If you want notifications on multiple devices:
   - Get chat ID from each device
   - Separate with commas: `123456789,987654321`

### Step 3: Configure Render Environment

Go to Render Dashboard → cryptovault-backend → Environment:

```bash
# Add these variables
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_TELEGRAM_CHAT_ID=123456789,987654321
```

**Important:** After adding, click "Restart Service"

### Step 4: Verify Setup

Check Render logs for:
```
✅ Telegram bot service initialized (2 admin(s))
```

---

## 📬 Webhook Configuration

### Step 1: Update CSRF Protection (CRITICAL)

The webhook endpoints must be exempted from CSRF protection. This has been done in the code:

**File:** `/app/backend/middleware/security.py`
**Added:** `/api/wallet/webhook` to SKIP_PATHS

### Step 2: Deploy Backend Changes

```bash
# Push changes to git (if using git deployment)
git add .
git commit -m "Enhanced Telegram bot and webhook handling"
git push origin main

# Or manually trigger deploy in Render dashboard
```

### Step 3: Configure NOWPayments

1. Log in to [NOWPayments Dashboard](https://account.nowpayments.io/)
2. Go to **Settings** → **API** → **IPN Settings**
3. Set **IPN Callback URL**:
   ```
   https://cryptovault-api.onrender.com/api/wallet/webhook/nowpayments
   ```
4. Enable **Send IPN Notifications**
5. Copy your **IPN Secret** (for signature verification)
6. Save changes

### Step 4: Update Render with IPN Secret

Go to Render Dashboard → Environment:

```bash
NOWPAYMENTS_IPN_SECRET=your-ipn-secret-here
```

---

## 🧪 Testing

### Test 1: Telegram Bot

Send a test command to your bot:

```
/stats
```

You should receive platform statistics.

### Test 2: Webhook Accessibility

```bash
curl -X POST https://cryptovault-api.onrender.com/api/wallet/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "verification"}'
```

Expected response:
```json
{
  "status": "success",
  "message": "Webhook endpoint is accessible and working",
  ...
}
```

### Test 3: E2E Deposit Flow

Run the automated test:

```bash
python3 /app/test_deposit_flow_e2e.py
```

---

## 📊 Notification Examples

### Deposit Created
```
💰 NEW DEPOSIT CREATED

👤 User Info:
━━━━━━━━━━━━━━
User ID: abc-123-def
Email: user@example.com

💵 Deposit Details:
━━━━━━━━━━━━━━
Amount: $100.00 USD
Pay With: BTC
Order ID: DEP-abc123-def456
Payment ID: 5077125051

📊 Status: ⏳ Waiting for payment
Time: 2025-02-05 12:00:00 UTC

━━━━━━━━━━━━━━
Monitor: /deposit_status DEP-abc123-def456
```

### Deposit Completed
```
✅ DEPOSIT COMPLETED

👤 User Info:
━━━━━━━━━━━━━━
User ID: abc-123-def
Email: user@example.com

💵 Deposit Details:
━━━━━━━━━━━━━━
Amount Deposited: $100.00 USD
Paid With: BTC
Order ID: DEP-abc123-def456
Payment ID: 5077125051

💰 Wallet Update:
New Balance: $600.00 USD

📊 Status: ✅ Completed & Credited
Time: 2025-02-05 12:05:00 UTC

━━━━━━━━━━━━━━
Action: Funds credited to user wallet
```

### Webhook Received
```
📬 WEBHOOK RECEIVED

Order ID: DEP-abc123-def456
Payment ID: 5077125051
Status: CONFIRMING

Time: 2025-02-05 12:03:00 UTC

━━━━━━━━━━━━━━
Check logs for details: DEP-abc123-def456
```

### Withdrawal Request
```
💸 WITHDRAWAL REQUESTED

👤 User Info:
━━━━━━━━━━━━━━
User ID: abc-123-def
Email: user@example.com

💵 Withdrawal Details:
━━━━━━━━━━━━━━
Amount: 0.00100000 BTC
Destination: bc1q...abc...xyz
Withdrawal ID: WD-123456

📊 Status: ⏳ Pending Approval
Time: 2025-02-05 13:00:00 UTC

━━━━━━━━━━━━━━
⚡ Quick Actions:
/approve_withdrawal WD-123456
/reject_withdrawal WD-123456 [reason]

⚠️ Security: Verify user and address before approval
```

---

## 🎮 Admin Commands Reference

### KYC Management
```
/approve <user_id>
/reject <user_id> [reason]
/info <user_id>
```

### Deposit Management
```
/deposit_status <order_id>
```

### Withdrawal Management
```
/approve_withdrawal <withdrawal_id>
/reject_withdrawal <withdrawal_id> [reason]
```

### Platform Statistics
```
/stats
```

---

## 🔐 Security Features

### 1. Signature Verification
All webhooks are verified using HMAC-SHA512 with IPN secret.

### 2. Idempotency
Duplicate webhooks are handled gracefully - no double-crediting.

### 3. CSRF Exemption
Webhook endpoints are exempted from CSRF protection (external services).

### 4. Rate Limiting
Applies to all endpoints including webhooks to prevent abuse.

### 5. Audit Logging
All deposit/withdrawal actions are logged with admin notifications.

---

## 📝 Monitoring & Logs

### Render Logs Search Terms

**Telegram Bot:**
```
✅ Telegram bot service initialized
✅ Telegram message sent to admin
❌ Telegram send failed
```

**Deposit Flow:**
```
📬 NOWPayments webhook received
✅ Webhook signature verified
💰 Processing successful payment
✅ Wallet updated
✅ Deposit completed
```

**Notifications:**
```
Failed to send Telegram notification
```

---

## 🐛 Troubleshooting

### Issue 1: Telegram Bot Not Sending

**Symptoms:**
- No Telegram messages received
- Logs show "Telegram bot not configured"

**Fix:**
1. Verify TELEGRAM_BOT_TOKEN is set in Render
2. Verify ADMIN_TELEGRAM_CHAT_ID is set
3. Restart backend service
4. Check logs for initialization message

### Issue 2: Webhook Returns 403

**Symptoms:**
- Webhook test returns "CSRF_TOKEN_MISSING"

**Fix:**
1. Ensure `/api/wallet/webhook` is in CSRF SKIP_PATHS
2. Deploy latest backend code to Render
3. Restart service
4. Test again

### Issue 3: Notifications Not Received

**Symptoms:**
- Deposits work but no Telegram messages

**Fix:**
1. Check Render logs for "Failed to send Telegram notification"
2. Verify bot token is correct
3. Verify chat ID is correct
4. Test bot by sending `/stats` command
5. Check if bot is blocked in Telegram

### Issue 4: Webhook Not Processing

**Symptoms:**
- Payments complete but wallet not credited

**Fix:**
1. Check NOWPayments IPN URL is correct
2. Verify IPN Secret matches in Render
3. Check Render logs for webhook receipt
4. Test webhook endpoint accessibility
5. Verify signature verification is working

---

## ✅ Production Checklist

Before going live:

- [ ] Telegram bot created and token obtained
- [ ] Admin chat ID(s) obtained
- [ ] TELEGRAM_BOT_TOKEN set in Render
- [ ] ADMIN_TELEGRAM_CHAT_ID set in Render
- [ ] Backend deployed with latest code
- [ ] CSRF skip paths include webhooks
- [ ] NOWPayments IPN URL configured
- [ ] NOWPAYMENTS_IPN_SECRET set in Render
- [ ] Webhook test endpoint returns 200 OK
- [ ] Test command sent to Telegram bot (e.g., `/stats`)
- [ ] Test deposit created (small amount)
- [ ] Telegram notification received for deposit creation
- [ ] Payment completed
- [ ] Telegram notification received for completion
- [ ] Wallet credited correctly
- [ ] All logs verified

---

## 📈 Expected Flow

### Complete Deposit Flow with Notifications

1. **User Creates Deposit**
   - Frontend → Backend API
   - Backend creates NOWPayments payment
   - 📬 Telegram: "NEW DEPOSIT CREATED"
   - Returns payment address

2. **User Sends Crypto**
   - User sends to payment address
   - NOWPayments detects payment

3. **Webhook Received (Status: confirming)**
   - NOWPayments → Backend webhook
   - 📬 Telegram: "WEBHOOK RECEIVED (CONFIRMING)"
   - Database updated

4. **Payment Confirmed**
   - NOWPayments confirms sufficient confirmations
   - Webhook sent with status: finished

5. **Webhook Processed (Status: finished)**
   - Backend verifies signature
   - 📬 Telegram: "WEBHOOK RECEIVED (FINISHED)"
   - Wallet credited
   - Transaction created
   - ✅ Telegram: "DEPOSIT COMPLETED"
   - Admin sees new balance

6. **User Sees Balance**
   - Frontend updates
   - User sees credited funds

---

## 🎯 Performance Notes

- Telegram bot uses async operations (non-blocking)
- Notifications sent in background
- Failed notifications don't block webhook processing
- Logs all notification attempts for debugging

---

## 📞 Support

### Telegram Bot Issues
- Check Telegram @BotFather for bot status
- Verify bot is not blocked
- Test bot by sending commands directly

### Webhook Issues
- Check NOWPayments dashboard for webhook delivery history
- Verify signature verification in logs
- Test webhook endpoint accessibility
- Check CORS and CSRF configuration

### Deployment Issues
- Check Render deployment logs
- Verify all environment variables are set
- Restart service after changes
- Check service health endpoints

---

**Last Updated:** 2025-02-05  
**Status:** ✅ Production Ready  
**Version:** 2.0 Enhanced

---

## 🎉 What's New

**v2.0 Enhancements:**
- ✅ Deposit lifecycle notifications (create → complete → fail)
- ✅ Withdrawal request notifications with admin commands
- ✅ Webhook status updates in real-time
- ✅ Platform statistics command
- ✅ Enhanced error handling and logging
- ✅ Idempotency protection for webhooks
- ✅ CSRF exemption for webhook endpoints
- ✅ Multiple admin support (comma-separated chat IDs)
- ✅ Emoji-based log levels for easy monitoring
- ✅ Complete audit trail

**Ready to deploy!** 🚀
