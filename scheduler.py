from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import TIMEZONE, BRIEFING_TIME, CHAT_ID
from calendar_handler import get_events
from gemini_handler import GeminiHandler
import logging

logger = logging.getLogger(__name__)

gemini = GeminiHandler()


def _do_briefing(bot):
    today = datetime.now().isoformat()[:10]
    try:
        events = get_events(today)
        prompt = (
            f"Resumi los eventos de hoy de forma clara y breve.\n"
            f"Si no hay eventos, decilo igual.\n\n{events}"
        )
        response = gemini.send_message(prompt)
        text = response.text

        # Build the complete message task for tool calls similar to run_tool_loop
        import telegram
        tool_messages = ""
        try:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fn = part.function_call
                    tool_messages += f"\n  -> Llamando {fn.name}({dict(fn.args)})\n"
        except Exception:
            pass

        if tool_messages:
            import bot
            bot.run_tool_loop(gemini, bot)

        text = response.text
        msg = f"☀️ Buenos dias! Aca va el resumen del dia:\n\n{text}"
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"Error en briefing: {e}")
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ No pude generar el resumen de hoy.")
        except Exception:
            pass


def start_scheduler(application):
    if not CHAT_ID:
        logger.warning("CHAT_ID no configurado, no se inicia scheduler")
        return

    hour, minute = BRIEFING_TIME.split(":")
    scheduler = BackgroundScheduler(timezone=TIMEZONE)

    # Briefing diario
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
