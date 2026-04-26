"""
import_existing.py
Populates grain_terminal.db from files in "Grain Terminal/".
Safe to re-run: uses INSERT OR IGNORE throughout.
Run from the project root:  python3 import_existing.py
"""

import os
import re
import sqlite3
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GRAIN_DIR    = os.path.join(PROJECT_ROOT, "Grain Terminal")
DB_PATH      = os.path.join(PROJECT_ROOT, "grain_terminal.db")

NOW = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------
FILENAME_RE = re.compile(
    r'^([A-Z0-9\-]+(?:\s*\([ivxIVX0-9]+\))?)\s*[-\u2013]\s*(.+?)(?:\s*[-\u2013]\s*SEAFORTH.*)?$'
)


def parse_filename(stem: str):
    """Return (drawing_ref, drawing_type, description) from a file stem."""
    stem_upper = stem.upper().strip()
    m = FILENAME_RE.match(stem_upper)
    if m:
        drawing_ref  = m.group(1).strip()
        description  = m.group(2).strip()
        drawing_type = drawing_ref.split("-")[0] if "-" in drawing_ref else None
        return drawing_ref, drawing_type, description
    # No match – use stem as description
    return None, None, stem.strip()


# ---------------------------------------------------------------------------
# Category / area / mcc from path
# ---------------------------------------------------------------------------
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic"}

def classify_file(abs_path: str, rel_path: str):
    """
    Return (category, area, mcc) based on file location and extension.
    rel_path is relative to GRAIN_DIR.
    """
    parts = rel_path.replace("\\", "/").split("/")
    top   = parts[0] if parts else ""
    ext   = os.path.splitext(abs_path)[1].lower()

    # Extension-first overrides
    if ext in PHOTO_EXTS:
        if top == "Ship Unloader BMH":
            return "photo", "Ship Unloader BMH", None
        return "photo", top if top else "Photos", None

    if ext == ".md":
        return "research", top if top else None, None

    if ext == ".html":
        return "research", top if top else None, None

    # Switchrooms sub-folder rules
    if top == "Switchrooms" and len(parts) >= 2:
        mcc_folder = parts[1]
        return "electrical_drawing", "Switchrooms", mcc_folder

    # Top-level folder rules
    folder_map = {
        "Obsolete":         ("obsolete",         "Obsolete",         None),
        "Photos":           ("photo",             "Photos",           None),
        "Compliance":       ("compliance",        "Compliance",       None),
        "Maintenance Logs": ("maintenance_log",   "Maintenance Logs", None),
        "Manuals":          ("manual",            "Manuals",          None),
        "Equipment":        ("research",          "Equipment",        None),
        # Folders with Electrical Schematics sub-folders
        "Basement-Receiving": ("electrical_drawing", "Basement-Receiving", None),
        "Dust Plants":        ("electrical_drawing", "Dust Plants",        None),
        "Mill Feed":          ("electrical_drawing", "Mill Feed",          None),
        "Silo 1":             ("electrical_drawing", "Silo 1",             None),
        "Silo 2":             ("electrical_drawing", "Silo 2",             None),
        "Silo 3":             ("electrical_drawing", "Silo 3",             None),
        "Ship Unloader BMH":  ("electrical_drawing", "Ship Unloader BMH",  None),
    }
    if top in folder_map:
        # Ship Unloader BMH / Photos sub-folder -> photo
        if top == "Ship Unloader BMH" and len(parts) >= 2 and parts[1] == "Photos":
            return "photo", "Ship Unloader BMH", None
        return folder_map[top]

    # Root-level files
    return "research", None, None


# ---------------------------------------------------------------------------
# Skip rules
# ---------------------------------------------------------------------------
SKIP_NAMES = {".DS_Store", "Equipment_List_Master.md"}


def should_skip(abs_path: str, rel_path: str) -> bool:
    filename = os.path.basename(abs_path)
    if filename in SKIP_NAMES:
        return True
    # README.md files inside Photos folders
    parts = rel_path.replace("\\", "/").split("/")
    if filename.lower() == "readme.md" and "Photos" in parts:
        return True
    return False


