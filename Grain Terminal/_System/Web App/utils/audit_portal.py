"""
audit_portal.py — Full data quality audit of grain_terminal.db.

Finds: duplicates, orphaned records, missing attributes, broken document
links, empty equipment, and consistency problems — without changing anything.

Run this BEFORE any cleanup. Fix nothing until you've seen the full picture.

Usage (run from Grain Terminal/_System/Web App/):
    python3 utils/audit_portal.py
    python3 utils/audit_portal.py > audit.txt   # save to file

Requires: grain_terminal.db in the current directory
"""

import sqlite3, json, sys, os
from datetime import datetime

DB = "grain_terminal.db"
SEP = "─" * 70

def connect():
    if not os.path.exists(DB):
        print(f"ERROR: {DB} not found. Run from Grain Terminal/_System/Web App/")
        sys.exit(1)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def section(title): print(f"\n{SEP}\n  {title}\n{SEP}")
def ok(msg):        print(f"  ✓  {msg}")
def warn(msg):      print(f"  ⚠  {msg}")
def err(msg):       print(f"  ✗  {msg}")

def columns(conn, table):
    """Return set of column names for a table."""
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}

def table_exists(conn, table):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None

# ─────────────────────────────────────────────────────────────────────────────

def audit_equipment_duplicates(conn, issues):
    section("1. EQUIPMENT — Duplicate names")
    rows = conn.execute("""
        SELECT name, COUNT(*) as n, GROUP_CONCAT(id) as ids
        FROM equipment
        GROUP BY name
        HAVING n > 1
        ORDER BY n DESC
    """).fetchall()
    if not rows:
        ok("No duplicate names.")
    else:
        err(f"{len(rows)} duplicate name(s) — will cause lookup conflicts:")
        for r in rows:
            print(f"     '{r['name']}' — {r['n']} rows (IDs: {r['ids']})")
        issues['duplicate_equipment'] = [dict(r) for r in rows]


def audit_equipment_no_attributes(conn, issues):
    section("2. EQUIPMENT — Records with zero attributes")
    rows = conn.execute("""
        SELECT e.id, e.name, e.equipment_type
        FROM equipment e
        LEFT JOIN equipment_attributes a ON a.equipment_id = e.id
        WHERE a.id IS NULL
        ORDER BY e.name
    """).fetchall()
    if not rows:
        ok("All equipment records have at least one attribute.")
    else:
        warn(f"{len(rows)} equipment record(s) with no attributes (empty shells):")
        for r in rows[:25]:
            print(f"     [{r['id']:>4}] {r['name']:<30}  type: {r['equipment_type'] or '—'}")
        if len(rows) > 25:
            print(f"     … and {len(rows)-25} more")
        issues['equipment_no_attributes'] = [dict(r) for r in rows]


def audit_equipment_missing_fields(conn, issues):
    section("3. EQUIPMENT — Missing area or equipment_type")
    no_area = conn.execute(
        "SELECT COUNT(*) FROM equipment WHERE area IS NULL OR area = ''"
    ).fetchone()[0]
    no_type = conn.execute(
        "SELECT COUNT(*) FROM equipment WHERE equipment_type IS NULL OR equipment_type = ''"
    ).fetchone()[0]
    total   = conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    print(f"  Total equipment records: {total}")
    if no_area:
        warn(f"{no_area} record(s) missing area.")
    else:
        ok("All records have an area.")
    if no_type:
        warn(f"{no_type} record(s) missing equipment_type.")
    else:
        ok("All records have an equipment_type.")
    if no_area: issues['equipment_no_area'] = no_area
    if no_type: issues['equipment_no_type'] = no_type


def audit_orphaned_attributes(conn, issues):
    section("4. ATTRIBUTES — Orphaned (no matching equipment)")
    rows = conn.execute("""
        SELECT a.equipment_id, COUNT(*) as n
        FROM equipment_attributes a
        LEFT JOIN equipment e ON e.id = a.equipment_id
        WHERE e.id IS NULL
        GROUP BY a.equipment_id
    """).fetchall()
    if not rows:
        ok("No orphaned attributes.")
    else:
        err(f"{len(rows)} equipment_id(s) in attributes with no matching equipment:")
        for r in rows:
            print(f"     equipment_id={r['equipment_id']}  ({r['n']} orphaned attribute rows)")
        issues['orphaned_attributes'] = [dict(r) for r in rows]


