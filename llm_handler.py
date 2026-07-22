import json
from openai import OpenAI
from config import GROQ_API_KEY, LLM_MODEL, LLM_BASE_URL

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
    "Cuando el usuario te pida algo del calendario, usa la funcion correspondiente. "
    "Cuando te pida buscar en Drive, usa search_drive. "
    "Confirma siempre antes de crear eventos. "
    "Si no entendes, pregunta."
)

TOOLS = [
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Crear un evento en el calendario",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Titulo del evento"
                    },
                    "date": {
                        "type": "string",
                        "description": "Fecha YYYY-MM-DD"
                    },
                    "time": {
                        "type": "string",
                        "description": "Hora HH:MM"
                    },
                    "duration_hours": {
                        "type": "number",
                        "description": "Duracion en horas (default 1)"
                    }
                },
                "required": ["summary", "date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_sheet",
            "description": "Leer el contenido de una planilla de Google Sheets y devolverlo",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "ID del archivo en Google Drive"
                    },
                    "range": {
                        "type": "string",
                        "description": "Rango de celdas (ej: 'A1:Z50')"
                    }
                },
                "required": ["file_id"]
            }
        }
    }
]


class LLMHandler:

    def __init__(self):
        self.client = OpenAI(api_key=GROQ_API_KEY, base_url=LLM_BASE_URL)
        self._messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._last_tool_calls = []
        self._last_content = ""

    def send_message(self, text: str) -> str:
        self._messages.append({"role": "user", "content": text})
        return self._cycle()

    def submit_results(self, results: list[dict]) -> str:
        for r in results:
            self._messages.append({
                "role": "tool",
                "tool_call_id": r["tool_call_id"],
                "content": r["content"],
            })
        return self._cycle()

    def _cycle(self) -> str:
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=self._messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        entry = {"role": "assistant", "content": msg.content}
        self._last_tool_calls = list(msg.tool_calls) if msg.tool_calls else []
        self._last_content = msg.content or ""

        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        self._messages.append(entry)
        return self._last_content

    @property
    def tool_calls(self):
        return self._last_tool_calls

    def reset(self):
        self._messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._last_tool_calls = []
        self._last_content = ""
