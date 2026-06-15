"""
OCR pipeline — extracts text from PDF files.

Strategy:
  1. pdfplumber — fast, lossless text extraction from PDFs with a text layer.
  2. pytesseract — image-based OCR fallback for scanned (image-only) PDFs.

Returns the extracted text string. Empty string means no text could be extracted.
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

log = logging.getLogger("postmule.ocr")

# Minimum characters from pdfplumber before we consider it "has text"
_MIN_TEXT_LENGTH = 50


_TESSERACT_DPI = 300
_TESSERACT_LANG = "eng"


def extract_text(pdf_path: Path) -> str:
    """
    Extract text from a PDF, trying pdfplumber first then pytesseract.

    Returns:
        Extracted text string. May be empty if extraction fails completely.
    """
    if not pdf_path.exists():
        log.error(f"PDF not found: {pdf_path}")
        return ""

    # --- Try pdfplumber first ---
    text = _extract_with_pdfplumber(pdf_path)
    if len(text.strip()) >= _MIN_TEXT_LENGTH:
        log.debug(f"pdfplumber extracted {len(text)} chars from {pdf_path.name}")
        return text

    log.debug(
        f"pdfplumber got only {len(text.strip())} chars from {pdf_path.name} "
        f"(threshold={_MIN_TEXT_LENGTH}) — trying tesseract"
    )

    # --- Fallback: pytesseract ---
    text = _extract_with_tesseract(pdf_path, _TESSERACT_DPI, _TESSERACT_LANG)
    if text:
        log.debug(f"tesseract extracted {len(text)} chars from {pdf_path.name}")
    else:
        log.warning(
            f"OCR failed for {pdf_path.name} — no text extracted by either method.\n"
            "The PDF may be blank, corrupted, or contain only images with no text.\n"
            "It will be filed as NeedsReview."
        )
    return text


def _extract_with_pdfplumber(pdf_path: Path) -> str:
    try:
        import pdfplumber  # type: ignore[import]
    except ImportError:
        log.warning("pdfplumber not installed — skipping text-layer extraction")
        return ""

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)
            return "\n\n".join(pages)
    except Exception as exc:
        log.debug(f"pdfplumber error on {pdf_path.name}: {exc}")
        return ""


def _tesseract_install_hint() -> str:
    """Per-OS instructions for installing the Tesseract OCR binary."""
    if sys.platform == "win32":
        return (
            "Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki "
            "and ensure tesseract.exe is on PATH."
        )
    if sys.platform == "darwin":
        return "Install Tesseract OCR with: brew install tesseract"
    return (
        "Install Tesseract OCR with: sudo apt install tesseract-ocr "
        "(or your distro's package manager)"
    )


def _extract_with_tesseract(pdf_path: Path, dpi: int, lang: str) -> str:
    try:
        import pytesseract  # type: ignore[import]
        from pdf2image import convert_from_path  # type: ignore[import]
    except ImportError:
        log.warning(
            "pytesseract or pdf2image not installed — cannot perform image OCR.\n"
            "Install with: pip install pytesseract pdf2image\n"
            f"Also install the Tesseract OCR binary. {_tesseract_install_hint()}"
        )
        return ""

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            images = convert_from_path(str(pdf_path), dpi=dpi, output_folder=tmpdir)
            pages = []
            for img in images:
                page_text = pytesseract.image_to_string(img, lang=lang)
                pages.append(page_text)
            return "\n\n".join(pages)
    except Exception as exc:
        not_found_cls = getattr(pytesseract, "TesseractNotFoundError", ())
        if isinstance(not_found_cls, type) and isinstance(exc, not_found_cls):
            log.warning(
                f"Tesseract binary not found — cannot OCR {pdf_path.name}. "
                f"{_tesseract_install_hint()}"
            )
        else:
            log.debug(f"tesseract error on {pdf_path.name}: {exc}")
        return ""
