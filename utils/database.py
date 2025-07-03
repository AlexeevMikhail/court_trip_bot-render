import os
import psycopg2
from datetime import datetime, date, time, timedelta

DEBUG_MODE = False
PG_DSN     = os.getenv("DATABASE_URL")  # e.g. postgresql://postgres:Пароль@…:6543/postgres

# Границы рабочего дня
WORKDAY_START = time(9, 0)
WORKDAY_END   = time(18, 0)

def get_now() -> datetime:
    """
    Возвращает текущее московское время (UTC+3) без секунд и микросекунд.
    """
    now_utc = datetime.utcnow()
    now_msk = now_utc + timedelta(hours=3)
    return now_msk.replace(second=0, microsecond=0)

def get_conn():
    """Создаёт и возвращает новое соединение с Postgres."""
    return psycopg2.connect(PG_DSN)

def init_db():
    """Инициализирует схему: создаёт таблицы, если их нет."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
          user_id BIGINT PRIMARY KEY,
          full_name TEXT NOT NULL,
          is_active BOOLEAN DEFAULT TRUE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS trips (
          id SERIAL PRIMARY KEY,
          user_id BIGINT REFERENCES employees(user_id),
          organization_id TEXT,
          organization_name TEXT,
          start_datetime TIMESTAMP,
          end_datetime TIMESTAMP,
          status TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS vacations (
          id SERIAL PRIMARY KEY,
          user_id BIGINT REFERENCES employees(user_id),
          start_date DATE,
          end_date DATE
        );
        """)
        conn.commit()

def is_registered(user_id: int) -> bool:
    """Проверяет, есть ли активный сотрудник с таким user_id."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM employees WHERE user_id = %s", (user_id,))
        return cur.fetchone() is not None

def adjust_to_work_hours(dt: datetime) -> datetime | None:
    """
    Переносит <09:00→09:00>, запрещает после 18:00 и в выходные.
    В DEBUG_MODE всегда возвращает dt без изменений.
    """
    if DEBUG_MODE:
        return dt
    if dt.weekday() >= 5:      # Saturday=5, Sunday=6
        return None
    if dt.time() < WORKDAY_START:
        return dt.replace(hour=9, minute=0)
    if dt.time() <= WORKDAY_END:
        return dt
    return None

def save_trip_start(user_id: int, org_id: str, org_name: str) -> bool:
    """
    Начинает новую поездку, если сотрудник зарегистрирован и не в пути.
    Возвращает True, если успешно; False, если уже есть in_progress или вне рабочего времени.
    """
    now = adjust_to_work_hours(get_now())
    if not now:
        return False

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
          "SELECT 1 FROM trips WHERE user_id = %s AND status = 'in_progress'",
          (user_id,)
        )
        if cur.fetchone():
            return False

        cur.execute("""
          INSERT INTO trips
            (user_id, organization_id, organization_name, start_datetime, status)
          VALUES (%s, %s, %s, %s, 'in_progress')
        """, (user_id, org_id, org_name, now))
        conn.commit()
        return True

def end_trip_db(user_id: int) -> bool:
    """
    Завершает текущую поездку (in_progress) для user_id.
    Возвращает True, если найдена и обновлена запись.
    """
    now = get_now()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          UPDATE trips
          SET end_datetime = %s, status = 'completed'
          WHERE user_id = %s AND status = 'in_progress'
        """, (now, user_id))
        updated = cur.rowcount
        conn.commit()
        return updated > 0

def close_expired_trips():
    """
    Автоматически закрывает все оставшиеся in_progress (по расписанию APScheduler).
    Если now < start → end = start + 1 min, иначе end = now.
    """
    now = get_now()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, start_datetime FROM trips WHERE status = 'in_progress'")
        rows = cur.fetchall()
        for trip_id, start in rows:
            end = (start + timedelta(minutes=1)) if now <= start else now
            cur.execute("""
              UPDATE trips
              SET end_datetime = %s, status = 'completed'
              WHERE id = %s
            """, (end, trip_id))
        conn.commit()
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Авто‑завершено {len(rows)} поездок.")
