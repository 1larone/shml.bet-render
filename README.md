# CS2 Tournament Betting Bot

A Telegram bot for betting on CS2 tournament matches between Sovkamax and Faze teams.

## Features

- **Multi-currency support**: USD, EUR, UAH, BTC, ETH
- **Team betting**: Sovkamax (1.82 coefficient) vs Faze (2.22 coefficient)
- **One bet per match**: Users can only place one bet per match
- **Admin controls**: Match management and winner announcement
- **Real-time payouts**: Automatic win calculation and notifications

## Setup

1. Install required dependencies:
```bash
pip install aiogram
```

2. Configure your bot token:
   - Set the `TELEGRAM_BOT_TOKEN` environment variable with your bot token
   - Or replace the token directly in `bot.py` (line 10)

3. Configure admin users:
   - Replace the admin user ID in the `ADMINS` list (line 26) with your Telegram user ID

4. Run the bot:
```bash
python bot.py
```

## Bot Commands

### User Commands
- `/start` - Begin interaction and show betting interface
- `/help` - Show available commands
- `/mybet` - Display your current bet for the match

### Admin Commands
- `/win <team>` - Announce match winner (Sovkamax or Faze)
- `/resetbets` - Clear all current bets
- `/newmatch` - Start a new match (clears all bets)

## Usage

1. Users start by typing `/start`
2. Click "СДЕЛАТЬ СТАВКУ ✅" to begin betting
3. Select currency (USD, EUR, UAH, BTC, ETH)
4. Choose team (Sovkamax with 1.82 coefficient or Faze with 2.22 coefficient)
5. Enter or select bet amount
6. Receive confirmation with potential winnings
7. Admins announce winners using `/win <team>` command
8. Users automatically receive payout notifications

## Bot Information

- **Bot Username**: @shmlbet_bot
- **Bot ID**: 8337218457
- **Display Name**: shml.bet

## Current Status

The bot is currently **RUNNING** and polling for messages from Telegram.
