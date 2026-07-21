import os
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TIMEZONE = "America/Argentina/Buenos_Aires"
BRIEFING_TIME = os.environ.get("BRIEFING_TIME", "08:00")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
GOOGLE_TOKEN_JSON = os.environ.get("GOOGLE_TOKEN_JSON")
GOOGLE_CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", "token.json")

def setup_google_files():
    if GOOGLE_CREDENTIALS_JSON:
        data = json.loads(GOOGLE_CREDENTIALS_JSON)
        with open(GOOGLE_CREDENTIALS_PATH, "w") as f:
            json.dump(data, f)
    if GOOGLE_TOKEN_JSON:
        data = json.loads(GOOGLE_TOKEN_JSON)
        with open(GOOGLE_TOKEN_PATH, "w") as f:
            json.dump(data, f)
