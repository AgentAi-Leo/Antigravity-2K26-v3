import os
import sys
import re
import argparse
import statistics

# ---------------------------------------------------------------------------
# Locate pdfplumber via local libs/ first, then shared _libs/ at skills root
# ---------------------------------------------------------------------------
_script_dir = os.path.dirname(os.path.abspath(__file__))
for _candidate in [
    os.path.join(_script_dir, "..", "libs"),
    os.path.join(_script_dir, "..", "..", "_libs"),
]:
    if os.path.exists(_candidate):
        sys.path.insert(0, os.path.abspath(_candidate))

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not found.\nRun: python3 -m pip install pdfplumber --target _libs/")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_heading(size: float, median: float, scale: float) -> int:
    """Return heading level 1-3, or 0 for body text."""
    if size >= median * (scale + 0.4):
        return 1
    if size >= median * (scale + 0.15):
        return 2
    if size >= median * scale:
        return 3
    return 0


def _table_to_md(table: list) -> str:
    """Convert a pdfplumber table (list of rows) to a Markdown table string."""
    if not table:
        return ""

    # Normalise cells
    rows = [[str(cell).strip() if cell is not None else "" for cell in row] for row in table]
    col_count = max(len(r) for r in rows)
    # Pad short rows
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    header = rows[0]
    body   = rows[1:]

    col_widths = [max(len(header[i]), *(len(r[i]) for r in body) if body else [0]) for i in range(col_count)]
    col_widths = [max(w, 3) for w in col_widths]

    def _fmt_row(row: list) -> str:
        return "| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * w for w in col_widths) + " |"
    lines = [_fmt_row(header), separator] + [_fmt_row(r) for r in body]
    return "\n".join(lines)


def _clean_line(text: str) -> str:
    """Remove control characters and normalise whitespace."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _looks_like_bullet(text: str) -> bool:
    return bool(re.match(r"^[\u2022\u2023\u25e6\u2043\u2219\*\-\+]\s", text))


# ---------------------------------------------------------------------------
# Core converter
# ---------------------------------------------------------------------------

def convert(input_path: str, output_path: str, heading_scale: float = 1.2, extract_tables: bool = True) -> None:
    md_lines = []

    with pdfplumber.open(input_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            # --- Table extraction (before text, to get bounding boxes) ---
            table_bboxes = []
            if extract_tables:
                tables = page.find_tables()
                for tbl in tables:
                    table_bboxes.append(tbl.bbox)
                    extracted = tbl.extract()
                    if extracted:
                        md_lines.append("")
                        md_lines.append(_table_to_md(extracted))
                        md_lines.append("")

            # --- Text extraction ---
            # Collect all char font sizes for median calculation
            chars = page.chars
            sizes = [c["size"] for c in chars if c.get("size")]
            if not sizes:
                continue
            median_size = statistics.median(sizes)

            # Walk word-level objects grouped into lines
            words = page.extract_words(keep_blank_chars=False, extra_attrs=["size", "fontname"])
            if not words:
                continue

            # Group words into lines by top-y coordinate (within 2pt tolerance)
            lines_by_y: dict = {}
            for word in words:
                # Skip words inside table bounding boxes
                in_table = any(
                    tbl[0] <= word["x0"] and word["x1"] <= tbl[2] and
                    tbl[1] <= word["top"] and word["bottom"] <= tbl[3]
                    for tbl in table_bboxes
                )
                if in_table:
                    continue

                y_key = round(word["top"] / 2) * 2  # bucket to 2pt
                if y_key not in lines_by_y:
                    lines_by_y[y_key] = []
                lines_by_y[y_key].append(word)

            prev_level = 0
            for y_key in sorted(lines_by_y):
                line_words = lines_by_y[y_key]
                line_text = _clean_line(" ".join(w["text"] for w in line_words))
                if not line_text:
                    continue

                # Use the dominant font size of the line
                line_size = statistics.median([w.get("size", median_size) for w in line_words])
                level = _classify_heading(line_size, median_size, heading_scale)

                if level == 1:
                    if prev_level != 1:
                        md_lines.append("")
                    md_lines.append(f"# {line_text}")
                elif level == 2:
                    md_lines.append(f"## {line_text}")
                elif level == 3:
                    md_lines.append(f"### {line_text}")
                elif _looks_like_bullet(line_text):
                    bullet_content = re.sub(r"^[\u2022\u2023\u25e6\u2043\u2219\*\-\+]\s*", "", line_text)
                    md_lines.append(f"- {bullet_content}")
                else:
                    md_lines.append(line_text)

                prev_level = level

            # Page break separator (omit for last page)
            if page_num < len(pdf.pages):
                md_lines.append("")
                md_lines.append("---")
                md_lines.append("")

    # Collapse excessive blank lines
    output = re.sub(r"\n{3,}", "\n\n", "\n".join(md_lines))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output.strip() + "\n")

    print(f"Saved: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a PDF to Markdown.")
    parser.add_argument("--input",         required=True,       help="Input .pdf file path")
    parser.add_argument("--output",        default=None,        help="Output .md file path (default: same name as input)")
    parser.add_argument("--heading-scale", type=float, default=1.2, help="Font size multiplier for heading detection (default: 1.2)")
    parser.add_argument("--no-tables",     action="store_true", help="Skip table extraction")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    output = args.output or os.path.splitext(args.input)[0] + ".md"
    convert(args.input, output, args.heading_scale, not args.no_tables)


if __name__ == "__main__":
    main()