def audit_duplicate_attributes(conn, issues):
    section("5. ATTRIBUTES — Duplicate key per equipment")
    rows = conn.execute("""
        SELECT a.equipment_id, e.name, a.attribute_key, COUNT(*) as n
        FROM equipment_attributes a
        LEFT JOIN equipment e ON e.id = a.equipment_id
        GROUP BY a.equipment_id, a.attribute_key
        HAVING n > 1
        ORDER BY n DESC
        LIMIT 30
    """).fetchall()
    if not rows:
        ok("No duplicate attribute keys per equipment.")
    else:
        err(f"{len(rows)} duplicate attribute key(s) — showing up to 30:")
        for r in rows:
            label = r['name'] or f"id={r['equipment_id']}"
            print(f"     {label:<30}  key='{r['attribute_key']}'  ×{r['n']}")
        issues['duplicate_attributes'] = [dict(r) for r in rows]


def audit_documents(conn, issues):
    section("6. DOCUMENTS — Duplicates & missing fields")

    total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    print(f"  Total documents: {total}")

    # Duplicate file paths
    dupes = conn.execute("""
        SELECT file_path, COUNT(*) as n, GROUP_CONCAT(id) as ids
        FROM documents
        WHERE file_path IS NOT NULL AND file_path != ''
        GROUP BY file_path
        HAVING n > 1
        ORDER BY n DESC
    """).fetchall()
    if not dupes:
        ok("No duplicate file_path entries.")
    else:
        err(f"{len(dupes)} duplicate file_path(s) — same file imported more than once:")
        for r in dupes[:15]:
            print(f"     '{r['file_path']}'  ×{r['n']}  (IDs: {r['ids']})")
        if len(dupes) > 15: print(f"     … and {len(dupes)-15} more")
        issues['duplicate_documents'] = [dict(r) for r in dupes]

    # Missing file_path
    no_path = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE file_path IS NULL OR file_path = ''"
    ).fetchone()[0]
    if no_path:
        err(f"{no_path} document(s) missing file_path — portal links will be broken.")
        issues['documents_no_path'] = no_path
    else:
        ok("All documents have a file_path.")

    # Missing title
    no_title = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE title IS NULL OR title = ''"
    ).fetchone()[0]
    if no_title:
        warn(f"{no_title} document(s) missing title (will show blank in portal).")
        issues['documents_no_title'] = no_title
    else:
        ok("All documents have a title.")

    # Duplicate filenames (different paths, same filename — worth flagging)
    dup_names = conn.execute("""
        SELECT filename, COUNT(*) as n
        FROM documents
        GROUP BY filename
        HAVING n > 1
        ORDER BY n DESC
        LIMIT 20
    """).fetchall()
    if dup_names:
        warn(f"{len(dup_names)} filename(s) appear more than once (may be intentional):")
        for r in dup_names[:10]:
            print(f"     '{r['filename']}'  ×{r['n']}")


def audit_document_categories(conn, issues):
    section("7. DOCUMENTS — Category breakdown")
    rows = conn.execute("""
        SELECT COALESCE(category, 'NULL') as category, COUNT(*) as n
        FROM documents
        GROUP BY category
        ORDER BY n DESC
    """).fetchall()
    total = sum(r['n'] for r in rows)
    for r in rows:
        pct = round(100 * r['n'] / total) if total else 0
        print(f"     {r['category']:<30} {r['n']:>5}  ({pct}%)")
    print(f"     {'TOTAL':<30} {total:>5}")

    nulls = next((r['n'] for r in rows if r['category'] == 'NULL'), 0)
    if nulls:
        warn(f"{nulls} document(s) with no category.")
        issues['documents_no_category'] = nulls


def audit_aliases(conn, issues):
    section("8. ALIASES — Broken (equipment_id not in equipment table)")
    rows = conn.execute("""
        SELECT a.id, a.alias_name, a.equipment_id
        FROM equipment_aliases a
        LEFT JOIN equipment e ON e.id = a.equipment_id
        WHERE e.id IS NULL
        LIMIT 30
    """).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM equipment_aliases").fetchone()[0]
    print(f"  Total aliases: {total}")
    if not rows:
        ok("All aliases resolve to a valid equipment record.")
    else:
        err(f"{len(rows)} alias(es) with no matching equipment_id:")
        for r in rows:
            print(f"     alias='{r['alias_name']}'  equipment_id={r['equipment_id']} (NOT FOUND)")
        issues['broken_aliases'] = [dict(r) for r in rows]


