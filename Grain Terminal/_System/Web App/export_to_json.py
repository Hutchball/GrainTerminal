#!/usr/bin/env python3
"""
PKA Grain Terminal — JSON Export Layer
=======================================
Reads from grain_terminal.db and writes JSON files to data/
so the web portal always has up-to-date data.

Usage:
    python3 export_to_json.py
"""

import json
import sqlite3
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent          # .../Web App/
DB_PATH = BASE / "grain_terminal.db"
OUT_DIR = BASE / "data"

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def parse_drawing_refs(raw) -> list:
    """Parse drawing_refs JSON string from DB into a Python list."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def parse_id_list(raw) -> list:
    if raw is None:
        return []
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(parsed, list):
        return []
    result = []
    for item in parsed:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return result


# ── Export functions ───────────────────────────────────────────────────────────

def export_stats(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM documents WHERE category='electrical_drawing' AND status='active'"
    )
    electrical_drawings = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM photos")
    photos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM equipment")
    equipment_items = cur.fetchone()[0]

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='electrical_motors'")
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) FROM electrical_motors")
        electrical_motors = cur.fetchone()[0]
    else:
        electrical_motors = 0

    cur.execute("SELECT COUNT(*) FROM documents WHERE category='obsolete'")
    obsolete_drawings = cur.fetchone()[0]

    cur.execute("SELECT MAX(imported_at) FROM documents")
    row = cur.fetchone()
    raw_ts = row[0] if row and row[0] else None
    # Truncate to minute precision (YYYY-MM-DDTHH:MM)
    if raw_ts and "T" in raw_ts:
        last_import = raw_ts[:16]
    elif raw_ts:
        last_import = raw_ts
    else:
        last_import = None

    cur.execute(
        """
        SELECT mcc, COUNT(*) AS cnt
        FROM documents
        WHERE category='electrical_drawing'
          AND mcc IS NOT NULL
        GROUP BY mcc
        ORDER BY mcc
        """
    )
    mcc_counts = {r["mcc"]: r["cnt"] for r in cur.fetchall()}

    return {
        "electrical_drawings": electrical_drawings,
        "photos": photos,
        "equipment_items": equipment_items,
        "electrical_motors": electrical_motors,
        "obsolete_drawings": obsolete_drawings,
        "last_import": last_import,
        "mcc_counts": mcc_counts,
    }


def export_documents(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, filename, drawing_ref, drawing_type, description,
               mcc, area, category, file_path, status, equipment_ids
        FROM documents
        ORDER BY mcc, filename
        """
    )
    rows = cur.fetchall()
    result = []
    for row in rows:
        fp = row["file_path"]
        pdf_link = ("../Grain Terminal/" + fp) if fp else None
        result.append({
            "id":           row["id"],
            "filename":     row["filename"],
            "drawing_ref":  row["drawing_ref"],
            "drawing_type": row["drawing_type"],
            "description":  row["description"],
            "mcc":          row["mcc"],
            "area":         row["area"],
            "category":     row["category"],
            "file_path":    fp,
            "pdf_link":     pdf_link,
            "status":       row["status"],
            "equipment_ids": parse_id_list(row["equipment_ids"]),
        })
    return result


