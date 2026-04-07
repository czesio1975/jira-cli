"""Markdown conversion utilities.

Converts between CommonMark and Jira wiki markup.
Ported from pkg/md/md.go and pkg/md/jirawiki/parser.go.

Jira wiki reference:
  https://jira.atlassian.com/secure/WikiRendererHelpAction.jspa?section=all
"""

import re


def to_jira_md(text: str) -> str:
    """Convert CommonMark markdown to Jira wiki markup.

    Handles: headings, bold, italic, strikethrough, inline code,
    code blocks, links, images, lists, blockquotes, horizontal rules.
    """
    if not text:
        return text

    lines = text.split("\n")
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code blocks: ```lang ... ```
        m = re.match(r"^```(\w*)$", line)
        if m:
            lang = m.group(1)
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not re.match(r"^```\s*$", lines[i]):
                code_lines.append(lines[i])
                i += 1
            tag = f"{{code:{lang}}}" if lang else "{code}"
            result.append(tag)
            result.extend(code_lines)
            result.append("{code}")
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}\s*$", line) or re.match(r"^\*{3,}\s*$", line) or re.match(r"^_{3,}\s*$", line):
            result.append("----")
            i += 1
            continue

        # Headings: # text -> h1. text
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            result.append(f"h{level}. {m.group(2)}")
            i += 1
            continue

        # Blockquote: > text -> bq. text
        m = re.match(r"^>\s?(.*)", line)
        if m:
            result.append(f"bq. {m.group(1)}")
            i += 1
            continue

        # Unordered list: - item or * item -> * item (with nesting)
        m = re.match(r"^(\s*)[*-]\s+(.+)$", line)
        if m:
            indent = len(m.group(1))
            depth = indent // 2 + 1
            result.append(f"{'*' * depth} {m.group(2)}")
            i += 1
            continue

        # Ordered list: 1. item -> # item (with nesting)
        m = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if m:
            indent = len(m.group(1))
            depth = indent // 2 + 1
            result.append(f"{'#' * depth} {m.group(2)}")
            i += 1
            continue

        result.append(line)
        i += 1

    text = "\n".join(result)

    # Inline conversions (order matters: code first to protect content)
    # Protect inline code spans by replacing them temporarily
    code_spans: list[str] = []

    def _save_code(m: re.Match[str]) -> str:
        code_spans.append(m.group(1))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", _save_code, text)

    # Bold: **text** -> *text* (Jira bold)
    # Use placeholder to prevent italic regex from matching the converted bold
    bold_spans: list[str] = []

    def _save_bold(m: re.Match[str]) -> str:
        bold_spans.append(m.group(1))
        return f"\x00BOLD{len(bold_spans) - 1}\x00"

    text = re.sub(r"\*\*(.+?)\*\*", _save_bold, text)

    # Italic: *text* -> _text_ (single asterisks become underscores in Jira)
    # Match *text* where text doesn't contain asterisks
    text = re.sub(r"\*([^*\n]+?)\*", r"_\1_", text)

    # Restore bold as *text* (Jira bold)
    for idx, content in enumerate(bold_spans):
        text = text.replace(f"\x00BOLD{idx}\x00", f"*{content}*")

    # Strikethrough: ~~text~~ -> -text-
    text = re.sub(r"~~(.+?)~~", r"-\1-", text)

    # Links: [text](url) -> [text|url]
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1|\2]", text)

    # Images: ![alt](url) -> !url|alt!
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f"!{m.group(2)}|{m.group(1)}!" if m.group(1) else f"!{m.group(2)}!", text)

    # Restore inline code: `code` -> {{code}}
    for idx, content in enumerate(code_spans):
        text = text.replace(f"\x00CODE{idx}\x00", f"{{{{{content}}}}}")

    return text


