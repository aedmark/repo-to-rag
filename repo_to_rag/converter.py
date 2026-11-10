"""
HTML to Markdown conversion using Python's standard library.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import List, Optional, Tuple


class SimpleHTMLToMarkdown(HTMLParser):
    """Converts HTML articles into clean Markdown without external dependencies."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: List[str] = []
        self.in_title = False
        self.in_script_or_style = False
        self.list_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag in ("script", "style"):
            self.in_script_or_style = True
            return
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.text_parts.append("\n\n# ")
        elif tag == "h2":
            self.text_parts.append("\n\n## ")
        elif tag == "h3":
            self.text_parts.append("\n\n### ")
        elif tag == "h4":
            self.text_parts.append("\n\n#### ")
        elif tag == "p":
            self.text_parts.append("\n\n")
        elif tag == "br":
            self.text_parts.append("\n")
        elif tag == "li":
            indent = "  " * (self.list_depth - 1) if self.list_depth > 1 else ""
            self.text_parts.append(f"\n{indent}- ")
        elif tag in ("ul", "ol"):
            self.list_depth += 1
        elif tag == "pre":
            self.text_parts.append("\n\n```\n")
        elif tag == "code" and self.text_parts and not self.text_parts[-1].endswith("```\n"):
            self.text_parts.append("`")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in ("script", "style"):
            self.in_script_or_style = False
            return
        if tag == "title":
            self.in_title = False
            self.text_parts.append("\n\n")
        elif tag in ("h1", "h2", "h3", "h4"):
            self.text_parts.append("\n")
        elif tag in ("ul", "ol"):
            self.list_depth = max(0, self.list_depth - 1)
        elif tag == "pre":
            self.text_parts.append("\n```\n")
        elif tag == "code" and self.text_parts and not self.text_parts[-1].endswith("```\n"):
            self.text_parts.append("`")

    def handle_data(self, data: str) -> None:
        if self.in_script_or_style:
            return
        clean = data.replace("\r", "")
        self.text_parts.append(clean)

    def get_markdown(self) -> str:
        raw = "".join(self.text_parts)
        # Collapse excessive blank lines
        collapsed = re.sub(r"\n{3,}", "\n\n", raw)
        return collapsed.strip()


def html_to_markdown(html_text: str) -> str:
    """Parses raw HTML and returns cleanly formatted Markdown text."""
    parser = SimpleHTMLToMarkdown()
    parser.feed(html_text)
    return parser.get_markdown()
