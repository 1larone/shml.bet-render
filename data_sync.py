"""
Shared data synchronization module for CS2 betting bot and web server.
This module provides shared data structures and utilities for both the Telegram bot and Flask web server.
Uses JSON files for cross-process synchronization.
"""

import json
import os
from threading import Lock

# File paths for data persistence
DATA_FILE = 'betting_data.json'
LOCK = Lock()

def load_data():
    """Load data from JSON file"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Convert user_bets back to set and keep user_id keys as strings for web compatibility
                data['user_bets'] = set(str(uid) for uid in data.get('user_bets', []))
                data['user_balances'] = {str(k): v for k, v in data.get('user_balances', {}).items()}
                data['user_state'] = {str(k): v for k, v in data.get('user_state', {}).items()}
                data['user_results'] = {str(k): v for k, v in data.get('user_results', {}).items()}
                return data
    except Exception as e:
        print(f"Error loading data: {e}")
    return {
        'user_balances': {},
        'user_bets': set(),
        'user_state': {},
        'match_result': None,
        'user_results': {}
    }

def save_data():
    """Save current data to JSON file"""
    try:
        with LOCK:
            data_to_save = {
                'user_balances': {str(k): v for k, v in user_balances.items()},
                'user_bets': list(user_bets),
                'user_state': {str(k): v for k, v in user_state.items()},
                'match_result': match_result,
                'user_results': {str(k): v for k, v in user_results.items()}
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            print(f"Data saved: {len(user_balances)} balances, {len(user_bets)} bets, match_result={match_result}")
    except Exception as e:
        print(f"Error saving data: {e}")

def reload_data():
    """Reload data from file"""
    global user_balances, user_bets, user_state, match_result, user_results
    data = load_data()
    user_balances = data['user_balances']
    user_bets = data['user_bets']  
    user_state = data['user_state']
    match_result = data['match_result']
    user_results = data['user_results']

# Load initial data
data = load_data()
user_balances = data['user_balances']
user_bets = data['user_bets']
user_state = data['user_state']
match_result = data['match_result']
user_results = data['user_results']

# Exchange rates and coefficients (same for both bot and web server)
EXCHANGE_RATES = {
    'USD': 41.18,
    'EUR': 47.87,
    'UAH': 1.0,
    'BTC': 4526731.0,
    'ETH': 152462.0
}

COEFFICIENTS = {
    "Sovkamax": 1.82,
    "Faze": 2.22
}

def convert_to_uah(amount, currency):
    """Convert amount from given currency to UAH"""
    import bot_settings
    rates = bot_settings.get_exchange_rates()
    currency_clean = currency.split(' ')[-1] if ' ' in currency else currency
    rate = rates.get(currency_clean, 1.0)
    return amount * rate

def get_currency_code(currency_with_emoji):
    """Extract currency code from emoji string"""
    return currency_with_emoji.split(' ')[-1]

def clear_all_bets():
    """Clear all user bets (for new matches)"""
    global user_bets, user_state, match_result, user_results
    user_bets.clear()
    user_state.clear()
    match_result = None
    user_results.clear()
    save_data()

def get_user_balance(user_id):
    """Get user balance safely"""
    return user_balances.get(user_id, 0.0)

def update_user_balance(user_id, amount):
    """Update user balance"""
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    user_balances[user_id] += amount
    
    # Ensure balance doesn't go negative
    if user_balances[user_id] < 0:
        user_balances[user_id] = 0.0
    
    save_data()
    return user_balances[user_id]

def set_user_balance(user_id, amount):
    """Set user balance to specific amount"""
    user_balances[user_id] = max(0.0, amount)
    save_data()
    return user_balances[user_id]

def set_match_result(winner):
    """Set match result for web app (without saving to avoid data loss)"""
    global match_result
    match_result = winner
    print(f"Match result set to: {winner}")

def get_match_result():
    """Get current match result"""
    reload_data()  # Always reload to get latest data
    return match_result

def set_user_result(user_id, result_data):
    """Set user's match result"""
    global user_results
    user_results[user_id] = result_data
    save_data()
    print(f"User result set for {user_id}: {result_data}")

def get_user_result(user_id):
    """Get user's match result"""
    reload_data()  # Always reload to get latest data
    return user_results.get(user_id, None)

def reset_user_after_match(user_id):
    """Reset user data after match completion"""
    global user_balances, user_state, user_bets, user_results
    
    # Remove user from active bets
    if user_id in user_bets:
        user_bets.discard(user_id)
    
    # Clear user state
    if user_id in user_state:
        del user_state[user_id]
    
    # Clear user results 
    if user_id in user_results:
        del user_results[user_id]
    
    # Reset balance to 0 if they lost (will be handled by deposit logic)
    save_data()
    print(f"Reset user {user_id} data after match completion")

def reset_all_balances():
    """Reset all user balances to 0"""
    global user_balances
    for user_id in user_balances:
        user_balances[user_id] = 0.0
    save_data()
    print(f"All user balances reset to 0 for {len(user_balances)} users")

def reset_everything():
    """Reset all balances to 0 and clear all bets for fresh start"""
    global user_balances, user_bets, user_state, match_result, user_results
    
    # Reset all balances to 0
    for user_id in user_balances:
        user_balances[user_id] = 0.0
    
    # Clear all bets and game state
    user_bets.clear()
    user_state.clear()
    match_result = None
    user_results.clear()
    
    save_data()
    print(f"Complete reset: {len(user_balances)} balances set to 0, all bets cleared")