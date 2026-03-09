import os
import argparse
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
        
        # 1. First, try the local gcloud CLI as it uses the active user session directly
        # This bypasses the need for explicit Application Default Credentials in Python
        try:
            res = subprocess.run(
                ["gcloud", "secrets", "versions", "access", "latest", f"--secret={secret_id}"],
                capture_output=True, text=True, timeout=10
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception as e:
            print(f"DEBUG_INFO: gcloud CLI fallback failed: {e}")

        # 2. Force the correct site-packages into sys.path
        # We look for the .venv relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Centralized token path for all Google integrations
        token_path = os.path.abspath(os.path.join(script_dir, "..", "..", "token.json"))
        venv_base = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".venv"))
        site_pkgs = os.path.join(venv_base, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
        
        if os.path.exists(site_pkgs) and site_pkgs not in sys.path:
            sys.path.insert(0, site_pkgs)
            
        # 3. Advanced Namespace Handling
        # Some environments have 'google' but not 'google.cloud' due to namespace clashing
        try:
            import google.cloud.secretmanager as secretmanager  # type: ignore
        except (ImportError, AttributeError):
            # Manually extend the google path if it's broken
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
        print(f"DEBUG_INFO: sys.executable={sys.executable}")
        
        # Safe limit for linting
        if hasattr(sys, 'path') and getattr(sys, 'path'):
            path_str = str(sys.path)
            print(f"DEBUG_INFO: sys.path={path_str[:300]}...")  # type: ignore
        return None

def authenticate(credentials_path):
    creds = None
    import json
    
    # Check for local token first
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid token, we need client secrets to perform flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Try to get credentials content
            creds_content = None
            if os.path.exists(credentials_path):
                with open(credentials_path, 'r') as f:
                    creds_content = f.read()
            else:
                # Fallback to Secret Manager
                project_id = os.environ.get("GCP_PROJECT_ID", "project-583e8414-7968-4f8c-aeb")
                secret_id = os.environ.get("GCP_SECRET_ID", "DEV-TEST4-GSHEETS")
                print(f"Local '{credentials_path}' not found. Attempting to fetch from Secret Manager ('{secret_id}')...")
                creds_content = get_secret(project_id, secret_id)

            if not creds_content:
                raise FileNotFoundError(f"Credentials not found locally at '{credentials_path}' and could not be retrieved from Secret Manager.")

            # Load credentials from content
            try:
                data = json.loads(creds_content)
                # Check if Service Account
                if data.get('type') == 'service_account':
                    # Temporary file for service account (google-auth requires a file path)
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
                        tmp.write(creds_content)
                        tmp_path = tmp.name
                    creds = service_account.Credentials.from_service_account_file(tmp_path, scopes=SCOPES)
                    os.unlink(tmp_path)
                    print(f"INFO: Authenticated as Service Account: {data.get('client_email')}")
                    print("IMPORTANT: If you don't see your sheets, ensure you share the parent folder with this email (if applicable) or wait for auto-sharing.")
                    return creds
                
                # Otherwise OAuth Desktop flow
                print("\n--- ACTION REQUIRED ---")
                print("This skill requires Google account authorization.")
                print("A browser window should open automatically.")
                print("If it doesn't, please copy the URL displayed here into your browser.")
                print("-----------------------\n")
                
                # Use prompt='select_account' to force the user to pick their email address rather than defaulting
                flow = InstalledAppFlow.from_client_config(data, SCOPES)
                creds = flow.run_local_server(port=0, prompt='select_account', open_browser=True)
            except Exception as e:
                raise ValueError(f"Failed to process credentials data: {e}")

        # Save the token for the next run
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
            
    return creds

def generate_sheet(title, fields, creds_path, share_with=None):
    try:
        creds = authenticate(creds_path)
    except Exception as e:
        print(f"Authentication Error: {e}")
        return

    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # 1. Create a new Spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        
        print(f"Creating Google Sheet: '{title}'...")
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId,spreadsheetUrl').execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        
        print(f"✅ Created successfully: {spreadsheet_url}")
        
        # 2. Add the fields as the first row if fields are provided
        if fields:
            print(f"Injecting {len(fields)} fields as column headers...")
            
            body = {
                'values': [
                    fields  # List of strings becomes the first row
                ]
            }
            
            # We assume the default sheet name is 'Sheet1'
            range_name = 'A1'
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='RAW', body=body).execute()
            
            print(f"✅ Headers updated: {result.get('updatedCells')} cells appended.")
            
        print("\nAll done!")
        print(f"🔗 Access your sheet here: {spreadsheet_url}")
        
        # Automatically open the new sheet in the user's default browser
        import webbrowser
        try:
            print("Opening sheet in your browser...")
            webbrowser.open(spreadsheet_url)
        except Exception as e:
            print(f"Note: Could not automatically open browser ({e}).")

        # 3. Handle Auto-sharing
        if share_with:
            print(f"Sharing sheet with: {share_with}...")
            # Use drive service for permissions
            drive_service = build('drive', 'v3', credentials=creds)
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': share_with
            }
            drive_service.permissions().create(fileId=spreadsheet_id, body=permission).execute()
            print(f"✅ Shared successfully.")

    except Exception as e:
        print(f"An error occurred calling the Google Sheets API: {e}")

def main():
    parser = argparse.ArgumentParser(description="Create a Google Sheet with specified column headers.")
    parser.add_argument("--title", required=True, help="The title of the new Google Sheet")
    parser.add_argument("--fields", nargs="+", default=[], help="List of column names (e.g. 'First Name' 'Email' 'Phone')")
    parser.add_argument("--credentials", default="credentials.json", help="Path to your Google API JSON credentials (default: credentials.json in current dir)")
    parser.add_argument("--share-with", help="Email address to share the new sheet with")
    
    args = parser.parse_args()
    
    generate_sheet(args.title, args.fields, args.credentials, args.share_with)

if __name__ == '__main__':
    main()
