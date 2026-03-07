import os
import sys
import subprocess
import argparse
import json
from datetime import datetime


def _run(cmd: list, cwd: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def _md_table(headers: list, rows: list) -> str:
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    widths = [max(w, 3) for w in widths]
    def fmt(row):
        return "| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([fmt(headers), sep] + [fmt(r) for r in rows])


def audit_python(project_dir: str, security: bool) -> str:
    lines = [f"## Python Dependencies — `{project_dir}`\n"]
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")

    # Outdated
    code, out, err = _run([sys.executable, "-m", "pip", "list", "--outdated", "--format=json"], project_dir)
    if code == 0 and out.strip():
        try:
            pkgs = json.loads(out)
            if pkgs:
                rows = [[p["name"], p["version"], p["latest_version"]] for p in pkgs]
                lines.append("### Outdated Packages\n")
                lines.append(_md_table(["Package", "Installed", "Latest"], rows))
            else:
                lines.append("### Outdated Packages\n\nAll packages up to date. ✅")
        except json.JSONDecodeError:
            lines.append(f"### Outdated Packages\n\nCould not parse output:\n```\n{out}\n```")
    else:
        lines.append(f"### Outdated Packages\n\nCould not run pip: `{err.strip()}`")

    # Security
    if security:
        lines.append("\n### Security Vulnerabilities\n")
        code, out, err = _run([sys.executable, "-m", "pip_audit", "--format=markdown"], project_dir)
        if code == -1:
            # pip-audit not installed — fall back to pip check
            code2, out2, _ = _run([sys.executable, "-m", "pip", "check"], project_dir)
            if code2 == 0:
                lines.append("No broken requirements detected via `pip check`. ✅\n")
                lines.append("> _Install `pip-audit` for full vulnerability scanning:_\n> `pip install pip-audit`")
            else:
                lines.append(f"```\n{out2}\n```")
        else:
            lines.append(out if out.strip() else "No vulnerabilities found. ✅")

    return "\n\n".join(lines)


def audit_node(project_dir: str, security: bool) -> str:
    lines = [f"## Node.js Dependencies — `{project_dir}`\n"]
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")

    # Outdated
    code, out, err = _run(["npm", "outdated", "--json"], project_dir)
    if out.strip():
        try:
            pkgs = json.loads(out)
            if pkgs:
                rows = [[name, info.get("current","?"), info.get("wanted","?"), info.get("latest","?")] for name, info in pkgs.items()]
                lines.append("### Outdated Packages\n")
                lines.append(_md_table(["Package", "Current", "Wanted", "Latest"], rows))
            else:
                lines.append("### Outdated Packages\n\nAll packages up to date. ✅")
        except json.JSONDecodeError:
            lines.append(f"### Outdated Packages\n\n```\n{out}\n```")
    elif code == -1:
        lines.append(f"### Outdated Packages\n\n`npm` not found in PATH.")
    else:
        lines.append("### Outdated Packages\n\nAll packages up to date. ✅")

    if security:
        lines.append("\n### Security Vulnerabilities\n")
        code2, out2, _ = _run(["npm", "audit", "--json"], project_dir)
        try:
            data = json.loads(out2)
            vulns = data.get("vulnerabilities", {})
            if vulns:
                rows = [[name, info.get("severity","?"), info.get("title", "-")] for name, info in vulns.items()]
                lines.append(_md_table(["Package", "Severity", "Title"], rows))
            else:
                lines.append("No vulnerabilities found. ✅")
        except Exception:
            lines.append(f"```\n{out2[:2000]}\n```")

    return "\n\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Python or Node.js dependencies.")
    parser.add_argument("--dir",         default=".",  help="Project root directory (default: .)")
    parser.add_argument("--output",      default=None, help="Save Markdown report to file")
    parser.add_argument("--no-security", action="store_true", help="Skip security scan")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.dir)
    if not os.path.isdir(project_dir):
        print(f"Error: '{project_dir}' is not a directory.")
        sys.exit(1)

    security = not args.no_security

    # Detect project type
    has_python = any(os.path.exists(os.path.join(project_dir, f))
                     for f in ["requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"])
    has_node   = os.path.exists(os.path.join(project_dir, "package.json"))

    if not has_python and not has_node:
        print("No Python or Node.js project markers found (requirements.txt / package.json).")
        sys.exit(1)

    report_parts = []
    if has_python:
        report_parts.append(audit_python(project_dir, security))
    if has_node:
        report_parts.append(audit_node(project_dir, security))

    report = "\n\n---\n\n".join(report_parts)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Saved: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