def export_photos(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, caption, file_path, area, equipment_subject,
               approved, notes, date_added
        FROM photos
        ORDER BY id
        """
    )
    rows = cur.fetchall()
    result = []
    for row in rows:
        fp = row["file_path"]
        url = ("../Grain Terminal/" + fp) if fp else None
        result.append({
            "id":               row["id"],
            "caption":          row["caption"],
            "file_path":        fp,
            "url":              url,
            "area":             row["area"],
            "equipment_subject": row["equipment_subject"],
            "approved":         bool(row["approved"]),
            "notes":            row["notes"],
            "date_added":       row["date_added"],
        })
    return result


def export_equipment(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    alias_map = export_equipment_aliases_by_id(conn)
    cur.execute(
        """
        SELECT id, name, long_name, equipment_type, area, mcc, drawing_refs,
               manufacturer, model, notes, location_description
        FROM equipment
        ORDER BY area, name
        """
    )
    rows = cur.fetchall()
    result = []
    for row in rows:
        result.append({
            "id":           row["id"],
            "name":         row["name"],
            "long_name":    row["long_name"],
            "type":         row["equipment_type"],
            "area":         row["area"],
            "mcc":          row["mcc"],
            "drawing_refs": parse_drawing_refs(row["drawing_refs"]),
            "manufacturer": row["manufacturer"],
            "model":        row["model"],
            "notes":        row["notes"],
            "location":     row["location_description"],
            "aliases":      alias_map.get(row["id"], []),
        })
    return result


def export_equipment_aliases_by_id(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_aliases'")
    if not cur.fetchone():
        return {}
    cur.execute(
        """
        SELECT equipment_id, alias_name, alias_type, source, notes
        FROM equipment_aliases
        ORDER BY equipment_id, alias_name
        """
    )
    result = {}
    for row in cur.fetchall():
        result.setdefault(row["equipment_id"], []).append({
            "name": row["alias_name"],
            "type": row["alias_type"] or "legacy_name",
            "source": row["source"],
            "notes": row["notes"],
        })
    return result


def export_equipment_aliases(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_aliases'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT a.equipment_id, e.name AS equipment_name, a.alias_name, a.alias_type, a.source, a.notes
        FROM equipment_aliases a
        JOIN equipment e ON e.id = a.equipment_id
        ORDER BY a.equipment_id, a.alias_name
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_equipment_attributes(conn: sqlite3.Connection) -> list:
    """Export all equipment attributes keyed by equipment_id for easy frontend lookup."""
    cur = conn.cursor()
    # Check table exists (may not if migrate_schema.py not yet run)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_attributes'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT equipment_id, attribute_key, attribute_value, attribute_unit,
               attribute_category, source, confidence_level, added_by, notes
        FROM equipment_attributes
        ORDER BY equipment_id, attribute_category, attribute_key
        """
    )
    rows = cur.fetchall()
    # Group by equipment_id
    by_equip: dict = {}
    for row in rows:
        eid = row["equipment_id"]
        if eid not in by_equip:
            by_equip[eid] = []
        by_equip[eid].append({
            "key":        row["attribute_key"],
            "value":      row["attribute_value"],
            "unit":       row["attribute_unit"],
            "category":   row["attribute_category"] or "general",
            "source":     row["source"],
            "confidence": row["confidence_level"] or "VERIFIED",
            "added_by":   row["added_by"],
            "notes":      row["notes"],
        })
    # Return as list of {equipment_id, attributes:[...]}
    return [{"equipment_id": eid, "attributes": attrs} for eid, attrs in sorted(by_equip.items())]


def export_equipment_relationships(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_relationships'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT r.parent_equipment_id, r.child_equipment_id, r.relationship_type, r.notes,
               p.name AS parent_name, c.name AS child_name
        FROM equipment_relationships r
        JOIN equipment p ON p.id = r.parent_equipment_id
        JOIN equipment c ON c.id = r.child_equipment_id
        ORDER BY r.parent_equipment_id
        """
    )
    return [
        {
            "parent_id":   row["parent_equipment_id"],
            "child_id":    row["child_equipment_id"],
            "parent_name": row["parent_name"],
            "child_name":  row["child_name"],
            "type":        row["relationship_type"],
            "notes":       row["notes"],
        }
        for row in cur.fetchall()
    ]


def export_verification_feedback(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verification_feedback'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT id, item_type, item_id, item_label, source_path, source_link,
               query_text, response_text, verdict, comments, reported_by,
               channel, status, created_at
        FROM verification_feedback
        ORDER BY created_at DESC, id DESC
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_lubricants(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lubricants'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT id, supplier, product_description, stock_quantity,
               ordering_instructions, used_for, source_file, imported_at
        FROM lubricants
        ORDER BY supplier, product_description, id
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_equipment_lubricants(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_lubricants'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT el.id, el.equipment_id, e.name AS equipment_name,
               el.lubricant_id, l.supplier, l.product_description,
               el.source_equipment_label, el.application, el.component,
               el.notes, el.source_file
        FROM equipment_lubricants el
        LEFT JOIN equipment e ON e.id = el.equipment_id
        JOIN lubricants l ON l.id = el.lubricant_id
        ORDER BY COALESCE(e.name, el.source_equipment_label), l.product_description, el.application
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_equipment_pulleys(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_pulleys'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT p.id, p.equipment_id, e.name AS equipment_name,
               p.source_equipment_label, p.pulley_label, p.pulley_type,
               p.stock_number, p.pulley_diameter, p.face_width,
               p.shaft_diameter, p.shaft_length, p.length_from_face,
               p.bearing_centre, p.bearing_details, p.quantity, p.notes,
               p.source_file, p.source_sheet, p.source_row, p.record_type
        FROM equipment_pulleys p
        LEFT JOIN equipment e ON e.id = p.equipment_id
        ORDER BY COALESCE(e.name, p.source_equipment_label), p.pulley_type, p.id
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_equipment_gearboxes(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_gearboxes'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT g.id, g.equipment_id, e.name AS equipment_name, e.area,
               g.gearbox_label, g.lubricant_id, g.oil_supplier,
               g.oil_product, g.oil_application, g.gearbox_make,
               g.gearbox_type, g.gearbox_reduction, g.gearbox_output_speed,
               g.source
        FROM equipment_gearboxes g
        JOIN equipment e ON e.id = g.equipment_id
        ORDER BY e.name, g.gearbox_label, g.id
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_electrical_motors(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='electrical_motors'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT m.id, m.equipment_id, e.name AS equipment_name,
               m.motor_reference, m.plant_label, m.section_name, m.source_equipment_label,
               m.motor_type, m.serial_number, m.make, m.volts, m.horsepower,
               m.amps, m.kilowatts, m.revs, m.phase,
               m.source_file, m.source_row
        FROM electrical_motors m
        LEFT JOIN equipment e ON e.id = m.equipment_id
        ORDER BY m.section_name, COALESCE(e.name, m.source_equipment_label, m.plant_label), m.id
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_dust_bag_stock(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dust_bag_stock'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT id, item_no, bag_type, application_summary, stock_quantity,
               min_quantity, max_quantity, notes, source_file, source_row
        FROM dust_bag_stock
        ORDER BY CAST(item_no AS INTEGER), id
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_equipment_dust_bags(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment_dust_bags'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT db.id, db.equipment_id, e.name AS equipment_name,
               db.bag_type, db.application_label, db.quantity_required,
               db.total_required, db.stock_quantity, db.date_checked,
               db.status, db.notes, db.source_file, db.source_row
        FROM equipment_dust_bags db
        LEFT JOIN equipment e ON e.id = db.equipment_id
        ORDER BY db.status, COALESCE(e.name, db.application_label), db.bag_type, db.id
        """
    )
    return [dict(row) for row in cur.fetchall()]


