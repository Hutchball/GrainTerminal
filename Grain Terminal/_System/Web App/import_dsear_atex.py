"""
import_dsear_atex.py
====================
Imports DSEAR ATEX area classification data from the 26 RSGT drawings
(7840-73-00001 to 7840-73-00026, Rev A, 2024 Periodic Inspection File).

Also registers each drawing in the documents table.

Run from inside:  Grain Terminal/_System/Web App/
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db_config import get_connection

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# SCHEMA MIGRATION — adds ATEX tables if they don't exist (idempotent)
# ---------------------------------------------------------------------------

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS atex_drawings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    drawing_number  TEXT NOT NULL UNIQUE,   -- e.g. 7840-73-00002
    drawing_title   TEXT NOT NULL,
    revision        TEXT NOT NULL DEFAULT 'A',
    location_area   TEXT,                   -- plain-text area description
    source_report   TEXT,                   -- underpinning DSEAR report reference
    drawn_by        TEXT,
    checked_by      TEXT,
    approved_by     TEXT,
    date_drawn      TEXT,
    date_approved   TEXT,
    general_notes   TEXT,
    confidence      TEXT NOT NULL DEFAULT 'VERIFIED',
    file_path       TEXT,                   -- relative to "Grain Terminal/"
    imported_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS atex_zones (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    drawing_id           INTEGER NOT NULL REFERENCES atex_drawings(id) ON DELETE CASCADE,
    zone_type            TEXT NOT NULL,     -- 'Zone 20', 'Zone 21', 'Zone 22'
    location_description TEXT NOT NULL,
    extent               TEXT,
    equipment_refs       TEXT,             -- JSON array of equipment names/tags from drawing
    notes                TEXT,
    dsear_report_ref     TEXT,             -- e.g. 'REF 4.45'
    confidence           TEXT NOT NULL DEFAULT 'VERIFIED'
);

CREATE TABLE IF NOT EXISTS atex_ip_standard (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_type       TEXT NOT NULL UNIQUE,
    min_ip_rating   TEXT NOT NULL,
    max_surface_temp_c INTEGER NOT NULL,
    notes           TEXT
);
"""

# ---------------------------------------------------------------------------
# IP STANDARD DATA (consistent across all 26 drawings)
# ---------------------------------------------------------------------------

IP_STANDARDS = [
    {"zone_type": "Zone 22", "min_ip_rating": "IP5X", "max_surface_temp_c": 205,
     "notes": "Based on 280°C LIT minus 75°C safety margin"},
    {"zone_type": "Zone 21", "min_ip_rating": "IP6X", "max_surface_temp_c": 205,
     "notes": "Based on 280°C LIT minus 75°C safety margin"},
    {"zone_type": "Zone 20", "min_ip_rating": "IP6X", "max_surface_temp_c": 205,
     "notes": "Based on 280°C LIT minus 75°C safety margin"},
]

# ---------------------------------------------------------------------------
# EXTRACTED ATEX DATA — all 26 drawings
# ---------------------------------------------------------------------------

