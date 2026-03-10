import os
import argparse
import sys
import json
import subprocess
import datetime
import tempfile
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from google.oauth2 import service_account  # type: ignore

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

HEADERS = ["Batch ID", "#", "Timestamp", "Original File", "Status", "Transcription", "Usage", "Preview", "Copy Link", "Notes-1", "Notes-2", "Google Drive Folder", "FolderID", "FileID", "SheetID", "Sharing With"]

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

def _sheet_cache_path(title):
    """Return a temp file path used to cache the sheet ID for a given title."""
    import hashlib
    safe = hashlib.md5(title.encode()).hexdigest()
    return os.path.join(tempfile.gettempdir(), f"sheet_cache_{safe}.txt")

def get_or_create_sheet(service, title, fields, share_with=None, creds=None):
    # 1) Check local cache first (avoids Drive API eventual-consistency issues
    #    where a just-created sheet isn't findable via files.list yet)
    cache_file = _sheet_cache_path(title)
    if os.path.exists(cache_file):
        cached_id = open(cache_file).read().strip()
        if cached_id:
            try:
                # Verify the cached sheet still exists
                service.spreadsheets().get(spreadsheetId=cached_id, fields='spreadsheetId').execute()
                return cached_id
            except Exception:
                pass  # Cache stale — fall through to search/create

    # 2) Search Drive for an existing sheet with this title
    query = f"name = '{title}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
    drive_service = build('drive', 'v3', credentials=creds)
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    if files:
        sheet_id = files[0]['id']
        # Cache it for subsequent files in the same batch
        with open(cache_file, 'w') as f:
            f.write(sheet_id)
        return sheet_id
    else:
        # 3) Create new sheet
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
            try:
                drive_service.permissions().create(fileId=ss_id, body=permission).execute()
            except Exception as share_err:
                print(f"⚠️ Warning: Could not share Google Sheet with {share_with}. You may need to share it manually. Error: {share_err}")
        
        # Cache the new sheet ID so the next file in the batch finds it instantly
        with open(cache_file, 'w') as f:
            f.write(ss_id)
            
        return ss_id

