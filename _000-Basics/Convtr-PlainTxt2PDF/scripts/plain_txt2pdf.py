import os
import sys
import re
import subprocess
import argparse

# ---------------------------------------------------------------------------
# Locate fpdf2 and striprtf: local libs/ first, then shared _libs/ at skills root
# ---------------------------------------------------------------------------
_script_dir = os.path.dirname(os.path.abspath(__file__))
for _candidate in [
    os.path.join(_script_dir, "..", "libs"),
    os.path.join(_script_dir, "..", "..", "_libs"),
    os.path.join(_script_dir, "..", "..", "..", "_libs"),
]:
    if os.path.exists(_candidate):
        sys.path.insert(0, os.path.abspath(_candidate))

try:
    from fpdf import FPDF # type: ignore
except ImportError:
    print("Error: fpdf2 not found.\nRun: python3 -m pip install fpdf2 --target _libs/")
    sys.exit(1)


# ---------------------------------------------------------------------------
# File readers — one per supported format
# ---------------------------------------------------------------------------

def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _read_rtf(path: str) -> str:
    """Extract plain text from an RTF file, preserving lists and indents via HTML."""
    # Attempt 1: Mac textutil via HTML (built-in, perfectly preserves bullets/indentation/lists)
    try:
        result = subprocess.run(
            ["textutil", "-stdout", "-convert", "html", path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            from html.parser import HTMLParser
            class RTFListParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self.in_body = False
                    self.list_stack = []
                    self.ol_counters = []

                def _add_newline_if_needed(self):
                    if self.text and not self.text[-1].endswith('\n') and not self.text[-1].endswith('\n '):
                        self.text.append('\n')

                def get_indent(self):
                    level = len(self.list_stack)
                    return "  " * level if level > 0 else ""

                def handle_starttag(self, tag, attrs):
                    if tag == 'body':
                        self.in_body = True
                    elif tag in ('p', 'div'):
                        self._add_newline_if_needed()
                    elif tag == 'br' and self.in_body:
                        self.text.append('\n')
                    elif tag == 'ul':
                        self.list_stack.append('ul')
                        self.ol_counters.append(0)
                        self._add_newline_if_needed()
                    elif tag == 'ol':
                        self.list_stack.append('ol')
                        self.ol_counters.append(1)
                        self._add_newline_if_needed()
                    elif tag == 'li':
                        self._add_newline_if_needed()
                        indent = self.get_indent()
                        if self.list_stack:
                            list_type = self.list_stack[-1]
                            if list_type == 'ul':
                                self.text.append(f"{indent}\u2022 ")
                            elif list_type == 'ol':
                                count = self.ol_counters[-1]
                                self.text.append(f"{indent}{count}. ")
                                self.ol_counters[-1] += 1

                def handle_endtag(self, tag):
                    if tag == 'body':
                        self.in_body = False
                    elif tag in ('p', 'div'):
                        self._add_newline_if_needed()
                    elif tag in ('ul', 'ol'):
                        if self.list_stack:
                            self.list_stack.pop()
                            self.ol_counters.pop()
                        self._add_newline_if_needed()

                def handle_data(self, data):
                    if self.in_body:
                        if not data.strip():
                            pass
                        else:
                            cleaned = re.sub(r'[\r\n]+', '', data)
                            if cleaned:
                                self.text.append(cleaned.strip() + " ")
                        
            parser = RTFListParser()
            parser.feed(result.stdout)
            extracted = "".join(parser.text).strip()
            return re.sub(r'\n{3,}', '\n\n', extracted)
    except Exception:
        pass

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    # Try striprtf (fallback)
    try:
        from striprtf.striprtf import rtf_to_text # type: ignore
        return rtf_to_text(raw)
    except ImportError:
        pass

    # Fallback: regex-based RTF stripper
    def _decode_hex(m: re.Match) -> str:
        try:
            return bytes.fromhex(m.group(1)).decode("latin-1", errors="replace")
        except Exception:
            return ""

    text = re.sub(r"\\'([0-9a-fA-F]{2})", _decode_hex, raw)
    text = re.sub(r"\\[a-z*]+\-?\d*[ ]?", " ", text)
    text = re.sub(r"\\[{}\\]", "", text)
    # Remove groups that are still wrapped in braces
    for _ in range(5):
        text = re.sub(r"\{[^{}]*\}", " ", text)
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _read_doc(path: str) -> str:
    """Extract plain text from a legacy binary .doc file."""

    # Attempt 1: antiword (brew install antiword)
    try:
        result = subprocess.run(
            ["antiword", path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except FileNotFoundError:
        pass  # antiword not installed
    except Exception:
        pass

    # Attempt 2: LibreOffice headless text export
    try:
        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "txt:Text", "--outdir", "/tmp", path],
            capture_output=True, text=True, timeout=60
        )
        tmp_txt = "/tmp/" + os.path.splitext(os.path.basename(path))[0] + ".txt"
        if os.path.exists(tmp_txt):
            with open(tmp_txt, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except FileNotFoundError:
        pass  # LibreOffice not installed
    except Exception:
        pass

    # Attempt 3: Binary printable-text extraction (last resort)
    print("Warning: neither antiword nor LibreOffice found. Extracting raw text from binary.")
    print("  For better results: brew install antiword")
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("latin-1", errors="replace")
    # Pull out runs of printable characters (length >= 4)
    runs = re.findall(r"[ -~\t]{4,}", text)
    # Filter out runs that look like binary metadata (mostly non-alpha)
    clean = [r for r in runs if sum(c.isalpha() or c.isspace() for c in r) / max(len(r), 1) > 0.5]
    return "\n".join(clean)


def _read_docx(path: str) -> str:
    """Extract plain text from a modern .docx (XML zip) file."""
    # Attempt 1: Mac textutil (built-in)
    try:
        result = subprocess.run(
            ["textutil", "-stdout", "-convert", "txt", path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass

    # Attempt 2: LibreOffice headless
    try:
        result = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "txt:Text", "--outdir", "/tmp", path],
            capture_output=True, text=True, timeout=60
        )
        tmp_txt = "/tmp/" + os.path.splitext(os.path.basename(path))[0] + ".txt"
        if os.path.exists(tmp_txt):
            with open(tmp_txt, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception:
        pass

    # Attempt 3: Primitive ZIP/XML parsing (stdlib only fallback)
    try:
        import zipfile
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read("word/document.xml").decode("utf-8")
        # Replace <w:p> tags with newlines to preserve paragraphs
        xml_content = re.sub(r'<w:p>|<w:p [^>]*>', '\n', xml_content)
        # Strip all remaining XML tags
        text = re.sub(r'<[^>]+>', '', xml_content)
        return text.strip()
    except Exception as e:
        print(f"Warning: primitive .docx extraction failed: {e}")
        return ""


def read_file(path: str) -> str:
    """Dispatch to the correct reader based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    
    # Pre-flight check: Mac TextEdit often saves RTF files with a .txt extension.
    # If a .txt file starts with "{\rtf", it's actually an RTF file.
    if ext == ".txt" and os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                if f.read(5).startswith("{\\rtf"):
                    ext = ".rtf" # Force routing to RTF parser
        except Exception:
            pass
            
    if ext == ".rtf":
        return _read_rtf(path)
    elif ext == ".doc":
        return _read_doc(path)
    elif ext == ".docx":
        return _read_docx(path)
    else:
        return _read_txt(path)


# ---------------------------------------------------------------------------
# PDF converter
# ---------------------------------------------------------------------------

def convert(input_path: str, output_path: str, font_size: int = 11, margin: int = 20) -> None:
    text = read_file(input_path)

    pdf = FPDF()
    pdf.set_margins(margin, margin, margin)
    pdf.set_auto_page_break(auto=True, margin=margin)
    pdf.add_page()

    import unicodedata

    def _safe_char_translate(c):
        """Translate characters that Helvetica cannot handle into bracketed text names."""
        try:
            c.encode('cp1252')
            return c
        except UnicodeEncodeError:
            try:
                name = unicodedata.name(c)
                name = name.replace(" VARIATION SELECTOR-16", "").replace(" COMBINING ENCLOSING KEYCAP", "").title()
                if "Check Mark" in name or "Heavy Check Mark" in name: return "[Check]"
                if "Cross Mark" in name: return "[X]"
                if "Digit " in name and len(name) == 7 and name[6].isdigit(): return f"{name[6]}."
                if "Variation Selector" in name or not name.strip(): return ""
                return f" [{name}] "
            except (ValueError, IndexError):
                return "?"

    import re
    # Pattern detects common emojis and specifically keycap sequences: Digit + VS16 + Keycap
    EMOJI_PATTERN = re.compile(r'([\u2600-\u27BF]|[\u203C-\u3299]|[\U0001f000-\U0001faff]|[0-9#*]\ufe0f?\u20e3)')

    def get_line_fragments(text):
        """Split a line into (is_emoji, text) fragments."""
        fragments = []
        last_end = 0
        for match in EMOJI_PATTERN.finditer(text):
            start, end = match.span()
            if start > last_end:
                fragments.append((False, text[last_end:start]))
            fragments.append((True, match.group()))
            last_end = end
        if last_end < len(text):
            fragments.append((False, text[last_end:]))
        return fragments

    def render_fragmented_line(fragments, f_size, align='L'):
        """Render a line piece-by-piece with font switching to keep boding intact."""
        # For simple left alignment, we use Write. For centering (footer), we skip fragmentation for now
        # as footers shouldn't contain complex emojis.
        pdf.set_x(margin)
        for is_emoji, content in fragments:
            if is_emoji:
                pdf.set_font("NotoEmoji", size=f_size)
            else:
                pdf.set_font("NotoSans", size=f_size)
            pdf.write(h=6, txt=content)
        pdf.ln(6)

    # ---- BUNDLE CUSTOM TRUETYPE FONTS ----
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(base_dir, "fonts")
    
    noto_sans_path = os.path.join(font_dir, "NotoSans-Regular.ttf")
    noto_emoji_path = os.path.join(font_dir, "NotoColorEmoji.ttf")
    
    use_latin_fallback = False
    try:
        pdf.set_text_shaping(True)
        pdf.add_font("NotoSans", style="", fname=noto_sans_path)
        pdf.add_font("NotoEmoji", style="", fname=noto_emoji_path)
        # We manually switch now, so we don't rely on automatic fallback which splits runs
        pdf.set_font("NotoSans", size=font_size)
    except Exception as e:
        print(f"Warning: Falling back to Helvetica due to font/shaper error: {e}")
        pdf.set_font("helvetica", size=font_size)
        use_latin_fallback = True

    lines = text.splitlines()
    total_lines = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "":
            pdf.ln(4)
            continue

        if use_latin_fallback:
            processed_chars = []
            for c in line:
                if c in ("◦", "○", "∘"): processed_chars.append("*")
                else: processed_chars.append(_safe_char_translate(c))
            safe_line = "".join(processed_chars).expandtabs(4).encode('cp1252', 'replace').decode('latin-1')
            
            # --- Document Header Styling ---
            if safe_line.startswith("--- Document:") or safe_line.startswith("Sourced from:"):
                orig_font = pdf.font_family
                orig_size = pdf.font_size_pt
                pdf.set_font("helvetica", style="B", size=int(orig_size * 1.15))
                pdf.set_text_color(255, 140, 0) # Orange
                pdf.multi_cell(0, 6, safe_line)
                pdf.set_text_color(0, 0, 0) # Reset to Black
                pdf.set_font(orig_font, style="", size=orig_size)
            else:
                pdf.multi_cell(0, 6, safe_line)
        else:
            safe_line = line.expandtabs(4)
            # Handle the separator and source file footer (keep them simple)
            if safe_line.startswith("Source File:") and i >= total_lines - 2:
                pdf.set_font("NotoSans", size=font_size if "---" in safe_line else int(font_size * 0.85))
                pdf.set_x(margin)
                pdf.multi_cell(0, 6, safe_line, align='C')
            elif (safe_line.startswith("--- Document:") or safe_line.startswith("Sourced from:")):
                # Handle Merge Source Headers: 115% size, Bold, Orange
                pdf.set_font("helvetica", style="B", size=int(font_size * 1.15))
                pdf.set_text_color(255, 140, 0) # Orange
                pdf.set_x(margin)
                pdf.multi_cell(0, 6, safe_line)
                pdf.set_text_color(0, 0, 0) # Reset to Black
                pdf.set_font("NotoSans", style="", size=font_size)
            else:
                # High-Fidelity Manual Fragmenting to preserve bonding!
                fragments = get_line_fragments(safe_line)
                render_fragmented_line(fragments, font_size)

    pdf.output(output_path)
    print(f"Saved: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert .txt, .rtf, .doc, or .docx files to PDF."
    )
    parser.add_argument("--input",     required=True, help="Input file (.txt, .rtf, .doc, or .docx)")
    parser.add_argument("--output",    default=None,  help="Output .pdf path (default: same name as input)")
    parser.add_argument("--font-size", type=int, default=11, help="Font size in pt (default: 11)")
    parser.add_argument("--margin",    type=int, default=20, help="Page margin in mm (default: 20)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    supported = {".txt", ".rtf", ".doc", ".docx"}
    ext = os.path.splitext(args.input)[1].lower()
    if ext not in supported:
        print(f"Warning: unrecognized extension '{ext}'. Treating as plain text.")

    output = args.output or os.path.splitext(args.input)[0] + ".pdf"
    convert(args.input, output, args.font_size, args.margin)


if __name__ == "__main__":
    main()
