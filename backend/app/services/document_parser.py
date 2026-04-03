"""Pass 1: Document structure extraction (no LLM cost).

Extracts text and detects heading/section structure from PDF, DOCX, HTML, and TXT files.
Produces a list of Section objects suitable for Pass 2 knowledge extraction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Section:
    """A structural section within a parsed document."""
    id: str
    title: str
    level: int
    char_start: int
    char_end: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    parent_section_id: Optional[str] = None


@dataclass
class DocumentStructure:
    """Full parsed structure of a document."""
    title: str
    total_pages: Optional[int]
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "total_pages": self.total_pages,
            "sections": [asdict(s) for s in self.sections],
        }


def extract_text_pdf(file_bytes: bytes) -> tuple[str, DocumentStructure]:
    """Extract text and structure from a PDF using PyMuPDF."""
    import fitz

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text: list[str] = []
    page_offsets: list[int] = []
    offset = 0

    for page in doc:
        text = page.get_text("text")
        page_offsets.append(offset)
        pages_text.append(text)
        offset += len(text) + 1  # +1 for joining newline

    full_text = "\n".join(pages_text)
    title = doc.metadata.get("title", "") or ""

    # Try TOC first
    toc = doc.get_toc()
    sections: list[Section] = []

    if toc:
        for i, entry in enumerate(toc):
            level, heading, page_num = entry[0], entry[1], entry[2]
            page_idx = max(0, page_num - 1)
            char_start = page_offsets[page_idx] if page_idx < len(page_offsets) else 0
            # char_end is start of next section or end of text
            if i + 1 < len(toc):
                next_page_idx = max(0, toc[i + 1][2] - 1)
                char_end = page_offsets[next_page_idx] if next_page_idx < len(page_offsets) else len(full_text)
            else:
                char_end = len(full_text)

            sections.append(Section(
                id=f"s{i}",
                title=heading.strip(),
                level=level,
                char_start=char_start,
                char_end=char_end,
                page_start=page_num,
                page_end=toc[i + 1][2] - 1 if i + 1 < len(toc) else doc.page_count,
            ))
    else:
        # Fallback: detect headings by font size analysis
        sections = _detect_headings_by_font(doc, full_text, page_offsets)

    if not title and sections:
        title = sections[0].title

    _assign_parents(sections)

    doc.close()
    structure = DocumentStructure(
        title=title,
        total_pages=len(pages_text),
        sections=sections,
    )
    return full_text, structure


def _detect_headings_by_font(
    doc: "fitz.Document",
    full_text: str,
    page_offsets: list[int],
) -> list[Section]:
    """Fallback heading detection using font size distribution."""
    import fitz

    # Collect font sizes for all text spans
    size_lines: list[tuple[float, str, int, int]] = []
    for page_idx, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                max_size = max(s.get("size", 10) for s in spans)
                text = "".join(s.get("text", "") for s in spans).strip()
                if text and len(text) < 200:
                    size_lines.append((max_size, text, page_idx, 0))

    if not size_lines:
        return _fallback_regex_sections(full_text)

    # Find the body text size (most common)
    from collections import Counter
    size_counts = Counter(round(s, 1) for s, _, _, _ in size_lines)
    body_size = size_counts.most_common(1)[0][0]

    # Headings are lines with font size notably larger than body
    threshold = body_size + 1.5
    sections: list[Section] = []

    for i, (size, text, page_idx, _) in enumerate(size_lines):
        if size < threshold:
            continue
        if len(text) < 2:
            continue

        # Determine heading level by size buckets
        if size >= body_size + 6:
            level = 1
        elif size >= body_size + 3:
            level = 2
        else:
            level = 3

        # Find char position in full text
        char_start = full_text.find(text)
        if char_start == -1:
            char_start = page_offsets[page_idx] if page_idx < len(page_offsets) else 0

        sections.append(Section(
            id=f"s{len(sections)}",
            title=text,
            level=level,
            char_start=char_start,
            char_end=0,
            page_start=page_idx + 1,
        ))

    # Fill in char_end values
    _fill_char_ends(sections, len(full_text))

    return sections if sections else _fallback_regex_sections(full_text)


def extract_text_docx(file_bytes: bytes) -> tuple[str, DocumentStructure]:
    """Extract text and structure from a DOCX file."""
    import io
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    lines: list[str] = []
    sections: list[Section] = []
    offset = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        style_name = (para.style.name or "").lower() if para.style else ""

        # Detect headings from styles
        heading_match = re.match(r"heading\s*(\d+)", style_name)
        if heading_match and text:
            level = int(heading_match.group(1))
            sections.append(Section(
                id=f"s{len(sections)}",
                title=text,
                level=level,
                char_start=offset,
                char_end=0,
            ))

        if text:
            lines.append(text)
            offset += len(text) + 1

    full_text = "\n".join(lines)
    _fill_char_ends(sections, len(full_text))
    _assign_parents(sections)

    title = sections[0].title if sections else ""
    if not sections:
        sections = _fallback_regex_sections(full_text)

    return full_text, DocumentStructure(title=title, total_pages=None, sections=sections)


def extract_text_html(file_bytes: bytes) -> tuple[str, DocumentStructure]:
    """Extract text and structure from an HTML file."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(file_bytes, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Remove script/style tags
    for tag in soup(["script", "style"]):
        tag.decompose()

    full_text = soup.get_text(separator="\n", strip=True)
    sections: list[Section] = []

    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        heading_text = tag.get_text(strip=True)
        if not heading_text:
            continue
        level = int(tag.name[1])
        char_start = full_text.find(heading_text)
        if char_start == -1:
            continue

        sections.append(Section(
            id=f"s{len(sections)}",
            title=heading_text,
            level=level,
            char_start=char_start,
            char_end=0,
        ))

    _fill_char_ends(sections, len(full_text))
    _assign_parents(sections)

    if not sections:
        sections = _fallback_regex_sections(full_text)

    return full_text, DocumentStructure(title=title, total_pages=None, sections=sections)


