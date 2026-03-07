import os
import sys
import re
import argparse
from datetime import date


def _build_new_name(filename: str, args, counter: int) -> str:
    name, ext = os.path.splitext(filename)

    # Regex find & replace on stem
    if args.find:
        name = re.sub(args.find, args.replace or "", name)

    # Remove spaces
    if args.no_spaces:
        name = name.replace(" ", "_")

    # Lowercase
    if args.lowercase:
        name = name.lower()
        ext = ext.lower()

    # Suffix (before extension)
    if args.suffix:
        name = name + args.suffix

    # Sequential number
    if args.number:
        pad = args.pad or 3
        name = f"{str(counter).zfill(pad)}_{name}"

    # Date prefix
    if args.date_prefix:
        today = date.today().strftime("%Y-%m-%d")
        name = f"{today}_{name}"

    # Prefix (outermost)
    if args.prefix:
        name = args.prefix + name

    return name + ext


def batch_rename(args) -> None:
    target_dir = os.path.abspath(args.dir)
    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a directory.")
        sys.exit(1)

    # Collect files
    def _collect(d: str) -> list:
        entries = []
        for entry in sorted(os.scandir(d), key=lambda e: e.name):
            if entry.is_file():
                entries.append(entry.path)
            elif entry.is_dir() and args.recursive:
                entries.extend(_collect(entry.path))
        return entries

    files = _collect(target_dir)

    # Filter by extension
    if args.ext:
        exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext}
        files = [f for f in files if os.path.splitext(f)[1].lower() in exts]

    if not files:
        print("No matching files found.")
        return

    start = args.start or 1
    rename_plan = []
    counter = start
    for filepath in files:
        dir_part = os.path.dirname(filepath)
        old_name = os.path.basename(filepath)
        new_name = _build_new_name(old_name, args, counter)
        new_path = os.path.join(dir_part, new_name)
        rename_plan.append((filepath, new_path, old_name, new_name))
        counter += 1

    # Detect conflicts
    new_paths = [p[1] for p in rename_plan]
    if len(new_paths) != len(set(new_paths)):
        print("Error: rename plan would create duplicate filenames. Aborting.")
        sys.exit(1)

    # Preview / apply
    changed = [(old, new, on, nn) for old, new, on, nn in rename_plan if old != new]

    if not changed:
        print("No renames needed — all filenames already match the target pattern.")
        return

    if args.dry_run:
        print(f"DRY-RUN — {len(changed)} file(s) would be renamed:\n")
        for _, _, old_name, new_name in changed:
            print(f"  {old_name}  →  {new_name}")
        print("\nRe-run without --dry-run to apply.")
    else:
        for old_path, new_path, _, _ in changed:
            os.rename(old_path, new_path)
        print(f"Renamed {len(changed)} file(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch rename files with prefix, suffix, regex, numbering, or date.")
    parser.add_argument("--dir",         required=True,          help="Directory containing files")
    parser.add_argument("--prefix",      default=None,           help="Prepend string to filename")
    parser.add_argument("--suffix",      default=None,           help="Append string before extension")
    parser.add_argument("--find",        default=None,           help="Regex pattern to find in filename")
    parser.add_argument("--replace",     default="",             help="Replacement string (used with --find)")
    parser.add_argument("--number",      action="store_true",    help="Add sequential number to filename")
    parser.add_argument("--pad",         type=int, default=3,    help="Zero-pad width for numbering (default: 3)")
    parser.add_argument("--start",       type=int, default=1,    help="Starting number (default: 1)")
    parser.add_argument("--date-prefix", action="store_true",    help="Prepend YYYY-MM-DD_ to filename")
    parser.add_argument("--lowercase",   action="store_true",    help="Convert filename to lowercase")
    parser.add_argument("--no-spaces",   action="store_true",    help="Replace spaces with underscores")
    parser.add_argument("--ext",         nargs="*",              help="Limit to extensions e.g. .jpg .png")
    parser.add_argument("--dry-run",     action="store_true",    help="Preview renames without applying")
    parser.add_argument("--recursive",   action="store_true",    help="Recurse into subdirectories")
    args = parser.parse_args()

    batch_rename(args)


if __name__ == "__main__":
    main()
