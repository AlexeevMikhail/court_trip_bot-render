# core/trip.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import time
from utils.database import (
    is_registered,
    save_trip_start,
    end_trip as db_end_trip,
    get_now
)

# Организации
ORGANIZATIONS = {
    'kuzminsky':      "Кузьминский районный суд",
    'lefortovsky':    "Лефортовский районный суд",
    'lyublinsky':     "Люблинский районный суд",
    'meshchansky':    "Мещанский районный суд",
    'nagatinsky':     "Нагатинский районный суд",
    'perovsky':       "Перовский районный суд",
    'shcherbinsky':   "Щербинский районный суд",
    'tverskoy':       "Тверской районный суд",
    'cheremushkinsky':"Черемушкинский районный суд",
    'chertanovsky':   "Чертановский районный суд",
    'msk_city':       "Московский городской суд",
    'kassatsionny2':  "Второй кассационный суд общей юрисдикции",
    'domodedovo':     "Домодедовский городской суд",
    'lyuberetsky':    "Люберецкий городской суд",
    'vidnoye':        "Видновский городской суд",
    'justice_peace':  "Мировые судьи (судебный участок)",
    'fns':            "ФНС",
    'gibdd':          "ГИБДД",
    'notary':         "Нотариус",
    'post':           "Почта России",
    'rosreestr':      "Росреестр",
    'other':          "Другая организация (введите вручную)"
}

async def start_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        return await update.message.reply_text(
            "❌ Вы не зарегистрированы!\n"
            "Используйте команду: /register Иванов Иван"
        )

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"org_{org_id}")]
        for org_id, name in ORGANIZATIONS.items()
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚗 *Куда вы отправляетесь?*\nВыберите пункт назначения:",
        parse_mode="Markdown",
        reply_markup=markup
    )

async def handle_trip_save(update: Update, context: ContextTypes.DEFAULT_TYPE, org_id: str, org_name: str):
    user_id = update.effective_user.id
    ok = await save_trip_start(user_id, org_id, org_name)
    ts = await get_now()
    ts_fmt = ts.strftime("%H:%M")
    if ok:
        await update.callback_query.edit_message_text(
            f"🚀 Поездка в *{org_name}* начата в {ts_fmt}",
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Не удалось начать поездку. Возможно, вы уже в пути.",
            parse_mode="Markdown"
        )

async def handle_custom_org_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    custom = update.message.text.strip()

    if not await is_registered(user_id):
        return await update.message.reply_text("❌ Вы не зарегистрированы.")

    if not custom:
        return await update.message.reply_text("❌ Название организации не может быть пустым.")

    ok = await save_trip_start(user_id, "other", custom)
    ts = await get_now()
    ts_fmt = ts.strftime("%H:%M")
    if ok:
        await update.message.reply_text(f"🚀 Поездка в *{custom}* начата в {ts_fmt}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Не удалось начать поездку. Возможно, вы уже в пути.")

async def end_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success = await db_end_trip(user_id)
    ts = await get_now()
    ts_fmt = ts.strftime("%H:%M")
    if success:
        await update.message.reply_text(f"🏁 Поездка завершена в {ts_fmt}")
    else:
        await update.message.reply_text("⚠️ У вас нет активной поездки.")
