import os
import sys
import subprocess
import argparse
import re
from datetime import datetime
from collections import defaultdict


def _git(args: list, cwd: str) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git"] + args, cwd=cwd,
            capture_output=True, text=True, timeout=30
        )
        return r.returncode, r.stdout
    except FileNotFoundError:
        print("Error: git not found in PATH.")
        sys.exit(1)


def _check_repo(cwd: str) -> None:
    code, _ = _git(["rev-parse", "--git-dir"], cwd)
    if code != 0:
        print(f"Error: '{cwd}' is not a git repository.")
        sys.exit(1)


def _current_branch(cwd: str) -> str:
    _, out = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return out.strip() or "HEAD"


def _get_commits(cwd: str, count: int | None, since: str | None, since_tag: str | None, branch: str) -> list:
    fmt = "%H%x00%an%x00%ae%x00%ad%x00%s"
    cmd = ["log", f"--format={fmt}", "--date=short"]

    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    elif since:
        cmd += [f"--since={since}"]

    if count and not since_tag:
        cmd += [f"-n{count}"]

    cmd.append(branch)

    _, out = _git(cmd, cwd)
    commits = []
    for line in out.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("\x00")
        if len(parts) < 5:
            continue
        commits.append({
            "hash": parts[0][:7],
            "author": parts[1],
            "date": parts[3],
            "subject": parts[4],
        })
    return commits


# Conventional commit type detection
_CONV_RE = re.compile(r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+?\))?!?:\s*(.+)", re.I)

def _commit_type(subject: str) -> str:
    m = _CONV_RE.match(subject)
    return m.group(1).lower() if m else "other"


def _get_diff(cwd: str, hash_: str) -> str:
    _, out = _git(["show", "--stat", "--no-patch", hash_], cwd)
    return out.strip()


def format_report(commits: list, branch: str, show_diff: bool, group_by_type: bool, cwd: str) -> str:
    if not commits:
        return "# Git Summary\n\n_No commits found._"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Git Summary — `{branch}`", f"_{ts} — {len(commits)} commit(s)_\n"]

    if group_by_type:
        by_type = defaultdict(list)
        for c in commits:
            by_type[_commit_type(c["subject"])].append(c)

        type_order = ["feat", "fix", "perf", "refactor", "docs", "test", "chore", "build", "ci", "other"]
        for t in type_order:
            if t not in by_type:
                continue
            lines.append(f"\n## {t.capitalize()}\n")
            for c in by_type[t]:
                lines.append(f"- **`{c['hash']}`** {c['subject']} _{c['author']}, {c['date']}_")
                if show_diff:
                    diff = _get_diff(cwd, c["hash"])
                    if diff:
                        lines.append(f"\n  ```\n  {diff}\n  ```\n")
    else:
        by_date = defaultdict(list)
        for c in commits:
            by_date[c["date"]].append(c)

        for date in sorted(by_date, reverse=True):
            lines.append(f"\n## {date}\n")
            for c in by_date[date]:
                lines.append(f"- **`{c['hash']}`** {c['subject']} — _{c['author']}_")
                if show_diff:
                    diff = _get_diff(cwd, c["hash"])
                    if diff:
                        lines.append(f"\n  ```\n  {diff}\n  ```\n")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Markdown git changelog/summary.")
    parser.add_argument("--dir",           default=".",    help="Path to git repository (default: .)")
    parser.add_argument("--count",         type=int, default=10, help="Number of commits (default: 10)")
    parser.add_argument("--since",         default=None,   help="Commits after date (YYYY-MM-DD)")
    parser.add_argument("--since-tag",     default=None,   help="Commits after this git tag")
    parser.add_argument("--branch",        default=None,   help="Branch to summarise (default: current)")
    parser.add_argument("--diff",          action="store_true", help="Include file change stats per commit")
    parser.add_argument("--output",        default=None,   help="Save Markdown to file")
    parser.add_argument("--group-by-type", action="store_true", help="Group by conventional commit type")
    args = parser.parse_args()

    cwd = os.path.abspath(args.dir)
    _check_repo(cwd)

    branch = args.branch or _current_branch(cwd)
    commits = _get_commits(cwd, args.count, args.since, args.since_tag, branch)
    report  = format_report(commits, branch, args.diff, args.group_by_type, cwd)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Saved: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
