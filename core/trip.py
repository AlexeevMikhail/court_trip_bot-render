# core/trip.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import sqlite3
from datetime import time
from utils.database import is_registered, save_trip_start, end_trip as db_end_trip, get_now

# Словарь организаций и кнопок
ORGANIZATIONS = {
    # 1. Районные суды Москвы
    'kuzminsky':      "Кузьминский районный суд",
    'lefortovsky':    "Лефортовский районный суд",
    'lyublinsky':     "Люблинский районный суд",
    'meshchansky':    "Мещанский районный суд",
    'nagatinsky':     "Нагатинский районный суд",
    'perovsky':       "Перовский районный суд",
    'shcherbinsky':   "Щербинский районный суд",
    'tverskoy':       "Тверской районный суд",
    'cheremushkinsky':"Чертановский районный суд",
    'chertanovsky':   "Чертановский районный суд",

    # 2. Мосгорсуд и кассация
    'msk_city':       "Московский городской суд",
    'kassatsionny2':  "Второй кассационный суд общей юрисдикции",

    # 3. Горсуды Подмосковья
    'domodedovo':     "Домодедовский городской суд",
    'lyuberetsky':    "Люберецкий городской суд",
    'vidnoye':        "Видновский городской суд",

    # 4. Прочие
    'justice_peace':  "Мировые судьи (судебный участок)",
    'fns':            "ФНС",
    'gibdd':          "ГИБДД",
    'notary':         "Нотариус",
    'post':           "Почта России",
    'rosreestr':      "Росреестр",

    # 5. Другая
    'other':          "Другая организация (введите вручную)"
}

async def start_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        return await update.message.reply_text(
            "❌ Вы не зарегистрированы!\n"
            "Используйте команду: /register Иванов Иван"
        )

    # Построим клавиатуру
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"org_{org_id}")]
        for org_id, name in ORGANIZATIONS.items()
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚗 *Куда вы отправляетесь?*\n"
        "Выберите пункт назначения:",
        parse_mode="Markdown",
        reply_markup=markup
    )

async def handle_custom_org_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # После выбора «Другая организация» бот ждёт текст
    user_id = update.effective_user.id
    custom = update.message.text.strip()
    if not is_registered(user_id):
        return await update.message.reply_text("❌ Вы не зарегистрированы.")
    if not custom:
        return await update.message.reply_text("❌ Название организации не может быть пустым.")

    ok = save_trip_start(user_id, "other", custom)
    ts = get_now().strftime("%H:%M")
    if ok:
        await update.message.reply_text(f"🚀 Поездка в *{custom}* начата в {ts}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Не удалось начать поездку. Возможно, вы уже в пути.")

async def end_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success = db_end_trip(user_id)
    ts = get_now().strftime("%H:%M")
    if success:
        await update.message.reply_text(f"🏁 Поездка завершена в {ts}")
    else:
        await update.message.reply_text("⚠️ У вас нет активной поездки.")

async def handle_trip_save(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    org_id: str,
    org_name: str
):
    """
    Вызывается из callbacks.py, когда
    пользователь нажал на конкретную кнопку.
    """
    user_id = update.effective_user.id
    ok = save_trip_start(user_id, org_id, org_name)
    ts = get_now().strftime("%H:%M")
    if ok:
        # Заменяем текст кнопок на подтверждение
        await update.callback_query.edit_message_text(
            f"🚀 Поездка в *{org_name}* начата в {ts}",
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Не удалось начать поездку. Возможно, вы уже в пути.",
            parse_mode="Markdown"
        )
