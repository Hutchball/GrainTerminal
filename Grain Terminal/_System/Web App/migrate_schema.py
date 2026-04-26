"""
migrate_schema.py
=================
Adds new tables and columns to an existing grain_terminal.db without
destroying any existing data.  Safe to run multiple times (idempotent).

Run from the project root:
    python3 migrate_schema.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "grain_terminal.db"


NEW_TABLES = """
-- Flexible key-value store for any equipment specification.
-- Grows dynamically as new data types are discovered.
CREATE TABLE IF NOT EXISTS equipment_attributes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id     INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    attribute_key    TEXT NOT NULL,      -- e.g. 'motor_kw', 'gearbox_ratio', 'drive_roller_dia_mm'
    attribute_value  TEXT NOT NULL,      -- stored as text; interpreted by the frontend
    attribute_unit   TEXT,               -- e.g. 'kW', 'mm', 'rpm', ':'
    attribute_category TEXT,             -- 'motor','gearbox','drive','fluid_coupling','belt','roller','bearing','general'
    source           TEXT,               -- 'OEM drawing', 'site measurement', 'nameplate', 'manual'
    confidence_level TEXT DEFAULT 'VERIFIED',  -- VERIFIED / LIKELY / UNCERTAIN / UNKNOWN
    added_by         TEXT,               -- team member name
    added_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes            TEXT
);

-- Cross-referencing between pieces of equipment.
CREATE TABLE IF NOT EXISTS equipment_relationships (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_equipment_id   INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    child_equipment_id    INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    relationship_type     TEXT,   -- 'drives','feeds_into','controlled_by','same_circuit','same_mcc'
    notes                 TEXT
);

-- Physical locations at the grain terminal.
CREATE TABLE IF NOT EXISTS equipment_locations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id     INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    building         TEXT,    -- 'Main Building', 'Silo Block', 'Basement'
    floor_level      TEXT,    -- 'Ground', 'Basement', 'Level 1', 'Roof'
    grid_reference   TEXT,    -- site grid reference if available
    description      TEXT     -- plain-English location
);

CREATE TABLE IF NOT EXISTS equipment_aliases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id     INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    alias_name       TEXT NOT NULL,
    alias_type       TEXT DEFAULT 'legacy_name',
    source           TEXT,
    notes            TEXT
);

CREATE TABLE IF NOT EXISTS verification_feedback (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type        TEXT NOT NULL,
    item_id          TEXT,
    item_label       TEXT NOT NULL,
    source_path      TEXT,
    source_link      TEXT,
    query_text       TEXT,
    response_text    TEXT,
    verdict          TEXT NOT NULL,
    comments         TEXT,
    reported_by      TEXT,
    channel          TEXT,
    status           TEXT DEFAULT 'open',
    created_at       TEXT NOT NULL
);
"""

COLUMN_MIGRATIONS = [
    # (table, column, definition) — added if not already present
    ("equipment", "equipment_type_detail",          "TEXT"),     # richer type beyond the existing equipment_type
    ("equipment", "location_description",           "TEXT"),     # quick plain-English location (shortcut vs full table)
    ("equipment", "temporarily_out_of_service",     "INTEGER DEFAULT 0"),  # flagged as temporarily not in use but still searchable
    ("equipment", "permanently_out_of_service",     "INTEGER DEFAULT 0"),  # flagged as decommissioned but retained for reference
    ("documents", "equipment_ids",                  "TEXT"),     # JSON array of linked equipment IDs
]

INDEX_MIGRATIONS = [
    "CREATE INDEX IF NOT EXISTS idx_equipment_area ON equipment(area)",
    "CREATE INDEX IF NOT EXISTS idx_equipment_mcc  ON equipment(mcc)",
    "CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type)",
    "CREATE INDEX IF NOT EXISTS idx_docs_mcc       ON documents(mcc)",
    "CREATE INDEX IF NOT EXISTS idx_docs_category  ON documents(category)",
    "CREATE INDEX IF NOT EXISTS idx_attrs_equip    ON equipment_attributes(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_attrs_key      ON equipment_attributes(attribute_key)",
    "CREATE INDEX IF NOT EXISTS idx_attrs_category ON equipment_attributes(attribute_category)",
    "CREATE INDEX IF NOT EXISTS idx_aliases_equip  ON equipment_aliases(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_aliases_name   ON equipment_aliases(alias_name)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_item   ON verification_feedback(item_type, item_id)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_status ON verification_feedback(status)",
]


def migrate():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run init_db.py first.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    print(f"Migrating {DB_PATH.name} ...")

    # 1. New tables
    conn.executescript(NEW_TABLES)
    print("  ✓ New tables: equipment_attributes, equipment_relationships, equipment_locations, equipment_aliases, verification_feedback")

    # 2. New columns (add only if missing)
    cursor = conn.cursor()
    for table, column, definition in COLUMN_MIGRATIONS:
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"  ✓ Added column {table}.{column}")
        else:
            print(f"  - Column {table}.{column} already exists, skipping")

    # 3. Indexes
    for stmt in INDEX_MIGRATIONS:
        conn.execute(stmt)
    print("  ✓ Indexes applied")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
