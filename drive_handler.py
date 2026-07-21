from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH, setup_google_files

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def _get_drive_service():
    setup_google_files()
    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    return build("drive", "v3", credentials=creds)


def _get_sheets_service():
    setup_google_files()
    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    return build("sheets", "v4", credentials=creds)


def search_file(query: str) -> str:
    service = _get_drive_service()
    results = service.files().list(
        q=f"name contains '{query}' and trashed=false",
        fields="files(id, name, mimeType)",
    ).execute()

    files = results.get("files", [])
    if not files:
        return f"No encontre archivos con '{query}' en Drive."

    lines = []
    for f in files[:5]:
        tipo = "Sheet" if "spreadsheet" in f.get("mimeType", "") else f.get("mimeType", "Archivo")
        lines.append(f"- {f['name']} ({tipo}) ID: {f['id']}")

    return "\n".join(lines)


def read_sheet(file_id: str, range_str: str = "A1:Z100") -> str:
    service = _get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=file_id,
        range=range_str,
    ).execute()

    values = result.get("values", [])
    if not values:
        return "La planilla esta vacia o no se pudo leer."

    lines = []
    for row in values[:50]:
        lines.append(" | ".join(str(cell) for cell in row))

    return "\n".join(lines)
