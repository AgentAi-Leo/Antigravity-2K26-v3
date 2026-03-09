import os
import argparse
import sys
import json
import subprocess
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from google.oauth2 import service_account  # type: ignore

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def get_secret(project_id, secret_id):
    try:
        res = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret_id}"],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except:
        pass
    return None

def authenticate(credentials_path):
    creds = None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Centralized token path for all Google integrations
    token_path = os.path.abspath(os.path.join(script_dir, "..", "..", "token.json"))
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_content = None
            if os.path.exists(credentials_path):
                with open(credentials_path, 'r') as f:
                    creds_content = f.read()
            else:
                project_id = os.environ.get("GCP_PROJECT_ID", "project-583e8414-7968-4f8c-aeb")
                secret_id = os.environ.get("GCP_SECRET_ID", "DEV-TEST4-GSHEETS")
                creds_content = get_secret(project_id, secret_id)

            if not creds_content:
                raise FileNotFoundError("Google API credentials not found.")

            data = json.loads(creds_content)
            if data.get('type') == 'service_account':
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
                    tmp.write(creds_content)
                    tmp_path = tmp.name
                creds = service_account.Credentials.from_service_account_file(tmp_path, scopes=SCOPES)
                os.unlink(tmp_path)
            else:
                flow = InstalledAppFlow.from_client_config(data, SCOPES)
                creds = flow.run_local_server(port=0, prompt='select_account', open_browser=True)

        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
            
    return creds

def get_or_create_sheet(service, title, fields, share_with=None, creds=None):
    # Search for an existing sheet with this title
    query = f"name = '{title}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
    drive_service = build('drive', 'v3', credentials=creds)
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    if files:
        return files[0]['id']
    else:
        # Create new one
        spreadsheet = {'properties': {'title': title}}
        ss = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        ss_id = ss.get('spreadsheetId')
        
        # Add headers
        if fields:
            body = {'values': [fields]}
            service.spreadsheets().values().update(
                spreadsheetId=ss_id, range='A1',
                valueInputOption='RAW', body=body).execute()
        
        # Share if requested
        if share_with:
            permission = {'type': 'user', 'role': 'writer', 'emailAddress': share_with}
            drive_service.permissions().create(fileId=ss_id, body=permission).execute()
            
        return ss_id

def append_to_sheet(title, values, creds_path, share_with=None):
    creds = authenticate(creds_path)
    service = build('sheets', 'v4', credentials=creds)
    
    # Values as first row if new
    headers = ["Timestamp", "Original File", "Status", "Transcript/Text", "Drive Link"]
    sheet_id = get_or_create_sheet(service, title, headers, share_with, creds)
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp] + values
    
    body = {'values': [row]}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id, range='A1',
        valueInputOption='RAW', body=body).execute()
    
    print(f"✅ Appended to Google Sheet: '{title}'")
    # Write purely parsable sheet ID to stderr for calling scripts
    sys.stderr.write(f"SheetID: {sheet_id}\n")

def main():
    parser = argparse.ArgumentParser(description="Appends a row to a Google Sheet (creates if missing).")
    parser.add_argument("--title", required=True, help="The title of the Google Sheet")
    parser.add_argument("--data", nargs="+", required=True, help="List of values to append")
    parser.add_argument("--credentials", default="credentials.json", help="Path to credentials")
    parser.add_argument("--share-with", help="Email to share with")
    
    args = parser.parse_args()
    append_to_sheet(args.title, args.data, args.credentials, args.share_with)

if __name__ == '__main__':
    main()
