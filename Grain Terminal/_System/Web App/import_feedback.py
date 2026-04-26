#!/usr/bin/env python3
"""
Import feedback JSON files exported from the standalone portal into the SQLite
verification_feedback table.

Usage:
    python3 import_feedback.py /path/to/feedback.json [...]
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "grain_terminal.db"


def load_feedback_entries(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError(f"{path} does not contain a feedback object or list")
    return payload


def normalise_entry(entry: dict):
    now = datetime.now(timezone.utc).isoformat()
    return (
        entry.get("item_type") or "grainbot_answer",
        entry.get("item_id"),
        entry.get("item_label") or "Unlabelled item",
        entry.get("source_path"),
        entry.get("source_link"),
        entry.get("query_text"),
        entry.get("response_text"),
        entry.get("verdict") or "incorrect",
        entry.get("comments"),
        entry.get("reported_by") or "portal-user",
        entry.get("channel") or "portal",
        entry.get("status") or "open",
        entry.get("created_at") or now,
    )


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 import_feedback.py /path/to/feedback.json [...]", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted = 0

    for arg in argv[1:]:
        path = Path(arg).expanduser()
        entries = load_feedback_entries(path)
        for entry in entries:
            cursor.execute(
                """
                INSERT INTO verification_feedback
                    (item_type, item_id, item_label, source_path, source_link,
                     query_text, response_text, verdict, comments, reported_by,
                     channel, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                normalise_entry(entry),
            )
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Imported {inserted} feedback entr{'y' if inserted == 1 else 'ies'} into {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