# ---------------------------------------------------------------------------
# Equipment seed data
# ---------------------------------------------------------------------------
EQUIPMENT_SEED = [
    # Ship Unloader
    ("BMH Ship Unloader", "ship_unloader", "Ship Unloader", None, "[]", "Siwertell (Bruks Siwertell)", None, "Current equipment - original marine legs defunct"),
    # Receiving Area
    ("Receiving Belt RB1", "belt_conveyor", "Receiving Area", "MCC1/MCC2", '["DTX-361-AA"]', None, None, ""),
    ("Receiving Belt RB2", "belt_conveyor", "Receiving Area", "MCC1/MCC2", '["DTX-361-AA"]', None, None, ""),
    ("Receiving Chain RC1", "chain_conveyor", "Receiving Area", "MCC1/MCC2", '[]', None, None, ""),
    ("Receiving Chain RC2", "chain_conveyor", "Receiving Area", "MCC1/MCC2", '[]', None, None, ""),
    ("Junction House Elevator JH El1", "bucket_elevator", "Receiving Area", "MCC1/MCC2", '[]', None, None, "Bucket elevator"),
    ("Junction House Elevator JH El2", "bucket_elevator", "Receiving Area", "MCC1/MCC2", '[]', None, None, "Bucket elevator"),
    ("Dust Filter Fan D.P.1", "dust_filter", "Receiving Area", "MCC1A", '["DTX-361-AA"]', None, None, "Includes DPDT relay"),
    ("Rotary Valve R.V.1", "rotary_valve", "Receiving Area", "MCC1A", '["DTX-361-AA"]', None, None, "ATEX - dust handling"),
    ("Junction Tower Elevator J.L.1", "bucket_elevator", "Receiving Area", "MCC1A", '["DTX-361-AA"]', None, None, "Bucket elevator"),
    # Silo 2
    ("Silo 2 Control Panel", "control_panel", "Silo 2", "MCC12B", '["DTX-361-DN"]', None, None, "Sheet 1 of 2"),
    ("Tripper RB8", "tripper", "Silo 2", "MCC12", '["GTX-361-CT"]', None, None, "Tripper control panel"),
    ("Tripper RB9", "tripper", "Silo 2", "MCC12", '["GTX-361-CU"]', None, None, "Tripper control panel"),
    # Dust Plants
    ("Dust Plant 12 - Elevator", "bucket_elevator", "Dust Plants", "MCC2", '["CTX-361-DS"]', None, None, "Motors M1, M2"),
    ("Dust Plant 12 - Chain Conveyor", "chain_conveyor", "Dust Plants", "MCC2", '["CTX-361-DS"]', None, None, ""),
    ("Dust Plant 12 - Fan", "dust_filter", "Dust Plants", "MCC2", '["CTX-361-D7","CTX-361-DT"]', None, None, ""),
    ("Dust Plant 13 - Elevator", "bucket_elevator", "Dust Plants", "MCC2", '["CTX-361-DS"]', None, None, "Slave relay system"),
    ("Dust Plant 13 - Chain Conveyor", "chain_conveyor", "Dust Plants", "MCC2", '["CTX-361-DS"]', None, None, ""),
    ("Dust Plant 13 - Fan", "dust_filter", "Dust Plants", "MCC2", '["CTX-361-DU"]', None, None, ""),
    # Basement
    ("Basement Belt Conveyor No 4", "belt_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-BN"]', None, None, ""),
    ("Basement Belt Conveyor No 5", "belt_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-BP"]', None, None, ""),
    ("Basement Belt Conveyor No 7", "belt_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-BZ"]', None, None, ""),
    ("Basement Chain Conveyor No 1", "chain_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-CD"]', None, None, ""),
    ("Basement Chain Conveyor No 2", "chain_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-CE"]', None, None, ""),
    ("Basement Chain Conveyor No 3", "chain_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-BX"]', None, None, ""),
    ("Receiving Chain Conveyor 3", "chain_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-CH"]', None, None, ""),
    ("Receiving Chain Conveyor 4", "chain_conveyor", "Basement-Receiving", "MCC2", '["CTX-361-CJ"]', None, None, ""),
    ("Basement Belt Valve 1", "rotary_valve", "Basement-Receiving", "MCC2", '["CTX-361-B"]', None, None, ""),
    ("Basement Chain Conv 1 Valve 1", "rotary_valve", "Basement-Receiving", "MCC2", '["CTX-361-BU"]', None, None, ""),
    ("Basement Chain Conv 1 Valve 2", "rotary_valve", "Basement-Receiving", "MCC2", '["CTX-361-BV"]', None, None, ""),
    ("Basement Chain Conv 2 Valve 1", "rotary_valve", "Basement-Receiving", "MCC2", '["CTX-361-BW"]', None, None, ""),
    ("Rotary Bin Discharger No 1", "rotary_valve", "Basement-Receiving", "MCC2", '["CTX-361-CG"]', None, None, ""),
    ("Rotary Bin Discharger No 2", "rotary_valve", "Basement-Receiving", "MCC2", '["CTX-361-CG"]', None, None, ""),
    # Trippers
    ("Tripper No 6", "tripper", "Silo 3", "MCC3", '["27A"]', None, None, "Compressor-tripper"),
    ("Tripper No 8", "tripper", "Silo 3", "MCC3", '["DTX-361-DC","CTX-361-CX"]', None, None, "Control circuits"),
    ("Tripper No 9", "tripper", "Silo 3", "MCC3", '["DTX-361-DE","CTX-361-CX"]', None, None, "Control circuits"),
    # MCC13 Silo 3
    ("Receiving Chain Conveyor 3 Valve 1", "chain_conveyor", "Silo 3", "MCC13", '["CTX-361-CH"]', None, None, "RCC3V1"),
    ("Receiving Chain Conveyor 4 Valve 1", "chain_conveyor", "Silo 3", "MCC13", '["CTX-361-CM"]', None, None, ""),
    ("Receiving Chain Conveyor 4 Valve 2", "chain_conveyor", "Silo 3", "MCC13", '["CTX-361-CL"]', None, None, ""),
    ("Receiving Chain Conveyor 4 Valve 3", "chain_conveyor", "Silo 3", "MCC13", '["CTX-361-CK"]', None, None, ""),
    ("Receiving Chain Conveyor 4 Valve 4", "chain_conveyor", "Silo 3", "MCC13", '["CTX-361-CJ"]', None, None, "RCC4V4"),
    ("Tripper Interlock Panel", "control_panel", "Silo 3", "MCC13", '["MTX-361-EL"]', None, None, "Anti-coincidence touch call section"),
]

