# Fragment Gifts Auction Monitor Bot

A Telegram bot that monitors Fragment.com gift auctions and sends instant notifications when new gifts appear.

## Features

- 🎁 Real-time monitoring of Fragment gift auctions
- 📱 Instant Telegram notifications
- 🔄 Configurable check interval
- 🌐 Deployed on Railway
- 🛡️ HTML escape protection for security

## Environment Variables

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_telegram_id
CHECK_EVERY=5  # seconds between checks (optional, default: 5)
```

## Getting Credentials

### BOT_TOKEN
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot
3. Copy the API token

### ADMIN_ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID

## Deployment

See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for step-by-step deployment instructions on Railway.

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN="your_token"
export ADMIN_ID=123456789

# Run
python fragment_monitor.py
```

## How It Works

1. Fetches latest auctions from Fragment.com
2. Parses HTML and/or embedded JSON
3. Tracks seen gifts to avoid duplicates
4. Sends Telegram notification for new gifts
5. Repeats every 5 seconds (configurable)

## Monitoring

Check Railway logs to verify:
- ✅ Telegram connection successful
- ✅ Startup notification received
- ✅ New gift notifications working

## Troubleshooting

- **No notifications?** → Check BOT_TOKEN and ADMIN_ID are set correctly
- **Connection errors?** → Verify Telegram API is accessible
- **Missing dependencies?** → Rebuild the Railway project

## License

Open source. Use at your own risk.
