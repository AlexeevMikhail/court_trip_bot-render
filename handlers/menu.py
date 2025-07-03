from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.trip import start_trip, end_trip, handle_custom_org_input

# Основное меню кнопок
main_menu_keyboard = [
    ["🚀 Поездка", "🏦 Возврат"],
    ["➕ Регистрация", "💼 Отчёт"]
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Если мы ожидали ручной ввод организации
    if context.user_data.get("awaiting_custom_org"):
        context.user_data["awaiting_custom_org"] = False
        return await handle_custom_org_input(update, context)

    if text == "🚀 Поездка":
        await start_trip(update, context)

    elif text == "🏦 Возврат":
        await end_trip(update, context)

    elif text == "➕ Регистрация":
        # При нажатии кнопки предлагаем команду /register
        await update.message.reply_text(
            "Чтобы зарегистрироваться, отправьте команду:\n"
            "/register ФИО",
            reply_markup=main_menu_markup,
            parse_mode="Markdown"
        )

    elif text == "💼 Отчёт":
        await update.message.reply_text(
            "Для создания отчёта используйте команду:\n"
            "/report ДД.MM.ГГГГ [ДД.MM.ГГГГ]",
            reply_markup=main_menu_markup,
            parse_mode="Markdown"
        )

    else:
        # Во всех остальных случаях показываем меню
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu_markup
        )
