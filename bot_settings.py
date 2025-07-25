"""
Настройки бота, которые можно изменять через админские команды
"""

import json
import os
from threading import Lock

SETTINGS_FILE = 'bot_settings.json'
LOCK = Lock()

# Дефолтные настройки
DEFAULT_SETTINGS = {
    "teams": {
        "team1": "Sovkamax",
        "team2": "Faze"
    },
    "coefficients": {
        "team1": 1.82,
        "team2": 2.22
    },
    "team_emojis": {
        "team1": "🧑‍💼",
        "team2": "🦅"
    },
    "exchange_rates": {
        "USD": 41.18,
        "EUR": 47.87,
        "UAH": 1.0,
        "BTC": 4526731.0,
        "ETH": 152462.0
    },
    "max_bet_uah": 100000,
    "min_bet_uah": 10,
    "max_balance_uah": 500000,
    "max_deposit_uah": 10000
}

def load_settings():
    """Загрузить настройки из файла"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Убеждаемся что все ключи есть
                for key in DEFAULT_SETTINGS:
                    if key not in settings:
                        settings[key] = DEFAULT_SETTINGS[key]
                return settings
    except Exception as e:
        print(f"Ошибка загрузки настроек: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Сохранить настройки в файл"""
    try:
        with LOCK:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            print(f"Настройки сохранены: {settings}")
            return True
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")
        return False

def get_setting(key, subkey=None):
    """Получить конкретную настройку"""
    settings = load_settings()
    if subkey:
        return settings.get(key, {}).get(subkey)
    return settings.get(key)

def set_setting(key, subkey, value):
    """Установить конкретную настройку"""
    settings = load_settings()
    print(f"DEBUG set_setting: key={key}, subkey={subkey}, value={value}")
    
    if subkey:
        if key not in settings:
            settings[key] = {}
        settings[key][subkey] = value
        print(f"DEBUG set_setting: updated {key}.{subkey} = {value}")
    else:
        settings[key] = value
        print(f"DEBUG set_setting: updated {key} = {value}")
    
    success = save_settings(settings)
    print(f"DEBUG set_setting: save_settings returned {success}")
    return success

def get_team_names():
    """Получить названия команд"""
    teams = get_setting('teams')
    return teams['team1'], teams['team2']

def get_coefficients():
    """Получить коэффициенты"""
    coefficients = get_setting('coefficients')
    team1, team2 = get_team_names()
    return {team1: coefficients['team1'], team2: coefficients['team2']}

def get_exchange_rates():
    """Получить курсы валют"""
    return get_setting('exchange_rates')

def get_team_emojis():
    """Получить эмодзи команд"""
    emojis = get_setting('team_emojis')
    team1, team2 = get_team_names()
    return {team1: emojis['team1'], team2: emojis['team2']}

# Инициализация
current_settings = load_settings()