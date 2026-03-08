import sys
import os

print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")
print(f"Current Directory: {os.getcwd()}")
print(f"Script Path: {__file__}")

print("\n--- sys.path ---")
for p in sys.path:
    print(p)

print("\n--- google packages ---")
try:
    import google
    print(f"google.__path__: {google.__path__}")
except Exception as e:
    print(f"Could not import 'google': {e}")

try:
    from google.cloud import secretmanager
    print("SUCCESS: Imported google.cloud.secretmanager")
except Exception as e:
    print(f"ERROR: Could not import 'google.cloud.secretmanager': {e}")

try:
    import pkg_resources
    installed_packages = sorted(["%s==%s" % (i.key, i.version) for i in pkg_resources.working_set])
    print("\n--- Installed Packages (via pkg_resources) ---")
    for pkg in installed_packages:
        if "google" in pkg:
            print(pkg)
except Exception as e:
    print(f"\nCould not list packages: {e}")
