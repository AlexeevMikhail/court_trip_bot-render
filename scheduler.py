import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.database import close_expired_trips

# Обязательно pytz‑таймзона, у неё есть метод normalize()
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=MOSCOW_TZ)

    # Пн–Чт в 18:00 по Москве
    scheduler.add_job(
        close_expired_trips,
        trigger=CronTrigger(
            day_of_week='mon-thu',
            hour=18,
            minute=0,
            timezone=MOSCOW_TZ
        ),
        id='close_trips_mon_thu',
        replace_existing=True,
    )
    print("📆 Автозакрытие Пн–Чт в 18:00 добавлено.")

    # Пт в 16:45 по Москве
    scheduler.add_job(
        close_expired_trips,
        trigger=CronTrigger(
            day_of_week='fri',
            hour=16,
            minute=45,
            timezone=MOSCOW_TZ
        ),
        id='close_trips_fri',
        replace_existing=True,
    )
    print("📆 Автозакрытие Пт в 16:45 добавлено.")

    scheduler.start()
    print("✅ Планировщик запущен.")
