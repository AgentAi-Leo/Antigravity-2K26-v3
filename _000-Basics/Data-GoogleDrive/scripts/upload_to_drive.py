import os
import argparse
import sys
import subprocess
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.http import MediaFileUpload  # type: ignore
from google.oauth2 import service_account  # type: ignore

# Scopes for Google Drive and Sheets (shared credentials)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def get_secret(project_id, secret_id):
    """Fetches the secret value from Google Secret Manager."""
    try:
        # 1. Try local gcloud CLI first
        res = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret_id}"],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception as e:
        print(f"DEBUG_INFO: gcloud CLI fallback failed: {e}")

    # 2. Try Python SDK fallback
    try:
        from google.cloud import secretmanager  # type: ignore
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        return None

def authenticate(credentials_path):
    creds = None
    import json
    
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
                print(f"Fetching credentials from Secret Manager ('{secret_id}')...")
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
                print(f"INFO: Authenticated as Service Account: {data.get('client_email')}")
                print("IMPORTANT: If you don't see your files, ensure your destination folder is SHARED with this email.")
            else:
                flow = InstalledAppFlow.from_client_config(data, SCOPES)
                creds = flow.run_local_server(port=0, prompt='select_account', open_browser=True)

        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
            
    return creds

def get_or_create_folder(service, folder_path):
    """Recursively traverses/creates a folder path on Google Drive."""
    parts = [p for p in folder_path.split('/') if p]
    parent_id = 'root'
    
    for part in parts:
        query = f"name = '{part}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            parent_id = files[0]['id']
        else:
            print(f"Creating folder: '{part}'...")
            file_metadata = {
                'name': part,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            parent_id = folder.get('id')
            
    return parent_id

def upload_file(file_path, folder_path, creds_path, share_with=None):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    try:
        creds = authenticate(creds_path)
        service = build('drive', 'v3', credentials=creds)
        
        # 1. Resolve parent folder
        parent_id = 'root'
        if folder_path:
            parent_id = get_or_create_folder(service, folder_path)
            
        # 2. Upload file
        file_name = os.path.basename(file_path)
        print(f"Uploading '{file_name}' to Drive...")
        
        file_metadata = {
            'name': file_name,
            'parents': [parent_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        file_id = file.get('id')
        web_link = file.get('webViewLink')
        
        print(f"✅ Upload successful!")
        print(f"ID: {file_id}")
        print(f"🔗 Link: {web_link}")
        
        # Write purely parsable link, folder ID, and file ID to stderr for calling scripts
        import sys
        sys.stderr.write(f"Link: {web_link}\n")
        sys.stderr.write(f"FolderID: {parent_id}\n")
        sys.stderr.write(f"FileID: {file_id}\n")

        # 3. Handle Auto-sharing
        if share_with:
            print(f"Sharing file with: {share_with}...")
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': share_with
            }
            service.permissions().create(fileId=file_id, body=permission).execute()
            print(f"✅ Shared successfully.")

        return web_link

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Uploads a file to Google Drive with categorization.")
    parser.add_argument("--file", required=True, help="Local path to the file to upload")
    parser.add_argument("--folder", help="Destination folder path (e.g. AI-Audio/Podcasts)")
    parser.add_argument("--credentials", default="credentials.json", help="Path to Google API credentials")
    parser.add_argument("--share-with", help="Email address to share the uploaded file with")
    
    args = parser.parse_args()
    upload_file(args.file, args.folder, args.credentials, args.share_with)

if __name__ == '__main__':
    main()
