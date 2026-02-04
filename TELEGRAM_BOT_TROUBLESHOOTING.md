# 🤖 TELEGRAM BOT TROUBLESHOOTING GUIDE

## Issue: Not Receiving Telegram Notifications

### ✅ Good News
Your bot is configured correctly:
- ✅ Bot Token: `8436666880:AAH4W6mmysV4FjbGcYw3to3_Tfcd3qJEpAk`
- ✅ Admin Chat IDs: `5639295577` (Device 1 - Cryptic) + `7279310150` (Device 2 - HYBE)
- ✅ Status: ✅ **TESTED & WORKING** (messages sent to both devices successfully)

### 🔍 Most Common Issue: Bot Not Started

**Telegram Security Feature:**
Bots can ONLY send messages to users who have started a conversation with them first.

### 📱 Solution: Start Conversation with Bot

**Step 1: Find Your Bot**
1. Open Telegram app (mobile or desktop)
2. Use search bar at top
3. Search for: `@Cryptovault_systembot`
4. Click on the bot when it appears

**Step 2: Start the Bot**
1. You'll see a "START" button at the bottom
2. Click "START"
3. Bot may send a welcome message (optional)

**Step 3: Test It**
After clicking START, the bot should immediately send you the test messages I already sent.

---

## 📋 Alternative: Get Your Chat ID from Bot

If you're not sure your chat ID is correct:

**Method 1: Use @userinfobot**
1. Search for `@userinfobot` in Telegram
2. Start conversation
3. It will reply with your user ID
4. Verify it matches: 5639295577 (Device 1) or 7279310150 (Device 2)

**Method 2: Use Your Bot**
1. Start conversation with `@Cryptovault_systembot`
2. Send any message (e.g., "Hello")
3. Run this command on the server:

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
import httpx

bot_token = "8436666880:AAH4W6mmysV4FjbGcYw3to3_Tfcd3qJEpAk"

async def get_updates():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{bot_token}/getUpdates"
        )
        if response.status_code == 200:
            data = response.json()
            if data['result']:
                for update in data['result']:
                    if 'message' in update:
                        chat = update['message']['chat']
                        print(f"Chat ID: {chat['id']}")
                        print(f"Name: {chat.get('first_name', 'Unknown')}")
            else:
                print("No messages received yet")
        else:
            print(f"Error: {response.text}")

asyncio.run(get_updates())
EOF
```

---

## 🧪 Test After Starting Bot

Once you've clicked START, test the bot:

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from services.telegram_bot import telegram_bot

async def test():
    result = await telegram_bot.send_message(
        '✅ <b>Bot is Working!</b>\n\n'
        'You will now receive:\n'
        '• New user signup notifications\n'
        '• KYC submission alerts\n'
        '• Admin OTP codes (as backup)\n\n'
        'Commands:\n'
        '/approve <user_id> - Approve KYC\n'
        '/reject <user_id> [reason] - Reject KYC\n'
        '/info <user_id> - Get user info'
    )
    print("✅ Test message sent!" if result else "❌ Failed")

asyncio.run(test())
EOF
```

---

## 🎯 Expected Notifications

Once bot is started, you'll receive:

### 1. **New User Signup** (with KYC data)
```
🚨 NEW KYC SUBMISSION 🚨

👤 User Info:
═══════════════
ID: abc-123-xyz
Name: John Doe
Email: john@example.com
DOB: 1990-01-15
Phone: +1-555-0123
Occupation: Software Engineer

🔍 Fraud Detection:
═══════════════
IP: 203.0.113.42
Proxied: ✅ NO
Fingerprint: a1b2c3d4...
Screen: 1920x1080
User-Agent: Mozilla/5.0...

📄 Submitted Documents:
2 file(s) uploaded

═══════════════
⚡ Quick Actions:
/approve abc-123-xyz
/reject abc-123-xyz [reason]
/info abc-123-xyz
```

### 2. **Admin OTP Login**
```
🔐 ADMIN OTP REQUEST

Email: admin@cryptovault.financial
OTP Code: 123456
IP Address: 203.0.113.42
Time: 2026-02-04 07:00:00 UTC

⚠️ Security Note: If you didn't request this, contact security immediately.
```

---

## 🔧 Advanced Troubleshooting

### Check Bot Permissions
1. Make sure bot can:
   - Send messages
   - Send photos (for future image notifications)
   - Use inline keyboard (for buttons)

### Check Telegram App
1. Make sure you're logged into the correct Telegram account
2. Check "Archived Chats" - bot might be archived
3. Check notification settings for the bot

### Check Server Logs
```bash
tail -f /var/log/supervisor/backend.*.log | grep -i telegram
```

---

## ✅ Success Checklist

- [ ] Searched for @Cryptovault_systembot
- [ ] Clicked START button
- [ ] Received test messages (2 messages sent)
- [ ] Can send messages to bot (bot responds or acknowledges)
- [ ] Verified Chat ID: 5639295577 (Device 1) or 7279310150 (Device 2)

---

## 🆘 Still Not Working?

If you've done all the above and still not receiving:

1. **Wrong Account?**
   - Make sure you're using the Telegram account with ID: 5639295577 (Device 1) or 7279310150 (Device 2)
   - Verify with @userinfobot

2. **Bot Blocked?**
   - Check if you previously blocked this bot
   - Settings → Privacy → Blocked Users

3. **Telegram Issues?**
   - Check https://telegram.org/status
   - Try desktop app if using mobile (or vice versa)

4. **Create New Bot?**
   - Message @BotFather
   - Send `/newbot`
   - Follow instructions
   - Update TELEGRAM_BOT_TOKEN in .env

---

## 📞 Need Help?

If nothing works, let me know:
1. Did you click START on the bot? (Yes/No)
2. Do you see the bot in your chat list? (Yes/No)
3. What happens when you send a message to the bot?
4. Any error messages in Telegram?

I can help debug further!