# ---------------------------------------------------------------------------
# Photo seed data
# ---------------------------------------------------------------------------
PHOTOS_SEED = [
    ("Port of Liverpool Grain Terminal", "Photos/Grain_Ship.png", "General", None, 1, "Site overview photo", "2026-04-19"),
    ("High Level Limit Switch - BMH Ship Unloader (1)", "Ship Unloader BMH/Photos/High Level Limit Switch - BMH Ship Unloader (1).jpg", "Ship Unloader BMH", "High Level Limit Switch", 0, "Filed 19 Apr 2026", "2026-04-19"),
    ("High Level Limit Switch - BMH Ship Unloader (2)", "Ship Unloader BMH/Photos/High Level Limit Switch - BMH Ship Unloader (2).jpg", "Ship Unloader BMH", "High Level Limit Switch", 0, "Filed 19 Apr 2026", "2026-04-19"),
]


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------
def import_documents(conn):
    cursor = conn.cursor()
    inserted = 0
    skipped  = 0

    for dirpath, dirnames, filenames in os.walk(GRAIN_DIR):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            # rel_path relative to GRAIN_DIR (not including "Grain Terminal/" prefix itself)
            rel_path = os.path.relpath(abs_path, GRAIN_DIR)

            if should_skip(abs_path, rel_path):
                skipped += 1
                continue

            stem = os.path.splitext(filename)[0]
            drawing_ref, drawing_type, description = parse_filename(stem)

            category, area, mcc = classify_file(abs_path, rel_path)

            # file_size_kb
            try:
                size_bytes   = os.path.getsize(abs_path)
                file_size_kb = max(1, round(size_bytes / 1024))
            except OSError:
                file_size_kb = None

            # status
            status = "obsolete" if category == "obsolete" else "active"

            cursor.execute(
                """
                INSERT OR IGNORE INTO documents
                    (filename, title, file_path, category, area, mcc,
                     drawing_ref, drawing_type, description,
                     status, file_size_kb, imported_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    description,          # title = same as description initially
                    rel_path,             # relative to Grain Terminal/
                    category,
                    area,
                    mcc,
                    drawing_ref,
                    drawing_type,
                    description,
                    status,
                    file_size_kb,
                    NOW,
                    NOW,
                ),
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1

    conn.commit()
    return inserted, skipped


def seed_equipment(conn):
    cursor = conn.cursor()
    inserted = 0
    for row in EQUIPMENT_SEED:
        name, eq_type, area, mcc, drawing_refs, manufacturer, model, notes = row
        cursor.execute(
            """
            INSERT OR IGNORE INTO equipment
                (name, equipment_type, area, mcc, drawing_refs,
                 manufacturer, model, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, eq_type, area, mcc, drawing_refs, manufacturer, model, notes, NOW),
        )
        if cursor.rowcount:
            inserted += 1
    conn.commit()
    return inserted


def seed_photos(conn):
    cursor = conn.cursor()
    inserted = 0
    for row in PHOTOS_SEED:
        caption, file_path, area, equipment_subject, approved, notes, date_added = row
        cursor.execute(
            """
            INSERT OR IGNORE INTO photos
                (caption, file_path, area, equipment_subject, approved, notes, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (caption, file_path, area, equipment_subject, approved, notes, date_added),
        )
        if cursor.rowcount:
            inserted += 1
    conn.commit()
    return inserted


def record_run(conn, docs_inserted, docs_skipped):
    conn.execute(
        """
        INSERT INTO processing_runs (run_at, files_processed, files_skipped, notes)
        VALUES (?, ?, ?, ?)
        """,
        (NOW, docs_inserted, docs_skipped, "Initial import via import_existing.py"),
    )
    conn.commit()


def main():
    if not os.path.exists(DB_PATH):
        print("ERROR: grain_terminal.db not found. Run init_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    print("Importing documents from Grain Terminal/ ...")
    docs_inserted, docs_skipped = import_documents(conn)

    print("Seeding equipment table ...")
    eq_inserted = seed_equipment(conn)

    print("Seeding photos table ...")
    ph_inserted = seed_photos(conn)

    record_run(conn, docs_inserted, docs_skipped)
    conn.close()

    print()
    print("=" * 50)
    print("Import complete.")
    print(f"  Documents inserted : {docs_inserted}")
    print(f"  Documents skipped  : {docs_skipped}")
    print(f"  Equipment inserted : {eq_inserted}")
    print(f"  Photos inserted    : {ph_inserted}")
    print("=" * 50)


if __name__ == "__main__":
    main()
