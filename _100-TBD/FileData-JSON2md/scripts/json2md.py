import json
import os
import sys
import argparse


def _is_flat(obj: dict) -> bool:
    """All values are primitives (not dict/list)."""
    return all(not isinstance(v, (dict, list)) for v in obj.values())


def _table_from_records(records: list) -> str:
    """Array of flat dicts → Markdown table."""
    headers = list(dict.fromkeys(k for r in records for k in r))
    rows = [[str(r.get(h, "")) for h in headers] for r in records]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    widths = [max(w, 3) for w in widths]
    def fmt(row):
        return "| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([fmt(headers), sep] + [fmt(r) for r in rows])


def _render(value, depth: int, max_depth: int, indent: int = 0) -> list:
    """Recursively render a JSON value as Markdown lines."""
    lines = []
    prefix = "  " * indent

    if max_depth is not None and depth > max_depth:
        lines.append(f"{prefix}*(depth limit reached)*")
        return lines

    if isinstance(value, dict):
        if not value:
            lines.append(f"{prefix}*(empty object)*")
        else:
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    heading = "#" * min(depth + 2, 6)
                    lines.append(f"\n{heading} {k}\n")
                    lines.extend(_render(v, depth + 1, max_depth, 0))
                else:
                    lines.append(f"{prefix}- **{k}**: {v}")

    elif isinstance(value, list):
        if not value:
            lines.append(f"{prefix}*(empty list)*")
        elif all(isinstance(i, dict) and _is_flat(i) for i in value):
            # Homogeneous flat records → table
            lines.append(_table_from_records(value))
        else:
            for i, item in enumerate(value, 1):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}{i}.")
                    lines.extend(_render(item, depth + 1, max_depth, indent + 1))
                else:
                    lines.append(f"{prefix}- {item}")

    else:
        lines.append(f"{prefix}`{value}`")

    return lines


def convert(data, title: str, max_depth: int | None, output_path: str | None) -> None:
    lines = [f"# {title}\n"]
    lines.extend(_render(data, depth=1, max_depth=max_depth))
    output = "\n".join(lines).strip() + "\n"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved: {output_path}")
    else:
        print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert JSON to Markdown.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",  help="Input .json file path")
    group.add_argument("--json",   help="Inline JSON string")
    parser.add_argument("--output", default=None, help="Output .md file (default: stdout)")
    parser.add_argument("--depth",  type=int, default=None, help="Max nesting depth to render")
    parser.add_argument("--title",  default=None, help="Top-level heading")
    args = parser.parse_args()

    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found.")
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            raw = f.read()
        title = args.title or os.path.splitext(os.path.basename(args.input))[0]
    else:
        raw = args.json
        title = args.title or "JSON"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}")
        sys.exit(1)

    convert(data, title, args.depth, args.output)


if __name__ == "__main__":
    main()
