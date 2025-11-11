from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json

SERVICE_ACCOUNT_FILE = "../SECRET/service_account.json"

SCOPES = ['https://www.googleapis.com/auth/drive']

def list_drive_files():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    results = service.files().list(
        pageSize=10,
        fields="files(id, name)"
    ).execute()

    items = results.get('files', [])
    if not items:
        print("Aucun fichier trouvé.")
    else:
        print("Fichiers trouvés :")
        for item in items:
            print(f"{item['name']} → ID: {item['id']}")

async def download_file(file_id, destination):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    request = service.files().export_media(
        fileId=file_id,
        mimeType='text/csv'
    )

    fh = io.FileIO(destination, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

if __name__ == '__main__':
    list_drive_files()
    download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","ernestien.csv")
