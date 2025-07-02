from telegram import Update
from telegram.ext import ContextTypes
import sqlite3

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "✏️ *Введите ваше ФИО после команды:*\n`/register Иванов Иван`",
            parse_mode="Markdown"
        )
        return

    full_name = ' '.join(args)
    conn = sqlite3.connect("court_tracking.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO employees (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
        conn.commit()
        await update.message.reply_text(
            f"👤 *Регистрация прошла успешно!*\nДобро пожаловать, *{full_name}* ✅",
            parse_mode="Markdown"
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "⚠️ *Вы уже зарегистрированы.*",
            parse_mode="Markdown"
        )
    finally:
        conn.close()
