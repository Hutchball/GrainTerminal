"""
file_incoming.py — Move a file from Incoming/ to its canonical location in one step.

Replaces the old two-move workflow. File lands once in its final home.
Processing log is updated automatically. Optional DB document record created.

Usage:
    python3 utils/file_incoming.py <source> <destination> [options]

Arguments:
    source          Filename or subfolder inside Incoming/ (e.g. "Fike panel manual.pdf")
    destination     Path relative to "Grain Terminal/" (e.g. "Manuals/" or "Switchrooms/MCC4/")

Options:
    --category      DB category: electrical_drawing | manual | compliance | maintenance_log
                                 research | photo | obsolete  (default: manual)
    --area          Site area, e.g. "MCC4", "Silo 2", "Basement-Receiving"
    --title         Human-readable title (defaults to filename without extension)
    --description   Brief description for the log and DB
    --equipment     Equipment tag to link (e.g. "RB1") — stored in area field if no --area
    --db            Insert a record into grain_terminal.db (flag, no value needed)
    --dry-run       Preview what would happen without moving anything

Examples:
    python3 utils/file_incoming.py "Fike panel manual.pdf" "Fike/" --category manual --area "Dust Plants" --db
    python3 utils/file_incoming.py "MCC4 schematic.pdf" "Switchrooms/MCC4/" --category electrical_drawing --area MCC4 --db
    python3 utils/file_incoming.py "DSEAR report.pdf" "Compliance/" --category compliance --db
    python3 utils/file_incoming.py "Tripper 9" "Silo 3/" --description "Tripper 9 drawings folder" --db

Run from: Grain Terminal/_System/Web App/
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

# ── Path anchors (derived from script location, so they never break) ─────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
WEB_APP_DIR  = os.path.dirname(SCRIPT_DIR)                      # Web App/
SYSTEM_DIR   = os.path.dirname(WEB_APP_DIR)                     # _System/
GT_DIR       = os.path.dirname(SYSTEM_DIR)                      # Grain Terminal/
ROOT_DIR     = os.path.dirname(GT_DIR)                          # LEEN/
INCOMING_DIR = os.path.join(ROOT_DIR, "Incoming")
LOG_DIR      = os.path.join(INCOMING_DIR, "Processed")
DB_PATH      = os.path.join(WEB_APP_DIR, "grain_terminal.db")

VALID_CATEGORIES = {
    "electrical_drawing", "manual", "compliance",
    "maintenance_log", "research", "photo", "obsolete"
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def today_log_path() -> str:
    fname = datetime.now().strftime("%Y-%m-%d") + "-processing-log.md"
    return os.path.join(LOG_DIR, fname)


def append_log(log_path: str, entry: dict, dry_run: bool):
    """Append a one-line audit entry to today's processing log."""
    header_needed = not os.path.exists(log_path)
    line = (
        f"| `{entry['source']}` "
        f"| `Grain Terminal/{entry['dest_rel']}` "
        f"| {entry['category']} "
        f"| {entry['area'] or '—'} "
        f"| {entry['description'] or '—'} "
        f"| {entry['timestamp']} |\n"
    )
    if dry_run:
        print(f"\n[DRY RUN] Would append to log: {log_path}")
        print(f"  {line.strip()}")
        return

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        if header_needed:
            date_str = datetime.now().strftime("%-d %B %Y")
            f.write(f"# Processing Log — {date_str}\n\n")
            f.write("| Source | Destination | Category | Area | Description | Filed at |\n")
            f.write("|---|---|---|---|---|---|\n")
        f.write(line)


