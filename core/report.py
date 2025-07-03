# core/report.py
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from utils.database import get_conn
import pandas as pd
from io import BytesIO

ADMIN_IDS = [414634622, 1745732977]  # ваши админ‑ID

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "🚫 У вас нет прав для получения отчёта.",
            parse_mode="Markdown"
        )
        return

    # Парсим аргументы /report [start] [end]
    args = context.args
    start_date = end_date = None
    try:
        if len(args) >= 1:
            start_date = datetime.strptime(args[0], "%d.%m.%Y").date()
        if len(args) >= 2:
            end_date   = datetime.strptime(args[1], "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text(
            "📌 Формат: `/report ДД.MM.ГГГГ [ДД.MM.ГГГГ]`",
            parse_mode="Markdown"
        )
        return

    # Загружаем все поездки из Postgres
    with get_conn() as conn:
        df = pd.read_sql("""
            SELECT
              e.full_name   AS ФИО,
              t.organization_name AS Организация,
              t.start_datetime,
              t.end_datetime
            FROM employees e
            JOIN trips t ON e.user_id = t.user_id
            WHERE e.is_active = TRUE
            ORDER BY t.start_datetime
        """, conn)

    if df.empty:
        await update.message.reply_text("📭 Нет данных для отчёта.", parse_mode="Markdown")
        return

    # Фильтрация по дате начала
    if start_date:
        iso = start_date.isoformat()
        df = df[df['start_datetime'].astype(str).str.startswith(iso)]
    if start_date and end_date and end_date != start_date:
        # диапазон
        days = pd.date_range(start_date, end_date).date
        mask = df['start_datetime'].astype(str).apply(
            lambda s: any(s.startswith(d.isoformat()) for d in days)
        )
        df = df[mask]

    if df.empty:
        await update.message.reply_text("📭 Нет данных за указанный период.", parse_mode="Markdown")
        return

    # Вычленяем дату и время
    df['Дата']          = df['start_datetime'].astype(str).str[0:10].str.replace('-', '.', regex=False)
    df['Начало поездки'] = df['start_datetime'].astype(str).str[11:16]
    df['Конец поездки']  = df['end_datetime'].astype(str).str[11:16].fillna('-')

    # Продолжительность (чч:мм)
    def calc_duration(row):
        s = row['start_datetime'][:16]
        e = row['end_datetime'][:16] if pd.notnull(row['end_datetime']) else None
        try:
            dt_s = datetime.strptime(s, "%Y-%m-%d %H:%M")
            dt_e = datetime.strptime(e, "%Y-%m-%d %H:%M") if e else None
            if dt_e and dt_e >= dt_s:
                delta = dt_e - dt_s
                h = delta.seconds // 3600
                m = (delta.seconds % 3600) // 60
                return f"{h:02}:{m:02}"
        except:
            pass
        return "-"

    df['Продолжительность'] = df.apply(calc_duration, axis=1)

    final = df[[
        'ФИО', 'Организация', 'Дата',
        'Начало поездки', 'Конец поездки', 'Продолжительность'
    ]]

    # Пишем в Excel с авто‑шириной
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final.to_excel(writer, sheet_name='Отчёт', index=False)
        wb = writer.book
        ws = writer.sheets['Отчёт']
        for i, col in enumerate(final.columns):
            width = max(final[col].astype(str).map(len).max(), len(col)) + 2
            ws.set_column(i, i, width)
    output.seek(0)

    # Формируем имя файла
    if start_date and not end_date:
        fname = f"отчет по поездкам {start_date.strftime('%d.%m.%Y')}.xlsx"
    elif start_date and end_date:
        fname = f"отчет по поездкам {start_date.strftime('%d.%m.%Y')}_{end_date.strftime('%d.%m.%Y')}.xlsx"
    else:
        today = datetime.now().strftime("%d.%m.%Y")
        fname = f"отчет по поездкам {today}.xlsx"

    # Отправляем
    await update.message.reply_document(document=output, filename=fname)
    await update.message.reply_text("📄 Отчёт сформирован и отправлен.", parse_mode="Markdown")
