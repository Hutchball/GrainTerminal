"""
scan_pdf_pages.py
=================
Scans a linked PDF document and records which pages mention each piece of
equipment linked to that document. Results are saved to document_page_refs.

Usage:
    python3 utils/scan_pdf_pages.py <document_id>

Example:
    python3 utils/scan_pdf_pages.py 450

Requires: pymupdf (fitz) — already installed on Paul's Mac.
Run from: Grain Terminal/_System/Web App/
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import fitz  # pymupdf

sys.path.insert(0, str(Path(__file__).parent.parent))
from db_config import get_connection

# Root of Grain Terminal/ folder — file_path in DB is relative to this
GRAIN_TERMINAL_ROOT = Path(__file__).parent.parent.parent.parent


def get_search_terms(name: str, aliases: list[str]) -> list[str]:
    """Return search terms for an equipment record.

    Strips common prefixes, generates progressively shorter variants, and adds
    known synonym expansions to account for drawing terminology differences.
    """
    SYNONYMS = {
        'TRAVEL':    ['TRAVEL', 'TRAVELLING'],
        'SLEW':      ['SLEW', 'SLEWING'],
        'HYDRAULIC': ['HYDRAULIC', 'HYDRAUL'],
        'COMPRESSOR':['COMPRESSOR'],
        'HORIZONTAL':['HORIZONTAL'],
        'VERTICAL':  ['VERTICAL'],
        'INLET':     ['INLET'],
        'DCE':       ['DCE', 'DUST COLLECTOR', 'DUST FILTER', 'DUST EXTRACTION'],
        'SWITCHROOM':['SWITCHBOARD', 'ELHOUSE', 'SWITCHROOM'],
        'UNLOADER':  ['SHIPUNLOADER', 'SHIP UNLOADER'],
        'CABIN':        ['CABIN'],
        'TRANSFORMER':  ['TRAFO', 'TRANSFORMER ROOM'],
        'HYDRAULIC HOUSE': ['HYDRAUL'],
        'FIRE':         ['FIRE ALARM', 'FIRE'],
        'STORMLOCK':    ['STORM', 'STORMLOCK'],
        'COMPUTER':     ['COMPUTER'],
        'UPS':          ['UPS'],
        'TRAVEL BRAKES':['TRAVELLING BRAKE', 'TRAVEL BRAKE'],
        'SLEW BRAKES':  ['SLEW BRAKE', 'SLEWING BRAKE'],
        'HEATERS':      ['HEATER'],
        'ANEMOMETER':   ['ANEMOMETER', 'WIND'],
        'RADIO':        ['RADIO'],
        'TELEPHONE':    ['TELEPHONE', 'INTERCOM'],
        'LUBRICATION':  ['LUBRICATION', 'GREASE'],
        'SIREN':        ['SIREN', 'SOUNDER', 'BEACON'],
        '240V':         ['240V', 'OUTLET', 'SOCKET'],
        '110V':         ['110V'],
        'FLOODLIGHTS':  ['FLOOD'],
        'LIGHTING':     ['ILLUMINAT', 'LAMP', 'LIGHTING'],
    }
    # Words too generic to use alone in this document
    SKIP_ALONE = {'MOTOR', 'PUMP', 'SHIP', 'UNLOADER', 'BMH', 'HEAD', 'UNIT'}

    terms = set()
    for raw in [name] + aliases:
        cleaned = re.sub(r'^BMH\s+Ship\s+Unloader\s+', '', raw, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^BMH\s+', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+\d+$', '', cleaned).strip()  # strip trailing number
        upper = cleaned.upper()

        # Add the full cleaned phrase
        if upper and len(upper) > 2 and upper not in SKIP_ALONE:
            terms.add(upper)

        # Add synonym expansions for each significant word
        for word in upper.split():
            if word in SYNONYMS:
                for syn in SYNONYMS[word]:
                    terms.add(syn)

    return list(terms)


def scan_document(doc_id: int):
    conn = get_connection()
    cur = conn.cursor()

    # Get document
    cur.execute("SELECT id, filename, file_path FROM documents WHERE id = ?", (doc_id,))
    doc_row = cur.fetchone()
    if not doc_row:
        print(f"ERROR: No document with id {doc_id}")
        conn.close()
        sys.exit(1)

    file_path = GRAIN_TERMINAL_ROOT / doc_row["file_path"]
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        conn.close()
        sys.exit(1)

    print(f"Document: {doc_row['filename']}")
    print(f"Path: {file_path}")

    # Get equipment linked to this document
    cur.execute("SELECT equipment_ids FROM documents WHERE id = ?", (doc_id,))
    raw_ids = cur.fetchone()["equipment_ids"]
    equipment_ids = json.loads(raw_ids) if raw_ids else []
    if not equipment_ids:
        print("No equipment linked to this document.")
        conn.close()
        return

    # Get equipment names and aliases
    equipment = {}
    for eid in equipment_ids:
        cur.execute("SELECT id, name FROM equipment WHERE id = ?", (eid,))
        row = cur.fetchone()
        if not row:
            continue
        cur.execute("SELECT alias_name FROM equipment_aliases WHERE equipment_id = ?", (eid,))
        aliases = [r["alias_name"] for r in cur.fetchall()]
        terms = get_search_terms(row["name"], aliases)
        equipment[eid] = {"name": row["name"], "terms": terms}

    print(f"Scanning {len(equipment)} equipment records across all pages...")

    # Extract text from every page
    pdf = fitz.open(str(file_path))
    page_texts = [pdf[i].get_text().upper() for i in range(len(pdf))]
    pdf.close()
    print(f"Pages extracted: {len(page_texts)}")

    # Match equipment to pages
    now = datetime.utcnow().isoformat()
    matched = 0
    for eid, info in equipment.items():
        pages_found = []
        for page_num, text in enumerate(page_texts, start=1):
            if any(term in text for term in info["terms"]):
                pages_found.append(page_num)

        if not pages_found:
            print(f"  {info['name']}: no pages found (terms: {info['terms']})")
            continue

        # Skip if term appears on more than half of all pages — it's in the header/boilerplate
        if len(pages_found) > len(page_texts) * 0.5:
            print(f"  {info['name']}: skipped — term appears on {len(pages_found)}/{len(page_texts)} pages (boilerplate)")
            continue

        print(f"  {info['name']}: {len(pages_found)} pages — {pages_found[:8]}{'...' if len(pages_found) > 8 else ''}")

        cur.execute("""
            INSERT INTO document_page_refs (document_id, equipment_id, pages, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(document_id, equipment_id) DO UPDATE SET pages = excluded.pages, created_at = excluded.created_at
        """, (doc_id, eid, json.dumps(pages_found), now))
        matched += 1

    conn.commit()
    conn.close()
    print(f"\nDone — {matched} equipment records matched and saved.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 utils/scan_pdf_pages.py <document_id>")
        sys.exit(1)
    scan_document(int(sys.argv[1]))
