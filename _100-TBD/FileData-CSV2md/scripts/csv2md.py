import csv
import os
import sys
import argparse


def _detect_delimiter(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".tsv":
        return "\t"
    # Sniff from first line
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            sample = f.read(4096)
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t|;")
        return dialect.delimiter
    except csv.Error:
        return ","


def _align_char(align: str) -> str:
    return {"left": ":-", "right": "-:", "center": ":-:"}. get(align, ":-")


def csv_to_md(input_path: str, output_path: str | None, delimiter: str | None,
              max_rows: int | None, align: str, no_header: bool) -> None:
    delim = delimiter or _detect_delimiter(input_path)

    with open(input_path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delim)
        rows = list(reader)

    if not rows:
        print("Error: file is empty.")
        sys.exit(1)

    if no_header:
        headers = [f"Col{i+1}" for i in range(len(rows[0]))]
        data = rows
    else:
        headers = rows[0]
        data = rows[1:]

    if max_rows is not None:
        data = data[:max_rows]

    # Compute column widths
    all_rows = [headers] + data
    col_count = max(len(r) for r in all_rows)
    headers = headers + [""] * (col_count - len(headers))
    data = [r + [""] * (col_count - len(r)) for r in data]

    widths = [max(len(str(headers[i])), *(len(str(r[i])) for r in data)) for i in range(col_count)]
    widths = [max(w, 3) for w in widths]

    align_str = _align_char(align)

    def fmt(row: list) -> str:
        return "| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(col_count)) + " |"

    sep = "| " + " | ".join(align_str + "-" * (widths[i] - len(align_str)) for i in range(col_count)) + " |"

    lines = [fmt(headers), sep] + [fmt(r) for r in data]
    output = "\n".join(lines) + "\n"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved: {output_path}  ({len(data)} rows)")
    else:
        print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert CSV/TSV to a Markdown table.")
    parser.add_argument("--input",     required=True,           help="Input .csv or .tsv file")
    parser.add_argument("--output",    default=None,            help="Output .md file (default: stdout)")
    parser.add_argument("--delimiter", default=None,            help="Force delimiter: comma or tab (auto-detected by default)")
    parser.add_argument("--max-rows",  type=int, default=None,  help="Limit number of data rows")
    parser.add_argument("--align",     default="left",          choices=["left", "right", "center"], help="Column alignment")
    parser.add_argument("--no-header", action="store_true",     help="Treat first row as data, not header")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    csv_to_md(args.input, args.output, args.delimiter, args.max_rows, args.align, args.no_header)


if __name__ == "__main__":
    main()