def append_to_sheet(title, values, creds_path, share_with=None, batch_id="", batch_seq="", batch_summary=False,
                    drive_folder_name="", folder_id="", file_id="", sheet_id_value="", sharing_with_email="",
                    usage=""):
    creds = authenticate(creds_path)
    service = build('sheets', 'v4', credentials=creds)
    
    sheet_id = get_or_create_sheet(service, title, HEADERS, share_with, creds)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = None
    
    if batch_summary:
        # Summary row: values should be ["N files", "X total words"] or similar
        summary_text = ", ".join(values) if values else "Batch complete"
        row = [
            batch_id or "—",
            "—",
            timestamp,
            f"✅ BATCH COMPLETE: {summary_text}",
            "—",
            "",
            ""
        ]
        body = {'values': [row]}
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range='A1',
            valueInputOption='RAW', body=body).execute()
        print(f"✅ Summary row appended to Google Sheet: '{title}'")
    else:
        # Build Drive Link columns:
        #   Col G "Preview"    = clickable preview  (=HYPERLINK(view_url, "📁 Open"))
        #   Col H "Copy Link"  = plain URL for copy-paste
        drive_link = values[3] if len(values) > 3 else ""
        if drive_link and drive_link.startswith("http"):
            open_formula = f'=HYPERLINK("{drive_link}","📁 Open")'
            # Quick Save: plain URL (not HYPERLINK) so user can copy-paste into any browser.
            # Google Sheets wraps HYPERLINK clicks through google.com/url redirect which
            # bypasses Chrome's save dialog and downloads to inaccessible cache.
            import re
            _fid_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_link) or re.search(r'[?&]id=([a-zA-Z0-9_-]+)', drive_link)
            if _fid_match:
                _file_id = _fid_match.group(1)
                save_url = f"https://drive.google.com/file/d/{_file_id}/view"
            else:
                save_url = drive_link
            row_values = list(values[:3]) + [open_formula, save_url]
        else:
            row_values = list(values)
        
        row = [
            batch_id or "—",
            batch_seq or "—",
            timestamp,
        ] + row_values
        
        # Insert Usage after Transcription (index 5 in row → insert at position 6)
        # row so far: [BatchID, #, Timestamp, OrigFile, Status, Transcript, Preview, CopyLink]
        # After insert: [BatchID, #, Timestamp, OrigFile, Status, Transcript, Usage, Preview, CopyLink]
        row.insert(6, usage)
        
        # Cols J & K (indices 9 & 10) are Notes-1 and Notes-2.
        while len(row) < 11:
            row.append("")
        # Cols L-P (indices 11-15): metadata columns
        row.append(drive_folder_name)  # L: Google Drive Folder
        row.append(folder_id)          # M: FolderID
        row.append(file_id)            # N: FileID
        # SheetID: the script itself knows the sheet_id; use it directly
        row.append(sheet_id_value or sheet_id)  # O: SheetID
        row.append(sharing_with_email or (share_with or ""))  # P: Sharing With
        body = {'values': [row]}
        # Use USER_ENTERED so =HYPERLINK formulas are interpreted
        # Retry once if append fails (first file after sheet creation can be flaky)
        import time
        for attempt in range(2):
            try:
                result = service.spreadsheets().values().append(
                    spreadsheetId=sheet_id, range='A1',
                    valueInputOption='USER_ENTERED', body=body).execute()
                print(f"✅ Appended to Google Sheet: '{title}'")
                break
            except Exception as append_err:
                if attempt == 0:
                    print(f"⚠️ Append attempt 1 failed, retrying in 2s: {append_err}")
                    time.sleep(2)
                else:
                    print(f"❌ Append failed after retry: {append_err}")
                    raise
    
    # Auto-resize column widths to fit content, EXCEPT Transcript/Text (col F = index 5)
    # HEADERS: A=BatchID, B=#, C=Timestamp, D=OrigFile, E=Status, F=Transcript, G=Preview, H=CopyLink
    try:
        resize_requests = []
        
        # 0) Parse appended row to add hover notes for long text (>20 chars)
        if result and 'updates' in result and 'updatedRange' in result['updates']:
            import re
            match = re.search(r'([A-Z]+)(\d+)', result['updates']['updatedRange'])
            if match:
                row_idx = int(match.group(2)) - 1
                for col_idx, cell_value in enumerate(row):
                    val_str = str(cell_value)
                    # Add note to cells with >1 chars (skip formulas, BatchID/Timestamp/Copy Link/Notes/Metadata ID columns)
                    # Indices: 0=BatchID, 2=Timestamp, 8=CopyLink, 9=Notes-1, 10=Notes-2, 12=FolderID, 13=FileID, 14=SheetID
                    if len(val_str) > 1 and not val_str.startswith('=') and col_idx not in (0, 2, 8, 9, 10, 12, 13, 14):
                        resize_requests.append({
                            'updateCells': {
                                'range': {
                                    'sheetId': 0,
                                    'startRowIndex': row_idx,
                                    'endRowIndex': row_idx + 1,
                                    'startColumnIndex': col_idx,
                                    'endColumnIndex': col_idx + 1
                                },
                                'rows': [{'values': [{'note': val_str}]}],
                                'fields': 'note'
                            }
                        })

        # 1) Auto-resize columns A-E (indices 0-4), G-P (indices 6-16)
        #    Col F (Transcription, index 5) gets a fixed width below
        auto_ranges = [(0, 5), (6, 16)]
        for col_range in auto_ranges:
            resize_requests.append({  # type: ignore[arg-type]
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': col_range[0],
                        'endIndex': col_range[1]
                    }
                }
            })
        # Set Transcription (col F = index 5) to fixed 250px width
        resize_requests.append({  # type: ignore[arg-type]
            'updateDimensionProperties': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 5,
                    'endIndex': 6
                },
                'properties': {'pixelSize': 250},
                'fields': 'pixelSize'
            }
        })
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': resize_requests}
        ).execute()
        
        # Add 20px padding to auto-resized columns so content isn't cut off
        sheet_meta = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields='sheets.data.columnMetadata.pixelSize'
        ).execute()
        col_widths = [c.get('pixelSize', 100) for c in
                      sheet_meta['sheets'][0]['data'][0].get('columnMetadata', [])]
        pad_requests = []
        skip_col = 5  # Transcription — already fixed
        for start, end in auto_ranges:
            for i in range(start, min(end, len(col_widths))):
                if i == skip_col:
                    continue
                # Extra padding overrides: 
                # - Notes columns (indices 9, 10): 75px
                # - Timestamp column (index 2): 35px (+15px standard)
                # - Others: 20px
                if i in (9, 10):
                    pad = 75
                elif i == 2:
                    pad = 35
                else:
                    pad = 20
                pad_requests.append({
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': 0,
                            'dimension': 'COLUMNS',
                            'startIndex': i,
                            'endIndex': i + 1
                        },
                        'properties': {'pixelSize': col_widths[i] + pad},  # type: ignore[operator]
                        'fields': 'pixelSize'
                    }
                })
        if pad_requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': pad_requests}
            ).execute()
    except Exception:
        pass  # Non-critical — don't fail the upload if resize fails
    
    # Write purely parsable sheet ID to stderr for calling scripts
    sys.stderr.write(f"SheetID: {sheet_id}\n")

def main():
    parser = argparse.ArgumentParser(description="Appends a row to a Google Sheet (creates if missing).")
    parser.add_argument("--title", required=True, help="The title of the Google Sheet")
    parser.add_argument("--data", nargs="+", required=True, help="List of values to append")
    parser.add_argument("--credentials", default="credentials.json", help="Path to credentials")
    parser.add_argument("--share-with", help="Email to share with")
    parser.add_argument("--batch-id", default="", help="Batch identifier for grouping rows")
    parser.add_argument("--batch-seq", default="", help="Sequence number within the batch")
    parser.add_argument("--batch-summary", action="store_true", help="Append a summary row instead of a data row")
    # Metadata columns
    parser.add_argument("--drive-folder-name", default="", help="Google Drive folder name")
    parser.add_argument("--folder-id", default="", help="Google Drive folder ID")
    parser.add_argument("--file-id", default="", help="Google Drive file ID")
    parser.add_argument("--sheet-id-value", default="", help="Google Sheet ID")
    parser.add_argument("--sharing-with-email", default="", help="Email the file was shared with")
    parser.add_argument("--usage", default="", help="Usage stats (e.g. '355 words, 2114 characters')")
    
    args = parser.parse_args()
    append_to_sheet(args.title, args.data, args.credentials, args.share_with,
                    batch_id=args.batch_id, batch_seq=args.batch_seq, batch_summary=args.batch_summary,
                    drive_folder_name=args.drive_folder_name, folder_id=args.folder_id,
                    file_id=args.file_id, sheet_id_value=args.sheet_id_value,
                    sharing_with_email=args.sharing_with_email, usage=args.usage)

if __name__ == '__main__':
    main()
