import os
import sys
import json
import argparse


def _load_spec(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".yaml", ".yml"}:
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            print("Error: PyYAML required for YAML specs — install with: pip install pyyaml")
            sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _swagger2_to_openapi3(spec: dict) -> dict:
    """Minimal Swagger 2 → OpenAPI 3 path/info normalization."""
    paths = spec.get("paths", {})
    host = spec.get("host", "localhost")
    base = spec.get("basePath", "/")
    spec.setdefault("info", {})
    spec["servers"] = [{"url": f"http://{host}{base}"}]
    return spec


def _method_table(spec: dict) -> list[dict]:
    """Extract all operations into flat list of dicts."""
    ops = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, detail in methods.items():
            if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}:
                ops.append({"method": method.upper(), "path": path, "detail": detail})
    return ops


def _render_params(params: list) -> str:
    if not params:
        return ""
    rows = ["| Name | In | Type | Required | Description |",
            "|---|---|---|---|---|"]
    for p in params:
        schema = p.get("schema", {})
        type_ = schema.get("type", p.get("type", "string"))
        rows.append(f"| `{p.get('name','')}` | {p.get('in','')} | {type_} | "
                    f"{'✅' if p.get('required') else ''} | {p.get('description','')} |")
    return "\n".join(rows)


def _render_responses(responses: dict, include_examples: bool) -> str:
    lines = []
    for code, resp in sorted(responses.items()):
        desc = resp.get("description", "")
        lines.append(f"- **{code}** — {desc}")
        if include_examples:
            content = resp.get("content", {})
            for media, mdata in content.items():
                example = mdata.get("example") or mdata.get("schema", {}).get("example")
                if example:
                    lines.append(f"  ```json\n  {json.dumps(example, indent=2)}\n  ```")
    return "\n".join(lines) if lines else "_No responses defined._"


def generate_docs(spec: dict, tag_filter: str | None, include_examples: bool) -> str:
    info = spec.get("info", {})
    title = info.get("title", "API Reference")
    version = info.get("version", "")
    description = info.get("description", "")
    servers = spec.get("servers", [])

    lines = [f"# {title}", ""]
    if version:
        lines += [f"**Version:** {version}", ""]
    if description:
        lines += [description, ""]
    if servers:
        lines += ["## Base URL", ""]
        for s in servers:
            lines.append(f"- `{s.get('url', '')}`")
        lines.append("")

    ops = _method_table(spec)
    if tag_filter:
        ops = [o for o in ops if tag_filter in o["detail"].get("tags", [])]

    if not ops:
        lines.append("_No operations found._")
        return "\n".join(lines)

    # Group by tag
    by_tag: dict[str, list] = {}
    for op in ops:
        tags = op["detail"].get("tags", ["General"])
        for tag in tags:
            by_tag.setdefault(tag, []).append(op)

    for tag, tag_ops in by_tag.items():
        lines += [f"## {tag}", ""]
        for op in tag_ops:
            d = op["detail"]
            summary = d.get("summary", op["path"])
            op_id = d.get("operationId", "")
            description = d.get("description", "")
            lines += [f"### `{op['method']}` {op['path']}", ""]
            if summary:
                lines += [f"**{summary}**", ""]
            if description:
                lines += [description, ""]
            params = _render_params(d.get("parameters", []))
            if params:
                lines += ["**Parameters:**", "", params, ""]
            resp_md = _render_responses(d.get("responses", {}), include_examples)
            lines += ["**Responses:**", "", resp_md, "", "---", ""]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Markdown API docs from OpenAPI spec.")
    parser.add_argument("--spec",     required=True, help="OpenAPI JSON or YAML spec file")
    parser.add_argument("--output",   default=None,  help="Save Markdown to file")
    parser.add_argument("--examples", action="store_true")
    parser.add_argument("--tag",      default=None,  help="Filter to one tag/group")
    args = parser.parse_args()

    if not os.path.exists(args.spec):
        print(f"Error: '{args.spec}' not found."); sys.exit(1)

    spec = _load_spec(args.spec)
    if "swagger" in spec:
        spec = _swagger2_to_openapi3(spec)

    docs = generate_docs(spec, args.tag, args.examples)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(docs + "\n")
        print(f"Saved: {args.output}")
    else:
        print(docs)


if __name__ == "__main__":
    main()
