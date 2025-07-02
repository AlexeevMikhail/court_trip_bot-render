import os
import time
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers.commands import register_command, trip_command, return_command, report_command
from handlers.callbacks import organization_callback
from handlers.menu import handle_main_menu
from utils.database import init_db
from dotenv import load_dotenv
from keep_alive import keep_alive
from scheduler import start_scheduler

# Загрузка переменных окружения из .env
load_dotenv()

# Запускаем Flask‑сервер health‑check
keep_alive()
time.sleep(3)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ ОШИБКА: переменная BOT_TOKEN не задана")
    exit(1)

async def on_startup(app):
    print("🟢 Бот успешно запущен")

def main():
    # Инициализация БД
    init_db()

    # Строим приложение
    app = ApplicationBuilder()\
        .token(TOKEN)\
        .post_init(on_startup)\
        .build()

    # Регистрируем handlers
    app.add_handler(register_command)
    app.add_handler(trip_command)
    app.add_handler(return_command)
    app.add_handler(report_command)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))
    app.add_handler(organization_callback)

    # Запуск автозакрытия поездок
    start_scheduler()

    # Старт polling
    print("⏳ Запуск polling...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Бот остановлен вручную.")
    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")
        raise
