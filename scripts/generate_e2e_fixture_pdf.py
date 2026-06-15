"""
Generate the committed E2E fixture PDF (tests/fixtures/e2e/sample_bill.pdf).

The PDF is hand-built with a plain-text content stream (no compression, no
external dependencies) so pdfplumber can extract its text layer directly.

Run once: python scripts/generate_e2e_fixture_pdf.py
"""

from __future__ import annotations

from pathlib import Path

LINES = [
    "Acme Utilities",
    "Statement Date: 2026-06-01",
    "Account Number: 9988776655",
    "Bill To: Alice Example",
    "Amount Due: $84.50",
    "Due Date: 2026-07-15",
    "Thank you for your business.",
]


def _escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 12 Tf", "50 750 Td", "14 TL", f"({_escape(lines[0])}) Tj"]
    for line in lines[1:]:
        content_lines.append("T*")
        content_lines.append(f"({_escape(line)}) Tj")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode("ascii")
        out += obj
        out += b"\nendobj\n"

    xref_offset = len(out)
    n = len(objects) + 1
    out += f"xref\n0 {n}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("ascii")
    out += b"trailer\n"
    out += f"<< /Size {n} /Root 1 0 R >>\n".encode("ascii")
    out += b"startxref\n"
    out += f"{xref_offset}\n".encode("ascii")
    out += b"%%EOF"
    return bytes(out)


def main() -> None:
    pdf = build_pdf(LINES)
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / "tests" / "fixtures" / "e2e" / "sample_bill.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(pdf)
    print(f"Wrote {out_path} ({len(pdf)} bytes)")


if __name__ == "__main__":
    main()
