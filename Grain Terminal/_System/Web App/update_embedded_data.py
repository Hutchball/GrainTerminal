"""
update_embedded_data.py
Reads JSON files from data/ and embeds them into app.js.
Run after export_to_json.py whenever the database changes.

Usage:
    python3 update_embedded_data.py
"""

import json
from pathlib import Path

BASE     = Path(__file__).parent
DATA_DIR = BASE / "data"
APP_PATH = BASE / "app.js"
MARKER   = "// Port of Liverpool Grain Terminal"


def load(name: str) -> str:
    return json.dumps(json.loads((DATA_DIR / name).read_text()), separators=(",", ":"))


def main():
    block = "\n".join([
        "// ── Embedded data (auto-generated — do not edit manually) ───────────────────",
        f"const DATA_STATS = {load('stats.json')};",
        f"const DATA_DOCUMENTS = {load('documents.json')};",
        f"const DATA_EQUIPMENT = {load('equipment.json')};",
        f"const DATA_ATTRS = {load('equipment_attributes.json')};",
        f"const DATA_RELATIONS = {load('equipment_relationships.json')};",
        f"const DATA_PHOTOS = {load('photos.json')};",
        f"const DATA_LAYOUT = {load('site_layout.json')};",
        f"const DATA_LUBRICANTS = {load('lubricants.json')};",
        f"const DATA_EQUIPMENT_LUBRICANTS = {load('equipment_lubricants.json')};",
        f"const DATA_EQUIPMENT_PULLEYS = {load('equipment_pulleys.json')};",
        f"const DATA_EQUIPMENT_GEARBOXES = {load('equipment_gearboxes.json')};",
        f"const DATA_ELECTRICAL_MOTORS = {load('electrical_motors.json')};",
        f"const DATA_DUST_BAG_STOCK = {load('dust_bag_stock.json')};",
        f"const DATA_EQUIPMENT_DUST_BAGS = {load('equipment_dust_bags.json')};",
        f"const DATA_DUST_BAG_CHANGE_HISTORY = {load('dust_bag_change_history.json')};",
        "",
    ])

    app = APP_PATH.read_text()
    idx = app.find(MARKER)
    if idx == -1:
        raise RuntimeError(f"Marker not found in app.js: {MARKER}")

    APP_PATH.write_text(block + app[idx:])
    print("Embedded app.js data refreshed.")


if __name__ == "__main__":
    main()
