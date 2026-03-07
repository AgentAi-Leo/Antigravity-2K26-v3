import os
import sys
import json
import argparse
from datetime import datetime


def load_schema(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_env(path: str) -> dict:
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def validate(schema: dict, env: dict) -> list:
    """Return list of issues."""
    issues = []
    for key, meta in schema.items():
        required = meta.get("required", False)
        default = meta.get("default")
        has_value = key in env and env[key] != ""
        if not has_value:
            if required and default is None:
                issues.append(f"MISSING (required): {key} — {meta.get('description','')}")
            elif required and default:
                issues.append(f"MISSING (using default '{default}'): {key}")
    return issues


def generate_example(schema: dict) -> str:
    lines = [f"# .env.example — generated {datetime.now().strftime('%Y-%m-%d')}", ""]
    for key, meta in schema.items():
        desc = meta.get("description", "")
        example = meta.get("example", meta.get("default", ""))
        required = meta.get("required", False)
        req_tag = "required" if required else "optional"
        lines.append(f"# {desc} [{req_tag}]")
        lines.append(f"{key}={example}")
        lines.append("")
    return "\n".join(lines)


def generate_env(schema: dict) -> str:
    lines = [f"# .env — generated {datetime.now().strftime('%Y-%m-%d')}", ""]
    for key, meta in schema.items():
        default = meta.get("default", "")
        lines.append(f"{key}={default}")
    return "\n".join(lines)


def generate_docs(schema: dict) -> str:
    lines = ["# Environment Variables\n",
             "| Variable | Required | Default | Description |",
             "|---|---|---|---|"]
    for key, meta in schema.items():
        required = "✅" if meta.get("required") else "—"
        default = f"`{meta['default']}`" if meta.get("default") else "—"
        desc = meta.get("description", "")
        lines.append(f"| `{key}` | {required} | {default} | {desc} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create, validate, and document .env files.")
    parser.add_argument("--schema",           required=True,       help="Path to .env.schema.json")
    parser.add_argument("--env",              default=".env",      help="Path to .env file to validate")
    parser.add_argument("--validate",         action="store_true", help="Validate .env against schema")
    parser.add_argument("--generate-example", action="store_true", help="Write .env.example")
    parser.add_argument("--generate-env",     action="store_true", help="Write .env with defaults")
    parser.add_argument("--docs",             action="store_true", help="Output Markdown documentation")
    parser.add_argument("--output",           default=None,        help="Output file path")
    args = parser.parse_args()

    if not os.path.exists(args.schema):
        print(f"Error: schema '{args.schema}' not found.")
        sys.exit(1)

    schema = load_schema(args.schema)

    if args.validate:
        env = load_env(args.env)
        issues = validate(schema, env)
        if issues:
            print(f"❌ Validation failed — {len(issues)} issue(s):\n")
            for issue in issues:
                print(f"  • {issue}")
            sys.exit(1)
        else:
            print(f"✅ .env valid — all required keys present ({len(schema)} variables checked).")

    elif args.generate_example:
        content = generate_example(schema)
        out = args.output or ".env.example"
        with open(out, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"Saved: {out}")

    elif args.generate_env:
        content = generate_env(schema)
        out = args.output or ".env"
        with open(out, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"Saved: {out}")

    elif args.docs:
        content = generate_docs(schema)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content + "\n")
            print(f"Saved: {args.output}")
        else:
            print(content)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
