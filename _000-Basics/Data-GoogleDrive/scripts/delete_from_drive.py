import os
import sys
import argparse
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

from upload_to_drive import authenticate

def delete_file(file_id, credentials_path="credentials.json"):
    """
    Deletes a file from Google Drive using its file ID.
    Used primarily for cleaning up orphaned files when a batch process is cancelled.
    """
    try:
        creds = authenticate(credentials_path)
        service = build('drive', 'v3', credentials=creds)
        
        service.files().delete(fileId=file_id).execute()
        print(f"✅ Successfully deleted file ID: {file_id}")
        return True
    except Exception as e:
        print(f"Error deleting file ID {file_id}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Deletes a specific file from Google Drive by ID.")
    parser.add_argument("--id", required=True, help="The Google Drive File ID to delete")
    parser.add_argument("--credentials", default="credentials.json", help="Path to Google API credentials")
    
    args = parser.parse_args()
    delete_file(args.id, args.credentials)

if __name__ == '__main__':
    main()
