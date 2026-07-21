import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_TOKEN, CHAT_ID
from gemini_handler import GeminiHandler
from calendar_handler import get_events, create_event
from drive_handler import search_file, read_sheet
from health import start_health_server
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

gemini = GeminiHandler()

TOOL_HANDLERS = {
    "get_calendar_events": lambda args: get_events(
        date_str=args.get("date", ""),
        days=args.get("days", 0),
    ),
    "create_calendar_event": lambda args: create_event(
        summary=args.get("summary", ""),
        date_str=args.get("date", ""),
        time_str=args.get("time", ""),
        duration_hours=args.get("duration_hours", 1.0),
    ),
    "search_drive": lambda args: search_file(query=args.get("query", "")),
    "read_sheet": lambda args: read_sheet(
        file_id=args.get("file_id", ""),
        range_str=args.get("range", "A1:Z100"),
    ),
}


def run_tool_loop(handler: GeminiHandler, max_turns: int = 5) -> str:
    for _ in range(max_turns):
        try:
            response = handler.chat.last
        except Exception:
            break

        if not response.candidates:
            break

        parts = response.candidates[0].content.parts
        has_tool_calls = False
        tool_results = []

        for part in parts:
            if part.function_call:
                has_tool_calls = True
                fn = part.function_call
                name = fn.name
                args = {k: v for k, v in fn.args.items()}
                logger.info(f"Tool call: {name}({args})")

                func = TOOL_HANDLERS.get(name)
                if func:
                    try:
                        result = func(args)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Funcion {name} no encontrada"

                tool_results.append({"name": name, "result": result})

        if not has_tool_calls:
            return response.text

        response = handler.resend_with_tool_result(tool_results)

    try:
        return response.text
    except Exception:
        return "No pude procesar eso. Preguntame de nuevo."


async def start(update: Update, context):
    await update.message.reply_text(
        "Hola! Soy Chila, tu asistente personal.\n"
        "Preguntame que tenes en el calendario, agendo reuniones, "
        "busco archivos en Drive, o simplemente charlamos."
    )


async def reset(update: Update, context):
    gemini.reset()
    await update.message.reply_text("Listo, empezamos de nuevo.")


async def handle_message(update: Update, context):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    logger.info(f"Mensaje: {user_text}")

    try:
        response = gemini.send_message(user_text)
        text = run_tool_loop(gemini)
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        await update.message.reply_text(
            "Upa, tuve un problema. Decime /reset y probamos de nuevo."
        )


def main():
    start_health_server()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    start_scheduler(app)

    logger.info("Chila iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
