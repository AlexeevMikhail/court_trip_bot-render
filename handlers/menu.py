# handlers/menu.py

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.trip import trip_command, return_command, handle_custom_org_input
from core.register import register_command

# Основное меню кнопок
main_menu_keyboard = [
    ["🚀 Поездка", "🏦 Возврат"],
    ["➕ Регистрация", "💼 Отчёт"]
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Если мы ждём ручной ввод названия «Другой организации» — передаём в соответствующий хэндлер
    if context.user_data.get("awaiting_custom_org"):
        context.user_data["awaiting_custom_org"] = False
        return await handle_custom_org_input(update, context)

    # Обработка нажатий «кнопок» основного меню
    if text == "🚀 Поездка":
        # Запустить диалог выбора организации
        await trip_command(update, context)

    elif text == "🏦 Возврат":
        # Завершить текущую поездку
        await return_command(update, context)

    elif text == "➕ Регистрация":
        # Зарегистрировать нового пользователя
        await register_command(update, context)

    elif text == "💼 Отчёт":
        # Подсказка по получению отчёта
        await update.message.reply_text(
            "Для получения отчёта используйте команду:\n"
            "/report [дд.мм.гггг] [дд.мм.гггг]\n"
            "— без аргументов за всю историю, один аргумент за один день, два аргумента за период.",
            parse_mode="Markdown"
        )

    else:
        # Если пришёл какой‑то другой текст — показываем клавиатуру
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu_markup
        )
