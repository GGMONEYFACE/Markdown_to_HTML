# Markdown and HTML converter

This script converts supported Markdown to an HTML fragment and converts that
HTML back to Markdown.

## The Idea:
This project started as a simple idea on converting similar languages back and forth.

## Use Cases:
Converting into a webpage:
- Github README files 
- Discord messages
- personal notes 

 This is useful for converting announcements in a Discord server into an announcement on your website or converting personal notes into an official write up.

 ## Thought Process:
 If I take the different symbols that indicate text manipulation within Markdown and convert them to their HTML equivilent, everything should be convertable fairly simply. Problems and edge cases with doubled symbols (i.e. *italics* and **bold**)

## Usage

Convert a Markdown file to an HTML fragment and print it to the terminal:

```bash
python3 conversion.py README.md
```

Write the result to a file instead:

```bash
python3 conversion.py README.md --output README.html
```

Convert the generated HTML back to Markdown:

```bash
python3 conversion.py README.html --from-html
```

The `--from-html` option also works with standard input and `--output`:

```bash
cat README.html | python3 conversion.py - --from-html --output README-restored.md
```

The starter converter supports headings, paragraphs, unordered and ordered
lists, bold and italic text, inline code, links, and fenced code blocks.
These supported elements round-trip between Markdown and HTML. HTML outside
that subset is preserved as plain text where possible, but arbitrary HTML and
Markdown extensions are not guaranteed to round-trip exactly.
 
