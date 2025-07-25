import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.filters import Command
from aiogram import F
import asyncio
from datetime import datetime

# Get API token from environment variable with fallback
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8337218457:AAGo9Jxfa3X1IYUtY3x80PtDoVBaAk9Ycwo')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Available currencies for betting
FAKE_CURRENCIES = ['💵 USD', '💶 EUR', '💸 UAH', '🪙 BTC', '🟣 ETH']

# Current exchange rates to UAH (updated July 24, 2025)
EXCHANGE_RATES = {
    'USD': 41.18,
    'EUR': 47.87,
    'UAH': 1.0,
    'BTC': 4526731.0,
    'ETH': 152462.0
}

# Initialize dynamic settings on startup (after import)
def get_current_coefficients():
    """Get current coefficients from settings"""
    return bot_settings.get_coefficients()

def get_current_exchange_rates():
    """Get current exchange rates from settings"""  
    return bot_settings.get_exchange_rates()

# Betting coefficients for teams (will be loaded after imports)
COEFFICIENTS = {}
EXCHANGE_RATES = {}

# Admin user IDs - replace with actual admin user IDs
ADMINS = [5118163519]  # Replace with actual Telegram user_id

# Import shared data management
import data_sync
import bot_settings

# Use shared data structures
user_state = data_sync.user_state
user_bets = data_sync.user_bets
user_balances = data_sync.user_balances

def get_main_menu():
    """Create main menu with balance and bet info (betting only through WebApp)"""
    buttons = [
        [InlineKeyboardButton(text="💰 БАЛАНС", callback_data="show_balance")],
        [InlineKeyboardButton(text="📊 МОЯ СТАВКА", callback_data="my_bet")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    return markup

def convert_to_uah(amount, currency):
    """Convert amount from given currency to UAH"""
    return data_sync.convert_to_uah(amount, currency)

def get_currency_code(currency_with_emoji):
    """Extract currency code from emoji string"""
    return currency_with_emoji.split(' ')[-1]

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Handle /start command - welcome message with balance and betting info"""
    await message.answer(
        "👋 Привет! Это Telegram-бот для ставок на турнир по CS2🔫\n\n"
        "🎯 *Делайте ставки через кнопку СТАВКИ рядом с полем ввода*\n\n"
        "💰 Доступные валюты: USD, EUR, UAH, BTC, ETH\n"
        "🏆 Коэффициенты: Sovkamax (1.82) | Faze (2.22)\n\n"
        "Используйте меню ниже для управления балансом:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def show_help(message: types.Message):
    """Handle /help command - show available commands"""
    user_id = message.from_user.id
    help_text = (
        "📋 Доступные команды:\n"
        "/start — начать работу с ботом\n"
        "/help — список команд\n"
        "/mybet — показать вашу ставку\n"
        "/balance — показать баланс\n"
    )
    
    # Add admin commands if user is admin
    if user_id in ADMINS:
        help_text += (
            "\n🔒 Админ-команды:\n"
            "/win <команда> — объявить победителя (Sovkamax или Faze)\n"
            "/resetbets — сбросить все ставки\n"
            "/newmatch — начать новый матч\n"
        )
    await message.answer(help_text)

@dp.message(Command("mybet"))
async def show_my_bet(message: types.Message):
    """Handle /mybet command - show user's current bet"""
    user_id = message.from_user.id
    
    # Reload data to get latest state from file
    data_sync.reload_data()
    
    if user_id not in data_sync.user_state or "bet" not in data_sync.user_state[user_id]:
        await message.answer("Вы ещё не сделали ставку на этот матч.")
        return
    
    state = data_sync.user_state[user_id]
    team_name = 'Sovkamax' if state['team'] == 'Sovkamax' else 'Faze'
    team_display = '*🧑‍💼 Sovkamax*' if state['team'] == 'Sovkamax' else '*Faze 🦅*'
    win_sum = state['bet'] * state['coef']
    
    await message.answer(
        f"🎯 *Ваша текущая ставка:*\n\n"
        f"💰 Сумма: {state['bet']} {state['currency']}\n"
        f"🏆 Команда: {team_display}\n"
        f"📈 Коэффициент: {state['coef']}\n"
        f"🎉 Потенциальный выигрыш: {win_sum:.2f} {state['currency']}",
        parse_mode="Markdown"
    )

@dp.message(Command("balance"))
async def show_balance_command(message: types.Message):
    """Handle /balance command - show user's balance"""
    user_id = message.from_user.id
    # Reload data to get latest balance from file
    data_sync.reload_data()
    balance = data_sync.user_balances.get(user_id, 0.0)
    await message.answer(f"💰 Ваш баланс: {balance:.2f} UAH")

@dp.message(Command("resetbets"))
async def reset_bets(message: types.Message):
    """Admin command - reset all bets"""
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    data_sync.clear_all_bets()
    await message.answer("Все ставки сброшены. Можно начинать новый матч!")

@dp.message(Command("newmatch"))
async def new_match(message: types.Message):
    """Admin command - start new match"""
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    data_sync.clear_all_bets()
    await message.answer("Новый матч! Ставки открыты. Нажмите /start для участия.")

@dp.callback_query(F.data == "show_balance")
async def show_balance_callback(callback: types.CallbackQuery):
    """Handle balance button click - show user's balance with deposit option"""
    user_id = callback.from_user.id
    # Reload data to get latest balance from file
    data_sync.reload_data()
    balance = data_sync.user_balances.get(user_id, 0.0)
    
    # Create inline keyboard with deposit option
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="deposit_balance")]]
    )
    
    await callback.message.answer(
        f"💰 *Ваш баланс:* {balance:.2f} UAH\n\n"
        f"📊 *Курсы валют:*\n"
        f"💵 1 USD = {EXCHANGE_RATES['USD']:.2f} UAH\n"
        f"💶 1 EUR = {EXCHANGE_RATES['EUR']:.2f} UAH\n"
        f"🪙 1 BTC = {EXCHANGE_RATES['BTC']:,.0f} UAH\n"
        f"🟣 1 ETH = {get_current_exchange_rates()['ETH']:,.0f} UAH\n\n"
        f"💡 *Все депозиты автоматически конвертируются в UAH*",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "deposit_balance")
