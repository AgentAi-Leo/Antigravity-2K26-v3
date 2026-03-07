import subprocess
from html.parser import HTMLParser
import re

class RTFListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_body = False
        
        # Track list state
        self.list_stack = [] # 'ul' or 'ol'
        self.ol_counters = [] # counts for nested ol's

    def get_indent(self):
        # 4 spaces per nesting level
        level = len(self.list_stack)
        return "    " * (level - 1) if level > 0 else ""

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        elif tag in ('p', 'div'):
            # Only add newline if we aren't at the very start to avoid weird spacing
            pass
        elif tag == 'br' and self.in_body:
            self.text.append('\n')
        elif tag == 'ul':
            self.list_stack.append('ul')
            self.ol_counters.append(0) # dummy
            self.text.append('\n')
        elif tag == 'ol':
            self.list_stack.append('ol')
            self.ol_counters.append(1)
            self.text.append('\n')
        elif tag == 'li':
            self.text.append('\n')
            indent = self.get_indent()
            if self.list_stack:
                list_type = self.list_stack[-1]
                if list_type == 'ul':
                    # Use a bullet
                    self.text.append(f"{indent}• ")
                elif list_type == 'ol':
                    # Use a number
                    count = self.ol_counters[-1]
                    self.text.append(f"{indent}{count}. ")
                    self.ol_counters[-1] += 1

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
        elif tag in ('p', 'div'):
            self.text.append('\n')
        elif tag in ('ul', 'ol'):
            if self.list_stack:
                self.list_stack.pop()
                self.ol_counters.pop()
            self.text.append('\n')
        elif tag == 'li':
            # don't append newline here, let the next block handle it to avoid double spacing
            pass

    def handle_data(self, data):
        if self.in_body:
            # Clean up newlines from HTML source formatting
            cleaned = re.sub(r'[\r\n]+', '', data)
            if cleaned:
                self.text.append(cleaned)

def rtf_to_text_with_lists(filepath):
    res = subprocess.run(["textutil", "-convert", "html", "-stdout", filepath], capture_output=True, text=True)
    if res.returncode != 0:
        return ""
    
    html_content = res.stdout
    parser = RTFListParser()
    parser.feed(html_content)
    text = "".join(parser.text).strip()
    return re.sub(r'\n{3,}', '\n\n', text)

output = rtf_to_text_with_lists("/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/__000-DASHBOARD-TEST1/_REF-FILES/Consistency_SAMSON.rtf")
print(output[:1500])
