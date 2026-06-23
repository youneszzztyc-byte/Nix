# Railway Configuration for Fragment Monitor Bot

## Configuration Files Added:
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version
- `fragment_monitor.py` - Updated to use environment variables

## Setup Instructions for Railway:

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Connect to Railway
- Go to https://railway.app
- Click "New Project" → "Deploy from GitHub"
- Select your repository: `youneszzztyc-byte/Nix`

### 3. Set Environment Variables
In Railway Dashboard, go to **Variables** and add:

```
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_admin_id_here
CHECK_EVERY=5
```

**How to get these:**
- **BOT_TOKEN**: Message @BotFather on Telegram, create a bot, copy the token
- **ADMIN_ID**: Message @userinfobot on Telegram to get your user ID

### 4. Configure Start Command
- In Railway, go to **Settings**
- Set the **Start Command** to:
```
python fragment_monitor.py
```

### 5. Deploy
- Click "Deploy" button
- Check logs to verify it's working

## Troubleshooting

**❌ "No module named 'httpx'"**
→ Railway didn't install requirements. Rebuild and redeploy.

**❌ "BOT_TOKEN not set"**
→ Add `BOT_TOKEN` to Environment Variables in Railway

**❌ "Connection refused"**
→ Check if Telegram API is accessible (it should be)

**✅ Success signs:**
- See "✅ تم الاتصال بـ Telegram بنجاح" in logs
- Get startup message in Telegram
- Notifications appear when new gifts are listed
