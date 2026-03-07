import os
import sys
import json
import re
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime


def _expand_env(s: str) -> str:
    """Replace $VAR_NAME with environment variable values."""
    return re.sub(r"\$([A-Z_][A-Z0-9_]*)", lambda m: os.environ.get(m.group(1), m.group(0)), s)


def _substitute(obj, fn):
    """Recursively apply fn to all string values in a dict/list."""
    if isinstance(obj, dict):
        return {k: _substitute(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute(i, fn) for i in obj]
    if isinstance(obj, str):
        return fn(obj)
    return obj


def run_test(test: dict, timeout: int, verbose: bool) -> dict:
    method   = test.get("method", "GET").upper()
    url      = _expand_env(test.get("url", ""))
    headers  = _substitute(test.get("headers", {}), _expand_env)
    body     = test.get("body")
    expect_status = test.get("expect_status")
    expect_contains = test.get("expect_body_contains")
    name     = test.get("name", url)

    if "Content-Type" not in headers and body:
        headers["Content-Type"] = "application/json"

    payload = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)

    start = time.monotonic()
    result = {"name": name, "method": method, "url": url, "passed": False,
              "status": None, "latency_ms": None, "error": None, "body_snippet": None}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - start) * 1000
            status = resp.status
            body_bytes = resp.read()
            body_text = body_bytes.decode("utf-8", errors="replace")

            result["status"] = status
            result["latency_ms"] = round(elapsed)
            if verbose:
                result["body_snippet"] = body_text[:300]

            ok = True
            if expect_status is not None and status != expect_status:
                ok = False
                result["error"] = f"Expected status {expect_status}, got {status}"
            if expect_contains and expect_contains not in body_text:
                ok = False
                result["error"] = (result["error"] or "") + f' Body missing: "{expect_contains}"'

            result["passed"] = ok

    except urllib.error.HTTPError as e:
        elapsed = (time.monotonic() - start) * 1000
        result["status"] = e.code
        result["latency_ms"] = round(elapsed)
        result["passed"] = (expect_status == e.code)
        if not result["passed"]:
            result["error"] = f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        result["error"] = str(e)

    return result


def format_report(results: list, verbose: bool) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    lines = [f"# API Test Report", f"_{ts} — {passed}/{total} passed_\n"]
    lines.append("| Test | Method | Status | Latency | Result |")
    lines.append("|---|---|---|---|---|")

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        status = str(r["status"]) if r["status"] else "—"
        latency = f"{r['latency_ms']}ms" if r["latency_ms"] else "—"
        err = f" — {r['error']}" if r["error"] else ""
        lines.append(f"| {r['name']} | `{r['method']}` | {status} | {latency} | {icon}{err} |")

    if verbose:
        for r in results:
            if r.get("body_snippet"):
                lines.append(f"\n### {r['name']} — Response\n```\n{r['body_snippet']}\n```")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HTTP API tests from a JSON test suite.")
    parser.add_argument("--tests",     required=True,              help="Path to JSON test suite file")
    parser.add_argument("--output",    default=None,               help="Save Markdown report to file")
    parser.add_argument("--timeout",   type=int,   default=30,     help="Request timeout per call (seconds)")
    parser.add_argument("--verbose",   action="store_true",        help="Include response body snippets")
    parser.add_argument("--fail-fast", action="store_true",        help="Stop on first failure")
    args = parser.parse_args()

    if not os.path.exists(args.tests):
        print(f"Error: '{args.tests}' not found.")
        sys.exit(1)

    with open(args.tests, "r", encoding="utf-8") as f:
        tests = json.load(f)

    results = []
    for test in tests:
        r = run_test(test, args.timeout, args.verbose)
        results.append(r)
        status = "✅" if r["passed"] else "❌"
        print(f"{status} {r['name']} — {r['status']} ({r['latency_ms']}ms)")
        if args.fail_fast and not r["passed"]:
            break

    report = format_report(results, args.verbose)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nSaved: {args.output}")
    else:
        print(f"\n{report}")

    passed = sum(1 for r in results if r["passed"])
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