def from_jira_md(text: str) -> str:
    """Convert Jira wiki markup to CommonMark markdown.

    Handles: headings, bold, italic, strikethrough, inline code,
    code blocks, noformat, links, images, lists, blockquotes,
    panels, quotes, tables.
    """
    if not text:
        return text

    lines = text.split("\n")
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code block: {code:lang} ... {code}
        m = re.match(r"^\{code(?::([^}]*))?\}\s*$", line)
        if m:
            lang = m.group(1) or ""
            # Extract language from possible attributes like "title=foo.py"
            if lang and "." in lang and "=" not in lang:
                # Could be a filename like "foo.py", extract extension
                pass
            code_lines: list[str] = []
            i += 1
            while i < len(lines):
                if re.match(r"^\{code\}\s*$", lines[i]):
                    break
                code_lines.append(lines[i])
                i += 1
            result.append(f"```{lang}")
            result.extend(code_lines)
            result.append("```")
            i += 1
            continue

        # Noformat block: {noformat} ... {noformat}
        if re.match(r"^\{noformat\}\s*$", line):
            code_lines = []
            i += 1
            while i < len(lines):
                if re.match(r"^\{noformat\}\s*$", lines[i]):
                    break
                code_lines.append(lines[i])
                i += 1
            result.append("```")
            result.extend(code_lines)
            result.append("```")
            i += 1
            continue

        # Quote block: {quote} ... {quote}
        if re.match(r"^\{quote\}\s*$", line):
            i += 1
            while i < len(lines):
                if re.match(r"^\{quote\}\s*$", lines[i]):
                    break
                result.append(f"> {lines[i]}")
                i += 1
            i += 1
            continue

        # Panel: {panel} or {panel:title=...}
        m = re.match(r"^\{panel(?::([^}]*))?\}\s*$", line)
        if m:
            attrs_str = m.group(1) or ""
            title = ""
            if attrs_str:
                for part in attrs_str.split("|"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        if k.strip() == "title":
                            title = v.strip()
                    else:
                        title = part.strip()
            result.append("---")
            if title:
                result.append(f"**{title}**")
                result.append("")
            i += 1
            while i < len(lines):
                if re.match(r"^\{panel\}\s*$", lines[i]):
                    break
                result.append(lines[i])
                i += 1
            result.append("---")
            i += 1
            continue

        # Headings: h1. text -> # text
        m = re.match(r"^h([1-6])\.\s+(.+)$", line)
        if m:
            level = int(m.group(1))
            result.append(f"{'#' * level} {m.group(2)}")
            i += 1
            continue

        # Block quote: bq. text -> > text
        m = re.match(r"^bq\.\s+(.+)$", line)
        if m:
            result.append(f"> {m.group(1)}")
            i += 1
            continue

        # Table header row: ||h1||h2|| -> |h1|h2| + separator
        if re.match(r"^\|\|.+\|\|\s*$", line):
            headers = line.replace("||", "|")
            result.append(headers)
            # Count columns for separator
            cols = [c for c in headers.split("|") if c or c == ""]
            # Number of cells = number of | minus 1, minus empty edges
            num_cols = headers.count("|") - 1
            result.append("|" + "|".join(["---"] * num_cols) + "|")
            i += 1
            continue

        # Table data row: |c1|c2| -> |c1|c2| (pass through)
        if re.match(r"^\|.+\|\s*$", line) and not line.startswith("||"):
            result.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{4,}\s*$", line):
            result.append("---")
            i += 1
            continue

        # Unordered list: * item, ** item (nested)
        m = re.match(r"^(\*+)\s+(.+)$", line)
        if m:
            depth = len(m.group(1))
            indent = "  " * (depth - 1)
            result.append(f"{indent}- {m.group(2)}")
            i += 1
            continue

        # Ordered list: # item, ## item (nested)
        m = re.match(r"^(#+)\s+(.+)$", line)
        if m:
            depth = len(m.group(1))
            indent = "  " * (depth - 1)
            result.append(f"{indent}1. {m.group(2)}")
            i += 1
            continue

        result.append(line)
        i += 1

    text = "\n".join(result)

    # Inline conversions (protect code spans first)
    # Protect inline code: {{code}} -> placeholder
    code_spans: list[str] = []

    def _save_code(m: re.Match[str]) -> str:
        code_spans.append(m.group(1))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    text = re.sub(r"\{\{(.+?)\}\}", _save_code, text)

    # Bold: *text* -> **text** (but not list items which are already handled)
    # Only match *text* that doesn't start a line (lists already converted)
    bold_spans: list[str] = []

    def _save_bold(m: re.Match[str]) -> str:
        bold_spans.append(m.group(1))
        return f"\x00BOLD{len(bold_spans) - 1}\x00"

    text = re.sub(r"(?<!\w)\*([^\s*].*?[^\s*]|[^\s*])\*(?!\w)", _save_bold, text)

    # Italic: _text_ -> *text*
    text = re.sub(r"(?<!\w)_([^\s_].*?[^\s_]|[^\s_])_(?!\w)", r"*\1*", text)

    # Restore bold as **text**
    for idx, content in enumerate(bold_spans):
        text = text.replace(f"\x00BOLD{idx}\x00", f"**{content}**")

    # Strikethrough: -text- -> ~~text~~
    # Be careful not to match hyphens in words or horizontal rules
    text = re.sub(r"(?<!\w)-([^\s-].*?[^\s-]|[^\s-])-(?!\w)", r"~~\1~~", text)

    # Links: [text|url] -> [text](url)
    text = re.sub(r"\[([^|\]]+)\|([^\]]+)\]", r"[\1](\2)", text)

    # Plain links: [url] -> [url](url) (no pipe means just a URL)
    text = re.sub(r"\[([^\]|]+)\](?!\()", r"[\1](\1)", text)

    # Images: !url|alt! -> ![alt](url)  or  !url! -> ![](url)
    def _convert_image(m: re.Match[str]) -> str:
        content = m.group(1)
        if "|" in content:
            url, alt = content.split("|", 1)
            return f"![{alt}]({url})"
        return f"![]({content})"

    text = re.sub(r"!([^!\n]+)!", _convert_image, text)

    # Restore inline code as `code`
    for idx, content in enumerate(code_spans):
        text = text.replace(f"\x00CODE{idx}\x00", f"`{content}`")

    return text
