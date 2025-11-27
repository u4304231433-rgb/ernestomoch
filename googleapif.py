from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json

SERVICE_ACCOUNT_FILE = "../SECRET/service_account.json"

SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/spreadsheets']

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

async def ajouter_ligne_sheet(spreadsheet_id, range_target="Dico", nouvelle_ligne=[]):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)

    body = {
        'values': [nouvelle_ligne]
    }

    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_target+"!A1",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

async def modifier_ligne_sheet(spreadsheet_id, ligne, range_target="Dico", nouvelle_ligne=[]):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)

    body = {
        'values': [nouvelle_ligne]
    }
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_target+f"!A{ligne+2}:C{ligne+2}", # +1 pour la ligne Francais,+1 car ça commence à 0
        valueInputOption="RAW",
        body={"values": [nouvelle_ligne]}
    ).execute()

async def supprimer_ligne_sheet(spreadsheet_id, ligne, range_target="Dico"):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)

    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_d = {}
    for sheet in sheet_metadata["sheets"]:
        sheet_d[sheet["properties"]["title"]] = sheet["properties"]["sheetId"]
        
    sheet_id = sheet_d[range_target]
    delete_request = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": ligne+1, #éviter la ligne Francais, etc, commence à 0
                        "endIndex": ligne+2
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=delete_request
    ).execute()


if __name__ == '__main__':
    list_drive_files()
    """ajouter_ligne_sheet(
        spreadsheet_id="1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q",
        range_target="Dico!A1",
        nouvelle_ligne=["test", "têst", "éthymologie bla bla"]
    )"""
    #download_file("1dhOPKsrHc8yShN8dJpp3eVmPXlZEL88LvCeYT6MJN0Q","ernestien.csv")