DRAWINGS = [
    {
        "drawing_number": "7840-73-00001",
        "drawing_title": "DSEAR Classified Areas",
        "revision": "A",
        "location_area": "Royal Seaforth Grain Terminal — site overview plan",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Site overview plan. Note 1: Minimum equipment standard IP5X (Zone 22), IP6X (Zone 21), max surface temp 205°C (280°C LIT - 75°C). Note 2: Blanket Zone 22 within galleries. Numbered callouts reference individual detail drawings. Only Zone 22 applied at overview scale.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00001.pdf",
        "zones": [
            {"zone_type": "Zone 22", "location_description": "Jetty Gallery", "extent": "Blanket Zone 22 within gallery", "equipment_refs": [], "notes": "Note 2 applies", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "RB3/RB4 Receiving Gallery", "extent": "Blanket Zone 22 within gallery", "equipment_refs": ["RB3", "RB4"], "notes": "Note 2 applies", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Mill Feed Gallery (DACSA & ADM)", "extent": "Blanket Zone 22 within gallery", "equipment_refs": [], "notes": "Note 2 applies", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "FB1 Gallery", "extent": "Blanket Zone 22 within gallery", "equipment_refs": ["FB1"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "RB12 Gallery (upper and lower runs)", "extent": "Blanket Zone 22 within gallery", "equipment_refs": ["RB12"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Cargills Soya Mill Gallery", "extent": "Blanket Zone 22 within gallery", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Junction Tower", "extent": "Blanket Zone 22", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Lorry Loading House", "extent": "Blanket Zone 22", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Workhouse", "extent": "Blanket Zone 22 — see individual floor drawings", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Silo 1, Silo 2, Silo 3", "extent": "Blanket Zone 22 — see individual silo drawings 00004, 00005, 00006", "equipment_refs": [], "notes": "Cross-ref: 7840-73-00004 (Silo 1), 7840-73-00005 (Silo 2), 7840-73-00006 (Silo 3)", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00002",
        "drawing_title": "Jetty Gallery Area Classification Drawing",
        "revision": "A",
        "location_area": "Jetty Gallery — including gallery basement and discharge chutes (RB1 to RC1, RB2 to RC2)",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X (Zone 22), IP6X (Zone 21), max 205°C. Note 2: Zone 20 up to filter medium, Zone 21 where fines dislodged and fall back. Note 3: Blanket Zone 22 within gallery. Note 4: Zone 21 within discharge chutes RB1-RC1 and RB2-RC2. Note 5: Blanket Zone 22 within gallery basement.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00002.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Internally within gallery up to the filter medium", "extent": "Inside gallery body upper section to filter medium boundary", "equipment_refs": [], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Within gallery where fines are dislodged and fall back to the conveyor", "extent": "Lower section of gallery body at conveyor level", "equipment_refs": ["RC1"], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Within discharge chutes from RB1 to RC1 and RB2 to RC2", "extent": "Interior of discharge chutes", "equipment_refs": ["RB1", "RC1", "RB2", "RC2"], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Jetty Gallery", "extent": "Full outer envelope of gallery structure", "equipment_refs": [], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Gallery Basement", "extent": "Entire gallery basement area", "equipment_refs": [], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00003",
        "drawing_title": "Junction House Area Classification Drawing",
        "revision": "A",
        "location_area": "Junction House — ground floor, first floor, second floor, basement",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X (Zone 22), IP6X (Zone 21), max 205°C. Note 2: Zone 21 of 1m radius down to ground from conveyor discharge to bucket elevator. Note 3: Blanket Zone 22 in all areas beneath top floor. Note 4: Zone 21 within bucket elevator. Note 5: Zone 22 of 1m radius from housekeeping/inspection hatches. Zones 0 and 20 in key but not applied.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00003.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within Bucket Elevator 1 and Bucket Elevator 2", "extent": "Full interior of bucket elevator shafts", "equipment_refs": ["Bucket Elevator 1", "Bucket Elevator 2"], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "1m radius down to ground from conveyor discharge to bucket elevator", "extent": "R1000 (1m radius) at ground and basement level at discharge points", "equipment_refs": ["RB3", "RB4"], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 in all areas beneath the top floor of the Junction House", "extent": "Full cross-section basement through first floor", "equipment_refs": ["RB3", "RB4", "RC1", "RC2"], "notes": "Ref [1] Table 2, Ref 4.15", "dsear_report_ref": "REF 4.15"},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 1m radius from housekeeping/inspection hatches", "extent": "R1000 at basement level", "equipment_refs": [], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00004",
        "drawing_title": "Silo 1 Elevation Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 1 — full elevation including bins, 6th (Cupola) Floor, and basement",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 throughout Silo 1 6th (Cupola) Floor — see 7840-73-00015 for tripper cart detail. Note 3: Zone 21 within bins. Note 4: Blanket Zone 22 throughout Silo 1 Basement — see 7840-73-00026 for basement detail.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00004.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the Silo 1 bins", "extent": "Full interior of all Silo 1 bin bodies", "equipment_refs": ["Silo 1 Bins"], "notes": "Ref [1] Table 2", "dsear_report_ref": "REF 4.45"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Silo 1 6th (Cupola) Floor", "extent": "Full cupola floor level", "equipment_refs": [], "notes": "Cross-ref: 7840-73-00015 for tripper cart", "dsear_report_ref": "REF 4.42"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Silo 1 Basement", "extent": "Full basement area below ground level", "equipment_refs": [], "notes": "Cross-ref: 7840-73-00026 for basement detail", "dsear_report_ref": "REF 4.60"},
        ]
    },
    {
        "drawing_number": "7840-73-00005",
        "drawing_title": "Silo 2 Elevation Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 2 — full elevation including bins, Cupola Floor, basement, and BB transfer area",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 Silo 2 Cupola Floor — see 7840-73-00015. Note 3: Zone 21 within bins. Note 4: Blanket Zone 22 Silo 2 Basement — see 7840-73-00026. Note 5: Blanket Zone 22 BB4/5 to BB6/7 transfer area. Note 6: Blanket Zone 22 BB6/7 Gallery. FLAG: drawing label reads 'BB3/4 to BB6/7 Transfer Area' but Note 5 text states 'BB4/5 to BB6/7' — verify against report REF 4.65.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00005.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the Silo 2 bins", "extent": "Full interior of all Silo 2 bin bodies", "equipment_refs": ["Silo 2 Bins"], "notes": "Ref [1] Table 2", "dsear_report_ref": "REF 4.45"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Silo 2 Cupola Floor", "extent": "Full cupola floor level", "equipment_refs": [], "notes": "Cross-ref: 7840-73-00015 for tripper cart", "dsear_report_ref": "REF 4.42"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Silo 2 Basement", "extent": "Full basement area below ground level", "equipment_refs": [], "notes": "Cross-ref: 7840-73-00026", "dsear_report_ref": "REF 4.63"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the BB4/5 to BB6/7 Transfer Area", "extent": "Full transfer area structure (label discrepancy noted: drawing says BB3/4, note says BB4/5)", "equipment_refs": ["BB3", "BB4", "BB5", "BB6", "BB7"], "notes": "LABEL DISCREPANCY: drawing label 'BB3/4 to BB6/7'; Note 5 text 'BB4/5 to BB6/7'. Verify vs REF 4.65.", "dsear_report_ref": "REF 4.65"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the BB6/7 Gallery", "extent": "Full gallery structure", "equipment_refs": ["BB6", "BB7"], "notes": "Ref [1] Table 2", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00006",
        "drawing_title": "Silo 3 Elevation Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 3 — full elevation including bins, basement, RB11 Gallery, turnheads, and Silo 3 Dust Plant",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within bins. Note 3: Blanket Zone 22 Silo 3 Basement. Note 4: Zone 21 within chutes and through turnheads. Note 5: Blanket Zone 22 in room containing turnheads. Note 6: Blanket Zone 22 throughout conveyor galleries. Cross-ref: 7840-73-00022 (Silo 3 Dust Plant).",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00006.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the Silo 3 bins", "extent": "Full interior of all Silo 3 bin bodies", "equipment_refs": ["Silo 3 Bins"], "notes": None, "dsear_report_ref": "REF 4.45"},
            {"zone_type": "Zone 21", "location_description": "Within the chutes and through the turnheads", "extent": "Interior of chutes and turnhead structures at apex of silo", "equipment_refs": ["Turnheads"], "notes": None, "dsear_report_ref": "REF 4.73"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Silo 3 Basement", "extent": "Full basement area", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.68"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 in the room containing the turnheads", "extent": "Full turnhead room structure at top of silo", "equipment_refs": ["Turnheads"], "notes": "Shares REF 4.73 with Zone 21 within chutes", "dsear_report_ref": "REF 4.73"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout conveyor galleries — RB11 Gallery", "extent": "Full RB11 gallery structure", "equipment_refs": ["RB11"], "notes": None, "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00007",
        "drawing_title": "Silo 3 Tower Elevation Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 3 Tower — Feed Elevator Tower (FE1) including conveyor FB1 and Silo 3 Basement connection",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 throughout feed elevator tower building. Note 3: Blanket Zone 22 throughout basement. Note 4: Zone 21 within bucket elevator FE1.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00007.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the bucket elevator FE1", "extent": "Full height of FE1 elevator shaft including head and boot", "equipment_refs": ["FE1"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Feed Elevator Tower building", "extent": "Full outer envelope of tower for entire height", "equipment_refs": ["FE1", "FB1"], "notes": None, "dsear_report_ref": "REF 4.69"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Silo 3 Basement (tower connection)", "extent": "Basement at foot of tower", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.66"},
        ]
    },
    {
        "drawing_number": "7840-73-00008",
        "drawing_title": "Silvertell Ship Unloader Area Classification Drawing",
        "revision": "A",
        "location_area": "Silvertell Ship Unloader (Jetty area)",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 22 within screw conveyors. Note 3: Zone 21 within chutes in turret. Note 4: Zone 20 within DCE unit up to filter medium. Note 5: Zone 21 where dust is dislodged back into system (DCE). Note 6: Blanket Zone 22 throughout conveyor galleries.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00008.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Within the DCE unit up to the filter medium", "extent": "Interior of DCE unit to filter medium boundary", "equipment_refs": ["DCE UNIT"], "notes": None, "dsear_report_ref": "REF 4.5"},
            {"zone_type": "Zone 21", "location_description": "Within the chutes in the turret", "extent": "Interior of turret chutes", "equipment_refs": ["Turret chutes"], "notes": None, "dsear_report_ref": "REF 4.4"},
            {"zone_type": "Zone 21", "location_description": "Where dust is dislodged back into the system (DCE unit)", "extent": "Area within DCE where dust is returned", "equipment_refs": ["DCE UNIT"], "notes": None, "dsear_report_ref": "REF 4.5"},
            {"zone_type": "Zone 22", "location_description": "Within the screw conveyors", "extent": "Interior of screw conveyors", "equipment_refs": ["Screw conveyor"], "notes": None, "dsear_report_ref": "REF 4.3"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout conveyor galleries — Jetty Gallery", "extent": "Full gallery area", "equipment_refs": ["Jetty Gallery"], "notes": None, "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00009",
        "drawing_title": "Workhouse 11th Floor Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 11th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within weighscale air ducts. Note 3: Zone 21 within bucket elevators. Entire floor area is Zone 21.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00009.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the weighscale air ducts", "extent": "Interior of weighscale air duct system on 11th floor", "equipment_refs": ["Weighscale air ducts"], "notes": None, "dsear_report_ref": "REF 4.21"},
            {"zone_type": "Zone 21", "location_description": "Within the bucket elevators — 11th floor", "extent": "Interior of bucket elevator shafts passing through 11th floor", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4"], "notes": "Entire 11th floor plan area is Zone 21", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00010",
        "drawing_title": "Workhouse 10th Floor Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 10th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within chute and upper garner. Note 3: Zone 21 within bucket elevators. Entire 10th floor area is Zone 21.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00010.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the chute and upper garner — 10th floor", "extent": "Interior of chutes and upper garner between 10th and 11th floors", "equipment_refs": ["Upper garner"], "notes": None, "dsear_report_ref": "REF 4.26"},
            {"zone_type": "Zone 21", "location_description": "Within the bucket elevators — 10th floor", "extent": "Interior of bucket elevator shafts passing through 10th floor", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4"], "notes": "Entire 10th floor plan area is Zone 21", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00011",
        "drawing_title": "Workhouse 9th Floor Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 9th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 21 within garner and weighscales. Note 3: Zone 22 of 1m radius from all hatches and skirts down to ground. Note 4: Zone 21 within bucket elevators.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00011.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Blanket Zone 21 within the garner and weighscales — 9th floor", "extent": "Entire garner and weighscales area on 9th floor", "equipment_refs": ["Garner", "Weighscales"], "notes": None, "dsear_report_ref": "REF 4.30"},
            {"zone_type": "Zone 21", "location_description": "Within the bucket elevators — 9th floor", "extent": "Interior of bucket elevator shafts passing through 9th floor", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 1m radius from all hatches and skirts down to ground", "extent": "R1000 (1m radius) at each hatch/skirt location extending to ground", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.30"},
        ]
    },
    {
        "drawing_number": "7840-73-00012",
        "drawing_title": "Workhouse 8th Floor Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 8th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 21 within garner and weighscales. Note 3: Zone 22 of 1m radius around hatches. Note 4: Zone 21 within bucket elevators.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00012.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Blanket Zone 21 within the garner and weighscales — 8th floor", "extent": "Entire garner and weighscale areas on 8th floor (Scale 1, 2, 3, 4)", "equipment_refs": ["Garner", "Scale 1", "Scale 2", "Scale 3", "Scale 4"], "notes": None, "dsear_report_ref": "REF 4.30"},
            {"zone_type": "Zone 21", "location_description": "Within the bucket elevators — 8th floor", "extent": "Interior of bucket elevator shafts passing through 8th floor", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 1m radius around the hatches — 8th floor", "extent": "R1000 (1m radius) at each hatch location", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.32"},
        ]
    },
    {
        "drawing_number": "7840-73-00013",
        "drawing_title": "Workhouse 7th Floor Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 7th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within discharge chute. Note 3: Zone 22 of 1m radius around turnhead hood. Note 4: Blanket Zone 22 throughout the 7th floor.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00013.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the discharge chute — 7th floor", "extent": "Interior of discharge chutes on 7th floor", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 1m radius around the turnhead hood", "extent": "R1000 (1m radius) at turnhead hood location", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.35"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the 7th floor", "extent": "Entire 7th floor area — blanket zone", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4"], "notes": None, "dsear_report_ref": "REF 4.36"},
        ]
    },
    {
        "drawing_number": "7840-73-00014",
        "drawing_title": "Workhouse 6th Floor (Cupola) Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 6th Floor (Cupola)",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 throughout area. Note 3: Zone 20 within DCE units up to filter medium. Note 4: Zone 21 within discharge chutes. Note 5: Zone 21 of 1m radius down to ground from discharge chutes. Note 6: Zone 21 within bucket elevators. RB12 enters from two sides.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00014.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Within the DCE units up to the filter medium — Cupola floor", "extent": "Interior of DCE units to filter medium boundary", "equipment_refs": ["DCE units"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Within discharge chutes — Cupola floor", "extent": "Interior of discharge chutes on 6th floor", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Zone 21 of 1m radius down to ground from discharge chutes", "extent": "R1000 (1m radius) at discharge chute outlets", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Within the bucket elevators — Cupola floor", "extent": "Interior of bucket elevator shafts on 6th floor", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4"], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the 6th (Cupola) Floor", "extent": "Entire Cupola floor — blanket zone", "equipment_refs": ["ELV1", "ELV2", "ELV3", "ELV4", "RB12", "DCE units"], "notes": None, "dsear_report_ref": "REF 4.40"},
        ]
    },
    {
        "drawing_number": "7840-73-00015",
        "drawing_title": "Tripper Cart Area Classification Drawing",
        "revision": "A",
        "location_area": "Tripper Cart — Silo cupola floors",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 throughout tripper cart area. Note 3: Zone 21 inside tripper cart legs (chutes). Note 4: Zone 20 up to filter medium. Note 5: Zone 21 within bins. Generic drawing referenced from 7840-73-00004, 00005, 00006.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00015.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Up to filter medium — tripper cart dust collection", "extent": "Interior of filter medium on tripper cart", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Inside the tripper cart legs (chutes)", "extent": "Interior of discharge chutes/legs on tripper cart", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.43"},
            {"zone_type": "Zone 21", "location_description": "Within bins (below tripper cart)", "extent": "Interior of bins receiving grain from tripper cart", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.45"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the tripper cart area", "extent": "Entire tripper cart area — blanket zone", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.42"},
        ]
    },
    {
        "drawing_number": "7840-73-00016",
        "drawing_title": "Lorry Loading House And Trailer Area Classification Drawing",
        "revision": "A",
        "location_area": "Lorry Loading House and Trailer Area",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 within chain conveyors. Note 3: Zone 21 within discharge legs and bins. Note 4: Zone 21 within weigh scales; Zone 22 external to weigh scales. Note 5: Zone 21 within trailer; Zone 22 of 1m radius around trailer (external).",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00016.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the discharge legs into the bins and blanket Zone 21 within the bins", "extent": "Discharge legs and interior of bins in lorry loading house", "equipment_refs": ["Discharge chutes", "Bins"], "notes": None, "dsear_report_ref": "REF 4.48"},
            {"zone_type": "Zone 21", "location_description": "Within the weigh scales", "extent": "Interior of weigh scales", "equipment_refs": ["Weigh scales"], "notes": None, "dsear_report_ref": "REF 4.50"},
            {"zone_type": "Zone 21", "location_description": "Within the trailer", "extent": "Interior of lorry trailer during loading", "equipment_refs": ["Trailer"], "notes": "1m radius Zone 22 external to trailer", "dsear_report_ref": "REF 4.52"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 within chain conveyors", "extent": "Interior of chain conveyor casings", "equipment_refs": ["Chain conveyor"], "notes": None, "dsear_report_ref": "REF 4.47"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 within area external to the weigh scales", "extent": "Area surrounding weigh scales", "equipment_refs": ["Weigh scales"], "notes": None, "dsear_report_ref": "REF 4.51"},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 1m radius external to the trailer", "extent": "R1000 (1m radius) around trailer exterior during loading", "equipment_refs": ["Trailer"], "notes": None, "dsear_report_ref": "REF 4.52"},
        ]
    },
    {
        "drawing_number": "7840-73-00017",
        "drawing_title": "Workhouse 5th Floor Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse 5th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "S. OWEN", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within discharge chute and 1m radius to ground from discharge points. Note 3: Blanket Zone 22 throughout the 5th floor.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00017.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the discharge chute and 1m radius down to ground from discharge points — 5th floor", "extent": "R1000 (1m radius) from each discharge point down to ground", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.53"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the 5th floor", "extent": "Entire 5th floor area", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.53"},
        ]
    },
    {
        "drawing_number": "7840-73-00018",
        "drawing_title": "Workhouse Sub-Basement Area Classification Drawing",
        "revision": "A",
        "location_area": "Workhouse Sub-Basement",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 throughout the area. Note 3: Zone 22 within lorry offtake chain conveyor. Note 4: Zone 21 of 1m radius from discharge points (BB1 to BB3) into bucket elevators.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00018.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Zone 21 of 1m radius from discharge points (conveyors BB1 to BB3) into bucket elevators", "extent": "R1000 (1m radius) at each BB1-BB3 discharge point at boot of each elevator", "equipment_refs": ["BB1", "BB2", "BB3", "ELV1", "ELV2", "ELV3", "ELV4"], "notes": None, "dsear_report_ref": "REF 4.58"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the Workhouse Sub-Basement", "extent": "Entire sub-basement area", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.55"},
            {"zone_type": "Zone 22", "location_description": "Zone 22 within the lorry offtake chain conveyor", "extent": "Interior of lorry offtake chain conveyor", "equipment_refs": ["Lorry offtake chain conveyor"], "notes": None, "dsear_report_ref": "REF 4.56"},
        ]
    },
    {
        "drawing_number": "7840-73-00019",
        "drawing_title": "Silo 2 Basement BB4/5 To BB6/7 Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 2 Basement — BB4/5 to BB6/7 Gallery",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Blanket Zone 22 throughout the area. Note 3: Zone 21 within discharge chutes. UNCERTAINTY: Note 3 sub-reference within DSEAR report Table 2 was not clearly legible at drawing resolution.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00019.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the discharge chutes — Silo 2 Basement BB4/5 to BB6/7", "extent": "Interior of discharge chutes in this basement section", "equipment_refs": [], "notes": "Sub-ref within DSEAR report Table 2 not fully legible on drawing", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the BB4/5 to BB6/7 gallery area", "extent": "Entire area including BB4, BB5, BB6, BB7 and BB6/7 Gallery", "equipment_refs": ["BB4", "BB5", "BB6", "BB7"], "notes": None, "dsear_report_ref": "REF 4.65"},
        ]
    },
    {
        "drawing_number": "7840-73-00020",
        "drawing_title": "4th Floor Mill Feed Conveyor Area Classification Drawing",
        "revision": "A",
        "location_area": "4th Floor Mill Feed Conveyor — 3rd to 5th Floor",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within discharge back to conveyors. Note 3: Blanket Zone 22 throughout the area (3rd-5th floors). FLAG: Title block shows drawing number as 7843-73-00020 — possible typographical error on original drawing. Content and context consistent with 7840 series.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00020.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the discharge back to conveyors — Mill Feed 4th floor", "extent": "Interior of discharge chute from 5th floor down to 4th floor level", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.78"},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the mill feed conveyor area (3rd to 5th floor)", "extent": "Full floor area 3rd to 5th floor", "equipment_refs": [], "notes": None, "dsear_report_ref": "REF 4.79"},
        ]
    },
    {
        "drawing_number": "7840-73-00021",
        "drawing_title": "Disab Dust Collection Area Classification Drawing",
        "revision": "A",
        "location_area": "Disab Dust Collection Unit (mobile)",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 20 within all pipes/hoses up to filter in Disab unit. Note 3: Zone 22 between main filter and safety filter. Covers the Disab mobile dust collection unit only — no surrounding area classification shown.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00021.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Within all pipes/hoses up to the filter in the Disab unit", "extent": "All pipes and hoses leading up to filter within the Disab unit", "equipment_refs": ["Disab dust collection unit"], "notes": None, "dsear_report_ref": "REF 4.81"},
            {"zone_type": "Zone 22", "location_description": "Between main filter and safety filter in the Disab unit", "extent": "Zone between main and safety filter elements inside Disab unit", "equipment_refs": ["Disab dust collection unit"], "notes": None, "dsear_report_ref": "REF 4.81"},
        ]
    },
    {
        "drawing_number": "7840-73-00022",
        "drawing_title": "Silo 3 Dust Plant Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 3 Dust Plant",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 20 within ductwork up to filter medium. Note 3: Zone 21 within area where dust is knocked back down to conveyors. Note 4: Zone 22 of 2m radius from filter exhaust down to ground (R2000). No equipment tags on drawing — generic schematic.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00022.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Within the ductwork up to the filter medium — Silo 3 Dust Plant", "extent": "Interior of ductwork from dust source up to filter medium", "equipment_refs": ["Silo 3 Dust Plant ductwork"], "notes": None, "dsear_report_ref": "REF 4.84"},
            {"zone_type": "Zone 21", "location_description": "Within the area where dust is knocked back down to conveyors — Silo 3 Dust Plant", "extent": "Area within dust plant body where dust is returned", "equipment_refs": ["Silo 3 Dust Plant"], "notes": None, "dsear_report_ref": "REF 4.84"},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 2m radius from filter exhaust down to ground — Silo 3 Dust Plant", "extent": "R2000 (2m radius) from filter exhaust outlet to ground level", "equipment_refs": ["Silo 3 Dust Plant filter exhaust"], "notes": None, "dsear_report_ref": "REF 4.85"},
        ]
    },
    {
        "drawing_number": "7840-73-00023",
        "drawing_title": "Main Dust Plant Area Classification Drawing",
        "revision": "A",
        "location_area": "Main Dust Plant",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 20 within ductwork up to filter medium. Note 3: Zone 22 within clean side of filter medium and 2m from filter exhaust (R2000). Note 4: Zone 22 within conveyors. Note 5: Zone 20 within bin. Zone 21 does NOT appear on this drawing — notable difference from Silo 3 Dust Plant (00022).",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00023.pdf",
        "zones": [
            {"zone_type": "Zone 20", "location_description": "Within the ductwork up to the filter medium — Main Dust Plant", "extent": "Interior of ductwork up to filter medium", "equipment_refs": ["Main Dust Plant ductwork"], "notes": None, "dsear_report_ref": "REF 4.89"},
            {"zone_type": "Zone 20", "location_description": "Within the bin — Main Dust Plant", "extent": "Interior of bin/hopper below main dust plant", "equipment_refs": ["Main Dust Plant bin/hopper"], "notes": None, "dsear_report_ref": "REF 4.91"},
            {"zone_type": "Zone 22", "location_description": "Within the clean side of the filter medium and 2m from filter exhaust — Main Dust Plant", "extent": "Clean side of filter plus R2000 (2m radius) from exhaust to ground", "equipment_refs": ["Main Dust Plant filter"], "notes": None, "dsear_report_ref": "REF 4.89"},
            {"zone_type": "Zone 22", "location_description": "Within the conveyors — Main Dust Plant", "extent": "Interior of conveyor enclosures served by main dust plant", "equipment_refs": ["Conveyors (generic)"], "notes": None, "dsear_report_ref": "REF 4.90"},
        ]
    },
    {
        "drawing_number": "7840-73-00024",
        "drawing_title": "Generic Discharge Chute Area Classification Drawing",
        "revision": "A",
        "location_area": "Generic — applies to all discharge chutes at the terminal",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within discharge chutes. Note 3: Zone 21 of 1m radius down to ground from discharge chutes. Generic drawing — applies to ALL discharge chutes on site.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00024.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within discharge chutes (generic — all chutes on site)", "extent": "Full interior volume of any discharge chute", "equipment_refs": [], "notes": "Generic — applies to all discharge chutes at RSGT", "dsear_report_ref": None},
            {"zone_type": "Zone 21", "location_description": "Zone 21 of 1m radius down to ground from discharge chutes (generic)", "extent": "R1000 (1m radius) arc from chute outlet to ground", "equipment_refs": [], "notes": "Generic — applies to all discharge chutes at RSGT", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00025",
        "drawing_title": "Generic Inspection Hatch Area Classification Drawing",
        "revision": "A",
        "location_area": "Generic — applies to all inspection hatches and housekeeping hatches at the terminal",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within bucket elevator. Note 3: Zone 22 of 1m radius from housekeeping/inspection hatches down to ground. Generic drawing — applies to ALL inspection hatches on site.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00025.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within bucket elevators (generic — applies to all)", "extent": "Full interior of bucket elevator casing", "equipment_refs": [], "notes": "Generic", "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Zone 22 of 1m radius from housekeeping/inspection hatches down to ground (generic)", "extent": "R1000 (1m radius) at each hatch location extending to ground", "equipment_refs": [], "notes": "Generic — applies to all inspection/housekeeping hatches at RSGT", "dsear_report_ref": None},
        ]
    },
    {
        "drawing_number": "7840-73-00026",
        "drawing_title": "Silo 1 & 2 Basement Area Classification Drawing",
        "revision": "A",
        "location_area": "Silo 1 & 2 Basement",
        "source_report": "7619_REP01 Royal Seaforth Grain Terminal DSEAR Hazardous Area Classification Report",
        "drawn_by": "H. RAZA", "checked_by": "S. OWEN", "approved_by": "A. WOOD",
        "date_drawn": "15/06/20", "date_approved": "09/07/20",
        "general_notes": "Note 1: IP5X/IP6X, max 205°C. Note 2: Zone 21 within discharge chutes. Note 3: Blanket Zone 22 throughout the area. IMPORTANT: The ENTIRE Silo 1 & 2 basement is a blanket Zone 22 — all equipment in this space must be Zone 22 rated as a minimum.",
        "confidence": "VERIFIED",
        "file_path": "Compliance/DSEAR/7840-73-00026.pdf",
        "zones": [
            {"zone_type": "Zone 21", "location_description": "Within the discharge chutes — Silo 1 & 2 Basement", "extent": "Interior of all discharge chutes in the Silo 1 & 2 basement", "equipment_refs": [], "notes": None, "dsear_report_ref": None},
            {"zone_type": "Zone 22", "location_description": "Blanket Zone 22 throughout the entire Silo 1 & 2 Basement", "extent": "BLANKET — entire basement space floor to ceiling, wall to wall. All equipment in this space is in Zone 22.", "equipment_refs": [], "notes": "SAFETY NOTE: Blanket classification — every item of equipment in this basement must be Zone 22 rated minimum.", "dsear_report_ref": "REF 4.60"},
        ]
    },
]