async def deposit_balance_callback(callback: types.CallbackQuery):
    """Handle deposit button click - show currency selection"""
    user_id = callback.from_user.id
    
    # Store that user wants to deposit
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["action"] = "deposit"
    
    # Create currency selection keyboard
    buttons = [KeyboardButton(text=currency) for currency in FAKE_CURRENCIES]
    markup = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)
    
    await callback.message.answer(
        "💰 *Пополнение баланса*\n\n"
        "Выберите валюту для пополнения:\n\n"
        f"💵 1 USD = {get_current_exchange_rates()['USD']:.2f} UAH\n"
        f"💶 1 EUR = {get_current_exchange_rates()['EUR']:.2f} UAH\n"
        f"🪙 1 BTC = {get_current_exchange_rates()['BTC']:,.0f} UAH\n"
        f"🟣 1 ETH = {get_current_exchange_rates()['ETH']:,.0f} UAH\n\n"
        f"💡 *Все депозиты конвертируются в UAH по текущему курсу*",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "my_bet")
async def show_my_bet(callback: types.CallbackQuery):
    """Show user's current bet information"""
    user_id = str(callback.from_user.id)
    
    # Reload data to get latest state
    data_sync.reload_data()
    
    if user_id not in data_sync.user_state or user_id not in data_sync.user_bets:
        await callback.message.answer(
            "📊 *Информация о ставке*\n\n"
            "❌ У вас нет активной ставки на текущий матч\n\n"
            "🎯 Чтобы сделать ставку, нажмите кнопку *СТАВКИ* рядом с полем ввода",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    bet_info = data_sync.user_state[user_id]
    team = bet_info.get("team", "Unknown")
    currency = bet_info.get("currency", "UAH")
    bet_amount = bet_info.get("bet", 0)
    coef = bet_info.get("coef", 1.0)
    bet_uah = bet_info.get("bet_uah", bet_amount)
    
    potential_win = bet_amount * coef
    potential_win_uah = bet_uah * coef
    
    team_emoji = "🧑‍💼" if team == "Sovkamax" else "🦅"
    
    await callback.message.answer(
        f"📊 *Ваша ставка*\n\n"
        f"{team_emoji} *Команда:* {team}\n"
        f"💰 *Сумма:* {bet_amount} {get_currency_code(currency)}\n"
        f"💱 *В гривнах:* {bet_uah:.2f} UAH\n"
        f"📈 *Коэффициент:* {coef}\n"
        f"🏆 *Потенциальный выигрыш:* {potential_win:.2f} {get_currency_code(currency)} ({potential_win_uah:.2f} UAH)\n\n"
        f"⏳ Ожидаем результатов матча...",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Help command - show available commands"""
    await message.answer(
        "📋 *Доступные команды:*\n\n"
        "🎯 `/start` - Главное меню\n"
        "💰 `/balance` - Показать баланс (или кнопка БАЛАНС)\n"
        "📊 `/mybet` - Моя ставка (или кнопка МОЯ СТАВКА)\n"
        "❓ `/help` - Эта справка\n\n"
        "🎯 *Чтобы сделать ставку:*\n"
        "Нажмите кнопку *СТАВКИ* рядом с полем ввода\n\n"
        "💡 *Поддерживаемые валюты:*\n"
        "💵 USD | 💶 EUR | 💸 UAH | 🪙 BTC | 🟣 ETH",
        parse_mode="Markdown"
    )

@dp.message(Command("balance"))
async def balance_command(message: types.Message):
    """Balance command - show user balance"""
    user_id = str(message.from_user.id)
    data_sync.reload_data()
    balance = data_sync.user_balances.get(user_id, 0.0)
    rates = get_current_exchange_rates()
    
    await message.answer(
        f"💰 *Ваш баланс: {balance:.2f} UAH*\n\n"
        f"📊 *Курсы валют:*\n"
        f"💵 1 USD = {rates['USD']:.2f} UAH\n"
        f"💶 1 EUR = {rates['EUR']:.2f} UAH\n"
        f"🪙 1 BTC = {rates['BTC']:,.0f} UAH\n"
        f"🟣 1 ETH = {rates['ETH']:,.0f} UAH\n\n"
        f"💡 *Для пополнения используйте кнопку БАЛАНС*",
        parse_mode="Markdown"
    )

@dp.message(Command("mybet"))
async def mybet_command(message: types.Message):
    """My bet command - show user's bet"""
    user_id = str(message.from_user.id)
    data_sync.reload_data()
    
    if user_id not in data_sync.user_state or user_id not in data_sync.user_bets:
        await message.answer(
            "📊 *Информация о ставке*\n\n"
            "❌ У вас нет активной ставки на текущий матч\n\n"
            "🎯 Чтобы сделать ставку, нажмите кнопку *СТАВКИ* рядом с полем ввода",
            parse_mode="Markdown"
        )
        return
    
    bet_info = data_sync.user_state[user_id]
    team = bet_info.get("team", "Unknown")
    currency = bet_info.get("currency", "UAH")
    bet_amount = bet_info.get("bet", 0)
    coef = bet_info.get("coef", 1.0)
    bet_uah = bet_info.get("bet_uah", bet_amount)
    
    potential_win = bet_amount * coef
    potential_win_uah = bet_uah * coef
    
    team_emoji = "🧑‍💼" if team == "Sovkamax" else "🦅"
    
    await message.answer(
        f"📊 *Ваша ставка*\n\n"
        f"{team_emoji} *Команда:* {team}\n"
        f"💰 *Сумма:* {bet_amount} {get_currency_code(currency)}\n"
        f"💱 *В гривнах:* {bet_uah:.2f} UAH\n"
        f"📈 *Коэффициент:* {coef}\n"
        f"🏆 *Потенциальный выигрыш:* {potential_win:.2f} {get_currency_code(currency)} ({potential_win_uah:.2f} UAH)\n\n"
        f"⏳ Ожидаем результатов матча...",
        parse_mode="Markdown"
    )

@dp.message(F.text.in_(FAKE_CURRENCIES))
async def currency_chosen(message: types.Message):
    """Handle currency selection for deposit only"""
    user_id = message.from_user.id
    currency = message.text
    
    # Check if user is in deposit mode
    if user_id in user_state and user_state[user_id].get("action") == "deposit":
        # User is depositing - show amount selection
        user_state[user_id]["deposit_currency"] = currency
        
        # Create amount selection based on currency
        if currency in ['💵 USD', '💶 EUR']:
            amounts = ['10', '50', '100', '500', '1000']
        elif currency == '💸 UAH':
            amounts = ['500', '1000', '5000', '10000', '25000']
        elif currency in ['🪙 BTC', '🟣 ETH']:
            amounts = ['0.001', '0.01', '0.1', '0.5', '1.0']
        else:
            amounts = ['10', '50', '100', '500', '1000']
        
        currency_code = get_currency_code(currency)
        buttons = [KeyboardButton(text=f"{amount} {currency_code} 💰") for amount in amounts]
        markup = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)
        
        rate = EXCHANGE_RATES[currency_code]
        await message.answer(
            f"💰 *Пополнение в {currency}*\n\n"
            f"📊 Курс: 1 {currency_code} = {rate:.2f} UAH\n\n"
            f"Выберите сумму или введите свою:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return
    
    # For betting, direct user to WebApp
    await message.answer(
        "🎯 *Для размещения ставок используйте мини-приложение*\n\n"
        "Нажмите кнопку *СТАВКИ* рядом с полем ввода сообщения",
        parse_mode="Markdown"
    )



@dp.message(~F.text.startswith('/'))
async def process_deposit_amount_only(message: types.Message):
    """Handle deposit amount input only (betting moved to WebApp)"""
    user_id = message.from_user.id
    
    # Check if user is depositing
    if user_id in user_state and user_state[user_id].get("action") == "deposit":
        await process_deposit_amount(message)
        return
    
    # For any other message, guide user to WebApp for betting
    await message.answer(
        "🎯 *Для размещения ставок используйте мини-приложение*\n\n"
        "Нажмите кнопку *СТАВКИ* рядом с полем ввода сообщения",
        parse_mode="Markdown"
    )

async def process_deposit_amount(message: types.Message):
    """Process deposit amount from user"""
    user_id = message.from_user.id
    
    # Check if user has selected currency
    if user_id not in user_state or "deposit_currency" not in user_state[user_id]:
        await message.answer("❌ Сначала выберите валюту для пополнения через /start → БАЛАНС → Пополнить баланс")
        return
    
    currency = user_state[user_id]["deposit_currency"]
    
    # Parse deposit amount from message
    deposit_text = message.text.replace("💰", "").replace(" ", "").strip()
    # Remove currency symbols
    for curr in ['UAH', 'USD', 'EUR', 'BTC', 'ETH', '💵', '💶', '💸', '🪙', '🟣']:
        deposit_text = deposit_text.replace(curr, "")
    
    try:
        amount = float(deposit_text)
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите число больше 0")
        return
    
    # Validate amount
    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0")
        return
    
    # Convert to UAH
    amount_uah = convert_to_uah(amount, currency)
    
    # Check max deposit in UAH
    if amount_uah > 50000:
        max_in_currency = 50000 / get_current_exchange_rates()[get_currency_code(currency)]
        await message.answer(f"❌ Максимальная сумма пополнения: {max_in_currency:.2f} {get_currency_code(currency)} (50,000 UAH)")
        return
    
    # Reload data to get latest balance
    data_sync.reload_data()
    
    print(f"BOT DEPOSIT DEBUG: user_id={user_id}, amount={amount} {get_currency_code(currency)}, amount_uah={amount_uah}")
    
    # Get current balance BEFORE any operations
    current_balance = data_sync.user_balances.get(user_id, 0.0)
    print(f"BOT DEPOSIT DEBUG: current_balance before operations = {current_balance}")
    
    # Add deposit amount in UAH to existing balance (correct logic)
    new_balance = current_balance + amount_uah
    
    # Check balance limit after adding deposit
    if new_balance > 500000:
        await message.answer(
            f"❌ *Превышен лимит баланса!*\n\n"
            f"💰 Текущий баланс: {current_balance:.2f} UAH\n"
            f"💱 Попытка добавить: {amount:.2f} {get_currency_code(currency)} ({amount_uah:.2f} UAH)\n"
            f"💳 Итоговый баланс: {new_balance:.2f} UAH\n"
            f"🚫 Максимальный баланс: 500,000 UAH\n\n"
            f"Максимальное пополнение: {500000 - current_balance:.2f} UAH",
            parse_mode="Markdown"
        )
        return
    
    # Set new balance (add UAH equivalent to existing)
    data_sync.user_balances[user_id] = new_balance
    print(f"BOT DEPOSIT DEBUG: added {amount_uah} UAH to {current_balance}, new balance = {new_balance}")
    
    # Clear any old match data for fresh start
    data_sync.reset_user_after_match(user_id)
    data_sync.save_data()
    
    # Clear deposit state
    if user_id in user_state and "action" in user_state[user_id]:
        del user_state[user_id]["action"]
        if "deposit_currency" in user_state[user_id]:
            del user_state[user_id]["deposit_currency"]
    
    currency_code = get_currency_code(currency)
    await message.answer(
        f"✅ *Баланс пополнен!*\n\n"
        f"💰 Пополнено: {amount:.2f} {currency_code} = {amount_uah:.2f} UAH\n"
        f"📊 Курс: 1 {currency_code} = {get_current_exchange_rates()[currency_code]:.2f} UAH\n"
        f"💳 Новый баланс: {new_balance:.2f} UAH",
        parse_mode="Markdown"
    )

@dp.message(Command("win"))
async def announce_winner(message: types.Message):
    """Admin command - announce match winner and distribute payouts"""
    user_id = message.from_user.id
    
    # Check admin permissions
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    # Parse winner from command arguments
    args = message.text.split()
    current_coefficients = get_current_coefficients()
    if len(args) < 2 or args[1] not in current_coefficients:
        team1, team2 = bot_settings.get_team_names()
        await message.answer(f"Укажите команду-победителя: /win {team1} или /win {team2}")
        return
    
    winner = args[1]
    
    # Log admin action
    logging.info(f"Admin {user_id} announcing winner: {winner}")
    
    # Load data FIRST to get latest state including web app bets
    data_sync.reload_data()
    
    # Debug: Show current data state BEFORE processing
    logging.info(f"Processing results - Current state: {len(data_sync.user_state)} users, {len(data_sync.user_bets)} bets")
    logging.info(f"User states: {list(data_sync.user_state.keys())}")
    logging.info(f"User bets: {list(data_sync.user_bets)}")
    
    # Store results for web app AFTER loading data but BEFORE processing
    data_sync.set_match_result(winner)
    
    # Process all user bets from data_sync (includes both bot and web app bets)
    for bet_user_id, state in data_sync.user_state.items():
        team = state["team"]
        currency = state["currency"]
        coef = state["coef"]
        bet = state.get("bet", None)
        
        # Skip if user didn't complete their bet
        if bet is None:
            continue
        
        try:
            bet_uah = state.get("bet_uah", convert_to_uah(bet, currency))
            
            if team == winner:
                # User won - calculate winnings (only profit, not bet amount)
                win_sum = bet * coef  # total payout
                win_uah = convert_to_uah(win_sum, currency)  # total payout in UAH
                profit_uah = win_uah - bet_uah  # profit only (without bet amount)
                
                # Add full winnings to balance (bet was already deducted when betting)
                if bet_user_id not in data_sync.user_balances:
                    data_sync.user_balances[bet_user_id] = 0.0
                data_sync.user_balances[bet_user_id] += win_uah
                
                # Store result for web app
                data_sync.set_user_result(bet_user_id, {
                    'result': 'win',
                    'balance': data_sync.user_balances[bet_user_id],
                    'winnings': profit_uah,  # Use profit_uah instead of full win_uah
                    'winning_team': winner,
                    'user_team': team
                })
                
                currency_code = get_currency_code(currency)
                rate = get_current_exchange_rates()[currency_code]
                
                try:
                    await bot.send_message(
                        bet_user_id,
                        f"🎉 *Поздравляем! Ваша ставка сыграла!*\n\n"
                        f"🏆 Общий выигрыш: {win_sum:.2f} {currency}\n"
                        f"💰 Выплата: +{win_uah:.2f} UAH\n"
                        f"💸 Ваш баланс: {data_sync.user_balances[bet_user_id]:.2f} UAH",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.warning(f"Could not send win message to {bet_user_id}: {e}")
            else:
                # User lost - balance already deducted when bet was placed
                # Do NOT deduct again - just store result and send notification
                
                # Store result for web app (balance already correct)
                data_sync.set_user_result(bet_user_id, {
                    'result': 'lose',
                    'balance': data_sync.user_balances[bet_user_id],
                    'lost': bet_uah,
                    'winning_team': winner,
                    'user_team': team
                })
                
                try:
                    await bot.send_message(
                        bet_user_id,
                        f"😔 *К сожалению, ваша ставка не сыграла.*\n\n"
                        f"💸 Проигрышная ставка: {bet:.2f} {currency}\n"
                        f"📉 Списано с баланса: -{bet_uah:.2f} UAH\n"
                        f"💰 Ваш баланс: {data_sync.user_balances[bet_user_id]:.2f} UAH\n\n"
                        f"🍀 *Удачи в следующий раз!*",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.warning(f"Could not send lose message to {bet_user_id}: {e}")
        except Exception as e:
            logging.error(f"Failed to send message to user {bet_user_id}: {e}")
    
    # Save all balance changes to file for web app sync
    data_sync.save_data()
    
    # Don't clear bets immediately - let web app process results first
    await message.answer(f"🏆 Результаты объявлены для победителя: {winner}!\n\n🔄 Ставки будут сброшены при начале нового матча. Используйте /resetbets для принудительного сброса.")

@dp.message(Command("resetbets"))
async def reset_bets(message: types.Message):
    """Admin command - clear all bets for new match"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    data_sync.clear_all_bets()
    await message.answer("🔄 Все ставки сброшены. Можно начинать новый матч.")

# === АДМИНСКИЕ КОМАНДЫ ДЛЯ НАСТРОЕК ===

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """Админ-панель - показать все доступные команды"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    settings = bot_settings.load_settings()
    team1, team2 = bot_settings.get_team_names()
    coeffs = bot_settings.get_coefficients()
    
    await message.answer(
        f"🔧 *АДМИН-ПАНЕЛЬ*\n\n"
        f"*Текущие настройки:*\n"
        f"🏆 Команды: {team1} vs {team2}\n"
        f"📊 Коэффициенты: {coeffs[team1]} | {coeffs[team2]}\n"
        f"💰 Макс. ставка: {settings['max_bet_uah']:,} UAH\n"
        f"💳 Макс. баланс: {settings['max_balance_uah']:,} UAH\n\n"
        f"*Команды для изменений:*\n"
        f"`/setteams Название1 Название2` - изменить названия команд\n"
        f"`/setcoef 1.85 2.15` - изменить коэффициенты\n"
        f"`/setlimits 50000 1000000` - лимиты (ставка, баланс)\n"
        f"`/setrate USD 42.5` - изменить курс валюты\n"
        f"`/settings` - показать все настройки\n"
        f"`/win Команда` - объявить победителя\n"
        f"`/resetbets` - сбросить все ставки\n\n"
        f"💡 *Примеры:*\n"
        f"`/setteams NAVI Astralis`\n"
        f"`/setcoef 1.75 2.35`\n"
        f"`/setrate BTC 4600000`",
        parse_mode="Markdown"
    )

@dp.message(Command("setteams"))
async def set_teams(message: types.Message):
    """Изменить названия команд: /setteams Team1 Team2"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    args = message.text.split()[1:]  # Убираем /setteams
    if len(args) < 2:
        await message.answer("❌ Формат: `/setteams Команда1 Команда2`\nПример: `/setteams NAVI Astralis`", parse_mode="Markdown")
        return
    
    team1 = args[0]
    team2 = args[1]
    
    # Обновляем настройки
    success1 = bot_settings.set_setting('teams', 'team1', team1)
    success2 = bot_settings.set_setting('teams', 'team2', team2)
    print(f"DEBUG setteams: set team1={team1} success={success1}, set team2={team2} success={success2}")
    
    # Обновляем глобальные переменные
    global COEFFICIENTS
    COEFFICIENTS = get_current_coefficients()
    
    # Обновляем data_sync тоже
    data_sync.COEFFICIENTS = COEFFICIENTS
    
    # Получаем коэффициенты для новых команд
    coeffs = bot_settings.get_coefficients()
    
    await message.answer(
        f"✅ *Команды обновлены!*\n\n"
        f"🏆 Новые команды: {team1} vs {team2}\n"
        f"📊 Коэффициенты: {coeffs[team1]} | {coeffs[team2]}",
        parse_mode="Markdown"
    )

@dp.message(Command("setcoef"))
async def set_coefficients(message: types.Message):
    """Изменить коэффициенты: /setcoef 1.85 2.15"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Формат: `/setcoef коэф1 коэф2`\nПример: `/setcoef 1.85 2.15`", parse_mode="Markdown")
        return
    
    try:
        coef1 = float(args[0])
        coef2 = float(args[1])
        
        if coef1 < 1.0 or coef2 < 1.0:
            await message.answer("❌ Коэффициенты должны быть больше 1.0")
            return
        
        # Обновляем настройки
        success1 = bot_settings.set_setting('coefficients', 'team1', coef1)
        success2 = bot_settings.set_setting('coefficients', 'team2', coef2)
        print(f"DEBUG setcoef: set coef1={coef1} success={success1}, set coef2={coef2} success={success2}")
        
        # Обновляем глобальные переменные
        global COEFFICIENTS
        COEFFICIENTS = get_current_coefficients()
        
        # Обновляем data_sync тоже
        data_sync.COEFFICIENTS = COEFFICIENTS
        
        team1, team2 = bot_settings.get_team_names()
        await message.answer(
            f"✅ *Коэффициенты обновлены!*\n\n"
            f"📊 {team1}: {coef1}\n"
            f"📊 {team2}: {coef2}",
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer("❌ Коэффициенты должны быть числами!")

@dp.message(Command("setrate"))
async def set_exchange_rate(message: types.Message):
    """Изменить курс валюты: /setrate USD 42.5"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Формат: `/setrate ВАЛЮТА курс`\nПример: `/setrate USD 42.5`", parse_mode="Markdown")
        return
    
    currency = args[0].upper()
    valid_currencies = ['USD', 'EUR', 'BTC', 'ETH']
    
    if currency not in valid_currencies:
        await message.answer(f"❌ Поддерживаемые валюты: {', '.join(valid_currencies)}")
        return
    
    try:
        rate = float(args[1])
        
        if rate <= 0:
            await message.answer("❌ Курс должен быть положительным числом")
            return
        
        # Обновляем настройки
        success = bot_settings.set_setting('exchange_rates', currency, rate)
        print(f"DEBUG setrate: set {currency}={rate} success={success}")
        
        # Обновляем глобальные переменные
        global EXCHANGE_RATES
        EXCHANGE_RATES = get_current_exchange_rates()
        
        # Обновляем data_sync тоже
        data_sync.EXCHANGE_RATES = EXCHANGE_RATES
        
        await message.answer(
            f"✅ *Курс обновлен!*\n\n"
            f"💱 1 {currency} = {rate:,.2f} UAH",
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer("❌ Курс должен быть числом!")

@dp.message(Command("setlimits"))
async def set_limits(message: types.Message):
    """Изменить лимиты: /setlimits макс_ставка макс_баланс"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Формат: `/setlimits макс_ставка макс_баланс`\nПример: `/setlimits 50000 1000000`", parse_mode="Markdown")
        return
    
    try:
        max_bet = float(args[0])
        max_balance = float(args[1])
        
        if max_bet <= 0 or max_balance <= 0:
            await message.answer("❌ Лимиты должны быть положительными числами")
            return
        
        # Обновляем настройки
        success1 = bot_settings.set_setting('max_bet_uah', None, max_bet)
        success2 = bot_settings.set_setting('max_balance_uah', None, max_balance)
        print(f"DEBUG setlimits: set max_bet={max_bet} success={success1}, max_balance={max_balance} success={success2}")
        
        await message.answer(
            f"✅ *Лимиты обновлены!*\n\n"
            f"💰 Макс. ставка: {max_bet:,.0f} UAH\n"
            f"💳 Макс. баланс: {max_balance:,.0f} UAH",
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer("❌ Лимиты должны быть числами!")

@dp.message(Command("setemoji"))
async def set_emoji(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    # Получаем аргументы команды  
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if len(args) != 2:
        await message.answer(
            f"❌ Неверный формат команды!\n\n"
            f"Используйте: `/setemoji <emoji1> <emoji2>`\n"
            f"Пример: `/setemoji 🔥 ⚡`\n"
            f"Можно использовать любые эмодзи, включая анимированные из Telegram",
            parse_mode="Markdown"
        )
        return
    
    emoji1 = args[0]
    emoji2 = args[1]
    
    # Обновляем настройки
    success1 = bot_settings.set_setting('team_emojis', 'team1', emoji1)
    success2 = bot_settings.set_setting('team_emojis', 'team2', emoji2)
    print(f"DEBUG setemoji: set emoji1={emoji1} success={success1}, emoji2={emoji2} success={success2}")
    
    # Получаем названия команд для отображения
    team1, team2 = bot_settings.get_team_names()
    
    await message.answer(
        f"✅ *Эмодзи команд обновлены!*\n\n"
        f"{emoji1} {team1}\n"
        f"{emoji2} {team2}",
        parse_mode="Markdown"
    )

@dp.message(Command("settings"))
async def show_all_settings(message: types.Message):
    """Показать все текущие настройки"""
    user_id = message.from_user.id
    
    if user_id not in ADMINS:
        await message.answer("⛔ Эта команда только для админов.")
        return
    
    settings = bot_settings.load_settings()
    team1, team2 = bot_settings.get_team_names()
    coeffs = bot_settings.get_coefficients()
    rates = bot_settings.get_exchange_rates()
    
    await message.answer(
        f"⚙️ *ВСЕ НАСТРОЙКИ БОТА*\n\n"
        f"*🏆 КОМАНДЫ:*\n"
        f"• Команда 1: {team1}\n"
        f"• Команда 2: {team2}\n\n"
        f"*📊 КОЭФФИЦИЕНТЫ:*\n"
        f"• {team1}: {coeffs[team1]}\n"
        f"• {team2}: {coeffs[team2]}\n\n"
        f"*💱 КУРСЫ ВАЛЮТ:*\n"
        f"• 1 USD = {rates['USD']:,.2f} UAH\n"
        f"• 1 EUR = {rates['EUR']:,.2f} UAH\n"
        f"• 1 BTC = {rates['BTC']:,.0f} UAH\n"
        f"• 1 ETH = {rates['ETH']:,.0f} UAH\n\n"
        f"*💰 ЛИМИТЫ:*\n"
        f"• Макс. ставка: {settings['max_bet_uah']:,.0f} UAH\n"
        f"• Мин. ставка: {settings['min_bet_uah']:,.0f} UAH\n"
        f"• Макс. баланс: {settings['max_balance_uah']:,.0f} UAH\n"
        f"• Макс. депозит: {settings['max_deposit_uah']:,.0f} UAH",
        parse_mode="Markdown"
    )

async def uptime_monitor():
    """Anti-sleep monitoring task - logs uptime status every 4 minutes"""
    while True:
        await asyncio.sleep(240)  # 4 minutes
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        active_users = len(user_state)
        total_bets = len(user_bets)
        logging.info(f"🟢 UptimeBot: Bot is active [{current_time}] | Users: {active_users} | Bets: {total_bets}")

async def set_bot_commands():
    """Set bot commands and menu button"""
    from aiogram.types import BotCommand, MenuButtonWebApp
    
    # Set list of commands that appear in menu
    commands = [
        BotCommand(command="start", description="🎯 Главное меню"),
        BotCommand(command="balance", description="💰 Показать баланс"),
        BotCommand(command="mybet", description="📊 Моя ставка"),
        BotCommand(command="admin", description="🔧 Админ-панель"),
        BotCommand(command="settings", description="⚙️ Настройки"),
        BotCommand(command="setemoji", description="😀 Установить эмодзи команд"),
        BotCommand(command="win", description="🏆 Объявить победителя"),
        BotCommand(command="resetbets", description="🔄 Сбросить ставки"),
    ]
    await bot.set_my_commands(commands)
    
    # Set the menu button to open Web App
    web_app_url = f"https://{os.getenv('REPLIT_DOMAINS', 'localhost:5000')}/"
    menu_button = MenuButtonWebApp(text="СТАВКИ", web_app=WebAppInfo(url=web_app_url))
    await bot.set_chat_menu_button(menu_button=menu_button)
    
    logging.info(f"✅ Bot commands and menu button set (Web App: {web_app_url})")

async def main():
    """Main function to start the bot"""
    logging.info("Starting CS2 Betting Bot...")
    try:
        # Initialize settings after all imports are done
        global COEFFICIENTS, EXCHANGE_RATES
        COEFFICIENTS = get_current_coefficients()
        EXCHANGE_RATES = get_current_exchange_rates()
        logging.info(f"Settings loaded: Teams={list(COEFFICIENTS.keys())}, Coeffs={COEFFICIENTS}")
        
        # Set bot commands and menu button
        await set_bot_commands()
        
        # Start uptime monitoring task
        asyncio.create_task(uptime_monitor())
        logging.info("🟢 UptimeBot: Anti-sleep monitoring started (4 min intervals)")
        
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot failed to start: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
