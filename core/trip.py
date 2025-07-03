from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.database import (
    is_registered,
    save_trip_start,
    end_trip_db,
    get_now
)

# Список организаций для выбора
ORGANIZATIONS = {
    'kuzminsky':    "Кузьминский районный суд",
    'lefortovsky':  "Лефортовский районный суд",
    'lyublinsky':   "Люблинский районный суд",
    'meshchansky':  "Мещанский районный суд",
    'nagatinsky':   "Нагатинский районный суд",
    'perovsky':     "Перовский районный суд",
    'shcherbinsky': "Щербинский районный суд",
    'tverskoy':     "Тверской районный суд",
    'cheremushkinsky': "Черемушкинский районный суд",
    'chertanovsky':    "Чертановский районный суд",
    'msk_city':        "Московский городской суд",
    'kassatsionny2':   "Второй кассационный суд общей юрисдикции",
    'domodedovo':      "Домодедовский городской суд",
    'lyuberetsky':     "Люберецкий городской суд",
    'vidnoye':         "Видновский городской суд",
    'justice_peace':   "Мировые судьи (участок)",
    'fns':             "ФНС",
    'gibdd':           "ГИБДД",
    'notary':          "Нотариус",
    'post':            "Почта России",
    'rosreestr':       "Росреестр",
    'other':           "Другая организация"
}

async def trip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text(
            "❌ Вы не зарегистрированы! Используйте `/register Фамилия Имя`",
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"org_{org_id}")]
        for org_id, name in ORGANIZATIONS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚗 *Куда вы отправляетесь?*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_custom_org_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    custom_org = update.message.text.strip()
    if not custom_org:
        await update.message.reply_text("❌ Название не может быть пустым.")
        return
    if not is_registered(user_id):
        await update.message.reply_text("❌ Вы не зарегистрированы.")
        return

    success = save_trip_start(user_id, "other", custom_org)
    time_now = get_now().strftime("%H:%M")
    if success:
        await update.message.reply_text(
            f"🚀 Поездка в *{custom_org}* начата в *{time_now}*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось начать поездку. Возможно, вы уже в пути.",
            parse_mode="Markdown"
        )

async def return_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success = end_trip_db(user_id)
    time_now = get_now().strftime("%H:%M")
    if success:
        await update.message.reply_text(
            f"🏁 Поездка завершена в *{time_now}*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚠️ У вас нет активной поездки.",
            parse_mode="Markdown"
        )

async def handle_trip_save(update: Update, context: ContextTypes.DEFAULT_TYPE, org_id: str, org_name: str):
    user_id = update.effective_user.id
    success = save_trip_start(user_id, org_id, org_name)
    time_now = get_now().strftime("%H:%M")
    if success:
        await update.callback_query.edit_message_text(
            f"🚌 Поездка в *{org_name}* начата в *{time_now}*",
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Не удалось начать поездку. Возможно, вы уже в пути.",
            parse_mode="Markdown"
        )