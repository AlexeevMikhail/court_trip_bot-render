# handlers/callbacks.py

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from core.trip import handle_trip_save, ORGANIZATIONS

async def handle_organization_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатий на inline‑кнопки org_<org_id>.
    Если выбрали «Другая организация», переключаем бота в режим ожидания текста.
    Иначе — сразу сохраняем поездку через handle_trip_save.
    """
    query = update.callback_query
    await query.answer()

    org_id = query.data.split("_", 1)[1]

    if org_id == "other":
        # Ждём, что пользователь введёт название
        context.user_data["awaiting_custom_org"] = True
        await query.edit_message_text(
            "✏️ Пожалуйста, введите название организации вручную:"
        )
    else:
        # Для всех остальных организаций
        # handle_trip_save внутри сам разбирает query.data и берет название из ORGANIZATIONS
        await handle_trip_save(update, context)

# Регистрируем CallbackQueryHandler, отлавливающий все callback_data, начинающиеся с "org_"
organization_callback = CallbackQueryHandler(
    handle_organization_callback,
    pattern=r"^org_"
)
