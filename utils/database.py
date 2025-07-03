# utils/database.py

import sqlite3
from datetime import datetime, date, time, timedelta

DEBUG_MODE = True   # False — рабочий режим, True — тестовый (отключает проверку рабочих часов)
DB_PATH = 'court_tracking.db'

def get_now() -> datetime:
    """Текущее системное время без секунд и микросекунд."""
    return datetime.now().replace(second=0, microsecond=0)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Сотрудники
    cur.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            user_id      INTEGER PRIMARY KEY,
            full_name    TEXT    NOT NULL,
            is_active    INTEGER DEFAULT 1
        )
    ''')
    # Поездки
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER,
            organization_id TEXT,
            organization_name TEXT,
            start_datetime  DATETIME,
            end_datetime    DATETIME,
            status          TEXT,
            FOREIGN KEY(user_id) REFERENCES employees(user_id)
        )
    ''')
    # Отпуска (если будет нужно)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS vacations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            start_date DATE,
            end_date   DATE,
            FOREIGN KEY(user_id) REFERENCES employees(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def is_registered(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM employees WHERE user_id = ?", (user_id,))
    ok = cur.fetchone() is not None
    conn.close()
    return ok

# Границы рабочего дня
WORKDAY_START = time(9, 0)
WORKDAY_END   = time(18, 0)

def is_workday(d: date) -> bool:
    return d.weekday() < 5  # 0=понедельник … 4=пятница

def adjust_to_work_hours(dt: datetime) -> datetime | None:
    """
    Если DEBUG_MODE=True — всегда возвращает dt.
    Иначе:
      • в выходные — None
      • до 09:00 — возвращает тот же день 09:00
      • между 09:00–18:00 — dt
      • после 18:00 — None
    """
    if DEBUG_MODE:
        return dt
    if not is_workday(dt.date()):
        return None
    if dt.time() < WORKDAY_START:
        return datetime.combine(dt.date(), WORKDAY_START)
    if dt.time() <= WORKDAY_END:
        return dt
    return None

def save_trip_start(user_id: int, org_id: str, org_name: str) -> bool:
    now = adjust_to_work_hours(get_now())
    if not now:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Проверка на уже в пути
    cur.execute(
        "SELECT 1 FROM trips WHERE user_id = ? AND status = 'in_progress'",
        (user_id,)
    )
    if cur.fetchone():
        conn.close()
        return False
    # Вставка новой поездки
    cur.execute('''
        INSERT INTO trips (
            user_id, organization_id, organization_name, start_datetime, status
        ) VALUES (?, ?, ?, ?, 'in_progress')
    ''', (user_id, org_id, org_name, now))
    conn.commit()
    conn.close()
    return True

def end_trip(user_id: int) -> bool:
    """
    Завершает единственную активную поездку user_id:
    ставит end_datetime = сейчас, status='completed'.
    Возвращает True, если была обновлена хотя бы одна строка.
    """
    now = get_now()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        UPDATE trips
        SET end_datetime = ?, status = 'completed'
        WHERE user_id = ? AND status = 'in_progress'
    ''', (now, user_id))
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def close_expired_trips():
    """
    Авто‑закрытие всех незавершённых поездок в базе:
    если now <= start → end = start + 1 мин, иначе end = now.
    """
    now = get_now()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, start_datetime FROM trips WHERE status = 'in_progress'")
    rows = cur.fetchall()
    count = 0
    for trip_id, start_str in rows:
        start_dt = datetime.fromisoformat(start_str).replace(second=0, microsecond=0)
        end_dt = (start_dt + timedelta(minutes=1)) if now <= start_dt else now
        cur.execute('''
            UPDATE trips
            SET end_datetime = ?, status = 'completed'
            WHERE id = ?
        ''', (end_dt, trip_id))
        count += 1
    conn.commit()
    conn.close()
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Авто‑завершено {count} поездок.")
