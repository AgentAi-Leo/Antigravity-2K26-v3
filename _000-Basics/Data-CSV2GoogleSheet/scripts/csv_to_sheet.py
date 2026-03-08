import os
import argparse
import csv
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from google.oauth2 import service_account  # type: ignore

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_secret(project_id, secret_id):
    """Fetches the secret value from Google Secret Manager with bulletproof namespace handling."""
    try:
        import sys
        import os
        import subprocess
        
        # 1. Try local gcloud CLI
        try:
            res = subprocess.run(
                ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret_id}"],
                capture_output=True, text=True, timeout=10
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception as e:
            print(f"DEBUG_INFO: gcloud CLI fallback failed: {e}")

        # 2. Force correct site-packages into sys.path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        venv_base = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".venv"))
        site_pkgs = os.path.join(venv_base, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
        
        if os.path.exists(site_pkgs) and site_pkgs not in sys.path:
            sys.path.insert(0, site_pkgs)
            
        # 3. Advanced Namespace Handling
        try:
            import google.cloud.secretmanager as secretmanager  # type: ignore
        except (ImportError, AttributeError):
            import google  # type: ignore
            google_pkg_path = os.path.join(site_pkgs, "google")
            if os.path.exists(google_pkg_path):
                if not hasattr(google, "__path__"):
                    google.__path__ = [google_pkg_path]
                elif google_pkg_path not in google.__path__:
                    google.__path__.append(google_pkg_path)
            from google.cloud import secretmanager  # type: ignore
            
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        import sys
        print(f"Warning: Could not fetch secret '{secret_id}' from project '{project_id}': {e}")
        return None

def authenticate(credentials_path):
    creds = None
    import json
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, "token.json")
    
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
                print(f"Attempting to fetch credentials from Secret Manager ('{secret_id}')...")
                creds_content = get_secret(project_id, secret_id)

            if not creds_content:
                raise FileNotFoundError("Credentials not found.")

            try:
                data = json.loads(creds_content)
                if data.get('type') == 'service_account':
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
                        tmp.write(creds_content)
                        tmp_path = tmp.name
                    creds = service_account.Credentials.from_service_account_file(tmp_path, scopes=SCOPES)
                    os.unlink(tmp_path)
                    return creds
                
                print("\n--- ACTION REQUIRED ---")
                print("This skill requires Google account authorization.")
                print("A browser window should open automatically.")
                print("-----------------------\n")
                
                flow = InstalledAppFlow.from_client_config(data, SCOPES)
                creds = flow.run_local_server(port=0, prompt='select_account', open_browser=True)
            except Exception as e:
                raise ValueError(f"Failed to process credentials data: {e}")

        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
            
    return creds

def csv_to_sheet(csv_file, title, creds_path):
    # Determine title from filename if not provided
    if not title:
        base_name = os.path.basename(csv_file)
        title = os.path.splitext(base_name)[0]
        
    print(f"Reading CSV file: {csv_file}")
    rows = []
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
    except UnicodeDecodeError:
        # Fallback to ansi/latin-1 if utf-8 fails
        with open(csv_file, 'r', newline='', encoding='latin-1') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
    if not rows:
        print("Warning: The CSV file is empty.")
        rows = [["(Empty File)"]]
        
    print(f"Successfully read {len(rows)} rows.")

    try:
        creds = authenticate(creds_path)
    except Exception as e:
        print(f"Authentication Error: {e}")
        return

    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # 1. Create a new Spreadsheet
        spreadsheet = {
            'properties': {'title': title}
        }
        
        print(f"Creating Google Sheet: '{title}'...")
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId,spreadsheetUrl').execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        
        print(f"✅ Created successfully: {spreadsheet_url}")
        
        # 2. Add the CSV data to the sheet starting at A1
        print(f"Uploading {len(rows)} rows of data...")
        body = {'values': rows}
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range='A1',
            valueInputOption='USER_ENTERED', body=body).execute()
        
        print(f"✅ Data updated: {result.get('updatedCells')} cells appended.")
        print("\nAll done!")
        print(f"🔗 Access your sheet here: {spreadsheet_url}")
        
        # Automatically open the new sheet in the user's default browser
        import webbrowser
        try:
            print("Opening sheet in your browser...")
            webbrowser.open(spreadsheet_url)
        except Exception as e:
            pass

    except Exception as e:
        print(f"An error occurred calling the Google Sheets API: {e}")

def main():
    parser = argparse.ArgumentParser(description="Uploads a CSV file to a new Google Sheet.")
    parser.add_argument("file", help="Path to your CSV file", nargs="?", default="")
    parser.add_argument("--file", dest="file_opt", help="Path to your CSV file (alternative)")
    parser.add_argument("--title", help="Optional: Override the title of the new Google Sheet")
    parser.add_argument("--credentials", default="credentials.json", help="Path to your Google API JSON credentials")
    
    args = parser.parse_args()
    file_path = args.file_opt if args.file_opt else args.file
    
    if not file_path or not os.path.exists(file_path):
        print(f"Error: Could not find CSV file at '{file_path}'")
        return
        
    csv_to_sheet(file_path, args.title, args.credentials)

if __name__ == '__main__':
    main()
