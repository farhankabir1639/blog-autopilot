"""
Converts Claude's structured JSON body blocks into Sanity Portable Text format.

Handles:
  - h2, h3 headings
  - paragraph blocks (with inline bold, italic, links)
  - blockquote
  - image references (inlineImage type in schema)
"""

import re
import uuid


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def blocks_to_portable_text(body_blocks: list, image_lookup: dict) -> list:
    """
    Convert Claude's body block list into Sanity Portable Text blocks.

    Args:
        body_blocks:  List of {"type": ..., "text"/"label": ...} dicts from Claude
        image_lookup: Dict mapping label → {asset_id, alt, caption}

    Returns:
        List of Sanity Portable Text block dicts
    """
    pt_blocks = []

    for block in body_blocks:
        btype = block.get("type", "paragraph")

        if btype == "image":
            label = block.get("label", "")
            img = image_lookup.get(label)
            if img and img.get("asset_id"):
                pt_blocks.append(_make_inline_image(img))
            # If image wasn't generated successfully, skip silently
            continue

        text = block.get("text", "")
        if not text:
            continue

        if btype == "h2":
            pt_blocks.append(_make_heading(text, "h2"))
        elif btype == "h3":
            pt_blocks.append(_make_heading(text, "h3"))
        elif btype == "blockquote":
            pt_blocks.append(_make_block(text, style="blockquote"))
        else:
            # Default: paragraph
            pt_blocks.append(_make_block(text, style="normal"))

    return pt_blocks


# ──────────────────────────────────────────────────────────────────────────────
# Block builders
# ──────────────────────────────────────────────────────────────────────────────

def _make_heading(text: str, style: str) -> dict:
    return {
        "_key":     _key(),
        "_type":    "block",
        "style":    style,
        "children": [_plain_span(text)],
        "markDefs": [],
    }


def _make_block(text: str, style: str = "normal") -> dict:
    """Parse inline markdown (bold, italic, links) into spans with marks."""
    children, mark_defs = _parse_inline(text)
    return {
        "_key":     _key(),
        "_type":    "block",
        "style":    style,
        "children": children,
        "markDefs": mark_defs,
    }


def _make_inline_image(img: dict) -> dict:
    return {
        "_key":   _key(),
        "_type":  "inlineImage",
        "image":  {
            "_type": "image",
            "asset": {
                "_type": "reference",
                "_ref":  img["asset_id"],
            },
        },
        "alt":     img.get("alt", ""),
        "caption": img.get("caption", ""),
    }


def _plain_span(text: str) -> dict:
    return {
        "_key":   _key(),
        "_type":  "span",
        "text":   text,
        "marks":  [],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Inline markdown parser  →  Sanity spans + markDefs
# ──────────────────────────────────────────────────────────────────────────────
# Handles: **bold**, *italic*, [text](url), combinations

def _parse_inline(text: str) -> tuple[list, list]:
    """
    Parse a markdown paragraph string into (children_spans, mark_defs).
    Supports: **bold**, *italic*, [link text](url)
    """
    spans = []
    mark_defs = []
    # Tokenise with a regex that captures the markdown constructs
    pattern = re.compile(
        r'(\[([^\]]+)\]\((https?://[^\)]+|/[^\)]*)\))'  # [text](url)
        r'|(\*\*([^*]+)\*\*)'                           # **bold**
        r'|(\*([^*]+)\*)'                               # *italic*
    )

    last_end = 0
    for m in pattern.finditer(text):
        start, end = m.start(), m.end()

        # Plain text before this match
        if start > last_end:
            spans.append(_plain_span(text[last_end:start]))

        if m.group(1):          # Link
            link_text = m.group(2)
            link_url  = m.group(3)
            link_key  = _key()
            mark_defs.append({
                "_key":  link_key,
                "_type": "link",
                "href":  _ensure_absolute(link_url),
            })
            spans.append({
                "_key":   _key(),
                "_type":  "span",
                "text":   link_text,
                "marks":  [link_key],
            })
        elif m.group(4):        # Bold
            spans.append({
                "_key":   _key(),
                "_type":  "span",
                "text":   m.group(5),
                "marks":  ["strong"],
            })
        elif m.group(6):        # Italic
            spans.append({
                "_key":   _key(),
                "_type":  "span",
                "text":   m.group(7),
                "marks":  ["em"],
            })

        last_end = end

    # Remaining plain text
    if last_end < len(text):
        spans.append(_plain_span(text[last_end:]))

    if not spans:
        spans.append(_plain_span(text))

    return spans, mark_defs


def _ensure_absolute(url: str) -> str:
    """Convert relative paths to absolute iTenX URLs for the link validator."""
    if url.startswith("/"):
        return f"https://itenx.com{url}"
    return url


def _key() -> str:
    """Generate a short unique Sanity _key."""
    return uuid.uuid4().hex[:12]
