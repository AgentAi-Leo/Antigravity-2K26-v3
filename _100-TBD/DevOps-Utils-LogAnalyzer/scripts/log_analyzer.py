import os
import sys
import re
import json
import argparse
from collections import Counter, defaultdict
from datetime import datetime


# ── Log parsing ───────────────────────────────────────────────────────────────

LEVEL_PATTERNS = [
    (re.compile(r'\b(ERROR|CRITICAL|FATAL)\b', re.I), "error"),
    (re.compile(r'\b(WARN(?:ING)?)\b', re.I),         "warn"),
    (re.compile(r'\b(INFO)\b', re.I),                  "info"),
    (re.compile(r'\b(DEBUG)\b', re.I),                 "debug"),
]

TIMESTAMP_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})'
)


def _detect_level(line: str) -> str:
    for pattern, level in LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return "info"


def _extract_timestamp(line: str) -> datetime | None:
    m = TIMESTAMP_RE.search(line)
    if m:
        try:
            return datetime.fromisoformat(m.group(1).replace(" ", "T"))
        except ValueError:
            pass
    return None


def _normalize_message(line: str) -> str:
    """Strip timestamps, PIDs, UUIDs for grouping similar messages."""
    s = TIMESTAMP_RE.sub("", line)
    s = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<uuid>', s, flags=re.I)
    s = re.sub(r'\b\d{3,}\b', '<N>', s)
    return s.strip()[:120]


def _parse_lines(lines: list, level_filter: str | None,
                 since: datetime | None, grep: str | None) -> list[dict]:
    parsed = []
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if grep and grep.lower() not in line.lower():
            continue
        level = _detect_level(line)
        if level_filter and level != level_filter:
            continue
        ts = _extract_timestamp(line)
        if since and ts and ts < since:
            continue
        parsed.append({"line": line, "level": level, "ts": ts, "norm": _normalize_message(line)})
    return parsed


# ── Report generation ─────────────────────────────────────────────────────────

LEVEL_ICON = {"error": "🔴", "warn": "🟡", "info": "🔵", "debug": "⚪"}


def _generate_report(parsed: list[dict], top_n: int, source: str) -> str:
    total = len(parsed)
    by_level = Counter(e["level"] for e in parsed)
    freq = Counter(e["norm"] for e in parsed)
    top_messages = freq.most_common(top_n)

    lines = [f"# Log Analysis Report", f"", f"**Source:** `{source}`  |  **Total lines:** {total}", ""]

    # Level summary
    lines += ["## Level Summary", ""]
    for level in ("error", "warn", "info", "debug"):
        count = by_level.get(level, 0)
        if count:
            lines.append(f"- {LEVEL_ICON[level]} **{level.upper()}**: {count}")
    lines.append("")

    # Top recurring messages
    lines += [f"## Top {top_n} Recurring Messages", ""]
    lines += ["| # | Count | Message |", "|---|---|---|"]
    for i, (msg, cnt) in enumerate(top_messages, 1):
        lines.append(f"| {i} | {cnt} | `{msg[:80]}` |")
    lines.append("")

    # Recent errors
    errors = [e for e in parsed if e["level"] == "error"][-20:]
    if errors:
        lines += ["## Recent Errors (last 20)", ""]
        for e in errors:
            ts_str = e["ts"].strftime("%H:%M:%S") if e["ts"] else "??:??:??"
            lines.append(f"- `{ts_str}` {e['line'][:120]}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse and summarize log files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Log file path")
    group.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--level",  default=None, choices=["error", "warn", "info", "debug"])
    parser.add_argument("--top",    type=int, default=10)
    parser.add_argument("--since",  default=None, help="Filter after datetime e.g. '2026-02-23 10:00'")
    parser.add_argument("--grep",   default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    since_dt = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since)
        except ValueError:
            print(f"Error: cannot parse --since '{args.since}'. Use format: 'YYYY-MM-DD HH:MM'")
            sys.exit(1)

    if args.stdin:
        raw_lines = sys.stdin.readlines()
        source = "stdin"
    else:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            raw_lines = f.readlines()
        source = args.input

    parsed = _parse_lines(raw_lines, args.level, since_dt, args.grep)
    report = _generate_report(parsed, args.top, source)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Saved: {args.output}  ({len(parsed)} lines analyzed)")
    else:
        print(report)


if __name__ == "__main__":
    main()
