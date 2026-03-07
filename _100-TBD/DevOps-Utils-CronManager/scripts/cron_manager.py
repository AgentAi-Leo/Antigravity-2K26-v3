import os
import sys
import re
import subprocess
import argparse
from datetime import datetime


def _get_crontab() -> str:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        # No crontab yet is fine
        return ""
    return result.stdout


def _set_crontab(content: str) -> None:
    result = subprocess.run(["crontab", "-"], input=content, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error setting crontab: {result.stderr.strip()}")
        sys.exit(1)


def _list_jobs(crontab: str) -> None:
    lines = crontab.splitlines()
    if not lines or not any(l.strip() and not l.startswith("#") for l in lines):
        print("No cron jobs configured.")
        return
    print(f"{'#':>3}  {'Schedule':<20}  {'Label / Command'}")
    print("─" * 70)
    i = 0
    label_buffer = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            label_buffer = ""
            continue
        if stripped.startswith("#"):
            label_buffer = stripped.lstrip("#").strip()
            continue
        # It's a cron entry
        parts = stripped.split(None, 5)
        if len(parts) >= 6:
            schedule = " ".join(parts[:5])
            command = parts[5]
            i += 1
            label = f"[{label_buffer}] " if label_buffer else ""
            print(f"{i:>3}  {schedule:<20}  {label}{command[:50]}")
        label_buffer = ""


def _add_job(crontab: str, expression: str, command: str, label: str | None) -> str:
    lines = crontab.splitlines()
    new_lines = []
    if label:
        new_lines.append(f"# {label}")
    new_lines.append(f"{expression} {command}")
    return "\n".join(lines + new_lines) + "\n"


def _remove_jobs(crontab: str, label: str | None, match: str | None) -> tuple[str, int]:
    lines = crontab.splitlines()
    result = []
    removed = 0
    skip_next = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if skip_next:
            skip_next = False
            removed += 1
            continue
        if stripped.startswith("#"):
            # Check if next non-empty line matches
            comment_text = stripped.lstrip("#").strip()
            # Peek ahead
            next_job = None
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith("#"):
                    next_job = lines[j]
                    break
            if label and label.lower() in comment_text.lower():
                skip_next = True  # skip the comment AND the next job line
                removed += 1
                continue
            if match and next_job and match.lower() in next_job.lower():
                skip_next = True
                removed += 1
                continue
        else:
            if match and match.lower() in stripped.lower():
                removed += 1
                continue
        result.append(line)
    return "\n".join(result) + "\n", removed


def _validate_cron(expression: str) -> bool:
    parts = expression.split()
    return len(parts) == 5


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage macOS/Linux cron jobs.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--list",      action="store_true")
    action.add_argument("--add",       nargs=2, metavar=("CRON_EXPR", "COMMAND"),
                        help="e.g. --add '0 9 * * *' 'python3 backup.py'")
    action.add_argument("--remove",    action="store_true")
    parser.add_argument("--label",     default=None, help="Tag/comment for job")
    parser.add_argument("--match",     default=None, help="Match string in command (for --remove)")
    args = parser.parse_args()

    crontab = _get_crontab()

    if args.list:
        _list_jobs(crontab)

    elif args.add:
        expr, command = args.add
        if not _validate_cron(expr):
            print(f"Error: '{expr}' is not a valid cron expression (needs 5 parts: min hr dom mon dow)")
            sys.exit(1)
        new_crontab = _add_job(crontab, expr, command, args.label)
        _set_crontab(new_crontab)
        label_str = f" [{args.label}]" if args.label else ""
        print(f"✅  Added cron job{label_str}: {expr}  {command}")

    elif args.remove:
        if not args.label and not args.match:
            parser.error("--remove requires --label or --match")
        new_crontab, count = _remove_jobs(crontab, args.label, args.match)
        if count == 0:
            print("No matching jobs found.")
        else:
            _set_crontab(new_crontab)
            print(f"✅  Removed {count} cron job(s).")


if __name__ == "__main__":
    main()