def extract_text_txt(file_bytes: bytes) -> tuple[str, DocumentStructure]:
    """Extract text and detect structure from a plain text file."""
    full_text = file_bytes.decode("utf-8", errors="replace")
    sections = _fallback_regex_sections(full_text)
    title = sections[0].title if sections else ""
    return full_text, DocumentStructure(title=title, total_pages=None, sections=sections)


# -- Shared helpers --

# Patterns for heading detection in plain text
_HEADING_PATTERNS = [
    # "Chapter 1: Title" or "CHAPTER 1 - Title"
    (re.compile(r"^(chapter|part)\s+(\d+|[IVXLC]+)[:\-.\s]+(.+)", re.IGNORECASE), 1),
    # "Section 1.2 Title" or "1.2 Title" (numbered sections)
    (re.compile(r"^(\d+\.)+\d*\s+(.+)"), 2),
    # ALL CAPS lines (at least 4 chars, not all punctuation)
    (re.compile(r"^([A-Z][A-Z\s\-&:,]{3,})$"), 2),
]


def _fallback_regex_sections(full_text: str) -> list[Section]:
    """Detect sections via regex patterns in plain text."""
    sections: list[Section] = []
    offset = 0

    for line in full_text.split("\n"):
        stripped = line.strip()
        for pattern, level in _HEADING_PATTERNS:
            if pattern.match(stripped) and len(stripped) < 200:
                sections.append(Section(
                    id=f"s{len(sections)}",
                    title=stripped,
                    level=level,
                    char_start=offset,
                    char_end=0,
                ))
                break
        offset += len(line) + 1

    _fill_char_ends(sections, len(full_text))
    _assign_parents(sections)

    # If no sections detected, treat entire doc as one section
    if not sections:
        sections = [Section(
            id="s0",
            title="Full Document",
            level=1,
            char_start=0,
            char_end=len(full_text),
        )]

    return sections


def _fill_char_ends(sections: list[Section], text_length: int) -> None:
    """Set char_end for each section to the start of the next section."""
    for i, sec in enumerate(sections):
        if i + 1 < len(sections):
            sec.char_end = sections[i + 1].char_start
        else:
            sec.char_end = text_length


def _assign_parents(sections: list[Section]) -> None:
    """Assign parent_section_id based on heading levels."""
    stack: list[Section] = []
    for sec in sections:
        while stack and stack[-1].level >= sec.level:
            stack.pop()
        if stack:
            sec.parent_section_id = stack[-1].id
        stack.append(sec)


def parse_document(
    file_bytes: bytes,
    file_format: str,
) -> tuple[str, DocumentStructure]:
    """Route to the correct parser based on file format.

    Returns (full_text, structure).
    """
    fmt = file_format.lower().strip(".")
    if fmt == "pdf":
        return extract_text_pdf(file_bytes)
    elif fmt in ("docx", "doc"):
        return extract_text_docx(file_bytes)
    elif fmt in ("html", "htm"):
        return extract_text_html(file_bytes)
    elif fmt == "txt":
        return extract_text_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
