# Hello! This script is used to convert Markdown (.md) text into HTML text.

## The Idea:
This project started as a simple idea on converting similar languages back and forth.

## Use Cases:
Converting into a webpage:
- Github README files 
- Discord messages
- personal notes 

 This is useful for converting announcements in a Discord server into an announcement on your website or converting personal notes into an official write up.

 ## Thought Process:
 If I take the different symbols that indicate text manipulation within Markdown and convert them to their HTML equivilent, everything should be convertable fairly simply. Problems and edge cases with doubled symbols (i.e. * * and ** **)

## Usage

Convert a Markdown file to an HTML fragment and print it to the terminal:

```bash
python3 conversion.py README.md
```

Write the result to a file instead:

```bash
python3 conversion.py README.md --output README.html
```

The starter converter supports headings, paragraphs, unordered and ordered
lists, bold and italic text, inline code, links, and fenced code blocks.
 