def audit_confidence_levels(conn, issues):
    section("9. DATA CONFIDENCE — Attribute confidence_level distribution")
    rows = conn.execute("""
        SELECT COALESCE(confidence_level, 'NULL') as lvl, COUNT(*) as n
        FROM equipment_attributes
        GROUP BY confidence_level
        ORDER BY n DESC
    """).fetchall()
    total = sum(r['n'] for r in rows)
    print(f"  Total attribute rows: {total}")
    for r in rows:
        pct = round(100 * r['n'] / total) if total else 0
        bar = "█" * (pct // 5)
        print(f"     {r['lvl']:<12} {r['n']:>6}  {pct:>3}%  {bar}")
    unknown = next((r['n'] for r in rows if r['lvl'] in ('UNKNOWN', 'NULL')), 0)
    if unknown > 50:
        warn(f"{unknown} attributes at UNKNOWN/NULL confidence — review priority.")
        issues['low_confidence_attributes'] = unknown


def audit_electrical_motors(conn, issues):
    section("10. ELECTRICAL MOTORS — Link status")
    if not table_exists(conn, 'electrical_motors'):
        warn("electrical_motors table not found — skipping.")
        return
    cols = columns(conn, 'electrical_motors')
    total = conn.execute("SELECT COUNT(*) FROM electrical_motors").fetchone()[0]

    if 'equipment_id' in cols:
        linked = conn.execute(
            "SELECT COUNT(*) FROM electrical_motors WHERE equipment_id IS NOT NULL"
        ).fetchone()[0]
        unlinked = total - linked
        print(f"  Total motors:    {total}")
        print(f"  Linked to equip: {linked}")
        if unlinked:
            warn(f"{unlinked} motor(s) not linked to any equipment record.")
            # Show tag column if it exists
            tag_col = 'tag' if 'tag' in cols else ('name' if 'name' in cols else None)
            if tag_col:
                rows = conn.execute(
                    f"SELECT id, {tag_col} FROM electrical_motors WHERE equipment_id IS NULL LIMIT 20"
                ).fetchall()
                for r in rows:
                    print(f"     [{r['id']}] {r[tag_col] or '—'}")
            issues['unlinked_motors'] = unlinked
        else:
            ok("All motors linked to equipment.")
    else:
        print(f"  Total motors: {total} (no equipment_id column — links not tracked)")


def audit_documents_vs_equipment(conn, issues):
    section("11. DOCUMENTS — Linked to equipment vs standalone")
    cols = columns(conn, 'documents')
    if 'equipment_ids' not in cols:
        warn("documents.equipment_ids column not present — link audit skipped.")
        return
    total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    linked = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE equipment_ids IS NOT NULL AND equipment_ids != '' AND equipment_ids != '[]'"
    ).fetchone()[0]
    unlinked = total - linked
    print(f"  Total documents: {total}")
    print(f"  Linked to equipment: {linked}")
    if unlinked:
        warn(f"{unlinked} document(s) not linked to any equipment record.")
        issues['unlinked_documents'] = unlinked
    else:
        ok("All documents linked to at least one equipment record.")


# ─────────────────────────────────────────────────────────────────────────────

def main():
    conn = connect()
    issues = {}

    print(f"\n{'='*70}")
    print(f"  GRAIN TERMINAL — PORTAL DATA AUDIT")
    print(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  DB:     {os.path.abspath(DB)}")
    print(f"{'='*70}")

    audit_equipment_duplicates(conn, issues)
    audit_equipment_no_attributes(conn, issues)
    audit_equipment_missing_fields(conn, issues)
    audit_orphaned_attributes(conn, issues)
    audit_duplicate_attributes(conn, issues)
    audit_documents(conn, issues)
    audit_document_categories(conn, issues)
    audit_aliases(conn, issues)
    audit_confidence_levels(conn, issues)
    audit_electrical_motors(conn, issues)
    audit_documents_vs_equipment(conn, issues)

    section("SUMMARY")
    if not issues:
        ok("No issues found. Data looks clean.")
    else:
        print(f"  {len(issues)} issue class(es) found:\n")
        for k, v in issues.items():
            count = len(v) if isinstance(v, list) else v
            print(f"     {k:<45} {count:>5}")
    print(f"\n{SEP}\n")
    conn.close()

if __name__ == "__main__":
    main()