def export_dust_bag_change_history(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dust_bag_change_history'")
    if not cur.fetchone():
        return []
    cur.execute(
        """
        SELECT h.id, h.equipment_id, e.name AS equipment_name,
               h.application_label, h.year_label, h.change_date,
               h.status, h.notes, h.source_file, h.source_row
        FROM dust_bag_change_history h
        LEFT JOIN equipment e ON e.id = h.equipment_id
        ORDER BY h.status, COALESCE(e.name, h.application_label), h.year_label, h.id
        """
    )
    return [dict(row) for row in cur.fetchall()]


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()

    attrs  = export_equipment_attributes(conn)
    rels   = export_equipment_relationships(conn)
    aliases = export_equipment_aliases(conn)
    feedback = export_verification_feedback(conn)
    lubricants = export_lubricants(conn)
    equipment_lubricants = export_equipment_lubricants(conn)
    equipment_pulleys = export_equipment_pulleys(conn)
    equipment_gearboxes = export_equipment_gearboxes(conn)
    electrical_motors = export_electrical_motors(conn)
    dust_bag_stock = export_dust_bag_stock(conn)
    equipment_dust_bags = export_equipment_dust_bags(conn)
    dust_bag_change_history = export_dust_bag_change_history(conn)

    exports = [
        ("stats.json",                    export_stats(conn),       None),
        ("documents.json",                export_documents(conn),   "documents"),
        ("photos.json",                   export_photos(conn),      "photos"),
        ("equipment.json",                export_equipment(conn),   "equipment"),
        ("equipment_aliases.json",        aliases,                  "aliases"),
        ("equipment_attributes.json",     attrs,                    "attributes"),
        ("equipment_relationships.json",  rels,                     "relationships"),
        ("verification_feedback.json",    feedback,                 "feedback"),
        ("lubricants.json",               lubricants,               "lubricants"),
        ("equipment_lubricants.json",     equipment_lubricants,     "equipment lubricant links"),
        ("equipment_pulleys.json",        equipment_pulleys,        "equipment pulley records"),
        ("equipment_gearboxes.json",      equipment_gearboxes,      "equipment gearbox records"),
        ("electrical_motors.json",        electrical_motors,        "electrical motor records"),
        ("dust_bag_stock.json",           dust_bag_stock,           "dust bag stock records"),
        ("equipment_dust_bags.json",      equipment_dust_bags,      "equipment dust bag requirements"),
        ("dust_bag_change_history.json",  dust_bag_change_history,  "dust bag change history records"),
    ]
    conn.close()

    for filename, data, list_key in exports:
        out_path = OUT_DIR / filename
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        if list_key is None:
            print(f"  Wrote {out_path}  (stats dict)")
        else:
            print(f"  Wrote {out_path}  ({len(data)} records)")

    print("Export complete.")


if __name__ == "__main__":
    main()
