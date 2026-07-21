import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

if not os.path.exists(CREDENTIALS_FILE):
    print(f"No encontre {CREDENTIALS_FILE}")
    print("1. Anda a https://console.cloud.google.com/")
    print("2. Crea un proyecto o selecciona uno existente")
    print("3. Habilita Calendar API, Drive API y Sheets API")
    print("4. Ve a Credenciales > Crear credenciales > ID de cliente OAuth")
    print("5. Tipo: Aplicacion de escritorio")
    print("6. Descarga el JSON y guardalo como 'credentials.json'")
    print("En la misma carpeta que este script.")
    exit(1)

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0, open_browser=True)

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print(f"Autenticacion exitosa! Token guardado en {TOKEN_FILE}")
print("Ya podes cerrar el navegador.")
