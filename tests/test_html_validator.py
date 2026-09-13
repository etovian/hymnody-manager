import os
from html.parser import HTMLParser
import pytest

VOID_ELEMENTS = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
    'link', 'meta', 'param', 'source', 'track', 'wbr'
}

class HTMLStructureValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag_stack = []  # tuple of (tag, line_no)
        self.errors = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower not in VOID_ELEMENTS:
            line_no = self.getpos()[0]
            self.tag_stack.append((tag_lower, line_no))

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in VOID_ELEMENTS:
            return

        line_no = self.getpos()[0]
        if not self.tag_stack:
            self.errors.append(f"Unexpected closing tag </{tag_lower}> at line {line_no} with empty stack.")
            return

        expected_tag, start_line = self.tag_stack[-1]
        if expected_tag == tag_lower:
            self.tag_stack.pop()
        else:
            # Mismatch detected
            self.errors.append(
                f"Mismatched closing tag </{tag_lower}> at line {line_no}. "
                f"Expected </{expected_tag}> (opened at line {start_line})."
            )
            # Try to recover if tag is further up the stack
            matching_indices = [i for i, (t, _) in enumerate(self.tag_stack) if t == tag_lower]
            if matching_indices:
                unclosed = self.tag_stack[matching_indices[-1]:]
                for ut, ul in reversed(unclosed):
                    self.errors.append(f"Unclosed tag <{ut}> opened at line {ul}")
                self.tag_stack = self.tag_stack[:matching_indices[-1]]

    def finalize(self):
        for tag, line_no in reversed(self.tag_stack):
            self.errors.append(f"Unclosed tag <{tag}> opened at line {line_no} remaining at end of file.")


def validate_html_file(file_path):
    validator = HTMLStructureValidator()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    validator.feed(content)
    validator.finalize()
    return validator.errors


def test_index_html_tag_structure():
    """Verify that src/static/index.html has balanced opening and closing HTML tags."""
    index_html_path = os.path.join(os.path.dirname(__file__), "..", "src", "static", "index.html")
    assert os.path.exists(index_html_path), f"File not found: {index_html_path}"
    
    errors = validate_html_file(index_html_path)
    assert not errors, f"HTML structure errors found in index.html:\n" + "\n".join(errors)
