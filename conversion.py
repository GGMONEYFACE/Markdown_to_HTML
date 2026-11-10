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
from html.parser import HTMLParser


INLINE_PATTERNS = (
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__"), r"<strong>\1\2</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)"), r"<em>\1\2</em>"),
)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")


class _HtmlNode:
    def __init__(self, tag: str | None = None, attrs: dict[str, str] | None = None) -> None:
        self.tag = tag
        self.attrs = attrs or {}
        self.children: list[_HtmlNode | str] = []


class _MarkdownHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _HtmlNode()
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HtmlNode(tag.lower(), {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag.lower() not in {"br", "hr", "img", "input", "meta", "link"}:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag.lower():
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag.lower():
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


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
        matched_list = unordered or ordered
        if matched_list is not None:
            flush_paragraph()
            wanted_type = "ul" if unordered else "ol"
            if list_type != wanted_type:
                close_list()
                output.append(f"<{wanted_type}>")
                list_type = wanted_type
            item = matched_list.group(1)
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


def _render_inline_html(node: _HtmlNode | str) -> str:
    if isinstance(node, str):
        return node
    content = "".join(_render_inline_html(child) for child in node.children)
    if node.tag == "strong" or node.tag == "b":
        return f"**{content}**"
    if node.tag == "em" or node.tag == "i":
        return f"*{content}*"
    if node.tag == "code":
        return f"`{content}`"
    if node.tag == "a":
        href = node.attrs.get("href", "")
        title = node.attrs.get("title")
        title_part = f' "{title}"' if title else ""
        return f"[{content}]({href}{title_part})"
    if node.tag == "br":
        return "\n"
    return content


def _render_html_block(node: _HtmlNode | str) -> str:
    if isinstance(node, str):
        return node
    if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        content = "".join(_render_inline_html(child) for child in node.children).strip()
        return f'{"#" * int(node.tag[1])} {content}'
    if node.tag == "p":
        return "".join(_render_inline_html(child) for child in node.children).strip()
    if node.tag in {"ul", "ol"}:
        items = []
        for child in node.children:
            if isinstance(child, _HtmlNode) and child.tag == "li":
                content = "".join(_render_inline_html(item) for item in child.children).strip()
                prefix = "-" if node.tag == "ul" else f"{len(items) + 1}."
                items.append(f"{prefix} {content}")
        return "\n".join(items)
    if node.tag == "pre":
        code = next(
            (child for child in node.children if isinstance(child, _HtmlNode) and child.tag == "code"),
            None,
        )
        content = (
            "".join(_render_inline_html(child) for child in code.children)
            if code is not None
            else _render_inline_html(node)
        )
        return f"```\n{content}\n```"
    if node.tag in {"script", "style"}:
        return ""
    return _render_inline_html(node)


def convert_html(markup: str) -> str:
    """Convert the HTML emitted by this module back into Markdown."""
    parser = _MarkdownHtmlParser()
    parser.feed(markup)
    blocks = [
        _render_html_block(child).strip()
        for child in parser.root.children
        if not isinstance(child, str) or child.strip()
    ]
    return "\n\n".join(block for block in blocks if block)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert between Markdown and HTML fragments.")
    parser.add_argument("input", type=Path, help="Markdown file to read, or '-' for stdin")
    parser.add_argument("-o", "--output", type=Path, help="HTML file to write (defaults to stdout)")
    parser.add_argument(
        "--from-html",
        action="store_true",
        help="convert an HTML fragment to Markdown instead of converting Markdown to HTML",
    )
    args = parser.parse_args()

    source = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
    result = convert_html(source) if args.from_html else convert_markdown(source)
    if args.output:
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()