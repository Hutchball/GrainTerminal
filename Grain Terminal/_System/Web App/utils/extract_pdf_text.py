"""
extract_pdf_text.py — Extract all text from a PDF to a plain .txt file.

Purpose:
    Avoids loading large PDFs into an LLM context as images.
    Run this first; then read the .txt file — much cheaper per page.

Inputs:
    <pdf_path>      Path to the source PDF
    [output_path]   Optional: path for the output .txt file
                    Defaults to same directory as PDF, same name, .txt extension

Outputs:
    A .txt file containing all extracted text, with page separators.

Dependencies:
    pip install pdfplumber --break-system-packages

Example:
    python3 utils/extract_pdf_text.py "Manuals/Fike panel manual.pdf"
    python3 utils/extract_pdf_text.py "Manuals/Fike panel manual.pdf" "data/fike_text.txt"
"""

import sys
import os

def extract(pdf_path: str, output_path: str | None = None) -> str:
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Run:")
        print("  pip install pdfplumber --break-system-packages")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    if output_path is None:
        base = os.path.splitext(pdf_path)[0]
        output_path = base + ".txt"

    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines.append(f"--- PAGE {i} of {total} ---")
            lines.append(text.strip())
            lines.append("")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    word_count = len(content.split())
    print(f"Extracted {total} pages → {output_path} ({word_count:,} words)")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 utils/extract_pdf_text.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    extract(pdf_path, output_path)
