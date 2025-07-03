# core/register.py
from telegram import Update
from telegram.ext import ContextTypes
from utils.database import get_conn

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    full_name = " ".join(context.args).strip()
    if not full_name:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите имя: `/register Фамилия Имя`",
            parse_mode="Markdown"
        )
        return

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO employees (user_id, full_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
              SET full_name = EXCLUDED.full_name,
                  is_active = TRUE
        """, (user_id, full_name))
        conn.commit()

    await update.message.reply_text(
        f"✅ Вы успешно зарегистрированы как *{full_name}*",
        parse_mode="Markdown"
    )
