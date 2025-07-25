#!/usr/bin/env python3
"""
CS2 Betting Bot - Специальная версия для Render.com
Автоматически настраивается для работы на Render хостинге
"""

import os
import asyncio
import threading
import time
from flask import Flask
from bot import main as bot_main
from web_server import create_app

def get_render_config():
    """Получает конфигурацию для Render"""
    port = int(os.getenv('PORT', 5000))
    
    # Автоматически определяем URL для Render
    service_name = os.getenv('RENDER_SERVICE_NAME', 'cs2-betting-bot')
    host_url = os.getenv('HOST_URL', f"{service_name}.onrender.com")
    
    return {
        'port': port,
        'host_url': host_url,
        'host': '0.0.0.0'  # Render требует 0.0.0.0
    }

def run_telegram_bot():
    """Запускает Telegram бота в отдельном потоке"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot_main())
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

def create_render_app():
    """Создает Flask приложение для Render"""
    app = create_app()
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'cs2-betting-bot'}, 200
    
    @app.route('/')
    def render_info():
        return {
            'service': 'CS2 Betting Bot',
            'status': 'running',
            'platform': 'Render',
            'endpoints': {
                'health': '/health',
                'webapp': '/static/index.html',
                'api': '/api/*'
            }
        }
    
    return app

def main():
    """Главная функция для Render"""
    print("🚀 Запуск CS2 Betting Bot на Render.com")
    
    config = get_render_config()
    print(f"🌐 Порт: {config['port']}")
    print(f"🔗 URL: https://{config['host_url']}")
    
    # Проверяем токен бота
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        print("Добавьте переменную окружения в настройках Render:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        return
    
    # Устанавливаем HOST_URL для антисон системы
    os.environ['HOST_URL'] = config['host_url']
    
    # Запускаем Telegram бота в отдельном потоке
    print("🤖 Запуск Telegram бота...")
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Небольшая задержка для инициализации бота
    time.sleep(3)
    
    # Создаем и запускаем Flask приложение
    print("🌐 Запуск веб-сервера...")
    app = create_render_app()
    
    try:
        app.run(
            host=config['host'],
            port=config['port'],
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

if __name__ == "__main__":
    main()