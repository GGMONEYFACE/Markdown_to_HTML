"""A small, dependency-free Markdown to HTML converter.

This is intentionally a starter implementation rather than a complete
Markdown specification. It handles the formatting most useful for README
files, notes, and simple announcements.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


INLINE_PATTERNS = (
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__"), r"<strong>\1\2</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)"), r"<em>\1\2</em>"),
)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")


def convert_inline(text: str) -> str:
    """Convert a few inline Markdown markers after escaping HTML."""
    converted = html.escape(text, quote=False)
    for pattern, replacement in INLINE_PATTERNS:
        converted = pattern.sub(replacement, converted)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = html.escape(match.group(2), quote=True)
        title = match.group(3)
        title_attribute = (
            f' title="{html.escape(title, quote=True)}"' if title is not None else ""
        )
        return f'<a href="{url}"{title_attribute}>{label}</a>'

    return LINK_PATTERN.sub(replace_link, converted)


def convert_markdown(markdown: str) -> str:
    """Convert basic Markdown blocks into an HTML fragment."""
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{convert_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type is not None:
            output.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        if in_code:
            if line.strip().startswith("```"):
                output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                code_lines.append(line)
            continue

        if line.strip().startswith("```"):
            flush_paragraph()
            close_list()
            in_code = True
            continue

        heading = re.match(r"^\s*(#{1,6})\s+(.+?)\s*#*$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{convert_inline(heading.group(2))}</h{level}>")
            continue

        unordered = re.match(r"^\s*[-*+]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            flush_paragraph()
            wanted_type = "ul" if unordered else "ol"
            if list_type != wanted_type:
                close_list()
                output.append(f"<{wanted_type}>")
                list_type = wanted_type
            item = (unordered or ordered).group(1)
            output.append(f"<li>{convert_inline(item)}</li>")
            continue

        if not line.strip():
            flush_paragraph()
            close_list()
            continue

        close_list()
        paragraph.append(line.strip())

    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    close_list()
    return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Markdown file to an HTML fragment.")
    parser.add_argument("input", type=Path, help="Markdown file to read, or '-' for stdin")
    parser.add_argument("-o", "--output", type=Path, help="HTML file to write (defaults to stdout)")
    args = parser.parse_args()

    markdown = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
    result = convert_markdown(markdown)
    if args.output:
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()