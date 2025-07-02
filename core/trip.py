from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.database import is_registered, save_trip_start, get_now
import sqlite3

# Список организаций
ORGANIZATIONS = {
    'kuzminsky': "Кузьминский районный суд",
    'lefortovsky': "Лефортовский районный суд",
    'lyublinsky': "Люблинский районный суд",
    'meshchansky': "Мещанский районный суд",
    'nagatinsky': "Нагатинский районный суд",
    'perovsky': "Перовский районный суд",
    'shcherbinsky': "Щербинский районный суд",
    'tverskoy': "Тверской районный суд",
    'cheremushkinsky': "Черемушкинский районный суд",
    'chertanovsky': "Чертановский районный суд",
    'msk_city': "Московский городской суд",
    'kassatsionny2': "Второй кассационный суд общей юрисдикции",
    'domodedovo': "Домодедовский городской суд",
    'lyuberetsky': "Люберецкий городской суд",
    'vidnoye': "Видновский городской суд",
    'justice_peace': "Мировые судьи (участок)",
    'fns': "ФНС",
    'gibdd': "ГИБДД",
    'notary': "Нотариус",
    'post': "Почта России",
    'rosreestr': "Росреестр",
    'other': "Другая организация"
}

async def start_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text(
            "❌ Вы не зарегистрированы!\n"
            "/register Иванов Иван",
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
    t = get_now().strftime("%H:%M")
    if success:
        await update.message.reply_text(f"🚀 Поездка в *{custom_org}* начата в *{t}*", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Не удалось начать поездку.", parse_mode="Markdown")

async def handle_trip_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатия inline‑кнопки с организацией.
    """
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id or update.effective_user.id
    org_id = query.data.split("org_", 1)[1]
    org_name = ORGANIZATIONS.get(org_id, "Неизвестная")
    success = save_trip_start(user_id, org_id, org_name)
    t = get_now().strftime("%H:%M")

    if success:
        await query.edit_message_text(
            f"🚌 Поездка в *{org_name}* начата в *{t}*",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Не удалось начать поездку.\nВозможно, вы уже в пути.",
            parse_mode="Markdown"
        )

async def end_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('court_tracking.db')
    cursor = conn.cursor()
    now = get_now()

    cursor.execute('''
        UPDATE trips 
        SET end_datetime = ?, status = 'completed'
        WHERE user_id = ? AND status = 'in_progress'
    ''', (now, user_id))
    conn.commit()
    conn.close()

    if cursor.rowcount > 0:
        await update.message.reply_text(f"🏁 Поездка завершена в *{now.strftime('%H:%M')}*", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ У вас нет активной поездки", parse_mode="Markdown")
