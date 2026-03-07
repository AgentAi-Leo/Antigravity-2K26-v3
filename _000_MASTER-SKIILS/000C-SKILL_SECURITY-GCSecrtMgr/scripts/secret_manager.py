import os
import sys
import subprocess
import argparse


def _run_gcloud(command_args: list, input_data: str | bytes = None, capture=True) -> str:
    """Helper to run gcloud commands and capture output."""
    cmd = ["gcloud", "secrets"] + command_args
    try:
        # If input is provided, pass via stdin (useful for writing secrets securely)
        if input_data is not None:
            if isinstance(input_data, str):
                input_data = input_data.encode()
            res = subprocess.run(cmd, input=input_data, capture_output=capture, check=True)
        else:
            res = subprocess.run(cmd, capture_output=capture, text=True, check=True)
            
        return res.stdout.strip() if capture else ""
        
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        if isinstance(err_msg, bytes):
            err_msg = err_msg.decode(errors="replace")
        print(f"🚨 GCP Secret Manager Error:\n{err_msg}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("🚨 Error: 'gcloud' CLI not found. Please install the Google Cloud SDK.", file=sys.stderr)
        sys.exit(1)


def list_secrets() -> None:
    print("Fetching secrets from GCP...")
    result = _run_gcloud(["list"])
    if not result:
        print("No secrets found in this project.")
    else:
        print("\n" + result)


def get_secret(name: str) -> str:
    """Fetch the latest version payload of a secret."""
    return _run_gcloud(["versions", "access", "latest", f"--secret={name}"])


def set_secret(name: str, value: str | bytes) -> None:
    """Creates the secret if missing, then adds a new version."""
    # Check if secret exists first
    check = subprocess.run(
        ["gcloud", "secrets", "describe", name],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        # Secret doesn't exist, create it
        print(f"Secret '{name}' not found. Creating it...", file=sys.stderr)
        _run_gcloud(["create", name, "--replication-policy=automatic"])
        
    print(f"Adding new version for secret '{name}'...", file=sys.stderr)
    _run_gcloud(["versions", "add", name, "--data-file=-"], input_data=value)
    print("✅ Secret updated successfully.", file=sys.stderr)


def run_injected(injections: list[str], command: str) -> None:
    """
    injections: list of 'SecretName:ENV_VAR'
    Fetches secrets and runs the command with them injected into environment.
    """
    env = os.environ.copy()
    
    print("🔐 Fetching secure context...", file=sys.stderr)
    for inj in injections:
        if ":" not in inj:
            print(f"Error: Injection argument '{inj}' must be format SecretName:ENV_VAR", file=sys.stderr)
            sys.exit(1)
            
        secret_name, env_var = inj.split(":", 1)
        print(f"   ↓ Loading {secret_name} into ${env_var}...", file=sys.stderr)
        
        secret_value = get_secret(secret_name)
        env[env_var] = secret_value
        
    print(f"\n🚀 Running: {command}\n" + "-"*40, file=sys.stderr)
    
    # Run the user's command passing the secure environment
    try:
        subprocess.run(command, shell=True, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Securely manage and inject GCP Cloud Secrets.")
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument("--list", action="store_true", help="List all secrets in the project")
    group.add_argument("--get", metavar="NAME", help="Read the latest value of a secret")
    group.add_argument("--set", metavar="NAME", help="Create or update a secret")
    group.add_argument("--inject", action="append", metavar="NAME:ENV_VAR",
                       help="Inject secret into environment (can be used multiple times)")
                       
    # Options for --get
    parser.add_argument("--reveal", action="store_true", help="Reveal unmasked secret in terminal (use with --get)")
    
    # Options for --set
    parser.add_argument("--value", help="Value to set (use with --set)")
    parser.add_argument("--file", help="File containing value to set (use with --set)")
    
    # Options for --inject
    parser.add_argument("--run", help="Command to run securely (required with --inject)")
    
    args = parser.parse_args()

    if args.list:
        list_secrets()
        
    elif args.get:
        val = get_secret(args.get)
        # If outputting directly to a terminal, mask the secret by default to prevent logging/chat leaks
        if sys.stdout.isatty() and not getattr(args, 'reveal', False):
            if len(val) > 4:
                masked = val[:2] + "*" * (len(val) - 4) + val[-2:]
            else:
                masked = "***MASKED***"
            print(f"🔒 {masked}", file=sys.stderr)
            print("⚠️ Masked for terminal security. Use --reveal or pipe to a file to access raw value.", file=sys.stderr)
        else:
            # Print raw value directly to stdout so it can be piped
            print(val, end="")
        
    elif args.set:
        if args.value is not None:
            set_secret(args.set, args.value)
        elif args.file is not None:
            if not os.path.exists(args.file):
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(1)
            with open(args.file, "rb") as f:
                set_secret(args.set, f.read())
        else:
            parser.error("--set requires either --value or --file")
            
    elif args.inject:
        if not args.run:
            parser.error("--inject requires a --run command")
        run_injected(args.inject, args.run)


if __name__ == "__main__":
    main()
