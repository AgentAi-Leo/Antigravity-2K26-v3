import os
import google.auth
print("Checking Application Credentials...")
print(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")
print(f"GCP_SECRET_ID: {os.environ.get('GCP_SECRET_ID')}")