# ---------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------

def run_import():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Apply migration
    for statement in MIGRATION_SQL.split(";"):
        s = statement.strip()
        if s:
            cur.execute(s)
    conn.commit()
    print("✓ Schema migrated")

    # 2. IP standards (idempotent)
    for ip in IP_STANDARDS:
        cur.execute("""
            INSERT OR REPLACE INTO atex_ip_standard (zone_type, min_ip_rating, max_surface_temp_c, notes)
            VALUES (?, ?, ?, ?)
        """, (ip["zone_type"], ip["min_ip_rating"], ip["max_surface_temp_c"], ip["notes"]))
    conn.commit()
    print("✓ IP standards loaded")

    # 3. Drawings and zones
    drawings_inserted = 0
    zones_inserted = 0

    for d in DRAWINGS:
        # Upsert drawing
        cur.execute("""
            INSERT INTO atex_drawings
                (drawing_number, drawing_title, revision, location_area, source_report,
                 drawn_by, checked_by, approved_by, date_drawn, date_approved,
                 general_notes, confidence, file_path, imported_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(drawing_number) DO UPDATE SET
                drawing_title=excluded.drawing_title,
                revision=excluded.revision,
                location_area=excluded.location_area,
                source_report=excluded.source_report,
                drawn_by=excluded.drawn_by,
                checked_by=excluded.checked_by,
                approved_by=excluded.approved_by,
                date_drawn=excluded.date_drawn,
                date_approved=excluded.date_approved,
                general_notes=excluded.general_notes,
                confidence=excluded.confidence,
                file_path=excluded.file_path
        """, (
            d["drawing_number"], d["drawing_title"], d["revision"],
            d["location_area"], d["source_report"],
            d.get("drawn_by"), d.get("checked_by"), d.get("approved_by"),
            d.get("date_drawn"), d.get("date_approved"),
            d.get("general_notes"), d["confidence"],
            d.get("file_path"), NOW
        ))
        drawing_id = cur.execute(
            "SELECT id FROM atex_drawings WHERE drawing_number=?", (d["drawing_number"],)
        ).fetchone()[0]

        # Delete existing zones for this drawing (re-import is idempotent)
        cur.execute("DELETE FROM atex_zones WHERE drawing_id=?", (drawing_id,))

        for z in d.get("zones", []):
            equipment_json = json.dumps(z.get("equipment_refs", []))
            cur.execute("""
                INSERT INTO atex_zones
                    (drawing_id, zone_type, location_description, extent,
                     equipment_refs, notes, dsear_report_ref, confidence)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                drawing_id, z["zone_type"], z["location_description"],
                z.get("extent"), equipment_json,
                z.get("notes"), z.get("dsear_report_ref"), "VERIFIED"
            ))
            zones_inserted += 1

        drawings_inserted += 1

        # Register in documents table
        cur.execute("""
            INSERT OR IGNORE INTO documents
                (filename, title, file_path, category, area,
                 drawing_ref, drawing_type, description, assignee,
                 status, imported_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            d["drawing_number"] + ".pdf",
            d["drawing_title"],
            d.get("file_path", f"Compliance/DSEAR/{d['drawing_number']}.pdf"),
            "compliance",
            d["location_area"][:200] if d.get("location_area") else None,
            d["drawing_number"],
            "DSEAR",
            d["drawing_title"],
            "Heath",
            "active",
            NOW, NOW
        ))

    conn.commit()
    conn.close()
    print(f"✓ {drawings_inserted} drawings imported")
    print(f"✓ {zones_inserted} zone records inserted")
    print(f"✓ Documents table updated")
    print("\nDone. Run export_to_json.py then update_embedded_data.mjs to publish.")


if __name__ == "__main__":
    run_import()