def insert_db_record(entry: dict, dry_run: bool):
    """Insert a row into the documents table."""
    try:
        import sqlite3
    except ImportError:
        print("WARNING: sqlite3 not available — skipping DB insert.")
        return

    now = datetime.utcnow().isoformat()
    file_path_rel = entry['dest_rel']  # relative to Grain Terminal/
    filename = os.path.basename(entry['dest_abs'])
    file_size_kb = None
    if os.path.isfile(entry['dest_abs']):
        file_size_kb = round(os.path.getsize(entry['dest_abs']) / 1024)

    sql = """
        INSERT OR IGNORE INTO documents
            (filename, title, file_path, category, area, description, file_size_kb, imported_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    vals = (
        filename,
        entry['title'],
        file_path_rel,
        entry['category'],
        entry['area'],
        entry['description'],
        file_size_kb,
        now,
        now,
    )

    if dry_run:
        print(f"\n[DRY RUN] Would insert into documents:")
        cols = ["filename","title","file_path","category","area","description","file_size_kb","imported_at","updated_at"]
        for col, val in zip(cols, vals):
            print(f"  {col}: {val}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute(sql, vals)
        conn.commit()
        print(f"  DB: document record inserted (file_path='{file_path_rel}')")
    except sqlite3.IntegrityError:
        print(f"  DB: record already exists for '{file_path_rel}' — skipped.")
    finally:
        conn.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Move a file from Incoming/ to its canonical location."
    )
    parser.add_argument("source",      help="Filename or subfolder inside Incoming/")
    parser.add_argument("destination", help="Path relative to 'Grain Terminal/' (e.g. 'Manuals/')")
    parser.add_argument("--category",    default="manual",   help="DB document category")
    parser.add_argument("--area",        default=None,       help="Site area (e.g. MCC4, Silo 2)")
    parser.add_argument("--title",       default=None,       help="Human-readable title")
    parser.add_argument("--description", default=None,       help="Brief description")
    parser.add_argument("--equipment",   default=None,       help="Equipment tag (e.g. RB1)")
    parser.add_argument("--db",          action="store_true",help="Insert record into grain_terminal.db")
    parser.add_argument("--dry-run",     action="store_true",help="Preview only — no changes made")
    args = parser.parse_args()

    # ── Validate category ───────────────────────────────────────────────────
    if args.category not in VALID_CATEGORIES:
        print(f"ERROR: unknown category '{args.category}'.")
        print(f"  Valid: {', '.join(sorted(VALID_CATEGORIES))}")
        sys.exit(1)

    # ── Resolve paths ───────────────────────────────────────────────────────
    source_abs = os.path.join(INCOMING_DIR, args.source)
    dest_dir_abs = os.path.join(GT_DIR, args.destination.rstrip("/"))
    dest_abs = os.path.join(dest_dir_abs, os.path.basename(args.source))
    dest_rel = os.path.join(args.destination.rstrip("/"), os.path.basename(args.source))

    # ── Validate source ─────────────────────────────────────────────────────
    if not os.path.exists(source_abs):
        print(f"ERROR: not found in Incoming/: '{args.source}'")
        print(f"  Looked at: {source_abs}")
        sys.exit(1)

    # ── Validate / create destination ───────────────────────────────────────
    if not os.path.exists(dest_dir_abs):
        if args.dry_run:
            print(f"[DRY RUN] Would create destination folder: Grain Terminal/{args.destination}")
        else:
            os.makedirs(dest_dir_abs, exist_ok=True)
            print(f"  Created: Grain Terminal/{args.destination}")

    # ── Defaults ────────────────────────────────────────────────────────────
    title = args.title or os.path.splitext(os.path.basename(args.source))[0]
    area  = args.area or args.equipment or None

    entry = {
        "source":      args.source,
        "dest_abs":    dest_abs,
        "dest_rel":    dest_rel,
        "category":    args.category,
        "area":        area,
        "title":       title,
        "description": args.description,
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # ── Preview ─────────────────────────────────────────────────────────────
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Filing:")
    print(f"  FROM  Incoming/{args.source}")
    print(f"  TO    Grain Terminal/{dest_rel}")
    print(f"  Cat   {args.category}  |  Area: {area or '—'}  |  Title: {title}")

    # ── Move ────────────────────────────────────────────────────────────────
    if not args.dry_run:
        if os.path.exists(dest_abs):
            print(f"WARNING: destination already exists: {dest_abs}")
            print("  Rename the source or remove the existing file first.")
            sys.exit(1)
        shutil.move(source_abs, dest_abs)
        print(f"  Moved ✓")

    # ── Log ─────────────────────────────────────────────────────────────────
    append_log(today_log_path(), entry, args.dry_run)
    if not args.dry_run:
        print(f"  Log  ✓  ({os.path.basename(today_log_path())})")

    # ── DB ──────────────────────────────────────────────────────────────────
    if args.db:
        insert_db_record(entry, args.dry_run)

    if not args.dry_run:
        print(f"\nDone. File is at: Grain Terminal/{dest_rel}")


if __name__ == "__main__":
    main()
