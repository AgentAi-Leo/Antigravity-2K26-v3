#!/usr/bin/env python3
"""
Watch Folder Processor for Convtr-PlainTxt2PDF
Scans a target folder for supported files and converts them to PDF.
Processed PDFs go into <folder>/zProcessed/YYYY-MM-DD/ and originals are purged.
"""
import os
import sys
import argparse
import subprocess
import datetime

SUPPORTED_EXTENSIONS = {".txt", ".rtf", ".doc", ".docx"}

def get_supported_files(folder: str) -> list[str]:
    """Return a list of supported files in the top-level of the folder."""
    files = []
    try:
        for entry in os.scandir(folder):
            if entry.is_file():
                ext = os.path.splitext(entry.name)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    files.append(entry.path)
    except OSError as e:
        print(f"Error scanning folder: {e}", file=sys.stderr)
    return sorted(files)


def process_folder(folder: str, dry_run: bool = False) -> list[dict]:
    """
    Process all supported files in the folder.
    Returns a list of dicts with 'input', 'output', 'success' keys.
    """
    files = get_supported_files(folder)
    if not files:
        return []

    # Locate plain_txt2pdf.py relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    converter = os.path.join(script_dir, "plain_txt2pdf.py")
    if not os.path.exists(converter):
        print(f"Error: converter not found at {converter}", file=sys.stderr)
        sys.exit(1)

    # Build dated output directory
    today = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(folder, "zProcessed", today)
    os.makedirs(output_dir, exist_ok=True)

    python_cmd = sys.executable
    results = []

    for filepath in files:
        basename = os.path.basename(filepath)
        pdf_name = os.path.splitext(basename)[0] + ".pdf"
        output_path = os.path.join(output_dir, pdf_name)

        if dry_run:
            print(f"[DRY RUN] Would process: {basename} -> zProcessed/{today}/{pdf_name}")
            results.append({"input": basename, "output": output_path, "success": True})
            continue

        cmd = [python_cmd, converter, "--input", filepath, "--output", output_path]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0 and os.path.exists(output_path):
                print(f"Processed: {basename} -> zProcessed/{today}/{pdf_name}")
                # Purge original
                try:
                    os.remove(filepath)
                    print(f"Purged: {basename}")
                except OSError as e:
                    print(f"Warning: could not purge {basename}: {e}", file=sys.stderr)
                results.append({"input": basename, "output": output_path, "success": True})
            else:
                print(f"Failed: {basename}", file=sys.stderr)
                if res.stderr:
                    print(f"  Error: {res.stderr.strip()}", file=sys.stderr)
                results.append({"input": basename, "output": output_path, "success": False})
        except subprocess.TimeoutExpired:
            print(f"Timeout: {basename} (exceeded 120s)", file=sys.stderr)
            results.append({"input": basename, "output": output_path, "success": False})
        except Exception as e:
            print(f"Error processing {basename}: {e}", file=sys.stderr)
            results.append({"input": basename, "output": output_path, "success": False})

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch Folder Processor — scans a folder for .txt/.rtf/.doc/.docx files, "
                    "converts them to PDF via plain_txt2pdf.py, and purges originals."
    )
    parser.add_argument("--folder", required=True,
                        help="Absolute path to the folder to scan for supported files.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without actually converting or purging.")
    args = parser.parse_args()

    folder = os.path.expanduser(args.folder)
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    results = process_folder(folder, dry_run=args.dry_run)

    if not results:
        print("No supported files found.")
    else:
        success_count = sum(1 for r in results if r["success"])
        print(f"\nSummary: {success_count}/{len(results)} files processed successfully.")


if __name__ == "__main__":
    main()
