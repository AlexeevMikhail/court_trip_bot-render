import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, time, timedelta
import pytz

# Тестовый режим — отключает ограничения по рабочему расписанию
DEBUG_MODE = False  
# Подключение к Postgres через URL из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")
# Московский часовой пояс для get_now()
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Рабочие рамки
WORKDAY_START      = time(9,  0)   # 09:00
WORKDAY_END_NORMAL = time(18, 0)   # 18:00 пн–чт
WORKDAY_END_FRIDAY = time(16, 45)  # 16:45 в пятницу

def get_conn():
    """
    Открывает новое соединение к Postgres.
    """
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_now() -> datetime:
    """
    Текущее московское время без tzinfo, без секунд и микросекунд.
    """
    if DEBUG_MODE:
        # локальное системное время (наивное) без секунд и микр.
        return datetime.now().replace(second=0, microsecond=0)
    # UTC -> Moscow
    utc_dt = datetime.now(pytz.utc)
    msk_dt = utc_dt.astimezone(MOSCOW_TZ)
    # отбрасываем tzinfo, секунды и микросекеунды
    return msk_dt.replace(tzinfo=None, second=0, microsecond=0)

def init_db():
    """
    Создает схемы tables employees, trips, vacations в Postgres, если их нет.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
          user_id       BIGINT PRIMARY KEY,
          full_name     TEXT    NOT NULL,
          is_active     BOOLEAN DEFAULT TRUE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS trips (
          id               SERIAL PRIMARY KEY,
          user_id          BIGINT REFERENCES employees(user_id),
          organization_id   TEXT,
          organization_name TEXT,
          start_datetime    TIMESTAMP,
          end_datetime      TIMESTAMP,
          status            TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS vacations (
          id         SERIAL PRIMARY KEY,
          user_id    BIGINT REFERENCES employees(user_id),
          start_date DATE,
          end_date   DATE
        );
        """)
        conn.commit()

def is_registered(user_id: int) -> bool:
    """
    Проверяет, есть ли активный сотрудник с данным user_id.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM employees WHERE user_id = %s", (user_id,))
        return cur.fetchone() is not None

def is_workday(d: date) -> bool:
    """
    Рабочие дни: понедельник (0) — пятница (4).
    """
    return d.weekday() < 5

def adjust_to_work_hours(dt: datetime) -> datetime | None:
    """
    Пн–Чт: начало не раньше 09:00, конец не позже 18:00.
    Пт:   начало не раньше 09:00, конец не позже 16:45.
    Выходные — запрещены (None).
    DEBUG_MODE=True — любые dt разрешены.
    """
    if DEBUG_MODE:
        return dt

    wd = dt.date().weekday()
    if wd >= 5:
        # Суббота или воскресенье
        return None

    # Сдвиг раннего утра на начало рабочего
    if dt.time() < WORKDAY_START:
        return datetime.combine(dt.date(), WORKDAY_START)

    # Верхняя граница для Пт и для Пн–Чт
    end_limit = WORKDAY_END_FRIDAY if wd == 4 else WORKDAY_END_NORMAL
    if dt.time() > end_limit:
        return None

    return dt

def save_trip_start(user_id: int, org_id: str, org_name: str) -> bool:
    """
    Начать новую поездку: проверяем,
    что нет активной in_progress, и вставляем запись.
    """
    now = adjust_to_work_hours(get_now())
    if not now:
        return False

    with get_conn() as conn:
        cur = conn.cursor()
        # Есть ли уже активная поездка?
        cur.execute("""
            SELECT 1 FROM trips
            WHERE user_id = %s AND status = 'in_progress'
        """, (user_id,))
        if cur.fetchone():
            return False

        cur.execute("""
            INSERT INTO trips
              (user_id, organization_id, organization_name, start_datetime, status)
            VALUES (%s, %s, %s, %s, 'in_progress')
        """, (user_id, org_id, org_name, now))
        conn.commit()
    return True

def end_trip(user_id: int) -> bool:
    """
    Завершить текущую поездку: ставим end_datetime = now, status = completed.
    """
    now = get_now()
    with get_conn() as conn:
        cur = conn.cursor()
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
    Авто‑закрытие всех поездок в статусе in_progress:
    если now <= start — end = start+1мин, иначе end = now.
    """
    now = get_now()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, start_datetime
            FROM trips
            WHERE status = 'in_progress'
        """)
        rows = cur.fetchall()

        count = 0
        for row in rows:
            trip_id    = row['id']
            start_dt   = row['start_datetime']
            # обрезаем до минут
            start_dt   = start_dt.replace(second=0, microsecond=0)
            # выбираем конец
            end_dt = start_dt + timedelta(minutes=1) if now <= start_dt else now

            cur.execute("""
                UPDATE trips
                SET end_datetime = %s, status = 'completed'
                WHERE id = %s
            """, (end_dt, trip_id))
            count += 1

        conn.commit()

    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Авто‑завершено {count} поездок.")
