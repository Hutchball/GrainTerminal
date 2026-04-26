#!/usr/bin/env python3
"""
Import compressor manuals/certification documents into grain_terminal.db.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SOURCE_ROOT = BASE.parents[1] / "Compressors" / "Compressors"
SOURCE_PREFIX = "Compressors/Compressors"
CREATED_AT = "2026-04-26T01:05:00"


EQUIPMENT = [
    {
        "name": "BMH Compressor",
        "equipment_type": "compressor",
        "area": "BMH",
        "notes": "Placeholder compressor asset created from BMH compressor controller manual.",
        "aliases": ["Champion BMH Compressor", "BMH Air Compressor"],
    },
    {
        "name": "SCR Compressor 7th Floor",
        "equipment_type": "compressor",
        "area": "Compressor Room / Workhouse Floor 7",
        "notes": "Placeholder compressor asset created from SCR compressor 7th floor certification pack.",
        "aliases": ["SCR compressor 7th floor", "7th Floor SCR Compressor"],
    },
]


def clean(value):
    return " ".join((value or "").replace("_", " ").split()).strip()


def add_alias(cur, equipment_id, alias_name, notes):
    alias = clean(alias_name)
    if not alias:
        return
    exists = cur.execute(
        "SELECT 1 FROM equipment_aliases WHERE equipment_id = ? AND UPPER(alias_name) = ? LIMIT 1",
        (equipment_id, alias.upper()),
    ).fetchone()
    if exists:
        return
    cur.execute(
        """
        INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source, notes)
        VALUES (?, ?, 'compressor_document', ?, ?)
        """,
        (equipment_id, alias, SOURCE_PREFIX, notes),
    )


def ensure_equipment(cur, item):
    row = cur.execute("SELECT id FROM equipment WHERE UPPER(name) = ?", (item["name"].upper(),)).fetchone()
    if row:
        equipment_id = row[0]
    else:
        cur.execute(
            """
            INSERT INTO equipment
                (name, equipment_type, area, mcc, drawing_refs, manufacturer, model, notes, created_at, location_description)
            VALUES (?, ?, ?, NULL, '[]', NULL, NULL, ?, ?, ?)
            """,
            (
                item["name"],
                item["equipment_type"],
                item["area"],
                item["notes"],
                CREATED_AT,
                item["area"],
            ),
        )
        equipment_id = cur.lastrowid
    for alias in item.get("aliases", []):
        add_alias(cur, equipment_id, alias, f"Alias from {SOURCE_PREFIX}.")
    return equipment_id


def document_description(path):
    stem = path.stem
    if stem.lower().startswith("c-pro"):
        return "C-PRO 2.0 controller operation instruction for Champion BMH compressor"
    if stem.lower().startswith("atlas copco"):
        return "Atlas Copco Elektronikon MK5 Swipe controller instruction book"
    if "Certification" in str(path.parent):
        return f"SCR compressor 7th floor certification - {clean(stem)}"
    return clean(stem)


def document_category(path):
    text = str(path).lower()
    if "certification" in text or "certificate" in text or "declaration" in text or "risk" in text or "pressure" in text:
        return "compliance"
    return "manual"


def equipment_ids_for(path, bmh_id, scr_id):
    text = str(path).lower()
    if "bmh compressor" in text or "champion" in text:
        return [bmh_id]
    if "scr compressor 7th floor certification" in text:
        return [scr_id]
    if "atlas copco" in text:
        return [scr_id]
    return []


def insert_document(cur, path, bmh_id, scr_id):
    rel = path.relative_to(BASE.parents[1]).as_posix()
    filename = path.name
    description = document_description(path)
    equipment_ids = equipment_ids_for(path, bmh_id, scr_id)
    area = "BMH" if equipment_ids == [bmh_id] else "Compressor Room / Workhouse Floor 7" if equipment_ids == [scr_id] else "Compressors"
    now = datetime.now().isoformat(timespec="seconds")
    size_kb = max(1, int(path.stat().st_size / 1024))
    cur.execute(
        """
        INSERT INTO documents
            (filename, title, file_path, category, area, mcc, drawing_ref, drawing_type,
             description, assignee, status, file_size_kb, imported_at, updated_at, equipment_ids)
        VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, NULL, 'active', ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            title = excluded.title,
            category = excluded.category,
            area = excluded.area,
            description = excluded.description,
            status = excluded.status,
            file_size_kb = excluded.file_size_kb,
            updated_at = excluded.updated_at,
            equipment_ids = excluded.equipment_ids
        """,
        (
            filename,
            description,
            rel,
            document_category(path),
            area,
            description,
            size_kb,
            now,
            now,
            json.dumps(equipment_ids),
        ),
    )
    return 1


def main():
    if not SOURCE_ROOT.exists():
        raise SystemExit(f"Missing compressor source folder: {SOURCE_ROOT}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    bmh_id = ensure_equipment(cur, EQUIPMENT[0])
    scr_id = ensure_equipment(cur, EQUIPMENT[1])
    count = 0
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if path.name == ".DS_Store" or not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            continue
        count += insert_document(cur, path, bmh_id, scr_id)
    conn.commit()
    total_docs = cur.execute("SELECT COUNT(*) FROM documents WHERE file_path LIKE 'Compressors/Compressors/%'").fetchone()[0]
    conn.close()
    print(f"Imported/updated {count} compressor documents.")
    print(f"Compressor documents registered: {total_docs}.")
    print(f"Equipment linked: BMH Compressor={bmh_id}, SCR Compressor 7th Floor={scr_id}.")


if __name__ == "__main__":
    main()
