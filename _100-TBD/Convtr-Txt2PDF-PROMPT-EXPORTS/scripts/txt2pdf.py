import os
import sys
import re
import subprocess
import argparse

# Add local libs to path if they exist
local_libs = os.path.join(os.path.dirname(__file__), "..", "libs")
if os.path.exists(local_libs):
    sys.path.append(os.path.abspath(local_libs))

try:
    from fpdf import FPDF
except ImportError:
    # If not found, try common system paths or temp paths used during setup
    sys.path.append(os.path.abspath("/tmp/fpdf_libs_final"))
    try:
        from fpdf import FPDF
    except ImportError:
        print("Error: fpdf2 not found. Please install it using 'pip install fpdf2'.")
        sys.exit(1)

class PromptPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        footer_text = os.getenv("PDF_FOOTER_TEXT", "For more resources, visit: https://offers.hubspot.com/view/the-claude-cowork-stack")
        footer_link = os.getenv("PDF_FOOTER_LINK", "https://offers.hubspot.com/view/the-claude-cowork-stack")
        self.cell(0, 10, footer_text, align="C", link=footer_link)

def set_finder_label(filepath, color):
    """Sets the Finder label using AppleScript."""
    colors = {
        "orange": 1,
        "red": 2,
        "yellow": 3,
        "blue": 4,
        "purple": 5,
        "green": 6,
        "gray": 7
    }
    index = colors.get(color.lower(), 0)
    if index == 0: return

    abs_path = os.path.abspath(filepath)
    script = f'tell application "Finder" to set label index of (POSIX file "{abs_path}" as alias) to {index}'
    try:
        subprocess.run(["osascript", "-e", script], check=True, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def create_pdf(prompt_num, content, output_prefix, logo_path, label_color):
    filename = f"{output_prefix}Prompt{prompt_num}.pdf"
    
    # Cleaning
    content = re.sub(r"_{10,}", "", content)
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)
    
    replacements = {
        "\u2014": "--", "\u2013": "-", "\u201c": '"', "\u201d": '"',
        "\u2018": "'", "\u2019": "'", "\u00a0": " ", "\u2022": "*"
    }
    for char, rep in replacements.items():
        content = content.replace(char, rep)
    
    clean_content = content.strip()
    
    pdf = PromptPDF()
    pdf.add_page()
    
    # Logo
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=79, y=10, w=52)
    
    pdf.set_y(35)
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 10, f"Prompt {prompt_num}", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    pdf.set_font("helvetica", "", 11)
    
    lines = clean_content.split("\n")
    for line_text in lines:
        line_text = line_text.strip()
        if not line_text:
            pdf.ln(5)
            continue
            
        if any(x in line_text for x in ["Use Case:", "Key Inputs:", "Expected Output:", "//// PROMPT"]):
            pdf.set_font("helvetica", "B", 12)
            pdf.ln(5)
            pdf.write(h=8, text=line_text)
            pdf.ln(8)
            pdf.set_font("helvetica", "", 11)
        else:
            pdf.write(h=7, text=line_text)
            pdf.ln(7)
    
    pdf.output(filename)
    print(f"Generated {filename}")
    if label_color:
        set_finder_label(filename, label_color)

def main():
    parser = argparse.ArgumentParser(description="Convert text prompts to PDF.")
    parser.add_argument("--input", required=True, help="Input text file path")
    parser.add_argument("--prefix", default="HUBSPOT_", help="Output filename prefix")
    parser.add_argument("--logo", help="Path to logo image")
    parser.add_argument("--label", help="Finder label color (orange, green, etc.)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.")
        return

    with open(args.input, "r") as f:
        file_content = f.read()
    
    pattern = r"(Prompt\s+\d+:.*?)(?=Prompt\s+\d+:|$)"
    prompt_sections = re.findall(pattern, file_content, re.DOTALL | re.IGNORECASE)
    
    if not prompt_sections:
        prompt_sections = re.split(r"_{10,}\s*\n_{10,}", file_content)
        prompt_sections = [s for s in prompt_sections if any(x in s.upper() for x in ["PROMPT", "USE CASE"])]

    for i, section in enumerate(prompt_sections, 1):
        num_match = re.search(r"Prompt\s+(\d+)", section, re.IGNORECASE)
        num = num_match.group(1) if num_match else str(i)
        create_pdf(num, section.strip(), args.prefix, args.logo, args.label)

if __name__ == "__main__":
    main()
