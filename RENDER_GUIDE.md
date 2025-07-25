# Развертывание CS2 Betting Bot на Render.com

## Быстрый старт

### 1. Создание сервиса на Render
1. Зайдите на https://render.com и войдите в аккаунт
2. Нажмите "New +" → "Web Service"
3. Выберите "Build and deploy from a Git repository"
4. Подключите GitHub репозиторий или загрузите файлы

### 2. Настройки сервиса
```
Name: cs2-betting-bot
Environment: Python 3
Build Command: pip install -r requirements.txt  
Start Command: python main_render.py
```

### 3. Переменные окружения
Добавьте в Environment Variables:
```
TELEGRAM_BOT_TOKEN = ваш_токен_бота
HOST_URL = ваш-сервис-name.onrender.com
PORT = 5000
```

### 4. Развертывание
1. Нажмите "Create Web Service"
2. Дождитесь завершения сборки (3-5 минут)
3. Получите URL: https://ваш-сервис-name.onrender.com

## Особенности для Render

✅ **Автоматическая настройка** - main_render.py автоматически определяет настройки
✅ **Health checks** - встроенная проверка работоспособности
✅ **Антисон система** - автоматически настраивается для Render URL
✅ **24/7 работа** - поддерживает постоянную активность

## Файлы в архиве
- main_render.py - точка входа для Render
- render.yaml - конфигурация сервиса (опционально)
- requirements.txt - зависимости Python
- Все файлы бота и веб-приложения

## Проверка работы
После развертывания:
- https://ваш-сервис.onrender.com/ - информация о сервисе
- https://ваш-сервис.onrender.com/health - проверка здоровья
- Telegram бот должен отвечать на команды

Создано: 2025-07-25 17:55:39
