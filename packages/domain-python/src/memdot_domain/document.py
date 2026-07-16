"""MemdotDocument v1 validation, extraction, and import/export adapters."""

# JSON tree walkers intentionally use loosely typed dict nodes.
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownLambdaType=false

from __future__ import annotations

import hashlib
import json
import re
import uuid
from enum import StrEnum
from typing import Any, cast
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from memdot_domain.ids import new_uuid7


class DocumentValidationError(ValueError):
    """Raised when a document envelope or node policy is violated."""


class BlockType(StrEnum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    BULLET_LIST = "bulletList"
    ORDERED_LIST = "orderedList"
    LIST_ITEM = "listItem"
    BLOCKQUOTE = "blockquote"
    CODE_BLOCK = "codeBlock"
    HORIZONTAL_RULE = "horizontalRule"
    IMAGE = "image"
    UNSUPPORTED = "unsupported_block"


class MarkType(StrEnum):
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"


ALLOWED_BLOCK_TYPES = frozenset(t.value for t in BlockType)
ALLOWED_MARK_TYPES = frozenset(t.value for t in MarkType)


def is_https_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def sanitize_url(url: str) -> str:
    if not is_https_url(url):
        msg = "url_must_be_https"
        raise DocumentValidationError(msg)
    return url.strip()


class MarkAttrs(BaseModel):
    href: str | None = None

    @field_validator("href")
    @classmethod
    def validate_href(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return sanitize_url(value)


class MarkNode(BaseModel):
    type: MarkType
    attrs: MarkAttrs | None = None


class TextNode(BaseModel):
    type: str = "text"
    text: str = ""
    marks: list[MarkNode] = Field(default_factory=lambda: [])


class BlockAttrs(BaseModel):
    blockId: uuid.UUID
    level: int | None = Field(default=None, ge=1, le=6)
    src: str | None = None
    alt: str | None = None

    @field_validator("src")
    @classmethod
    def validate_src(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return sanitize_url(value)


class BlockNode(BaseModel):
    type: BlockType
    attrs: BlockAttrs
    content: list[Any] = Field(default_factory=lambda: [])

    @model_validator(mode="after")
    def validate_heading_level(self) -> BlockNode:
        if self.type == BlockType.HEADING and self.attrs.level is None:
            msg = "heading_requires_level"
            raise ValueError(msg)
        if self.type == BlockType.IMAGE and not self.attrs.src:
            msg = "image_requires_src"
            raise ValueError(msg)
        return self


class DocRoot(BaseModel):
    type: str = "doc"
    content: list[BlockNode] = Field(default_factory=lambda: [])


class MemdotDocument(BaseModel):
    schema_name: str = Field(alias="schema", default="memdot-document")
    schemaVersion: int = 1
    documentId: uuid.UUID
    root: DocRoot

    model_config = {"populate_by_name": True}

    @field_validator("schema_name")
    @classmethod
    def validate_schema(cls, value: str) -> str:
        if value != "memdot-document":
            msg = "invalid_schema"
            raise ValueError(msg)
        return value

    @field_validator("schemaVersion")
    @classmethod
    def validate_version(cls, value: int) -> int:
        if value != 1:
            msg = "unsupported_schema_version"
            raise ValueError(msg)
        return value


def _collect_block_ids(node: dict[str, Any], seen: set[str]) -> None:
    attrs = node.get("attrs") or {}
    block_id = attrs.get("blockId")
    if block_id:
        if block_id in seen:
            msg = "duplicate_block_id"
            raise DocumentValidationError(msg)
        seen.add(str(block_id))
    for child in node.get("content") or []:
        if isinstance(child, dict):
            if child.get("type") == "text":
                for mark in child.get("marks") or []:
                    if isinstance(mark, dict) and mark.get("type") == "link":
                        href = (mark.get("attrs") or {}).get("href")
                        if href:
                            sanitize_url(str(href))
            else:
                _collect_block_ids(child, seen)


def validate_document_payload(payload: dict[str, Any]) -> MemdotDocument:
    """Validate envelope, block IDs, and HTTPS URL policy."""
    try:
        doc = MemdotDocument.model_validate(payload)
    except Exception as exc:
        raise DocumentValidationError(str(exc)) from exc
    seen: set[str] = set()
    root = payload.get("root") or {}
    for block in root.get("content") or []:
        if isinstance(block, dict):
            _collect_block_ids(block, seen)
    return doc


def canonical_document_json(doc: MemdotDocument | dict[str, Any]) -> str:
    if isinstance(doc, MemdotDocument):
        data = doc.model_dump(mode="json", by_alias=True)
    else:
        # Normalize dict payloads through the model so hashes match validated docs.
        data = MemdotDocument.model_validate(doc).model_dump(mode="json", by_alias=True)
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def content_sha256(doc: MemdotDocument | dict[str, Any]) -> str:
    return hashlib.sha256(canonical_document_json(doc).encode("utf-8")).hexdigest()


def _inline_plain(node: dict[str, Any]) -> str:
    return str(node.get("text") or "")


def _block_plain(node: dict[str, Any]) -> str:
    node_type = node.get("type")
    if node_type == "horizontalRule":
        return "\n---\n"
    parts: list[str] = []
    for child in node.get("content") or []:
        if not isinstance(child, dict):
            continue
        if child.get("type") == "text":
            parts.append(_inline_plain(child))
        else:
            parts.append(_block_plain(child))
    text = "".join(parts).strip()
    if node_type == "heading" and text:
        level = (node.get("attrs") or {}).get("level") or 1
        return f"{'#' * int(level)} {text}\n"
    if node_type in {"paragraph", "codeBlock", "listItem"} and text:
        return f"{text}\n"
    if node_type == "blockquote" and text:
        return f"> {text}\n"
    return text


def extract_plain_text(doc: MemdotDocument | dict[str, Any]) -> str:
    if isinstance(doc, MemdotDocument):
        root = doc.root.model_dump(mode="json")
    else:
        root = doc.get("root") or {}
    lines: list[str] = []
    for block in root.get("content") or []:
        if isinstance(block, dict):
            chunk = _block_plain(block).strip()
            if chunk:
                lines.append(chunk)
    return "\n".join(lines).strip()


def document_from_markdown(markdown: str, *, document_id: uuid.UUID | None = None) -> dict[str, Any]:
    """Simple markdown import: headings and paragraphs only."""
    doc_id = document_id or new_uuid7()
    blocks: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            blocks.append(
                {
                    "type": "heading",
                    "attrs": {"blockId": str(new_uuid7()), "level": level},
                    "content": [{"type": "text", "text": text}],
                }
            )
        else:
            blocks.append(
                {
                    "type": "paragraph",
                    "attrs": {"blockId": str(new_uuid7())},
                    "content": [{"type": "text", "text": stripped}],
                }
            )
    return {
        "schema": "memdot-document",
        "schemaVersion": 1,
        "documentId": str(doc_id),
        "root": {"type": "doc", "content": blocks},
    }


def document_to_markdown(doc: MemdotDocument | dict[str, Any]) -> str:
    return extract_plain_text(doc)


def document_to_html(doc: MemdotDocument | dict[str, Any]) -> str:
    """Minimal HTML export with escaped text only (no raw HTML passthrough)."""
    import html

    if isinstance(doc, MemdotDocument):
        root = doc.root.model_dump(mode="json")
    else:
        root = doc.get("root") or {}

    def render_inline(node: dict[str, Any]) -> str:
        text = html.escape(str(node.get("text") or ""))
        for mark in node.get("marks") or []:
            if not isinstance(mark, dict):
                continue
            mtype = mark.get("type")
            if mtype == "bold":
                text = f"<strong>{text}</strong>"
            elif mtype == "italic":
                text = f"<em>{text}</em>"
            elif mtype == "code":
                text = f"<code>{text}</code>"
            elif mtype == "link":
                href = html.escape(str((mark.get("attrs") or {}).get("href") or ""))
                text = f'<a href="{href}">{text}</a>'
        return text

    def render_block(node: dict[str, Any]) -> str:
        ntype = node.get("type")
        children = [
            cast(dict[str, Any], child)
            for child in cast(list[Any], node.get("content") or [])
            if isinstance(child, dict)
        ]
        inner = "".join(
            render_inline(child) if child.get("type") == "text" else render_block(child)
            for child in children
        )
        if ntype == "heading":
            attrs = cast(dict[str, Any], node.get("attrs") or {})
            level = int(cast(Any, attrs.get("level") or 1))
            return f"<h{level}>{inner}</h{level}>"
        if ntype == "paragraph":
            return f"<p>{inner}</p>"
        if ntype == "codeBlock":
            return f"<pre><code>{inner}</code></pre>"
        if ntype == "blockquote":
            return f"<blockquote>{inner}</blockquote>"
        if ntype == "horizontalRule":
            return "<hr/>"
        if ntype == "image":
            attrs = cast(dict[str, Any], node.get("attrs") or {})
            src = html.escape(str(attrs.get("src") or ""))
            alt = html.escape(str(attrs.get("alt") or ""))
            return f'<img src="{src}" alt="{alt}"/>'
        if ntype in {"bulletList", "orderedList"}:
            tag = "ul" if ntype == "bulletList" else "ol"
            items = "".join(render_block(child) for child in children)
            return f"<{tag}>{items}</{tag}>"
        if ntype == "listItem":
            return f"<li>{inner}</li>"
        return f"<div data-unsupported>{inner}</div>"

    root_blocks = [
        cast(dict[str, Any], block)
        for block in cast(list[Any], root.get("content") or [])
        if isinstance(block, dict)
    ]
    body = "".join(render_block(block) for block in root_blocks)
    return f"<!DOCTYPE html><html><body>{body}</body></html>"
