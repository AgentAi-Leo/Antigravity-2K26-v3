import os
import sys
import re
import argparse

# Locate fpdf2: look locally first, then fall back to shared _libs/ at skills root
_script_dir = os.path.dirname(os.path.abspath(__file__))
for _candidate in [
    os.path.join(_script_dir, "..", "libs"),
    os.path.join(_script_dir, "..", "..", "_libs"),
]:
    if os.path.exists(_candidate):
        sys.path.insert(0, os.path.abspath(_candidate))

try:
    from fpdf import FPDF
except ImportError:
    print("Error: fpdf2 not found.\nRun: python3 -m pip install fpdf2 --target libs/")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def _strip_inline(text: str) -> str:
    """Remove inline markers: **bold**, *italic*, `code`."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",     r"\1", text)
    text = re.sub(r"`(.+?)`",       r"\1", text)
    return text


def parse_markdown(text: str) -> list:
    """
    Returns a list of (type, content) tuples.
    Types: h1, h2, h3, bullet, code, body, blank
    """
    segments = []
    in_code = False
    code_buf = []

    for line in text.splitlines():
        # Code fence toggle
        if line.strip().startswith("```"):
            if in_code:
                segments.append(("code", "\n".join(code_buf)))
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        # Headings
        if line.startswith("### "):
            segments.append(("h3", _strip_inline(re.sub(r"^###\s+", "", line).strip())))
        elif line.startswith("## "):
            segments.append(("h2", _strip_inline(re.sub(r"^##\s+", "", line).strip())))
        elif line.startswith("# "):
            segments.append(("h1", _strip_inline(re.sub(r"^#\s+", "", line).strip())))
        # Bullets
        elif re.match(r"^[-*]\s+", line):
            bullet_text = re.sub(r"^[-*]\s+", "", line).strip()
            segments.append(("bullet", _strip_inline(bullet_text)))
        # Blank
        elif line.strip() == "":
            segments.append(("blank", ""))
        # Body
        else:
            segments.append(("body", _strip_inline(line)))

    # Close unclosed code block
    if in_code and code_buf:
        segments.append(("code", "\n".join(code_buf)))

    return segments


# ---------------------------------------------------------------------------
# PDF renderer
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PDF renderer
# ---------------------------------------------------------------------------

def convert(source: str, output_path: str, font_size: int = 11, margin: int = 20, is_text: bool = False) -> None:
    """
    source: file path OR direct markdown text
    is_text: True if source is markdown content, False if it's a file path
    """
    if is_text:
        text = source
    else:
        with open(source, "r", encoding="utf-8") as f:
            text = f.read()

    segments = parse_markdown(text)

    pdf = FPDF()
    pdf.set_margins(margin, margin, margin)
    pdf.set_auto_page_break(auto=True, margin=margin)
    pdf.add_page()

    effective_w = pdf.w - 2 * margin
    last_type = None

    for seg_type, content in segments:
        if seg_type == "blank":
            if last_type not in ("blank", None):
                pdf.ln(4)

        elif seg_type == "h1":
            pdf.ln(6)
            pdf.set_font("helvetica", "B", font_size + 10)
            pdf.multi_cell(effective_w, 11, content)
            pdf.ln(2)

        elif seg_type == "h2":
            pdf.ln(5)
            pdf.set_font("helvetica", "B", font_size + 5)
            pdf.multi_cell(effective_w, 9, content)
            pdf.ln(1)

        elif seg_type == "h3":
            pdf.ln(3)
            pdf.set_font("helvetica", "B", font_size + 2)
            pdf.multi_cell(effective_w, 7, content)

        elif seg_type == "bullet":
            pdf.set_font("helvetica", "", font_size)
            pdf.set_x(margin + 5)
            pdf.multi_cell(effective_w - 5, 6, f"- {content}")

        elif seg_type == "code":
            pdf.ln(2)
            pdf.set_fill_color(235, 235, 235)
            pdf.set_font("courier", "", max(font_size - 1, 8))
            for code_line in content.splitlines():
                pdf.multi_cell(effective_w, 5.5, code_line, fill=True)
            pdf.set_fill_color(255, 255, 255)
            pdf.ln(2)

        elif seg_type == "body":
            pdf.set_font("helvetica", "", font_size)
            pdf.multi_cell(effective_w, 6, content)

        last_type = seg_type

    pdf.output(output_path)
    print(f"Saved: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def download_url(url: str) -> str:
    """Fetches text content from a URL with a browser-like User-Agent."""
    import urllib.request
    
    # Add a User-Agent to avoid 403 Forbidden errors from sites like Notion or GitHub
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                # If it's HTML, Notion and similar sites return a JS shell. 
                # We can't parse this as Markdown easily.
                return "ERROR_IS_HTML"
            
            content = response.read().decode('utf-8')
            return content
    except Exception as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)

def capture_html(url: str, output_path: str) -> None:
    """Uses system Google Chrome to capture a high-fidelity PDF of a web page."""
    import subprocess
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    if not os.path.exists(chrome_path):
        print(f"Error: Google Chrome not found at {chrome_path}")
        sys.exit(1)
        
    print(f"Capturing high-fidelity PDF via Chrome: {url}")
    # --print-to-pdf works in headless mode to render the page exactly as a browser would
    command = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={output_path}",
        "--no-margins",
        url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Saved: {output_path}")
        else:
            print(f"Chrome error (exit {result.returncode}): {result.stderr}")
            sys.exit(1)
    except Exception as e:
        print(f"Failed to execute Chrome: {e}")
        sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Markdown (.md) file or URL to a styled PDF.")
    parser.add_argument("--input",     help="Input .md file path")
    parser.add_argument("--url",       help="Remote Markdown URL")
    parser.add_argument("--output",    default=None,  help="Output .pdf path")
    parser.add_argument("--font-size", type=int, default=11, help="Body font size in pt")
    parser.add_argument("--margin",    type=int, default=20, help="Page margin in mm")
    parser.add_argument("--capture",   action="store_true", help="Force high-fidelity HTML capture (supports icons/emojis)")
    args = parser.parse_args()

    if not args.input and not args.url:
        print("Error: Either --input or --url must be provided.")
        sys.exit(1)

    if args.url:
        output = args.output or "remote_markdown.pdf"
        
        if args.capture:
            capture_html(args.url, output)
            return

        print(f"Fetching: {args.url}")
        md_content = download_url(args.url)
        
        if md_content == "ERROR_IS_HTML":
            print("\n" + "="*50)
            print("ERROR: This URL appears to be a WEB PAGE (HTML), not RAW MARKDOWN.")
            print("Sites like Notion and regular GitHub pages return complex HTML.")
            print("To capture this as-is (with icons/emojis), use the --capture flag.")
            print("Or use a 'Raw' link (e.g. raw.githubusercontent.com) for Markdown.")
            print("="*50 + "\n")
            sys.exit(1)
            
        print(md_content)
        convert(md_content, output, args.font_size, args.margin, is_text=True)
    else:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found.")
            sys.exit(1)
        output = args.output or os.path.splitext(args.input)[0] + ".pdf"
        convert(args.input, output, args.font_size, args.margin, is_text=False)

if __name__ == "__main__":
    main()
