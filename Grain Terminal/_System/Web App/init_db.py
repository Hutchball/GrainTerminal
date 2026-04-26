"""
init_db.py
Creates grain_terminal.db at the project root with the full schema.
Run from the project root:  python3 init_db.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grain_terminal.db")

DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    filename     TEXT NOT NULL,
    title        TEXT,
    file_path    TEXT NOT NULL UNIQUE,   -- relative to "Grain Terminal/"
    category     TEXT NOT NULL,          -- 'electrical_drawing','photo','manual','compliance','maintenance_log','research','obsolete'
    area         TEXT,                   -- 'MCC1','Silo 2','Basement-Receiving', etc.
    mcc          TEXT,                   -- 'MCC1','SCP','Scale Room', NULL if not electrical
    drawing_ref  TEXT,                   -- e.g. 'DTX-361-AA'
    drawing_type TEXT,                   -- 'DTX','STX','CTX','GTX','MTX','LTX','BTY','QTY','RTX','HTX','FTX','ETF'
    description  TEXT,                   -- human-readable title extracted from filename
    assignee     TEXT,
    status       TEXT DEFAULT 'active',  -- 'active','obsolete','pending_review'
    file_size_kb INTEGER,
    imported_at  TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS photos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    caption          TEXT NOT NULL,
    file_path        TEXT,              -- relative to "Grain Terminal/"
    area             TEXT,
    equipment_subject TEXT,
    approved         INTEGER DEFAULT 0, -- 0=pending, 1=approved
    notes            TEXT,
    date_added       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS equipment (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    equipment_type TEXT,               -- 'belt_conveyor','bucket_elevator','dust_filter','rotary_valve','chain_conveyor','tripper','control_panel','junction_box'
    area          TEXT,
    mcc           TEXT,
    drawing_refs  TEXT,                -- JSON array string e.g. '["DTX-361-AA","CTX-361-B"]'
    manufacturer  TEXT,
    model         TEXT,
    notes         TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processing_runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at           TEXT NOT NULL,
    files_processed  INTEGER DEFAULT 0,
    files_skipped    INTEGER DEFAULT 0,
    manifest_path    TEXT,
    notes            TEXT
);

-- Flexible key-value store for any equipment specification.
CREATE TABLE IF NOT EXISTS equipment_attributes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id     INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    attribute_key    TEXT NOT NULL,
    attribute_value  TEXT NOT NULL,
    attribute_unit   TEXT,
    attribute_category TEXT,
    source           TEXT,
    confidence_level TEXT DEFAULT 'VERIFIED',
    added_by         TEXT,
    added_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes            TEXT
);

-- Cross-referencing between pieces of equipment.
CREATE TABLE IF NOT EXISTS equipment_relationships (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_equipment_id   INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    child_equipment_id    INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    relationship_type     TEXT,
    notes                 TEXT
);

-- Physical locations at the grain terminal.
CREATE TABLE IF NOT EXISTS equipment_locations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id     INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    building         TEXT,
    floor_level      TEXT,
    grid_reference   TEXT,
    description      TEXT
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
    item_type        TEXT NOT NULL,      -- 'equipment','asset','drawing','document','photo','grainbot_answer'
    item_id          TEXT,
    item_label       TEXT NOT NULL,
    source_path      TEXT,
    source_link      TEXT,
    query_text       TEXT,
    response_text    TEXT,
    verdict          TEXT NOT NULL,      -- 'correct','incorrect'
    comments         TEXT,
    reported_by      TEXT,
    channel          TEXT,               -- 'portal','grainbot','agent'
    status           TEXT DEFAULT 'open',-- 'open','reviewed','resolved'
    created_at       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_equipment_area ON equipment(area);
CREATE INDEX IF NOT EXISTS idx_equipment_mcc  ON equipment(mcc);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_docs_mcc       ON documents(mcc);
CREATE INDEX IF NOT EXISTS idx_docs_category  ON documents(category);
CREATE INDEX IF NOT EXISTS idx_attrs_equip    ON equipment_attributes(equipment_id);
CREATE INDEX IF NOT EXISTS idx_attrs_key      ON equipment_attributes(attribute_key);
CREATE INDEX IF NOT EXISTS idx_attrs_category ON equipment_attributes(attribute_category);
CREATE INDEX IF NOT EXISTS idx_aliases_equip  ON equipment_aliases(equipment_id);
CREATE INDEX IF NOT EXISTS idx_aliases_name   ON equipment_aliases(alias_name);
CREATE INDEX IF NOT EXISTS idx_feedback_item   ON verification_feedback(item_type, item_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON verification_feedback(status);
"""


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Execute each statement separately (executescript handles multiple)
    conn.executescript(DDL)
    conn.commit()
    conn.close()

    print(f"Database initialised successfully at: {DB_PATH}")
    print("Tables created: documents, photos, equipment, processing_runs,")
    print("                equipment_attributes, equipment_relationships, equipment_locations,")
    print("                equipment_aliases, verification_feedback")
    print("WAL journal mode enabled.")


if __name__ == "__main__":
    main()
