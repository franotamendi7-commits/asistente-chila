import logging
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import TIMEZONE, BRIEFING_TIME, CHAT_ID
from calendar_handler import get_events
from llm_handler import LLMHandler

logger = logging.getLogger(__name__)


def _do_briefing(bot):
    today = date.today().isoformat()
    try:
        events_text = get_events(today)
        llm = LLMHandler()
        prompt = (
            f"Hoy es {today}. Estos son los eventos del dia:\n\n"
            f"{events_text}\n\n"
            f"Hace un resumen claro y breve en espanol argentino. "
            f"Si no hay eventos, decilo tranquilo."
        )
        llm.send_message(prompt)

        for _ in range(3):
            if not llm.tool_calls:
                break
            llm.submit_results([])

        text = llm._last_content or events_text
        msg = f"☀️ Buenos dias! Resumen del dia:\n\n{text}"
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"Error en briefing: {e}", exc_info=True)
        try:
            bot.send_message(
                chat_id=CHAT_ID,
                text="⚠️ No pude generar el resumen de hoy.",
            )
        except Exception:
            pass


def start_scheduler(application):
    if not CHAT_ID:
        logger.warning("CHAT_ID no configurado, no se inicia scheduler")
        return

    hour, minute = BRIEFING_TIME.split(":")
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        _do_briefing,
        CronTrigger(hour=int(hour), minute=int(minute), timezone=TIMEZONE),
        args=[application.bot],
        id="daily_briefing",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info(f"Briefing diario programado a las {BRIEFING_TIME} ARG")
