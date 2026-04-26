#!/usr/bin/env python3
"""
Apply the 25 Apr 2026 topology/equipment merge.

This script folds confirmed duplicate starter equipment into canonical
topology-backed records, preserves old names as aliases, and adds missing
process-schematic assets as equipment records.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).parent
DB_PATH = BASE / "grain_terminal.db"
SITE_LAYOUT_PATH = BASE / "data" / "site_layout.json"
SOURCE = "MERGE_PLAN_2026-04-25.md"
CREATED_AT = "2026-04-25T12:00:00"


def parse_refs(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        refs = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return refs if isinstance(refs, list) else []


def merge_refs(*raw_values: str | None) -> str:
    refs: list[str] = []
    for raw in raw_values:
        for ref in parse_refs(raw):
            if ref and ref not in refs:
                refs.append(ref)
    return json.dumps(refs)


def add_alias(cur: sqlite3.Cursor, equipment_id: int, alias: str, notes: str) -> None:
    if not alias:
        return
    cur.execute(
        """
        INSERT INTO equipment_aliases (equipment_id, alias_name, alias_type, source, notes)
        SELECT ?, ?, 'legacy_name', ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM equipment_aliases
            WHERE equipment_id = ? AND alias_name = ?
        )
        """,
        (equipment_id, alias, SOURCE, notes, equipment_id, alias),
    )


def merge_equipment(cur: sqlite3.Cursor, source_id: int, target_id: int) -> None:
    source = cur.execute("SELECT * FROM equipment WHERE id = ?", (source_id,)).fetchone()
    target = cur.execute("SELECT * FROM equipment WHERE id = ?", (target_id,)).fetchone()
    if not source or not target:
        return

    add_alias(
        cur,
        target_id,
        source["name"],
        f"Merged duplicate starter equipment record id {source_id}.",
    )
    for alias in cur.execute(
        "SELECT alias_name, notes FROM equipment_aliases WHERE equipment_id = ?",
        (source_id,),
    ).fetchall():
        add_alias(
            cur,
            target_id,
            alias["alias_name"],
            alias["notes"] or f"Moved from merged equipment record id {source_id}.",
        )

    merged_notes = target["notes"] or ""
    if source["notes"] and source["notes"] not in merged_notes:
        merged_notes = (merged_notes + " " if merged_notes else "") + source["notes"]

    cur.execute(
        """
        UPDATE equipment
        SET mcc = COALESCE(NULLIF(mcc, ''), ?),
            drawing_refs = ?,
            manufacturer = COALESCE(manufacturer, ?),
            model = COALESCE(model, ?),
            notes = NULLIF(?, '')
        WHERE id = ?
        """,
        (
            source["mcc"],
            merge_refs(target["drawing_refs"], source["drawing_refs"]),
            source["manufacturer"],
            source["model"],
            merged_notes,
            target_id,
        ),
    )
    cur.execute("UPDATE equipment_attributes SET equipment_id = ? WHERE equipment_id = ?", (target_id, source_id))
    cur.execute(
        "UPDATE equipment_locations SET equipment_id = ? WHERE equipment_id = ?",
        (target_id, source_id),
    )
    cur.execute(
        "UPDATE equipment_relationships SET parent_equipment_id = ? WHERE parent_equipment_id = ?",
        (target_id, source_id),
    )
    cur.execute(
        "UPDATE equipment_relationships SET child_equipment_id = ? WHERE child_equipment_id = ?",
        (target_id, source_id),
    )
    cur.execute("DELETE FROM equipment_aliases WHERE equipment_id = ?", (source_id,))
    cur.execute("DELETE FROM equipment WHERE id = ?", (source_id,))


def upsert_equipment(
    cur: sqlite3.Cursor,
    name: str,
    equipment_type: str,
    area: str,
    notes: str,
    aliases: list[str] | None = None,
    drawing_refs: list[str] | None = None,
    mcc: str | None = None,
    location: str | None = None,
) -> int:
    existing = cur.execute("SELECT id, drawing_refs, notes FROM equipment WHERE name = ?", (name,)).fetchone()
    if existing:
        equipment_id = existing["id"]
        merged_notes = existing["notes"] or ""
        if notes and notes not in merged_notes:
            merged_notes = (merged_notes + " " if merged_notes else "") + notes
        cur.execute(
            """
            UPDATE equipment
            SET equipment_type = COALESCE(NULLIF(equipment_type, ''), ?),
                area = COALESCE(NULLIF(area, ''), ?),
                mcc = COALESCE(NULLIF(mcc, ''), ?),
                drawing_refs = ?,
                notes = NULLIF(?, ''),
                location_description = COALESCE(location_description, ?)
            WHERE id = ?
            """,
            (
                equipment_type,
                area,
                mcc,
                merge_refs(existing["drawing_refs"], json.dumps(drawing_refs or [])),
                merged_notes,
                location,
                equipment_id,
            ),
        )
    else:
        cur.execute(
            """
            INSERT INTO equipment
                (name, equipment_type, area, mcc, drawing_refs, manufacturer, model, notes, created_at, location_description)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
            """,
            (
                name,
                equipment_type,
                area,
                mcc,
                json.dumps(drawing_refs or []),
                notes,
                CREATED_AT,
                location,
            ),
        )
        equipment_id = cur.lastrowid

    for alias in aliases or []:
        if alias != name:
            add_alias(cur, equipment_id, alias, f"Alias retained during {SOURCE} integration.")
    return equipment_id


def rename_existing(cur: sqlite3.Cursor, equipment_id: int, new_name: str, area: str, equipment_type: str) -> None:
    row = cur.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
    if not row:
        return
    if row["name"] != new_name:
        add_alias(cur, equipment_id, row["name"], f"Previous starter name before canonical rename to {new_name}.")
    cur.execute(
        """
        UPDATE equipment
        SET name = ?, area = ?, equipment_type = COALESCE(NULLIF(?, ''), equipment_type)
        WHERE id = ?
        """,
        (new_name, area, equipment_type, equipment_id),
    )


def load_site_assets() -> list[dict]:
    layout = json.loads(SITE_LAYOUT_PATH.read_text(encoding="utf-8"))
    assets: list[dict] = []
    for location in layout.get("locations", []):
        for asset in location.get("assets", []):
            item = dict(asset)
            item["_location_name"] = location.get("name")
            assets.append(item)
    return assets


def ensure_bmh_in_site_layout() -> None:
    layout = json.loads(SITE_LAYOUT_PATH.read_text(encoding="utf-8"))
    receiving = next((l for l in layout.get("locations", []) if l.get("id") == "receiving"), None)
    if not receiving:
        return
    if any(a.get("id") == "BMH_SHIP_UNLOADER" for a in receiving.get("assets", [])):
        return
    receiving.setdefault("assets", []).insert(
        0,
        {
            "id": "BMH_SHIP_UNLOADER",
            "name": "BMH Ship Unloader",
            "drawing_label": "Ship unloader",
            "canonical_name": "BMH_SHIP_UNLOADER",
            "long_name": "BMH Ship Unloader",
            "type": "ship_unloader",
            "notes": "Existing marine intake asset added to topology during 25 Apr 2026 merge.",
            "components": [],
        },
    )
    layout["_note"] = (
        layout.get("_note", "")
        + " BMH Ship Unloader added to receiving topology during merge pass."
    ).strip()
    SITE_LAYOUT_PATH.write_text(json.dumps(layout, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    ensure_bmh_in_site_layout()
    assets = load_site_assets()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("BEGIN")

    duplicate_map = {
        2: 43,
        3: 44,
        4: 45,
        5: 46,
        6: 51,
        7: 52,
        10: 51,
    }
    for source_id, target_id in duplicate_map.items():
        merge_equipment(cur, source_id, target_id)

    canonical_existing = {
        20: ("BB4", "Silo Cluster 2", "belt_conveyor"),
        21: ("BB5", "Silo Cluster 2", "belt_conveyor"),
        22: ("BB7", "Silo Cluster 2", "belt_conveyor"),
        26: ("RC3", "Main Elevators And Distribution", "chain_conveyor"),
        27: ("RC4", "Main Elevators And Distribution", "chain_conveyor"),
        12: ("RB8", "Silo Cluster 2", "tripper"),
        13: ("RB9", "Silo Cluster 2", "tripper"),
        51: ("JL1", "Receiving", "bucket_elevator"),
        52: ("JL2", "Receiving", "bucket_elevator"),
        61: ("BB1", "Silo Cluster 1", "belt_conveyor"),
        62: ("BB2", "Silo Cluster 1", "belt_conveyor"),
        63: ("BB3", "Silo Cluster 1", "belt_conveyor"),
        64: ("BB1_V1", "Silo Cluster 1", "rotary_valve"),
        65: ("BB2_V1", "Silo Cluster 1", "rotary_valve"),
        66: ("BB3_V1", "Silo Cluster 1", "rotary_valve"),
        67: ("ME1", "Silo Cluster 1", "bucket_elevator"),
        68: ("ME2", "Silo Cluster 1", "bucket_elevator"),
        69: ("ME3", "Silo Cluster 1", "bucket_elevator"),
        70: ("ME4", "Silo Cluster 1", "bucket_elevator"),
    }
    for equipment_id, args in canonical_existing.items():
        rename_existing(cur, equipment_id, *args)

    existing_asset_names = {row["name"] for row in cur.execute("SELECT name FROM equipment").fetchall()}
    for asset in assets:
        asset_name = asset.get("name") or asset.get("canonical_name") or asset.get("id")
        canonical_name = asset.get("canonical_name") or asset_name
        long_name = asset.get("long_name") or asset_name
        candidate_names = {asset_name, canonical_name, long_name, asset.get("id")}
        if existing_asset_names.intersection(candidate_names):
            equipment_id = cur.execute(
                "SELECT id FROM equipment WHERE name IN ({}) LIMIT 1".format(",".join(["?"] * len(candidate_names))),
                tuple(candidate_names),
            ).fetchone()["id"]
            for alias in candidate_names:
                add_alias(cur, equipment_id, alias, f"Topology label retained during {SOURCE} integration.")
            continue

        aliases = sorted(v for v in candidate_names if v and v != asset_name)
        notes = "Created from September 2021 process schematic topology."
        if asset.get("notes"):
            notes += " " + asset["notes"]
        upsert_equipment(
            cur,
            asset_name,
            asset.get("type") or "process_equipment",
            asset.get("_location_name") or "Topology",
            notes,
            aliases=aliases,
            location=asset.get("_location_name"),
        )
        existing_asset_names.add(asset_name)

    conn.commit()
    conn.close()
    print(f"Topology merge applied at {datetime.now().isoformat(timespec='seconds')}.")


if __name__ == "__main__":
    main()
