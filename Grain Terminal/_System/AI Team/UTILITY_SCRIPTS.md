# Utility Script Registry

Maintained by Finn. One entry per script. Check here before commissioning anything new.

| Script | Location | Purpose | Example call | Date added |
|---|---|---|---|---|
| `extract_pdf_text.py` | `_System/Web App/utils/` | Extract all text from a PDF to a .txt file (page-by-page, with separators) | `python3 utils/extract_pdf_text.py "path/to/file.pdf"` | 2026-05-13 |
| `file_incoming.py` | `_System/Web App/utils/` | Move a file from Incoming/ to its final home in one step — logs + optional DB insert | `python3 utils/file_incoming.py "manual.pdf" "Manuals/" --category manual --area MCC4 --db` | 2026-05-13 |
| `audit_portal.py` | `_System/Web App/utils/` | Full data quality audit — duplicates, orphans, broken links, missing fields. Read-only. | `python3 utils/audit_portal.py` | 2026-05-13 |

---

## Approved installed packages

| Package | Install command | Why installed | Date |
|---|---|---|---|
| `pdfplumber` | pre-installed in sandbox | PDF text + table extraction (used by extract_pdf_text.py) | 2026-05-13 |
| `camelot-py` | pre-installed in sandbox | PDF table extraction to CSV/DataFrame | 2026-05-13 |
| `tabula-py` | pre-installed in sandbox | PDF table extraction (reliable fallback) | 2026-05-13 |
| `pymupdf` | ✅ installed on Paul's Mac | Fast PDF text extraction, handles scanned/complex layouts | 2026-05-13 |
| `sqlite-utils` | ✅ installed on Paul's Mac | Query grain_terminal.db from Terminal without writing Python | 2026-05-13 |

---

## Commissioning a new script

Finn commissions scripts from Dave. Dave saves them to:
`Grain Terminal/_System/Web App/utils/<script_name>.py`

Every script must have:
1. A docstring: what it does, inputs, outputs, example usage
2. A passing test against one real file before sign-off
3. An entry in this registry

## Registry format

```
| script_name.py | _System/Web App/utils/ | One-line description | python3 utils/script_name.py <arg> | YYYY-MM-DD |
```
