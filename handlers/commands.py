
from telegram.ext import CommandHandler
from core.register import register_command as _register_fn
from core.trip import trip_command as _trip_fn, return_command as _return_fn
from core.report import generate_report as _report_fn

# Оборачиваем ваши функции‑обработчики в объекты CommandHandler:
register_command = CommandHandler("register", _register_fn)
trip_command     = CommandHandler("trip",     _trip_fn)
return_command   = CommandHandler("return",   _return_fn)
report_command   = CommandHandler("report",   _report_fn)
