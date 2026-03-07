import os
import sys
import subprocess
import argparse
import shlex
import time
from datetime import datetime


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str, log_path: str | None) -> None:
    print(msg)
    if log_path:
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def run(cmd: str, timeout: int, cwd: str, log_path: str | None, dry_run: bool) -> int:
    header = f"[{_timestamp()}] CMD: {cmd}"
    _log(header, log_path)
    _log(f"[{_timestamp()}] CWD: {cwd}", log_path)

    if dry_run:
        _log(f"[{_timestamp()}] DRY-RUN — command not executed.", log_path)
        return 0

    start = time.monotonic()
    try:
        result = subprocess.run(
            shlex.split(cmd),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout if timeout > 0 else None,
        )
        elapsed = time.monotonic() - start
        status = "success" if result.returncode == 0 else "FAILED"
        _log(f"[{_timestamp()}] EXIT: {result.returncode} ({status}) | elapsed: {elapsed:.2f}s", log_path)

        if result.stdout.strip():
            _log("STDOUT:", log_path)
            for line in result.stdout.splitlines():
                _log(f"  {line}", log_path)
        else:
            _log("STDOUT: (none)", log_path)

        if result.stderr.strip():
            _log("STDERR:", log_path)
            for line in result.stderr.splitlines():
                _log(f"  {line}", log_path)
        else:
            _log("STDERR: (none)", log_path)

        return result.returncode

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        _log(f"[{_timestamp()}] TIMEOUT after {elapsed:.1f}s — process killed.", log_path)
        return 124  # standard timeout exit code
    except FileNotFoundError as e:
        _log(f"[{_timestamp()}] ERROR: command not found — {e}", log_path)
        return 127
    except Exception as e:
        _log(f"[{_timestamp()}] ERROR: {e}", log_path)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a script safely with timeout and logging.")
    parser.add_argument("--cmd",      required=True,             help="Command string to execute")
    parser.add_argument("--timeout",  type=int,   default=60,    help="Seconds before killing (0=no limit, default: 60)")
    parser.add_argument("--log",      default=None,              help="File path to append log output")
    parser.add_argument("--cwd",      default=os.getcwd(),       help="Working directory (default: current dir)")
    parser.add_argument("--dry-run",  action="store_true",       help="Print command without executing")
    args = parser.parse_args()

    exit_code = run(args.cmd, args.timeout, args.cwd, args.log, args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
