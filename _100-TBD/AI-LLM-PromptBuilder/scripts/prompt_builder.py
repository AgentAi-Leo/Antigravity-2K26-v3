import os
import sys
import re
import json
import argparse


# ---------------------------------------------------------------------------
# Template loader
# ---------------------------------------------------------------------------

def _load_template(path: str) -> tuple[str, str]:
    """Parse YAML frontmatter + body. Returns (system_prompt, user_body)."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    system_prompt = ""
    body = content

    # Parse frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if fm_match:
        frontmatter = fm_match.group(1)
        body = fm_match.group(2)
        sys_match = re.search(r'^system:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
        if sys_match:
            system_prompt = sys_match.group(1).strip().strip('"').strip("'")

    return system_prompt, body.strip()


def _substitute(text: str, variables: dict) -> str:
    """Replace {{key}} with values from variables dict."""
    for key, val in variables.items():
        text = text.replace(f"{{{{{key}}}}}", val)
    # Warn on unfilled placeholders
    remaining = re.findall(r"\{\{(\w+)\}\}", text)
    for r in remaining:
        print(f"Warning: placeholder '{{{{ {r} }}}}' was not filled.", file=sys.stderr)
    return text


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _format_openai(system: str, user: str) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    return {"messages": messages}


def _format_anthropic(system: str, user: str) -> dict:
    payload = {"messages": [{"role": "user", "content": user}]}
    if system:
        payload["system"] = system
    return payload


def _format_raw(system: str, user: str) -> dict:
    return {"system": system, "user": user}


_FORMATTERS = {
    "openai":    _format_openai,
    "anthropic": _format_anthropic,
    "raw":       _format_raw,
}


# ---------------------------------------------------------------------------
# Template listing
# ---------------------------------------------------------------------------

def list_templates(template_dir: str) -> None:
    if not os.path.isdir(template_dir):
        print(f"No templates directory found at: {template_dir}")
        return
    templates = [f for f in os.listdir(template_dir) if f.endswith(".md")]
    if not templates:
        print("No templates found.")
        return
    for t in sorted(templates):
        print(f"  {t}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build structured LLM prompts from templates.")
    parser.add_argument("--template", default=None, help="Path to .md template file")
    parser.add_argument("--var",  nargs="*", default=[], help="Variables: key=value (repeatable as space-separated)")
    parser.add_argument("--format",  default="openai", choices=["openai", "anthropic", "raw"],
                        help="Output format (default: openai)")
    parser.add_argument("--output",  default=None,   help="Save JSON to file (default: stdout)")
    parser.add_argument("--list",    action="store_true", help="List available templates")
    args = parser.parse_args()

    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

    if args.list:
        list_templates(template_dir)
        return

    if not args.template:
        parser.error("--template is required unless using --list")

    # Parse variables
    variables = {}
    for v in args.var:
        if "=" in v:
            k, _, val = v.partition("=")
            variables[k.strip()] = val
        else:
            print(f"Warning: skipping malformed var '{v}' (expected key=value)", file=sys.stderr)

    system, body = _load_template(args.template)
    system = _substitute(system, variables)
    user   = _substitute(body,   variables)

    formatter = _FORMATTERS[args.format]
    result = formatter(system, user)
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"Saved: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
