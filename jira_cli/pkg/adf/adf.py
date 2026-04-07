"""Atlassian Document Format (ADF) handling.

Converted from pkg/adf/adf.go

ADF is the JSON format used by Jira API v3 for rich text content.
"""

from enum import Enum
from typing import Any, Optional


class NodeType(str, Enum):
    """ADF node types."""

    # Parent nodes
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    BLOCKQUOTE = "blockquote"
    CODE_BLOCK = "codeBlock"
    BULLET_LIST = "bulletList"
    ORDERED_LIST = "orderedList"
    TABLE = "table"
    PANEL = "panel"

    # Child nodes
    TEXT = "text"
    LIST_ITEM = "listItem"
    TABLE_ROW = "tableRow"
    TABLE_HEADER = "tableHeader"
    TABLE_CELL = "tableCell"

    # Inline nodes
    INLINE_CARD = "inlineCard"
    EMOJI = "emoji"
    MENTION = "mention"
    HARD_BREAK = "hardBreak"

    # Marks (formatting)
    MARK_EM = "em"
    MARK_LINK = "link"
    MARK_CODE = "code"
    MARK_STRIKE = "strike"
    MARK_STRONG = "strong"


class ADF:
    """Atlassian Document Format document."""

    def __init__(self, data: Optional[dict[str, Any]] = None) -> None:
        self.data = data or {"version": 1, "type": "doc", "content": []}

    @property
    def version(self) -> int:
        return self.data.get("version", 1)

    @property
    def doc_type(self) -> str:
        return self.data.get("type", "doc")

    @property
    def content(self) -> list[dict[str, Any]]:
        return self.data.get("content", [])

    def to_markdown(self) -> str:
        """Convert ADF to markdown string."""
        return self._render_content(self.content)

    def _render_content(self, content: list[dict[str, Any]]) -> str:
        """Render content list to markdown."""
        lines = []
        for node in content:
            lines.append(self._render_node(node))
        return "\n".join(lines)

    def _render_node(self, node: dict[str, Any]) -> str:
        """Render a single node to markdown."""
        node_type = node.get("type", "")

        if node_type == "paragraph":
            return self._render_paragraph(node)
        elif node_type == "heading":
            return self._render_heading(node)
        elif node_type == "bulletList":
            return self._render_bullet_list(node)
        elif node_type == "orderedList":
            return self._render_ordered_list(node)
        elif node_type == "codeBlock":
            return self._render_code_block(node)
        elif node_type == "blockquote":
            return self._render_blockquote(node)
        elif node_type == "table":
            return self._render_table(node)
        elif node_type == "text":
            return self._render_text(node)
        else:
            return ""

    def _render_paragraph(self, node: dict[str, Any]) -> str:
        """Render paragraph node."""
        content = node.get("content", [])
        return "".join(self._render_node(c) for c in content)

    def _render_heading(self, node: dict[str, Any]) -> str:
        """Render heading node."""
        level = node.get("attrs", {}).get("level", 1)
        content = node.get("content", [])
        text = "".join(self._render_node(c) for c in content)
        return f"{'#' * level} {text}"

    def _render_bullet_list(self, node: dict[str, Any]) -> str:
        """Render bullet list."""
        lines = []
        for item in node.get("content", []):
            text = self._render_node(item)
            for line in text.split("\n"):
                lines.append(f"- {line}")
        return "\n".join(lines)

    def _render_ordered_list(self, node: dict[str, Any]) -> str:
        """Render ordered list."""
        lines = []
        for i, item in enumerate(node.get("content", []), 1):
            text = self._render_node(item)
            for line in text.split("\n"):
                lines.append(f"{i}. {line}")
        return "\n".join(lines)

    def _render_code_block(self, node: dict[str, Any]) -> str:
        """Render code block."""
        language = node.get("attrs", {}).get("language", "")
        content = node.get("content", [])
        text = "".join(self._render_node(c) for c in content)
        return f"```{language}\n{text}\n```"

    def _render_blockquote(self, node: dict[str, Any]) -> str:
        """Render blockquote."""
        content = node.get("content", [])
        text = "\n".join(self._render_node(c) for c in content)
        lines = [f"> {line}" for line in text.split("\n")]
        return "\n".join(lines)

    def _render_table(self, node: dict[str, Any]) -> str:
        """Render table."""
        rows = []
        for row in node.get("content", []):
            cells = []
            for cell in row.get("content", []):
                cells.append(self._render_node(cell))
            rows.append("| " + " | ".join(cells) + " |")
        return "\n".join(rows)

    def _render_text(self, node: dict[str, Any]) -> str:
        """Render text node with marks."""
        text = node.get("text", "")
        marks = node.get("marks", [])

        for mark in reversed(marks):
            mark_type = mark.get("type", "")
            if mark_type == "strong":
                text = f"**{text}**"
            elif mark_type == "em":
                text = f"*{text}*"
            elif mark_type == "code":
                text = f"`{text}`"
            elif mark_type == "strike":
                text = f"~~{text}~~"
            elif mark_type == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"

        return text


def parse_adf(data: Any) -> Optional[ADF]:
    """Parse ADF from API response."""
    if data is None:
        return None
    if isinstance(data, dict):
        return ADF(data)
    return None


def adf_to_markdown(data: Any) -> str:
    """Convert ADF data to markdown string."""
    adf = parse_adf(data)
    if adf:
        return adf.to_markdown()
    return ""


def text_to_adf(text: str) -> dict[str, Any]:
    """Convert plain text to ADF format."""
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }