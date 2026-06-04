"""
pdf_parser.py
Extracts text AND tables from a financial PDF using pdfplumber.

Key insight for financial RAG:
  - Regular text extraction loses table structure (numbers get jumbled)
  - We handle text and tables separately, then merge them back in page order
  - Each chunk carries metadata: page number, type (text/table), source section
"""

import re
import pdfplumber
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Chunk:
    """A single retrievable unit of content from the PDF."""
    chunk_id: str
    text: str               # Human-readable content (what gets embedded & searched)
    page: int
    chunk_type: str         # "text" | "table"
    section: str            # Best-guess section heading (e.g. "Revenue by Business Segment")
    # Numeric metadata: extracted figures for exact-match fallback
    numbers: list[str] = field(default_factory=list)

    def __repr__(self):
        preview = self.text[:80].replace("\n", " ")
        return f"Chunk(id={self.chunk_id}, page={self.page}, type={self.chunk_type}, preview='{preview}...')"


def extract_numbers(text: str) -> list[str]:
    """Pull all dollar figures and percentages out of a text block."""
    # Matches: $4,820.5M  $612.4  4,820.5  17.3%  +21.2%
    pattern = r'\$[\d,]+\.?\d*\s*[MB]?|[\+\-]?\d+\.?\d*%|[\d,]+\.\d+'
    return re.findall(pattern, text)


def table_to_text(table: list[list]) -> str:
    """
    Convert a pdfplumber table (list of rows) into a readable text block.
    This is what gets stored in the chunk — readable by both BM25 and the LLM.
    """
    if not table or not table[0]:
        return ""
    rows = []
    for row in table:
        # Replace None cells with empty string
        cleaned = [str(cell).strip() if cell else "" for cell in row]
        rows.append(" | ".join(cleaned))
    return "\n".join(rows)


def detect_section(text: str, current_section: str) -> str:
    """
    Heuristic: if a line looks like a section heading (short, title-case, ends with no period),
    update the running section tracker.
    """
    for line in text.split("\n"):
        line = line.strip()
        # Numbered headings like "1. Executive Summary" or "4. Consolidated Income Statement"
        if re.match(r'^\d+\.\s+[A-Z]', line) and len(line) < 80:
            return line
        # Plain title-case short lines
        if len(line) > 5 and len(line) < 60 and line[0].isupper() and not line.endswith("."):
            return line
    return current_section


def parse_pdf(pdf_path: str, max_text_chunk_chars: int = 600) -> list[Chunk]:
    """
    Main parser. Returns a flat list of Chunk objects, one per logical unit.

    Strategy:
      1. For each page, extract tables first (pdfplumber does this well)
      2. Extract remaining text (pdfplumber masks out table areas automatically)
      3. Split long text blocks into overlapping chunks to avoid cutting mid-sentence
      4. Tag every chunk with page number, section, and extracted numbers
    """
    chunks = []
    chunk_counter = 0
    current_section = "Introduction"

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            # ── Step 1: Extract tables ──────────────────────────
            tables = page.extract_tables()
            table_texts = set()  # track table content to avoid duplicating in text

            for table in tables:
                if not table:
                    continue
                table_text = table_to_text(table)
                if len(table_text.strip()) < 10:
                    continue

                table_texts.add(table_text[:50])  # fingerprint first 50 chars
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"chunk_{chunk_counter:04d}",
                    text=table_text,
                    page=page_num,
                    chunk_type="table",
                    section=current_section,
                    numbers=extract_numbers(table_text),
                ))

            # ── Step 2: Extract page text ───────────────────────
            raw_text = page.extract_text() or ""

            # Update section heading tracker
            current_section = detect_section(raw_text, current_section)

            # Split into paragraphs; skip very short lines (page numbers, headers)
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 40]

            # ── Step 3: Chunk long paragraphs with overlap ──────
            buffer = ""
            for para in paragraphs:
                buffer = (buffer + " " + para).strip()

                if len(buffer) >= max_text_chunk_chars:
                    chunk_counter += 1
                    chunks.append(Chunk(
                        chunk_id=f"chunk_{chunk_counter:04d}",
                        text=buffer,
                        page=page_num,
                        chunk_type="text",
                        section=current_section,
                        numbers=extract_numbers(buffer),
                    ))
                    # Overlap: carry last ~150 chars into next chunk to avoid cutting context
                    buffer = buffer[-150:]

            # Flush remaining buffer
            if len(buffer) > 40:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"chunk_{chunk_counter:04d}",
                    text=buffer,
                    page=page_num,
                    chunk_type="text",
                    section=current_section,
                    numbers=extract_numbers(buffer),
                ))

    print(f"Parsed {len(chunks)} chunks from {pdf_path}")
    return chunks


if __name__ == "__main__":
    chunks = parse_pdf("/home/claude/financial_rag/data/novatech_earnings_report.pdf")
    for c in chunks[:5]:
        print(c)
        print(f"  Numbers found: {c.numbers[:5]}")
        print()
