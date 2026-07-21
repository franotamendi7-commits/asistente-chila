import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Sos Chila, un asistente personal argentino que vive en Telegram. "
    "Respondé siempre en español argentino, de forma natural, directa y con buena onda. "
    "No uses emojis. "
    "Tus capacidades:\n"
    "- Leer eventos del calendario de Google Calendar\n"
    "- Crear eventos en el calendario\n"
    "- Buscar archivos en Google Drive por nombre\n"
    "- Leer el contenido de planillas de Google Sheets\n"
    "- Tener conversaciones naturales\n\n"
    "Cuando el usuario te pida algo del calendario, usá la funcion correspondiente. "
    "Cuando te pida buscar en Drive, usá search_drive. "
    "Confirmá siempre antes de crear eventos. "
    "Si no entendés, preguntá."
)

TOOLS = [
    {
        "function_declarations": [
            {
                "name": "get_calendar_events",
                "description": "Obtener eventos del calendario para una fecha especifica",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Fecha en formato YYYY-MM-DD. Por defecto hoy."
                        },
                        "days": {
                            "type": "integer",
                            "description": "Cantidad de dias a partir de la fecha (0=solo ese dia)"
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "create_calendar_event",
                "description": "Crear un evento en el calendario",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Titulo del evento"},
                        "date": {"type": "string", "description": "Fecha YYYY-MM-DD"},
                        "time": {"type": "string", "description": "Hora HH:MM"},
                        "duration_hours": {
                            "type": "number",
                            "description": "Duracion en horas (default 1)"
                        }
                    },
                    "required": ["summary", "date", "time"]
                }
            },
            {
                "name": "search_drive",
                "description": "Buscar archivos en Google Drive por nombre",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Nombre del archivo a buscar"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "read_sheet",
                "description": "Leer el contenido de una planilla de Google Sheets y devolver un resumen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "ID del archivo en Google Drive"
                        },
                        "range": {
                            "type": "string",
                            "description": "Rango de celdas (ej: 'A1:Z100')"
                        }
                    },
                    "required": ["file_id"]
                }
            }
        ]
    }
]

SYSTEM_TOOLS_MAP = {
    "get_calendar_events": "calendar",
    "create_calendar_event": "calendar",
    "search_drive": "drive",
    "read_sheet": "drive",
}


class GeminiHandler:

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)

    def send_message(self, text: str) -> genai.types.GenerateContentResponse:
        return self.chat.send_message(text)

    def resend_with_tool_result(self, tool_responses: list[dict]) -> genai.types.GenerateContentResponse:
        parts = []
        for resp in tool_responses:
            parts.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=resp["name"],
                        response={"result": resp["result"]},
                    )
                )
            )
        return self.chat.send_message(parts)

    def reset(self):
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
