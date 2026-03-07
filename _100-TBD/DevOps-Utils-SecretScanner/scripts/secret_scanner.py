import os
import sys
import re
import math
import argparse
import fnmatch
from datetime import datetime
from collections import defaultdict


# ---------------------------------------------------------------------------
# Secret patterns — (label, compiled regex)
# ---------------------------------------------------------------------------
PATTERNS = [
    ("AWS Access Key",        re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key",        re.compile(r"(?i)aws.{0,20}secret.{0,20}[\'\"][0-9a-zA-Z/+]{40}[\'\"]")),
    ("OpenAI API Key",        re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("Anthropic API Key",     re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}")),
    ("GitHub PAT",            re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("Google API Key",        re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Stripe Secret Key",     re.compile(r"sk_live_[0-9a-zA-Z]{24,}")),
    ("Bearer Token",          re.compile(r"(?i)bearer\s+[a-zA-Z0-9\-_\.]{20,}")),
    ("Private Key Block",     re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("Password in code",      re.compile(r"(?i)(?:password|passwd|pwd|secret|api_key)\s*[:=]\s*[\'\"][^\'\"]{6,}[\'\"]")),
    ("JWT Token",             re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}")),
]

# File extensions to scan
SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".env.local",
    ".sh", ".bash", ".zsh", ".yaml", ".yml", ".json", ".toml",
    ".rb", ".go", ".php", ".java", ".kt", ".swift", ".cs",
    ".tf", ".tfvars", ".cfg", ".ini", ".conf", ".config",
}

DEFAULT_EXCLUDES = {".git", "node_modules", "__pycache__", "_libs", "dist", "build", ".venv", "venv"}


# ---------------------------------------------------------------------------
# Shannon entropy for high-entropy string detection
# ---------------------------------------------------------------------------
def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = defaultdict(int)
    for c in s:
        freq[c] += 1
    n = len(s)
    return -sum((f / n) * math.log2(f / n) for f in freq.values())


# Regex to find candidate high-entropy strings (quoted or bare alphanumeric runs)
_ENTROPY_RE = re.compile(r"['\"]([a-zA-Z0-9+/=_\-]{20,})['\"]")


def _high_entropy_strings(line: str, threshold: float) -> list:
    return [m.group(1) for m in _ENTROPY_RE.finditer(line)
            if _shannon_entropy(m.group(1)) >= threshold]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_directory(root: str, excludes: set, entropy_threshold: float, extensions: set | None) -> list:
    """
    Returns list of findings: [{"file", "line", "pattern", "snippet"}]
    """
    findings = []
    root = os.path.abspath(root)

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in-place
        dirnames[:] = [d for d in dirnames if d not in excludes]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if extensions and ext not in extensions:
                continue
            if not extensions and ext not in SCAN_EXTENSIONS and filename not in {".env", ".envrc"}:
                continue

            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root)

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    for lineno, line in enumerate(f, start=1):
                        # Pattern matching
                        for label, pattern in PATTERNS:
                            if pattern.search(line):
                                snippet = line.strip()[:120]
                                findings.append({
                                    "file": rel_path, "line": lineno,
                                    "pattern": label, "snippet": snippet
                                })

                        # High-entropy strings
                        for s in _high_entropy_strings(line, entropy_threshold):
                            findings.append({
                                "file": rel_path, "line": lineno,
                                "pattern": f"High-entropy string (entropy≥{entropy_threshold:.1f})",
                                "snippet": f"...{s[:40]}..."
                            })

            except (PermissionError, IsADirectoryError):
                continue

    return findings


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------

def format_report(findings: list, root: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Secret Scanner Report", f"_Scanned: `{root}` at {ts}_\n"]

    if not findings:
        lines.append("## ✅ No secrets found.\n")
        return "\n".join(lines)

    lines.append(f"## ⚠️ {len(findings)} Finding(s)\n")
    lines.append("| File | Line | Pattern | Snippet |")
    lines.append("|---|---|---|---|")
    for f in findings:
        snippet = f["snippet"].replace("|", "\\|")
        lines.append(f"| `{f['file']}` | {f['line']} | {f['pattern']} | `{snippet[:80]}` |")

    lines.append("\n> **Action:** Rotate any confirmed secrets immediately. Do not push to version control.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Scan source directories for accidentally committed secrets.")
    parser.add_argument("--dir",        default=".",  help="Directory to scan (default: .)")
    parser.add_argument("--output",     default=None, help="Save Markdown report to file")
    parser.add_argument("--exclude",    nargs="*",    default=list(DEFAULT_EXCLUDES), help="Directory names to skip")
    parser.add_argument("--entropy",    type=float,   default=3.8, help="Shannon entropy threshold (default: 3.8)")
    parser.add_argument("--extensions", nargs="*",    default=None, help="Limit to file extensions (e.g. .py .js)")
    args = parser.parse_args()

    root = os.path.abspath(args.dir)
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory.")
        sys.exit(1)

    excludes = set(args.exclude or [])
    extensions = set(args.extensions) if args.extensions else None

    print(f"Scanning: {root}")
    findings = scan_directory(root, excludes, args.entropy, extensions)
    report = format_report(findings, root)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Saved: {args.output}")
    else:
        print(report)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
