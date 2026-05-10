# LEEN Database & Web App Audit Report
**Date:** May 2026  
**Prepared by:** Kai (DB & Scripting Agent)  
**Database:** `Grain Terminal/_System/Web App/grain_terminal.db`

---

## Summary

Full audit of the SQLite database, source tracking implementation, duplicate/orphan cleanup, web app UI updates, and self-contained HTML rebuild. No records were deleted unless they were confirmed identical duplicates. Issues requiring a decision from Paul are flagged in the **Needs Attention** section.

---

## 1. Row Counts (post-audit)

| Table | Rows |
|---|---|
| asset_list_items | 156 |
| atex_drawings | 26 |
| atex_ip_standard | 3 |
| atex_zones | 92 |
| confined_spaces | 21 |
| documents | 449 |
| dust_bag_change_history | 75 |
| dust_bag_stock | 9 |
| electrical_motors | 304 |
| equipment | 211 |
| equipment_aliases | 622 |
| equipment_attributes | **1,306** (was 1,427 before dedup) |
| equipment_dust_bags | 25 |
| equipment_gearboxes | 73 |
| equipment_locations | 0 |
| equipment_lubricants | 277 |
| equipment_pulleys | 167 |
| equipment_relationships | 64 |
| fire_alarm_panel | 1 |
| fire_alarm_zones | 54 |
| lubricants | 13 |
| photos | 3 |
| processing_runs | 1 |
| verification_feedback | 0 |

---

## 2. Schema Observations

- **Missing FK constraint:** `fire_alarm_zones` has no `panel_id` column linking it to `fire_alarm_panel`. All 54 zones belong to the single panel in the DB, so no data integrity risk currently, but the formal relationship is implicit only. Recommend adding a `panel_id FK` in a future migration.
- **`equipment_locations`:** 0 rows. The table exists and has a FK to `equipment`, but has never been populated. Physical location data is stored in `equipment.location_description` instead. Either populate this table or treat it as vestigial.
- **`source_document` columns added** (new this audit) to: `equipment`, `documents`, `equipment_attributes`, `atex_zones`.
- **`confined_spaces`** already had `source_document` — no change needed.
- **`fire_alarm_zones` and `fire_alarm_panel`** already had a `source` column containing the full citation — no additional column needed.

---

## 3. Duplicates Found and Resolved

### 3a. Equipment
- **No duplicate equipment names found.** All 211 equipment records have unique names.

### 3b. Documents — duplicate filenames
- One duplicate filename found: `284595_4101_02.pdf` (two rows, IDs 435 and 448).
  - These are not true duplicates — they represent the same physical drawing stored in two different switchroom subfolders (MCC10 New Switchroom vs New Switchroom 2). The `file_path` and `description` differ. **Not deleted — flagged for Paul.**

### 3c. Documents — duplicate titles
- 20+ drawing titles appear on multiple rows (e.g. "SCHEMATIC DIAGRAM FOR SUPERVISORY CONTROL PANEL" appears 37 times).
  - Inspection confirmed these are different revisions or sheets of the same drawing — they have different `drawing_ref`, `file_path`, and `mcc` values. **Not deleted — expected behaviour for a multi-sheet drawing set.**

### 3d. Equipment Attributes — identical duplicates removed
- **121 identical duplicate attribute rows deleted** (same `equipment_id`, `attribute_key`, `attribute_value`, and `source` — exact copies with no information difference). These were created by reimport runs without deduplication.
- Equipment affected: Silo 3 Storage Bins (motor attrs), Mill Feed (motor_voltage), DCC (motor attrs), Main Elevator Pony Motors (motor attrs), Turnheads (motor attrs).
- The `equipment_attributes` table went from **1,427** to **1,306** rows.

---

## 4. Orphaned Records Found

### 4a. Orphaned equipment_attributes
- **None found.** All 1,306 attribute rows point to valid equipment IDs.

### 4b. Orphaned electrical_motors
- **3 motors point to non-existent equipment IDs** (IDs 146, 147, 148 — AUGER No 8, AUGER No 9, AUGER No 9A). These equipment records appear to have been deleted from the `equipment` table at some point. The motors themselves still hold useful data (serial numbers, ratings). **Not deleted — flagged for Paul.**
- **15 motors have NULL `equipment_id`** (unlinked). These include stored spare motors (LG/M/00018 through LG/M/00081), BCC2, COMP East/West, COMP 1/2 old, and ELEVATOR PONY. These are likely intentional — spare/surplus motors not assigned to a plant item. **No action taken.**

### 4c. Orphaned equipment_gearboxes
- **4 gearboxes point to non-existent equipment IDs** (IDs 67, 68, 69, 70 — labelled "Gearbox oil to confirm"). These are the ME1–ME4 gearboxes, where the equipment IDs were deleted during a topology merge. **Flagged for Paul.**

### 4d. Orphaned equipment_lubricants
- **28 lubricant assignment rows point to non-existent equipment IDs**, including Dust Plant 13 elevator/chain conveyor (IDs 17, 18), ME1–ME4 (IDs 67–70), and several Receiving Chain Conveyor valves (IDs 37–41). These equipment records were removed from the `equipment` table during a merge pass but their lubricant assignments were not cleaned up. **Flagged for Paul — do not delete without confirming the lubricant data is captured elsewhere.**

### 4e. equipment_dust_bags with NULL equipment_id
- 6 dust bag records have no `equipment_id`. **Not deleted — flagged for Paul.**

### 4f. fire_alarm_zones
- All 54 zones have the expected source citation. No FK to `fire_alarm_panel` but this is a schema design gap, not a data error.

---

## 5. Null / Blank Critical Fields

All core critical fields were clean:
- Equipment with no `area`: 0
- Equipment with no `equipment_type`: 0
- Documents with no `title`: 0
- Documents with no `file_path`: 0
- Attributes with no `confidence_level`: 0
- Attributes with no `source`: 0

### Equipment without any attributes: 126 of 211
This is expected — many equipment records are topology placeholders (e.g. bins, garners, process junctions) that do not yet have motor/gearbox specs. Not an error; gap to fill over time.

### Equipment not linked to any document: 207 of 211
The `documents.equipment_ids` linkage is sparsely populated. Most equipment is identifiable via drawing references rather than direct document links. Not an error but indicates the document-linking step has not been run for most records.

---

## 6. Source Document Backfill Coverage

| Table | Filled | Total | % |
|---|---|---|---|
| `documents.source_document` | 449 | 449 | 100% |
| `atex_zones.source_document` | 92 | 92 | 100% |
| `confined_spaces.source_document` | 21 | 21 | 100% (pre-existing) |
| `equipment_attributes.source_document` | 1,236 | 1,306 | 94% |
| `equipment.source_document` | 34 | 211 | 16% |

**Documents** — all 449 rows backfilled. Distribution:
- Switchroom Drawing Scan: 325
- RSGT Compliance Documents: 44
- Scales Documentation (MDHC/WD03021): 30
- HF Controls 284595 Drawing Set: 16
- Drawing Archive (Obsolete): 12
- Equipment Manuals: 9
- Site Photography: 5
- Service Drawings (PoL): 3
- Research Notes: 3
- Fike Fire Suppression Drawings: 1
- System Configuration: 1

**Equipment** — only 34 of 211 rows could be backfilled with high confidence:
- BMH area (20 records) → "BMH Manual (2006)"
- Switchrooms area (4 records) → "Switchroom Schematics"
- Weighback/Lorry Intake + scale-related (10 records) → "Scales Documentation (MDHC)"
- **177 equipment records left NULL** — these came from the process schematic / topology import which did not carry a specific source document reference. Paul should add a `source_document` value to these records as part of ongoing data entry. The MASTER_STRUCTURE_FROM_PROCESS_SCHEMATIC.md file is the likely source for most of them.

**Equipment attributes** — 70 rows (6%) remain NULL:
- These are attributes from sources that didn't match any known import batch pattern (e.g. ad-hoc or verbal entries without a clear file path). **Not a critical issue.**

---

## 7. Web App Changes

### New UI element: `Source:` label
Added a subtle italic `Source:` line in three views:
1. **Equipment detail panel** — shows `equipment.source_document` below the equipment name/meta line. Only rendered when non-NULL.
2. **Schematics / Drawings list** — shows `documents.source_document` below each drawing description. Only rendered when non-NULL.
3. **ATEX zones** — shows `atex_drawings.source_report` below the drawing title in each ATEX card. Only rendered when non-NULL.

CSS class `.record-source` added to `style.css`: small, muted, italic — non-intrusive.

Attribute source display updated: now shows the human-readable `source_document` label (e.g. "RSGT Asset List V2") instead of the raw file path (e.g. "Incoming/RSGT Asset ListV2/RSGT Motors-Table 1.csv"). The raw path is still accessible via tooltip hover.

### update_embedded_data.py patched
The Python embedder was missing `DATA_ATEX` (present in the `.mjs` version). Added `const DATA_ATEX = {load('atex_zones.json')};` to keep both embedders in sync.

---

## 8. Rebuild

Self-contained portal rebuilt and saved to:
`/Users/paulhutch/Desktop/PKA Paul/Projects/grain_terminal.html`  
File size: ~1.33 MB. All CSS, JS, and embedded data inlined.

---

## 9. Needs Attention — Items Requiring Paul's Decision

These issues were identified but not automatically resolved. Each requires a judgement call.

### ⚠️ HIGH PRIORITY

**A. Missing equipment IDs 17, 18, 37–41, 67–70**  
These IDs appear as foreign keys in `electrical_motors`, `equipment_gearboxes`, and `equipment_lubricants`, but the corresponding rows in `equipment` no longer exist. They were likely deleted during a topology merge. Options:
- If the equipment was intentionally merged/renamed: update the orphaned records to point to the new equipment IDs.
- If the equipment is genuinely gone: delete the orphaned motor/gearbox/lubricant rows.
Affected records: 3 motors (AUGER 8/9/9A), 4 gearboxes (ME1–ME4 "oil to confirm"), 28 lubricant assignments.

**B. Conflicting motor attributes on 12 equipment records**  
72 attribute rows were found with conflicting values for the same `(equipment_id, attribute_key)` pair. These were **not deleted** — the conflicts indicate multiple different physical motors have been imported under a single equipment record. Affected equipment:

| Equipment | Issue |
|---|---|
| Silo 3 Storage Bins 1 to 9 (ID 137) | 27× each of motor_current/make/power/serial/speed/type — 9 bins × 3 motor generations |
| DCC (UNUSED) (ID 90) | 4× each of motor attrs — 1 main motor + 3 small motors |
| JL1, JL2 (IDs 51, 52) | 2× each — main drive vs. pony motor |
| TH1–TH4 (IDs 84–87) | 2× each — two different motor records per turnhead |
| FE1 (ID 103) | 2× each — two different motor records |
| RB11, RB12 (IDs 116, 117) | 2× each — main drive vs. smaller motor |
| LORRY INTAKE (ID 119) | 2× power/current/serial/type |
| Mill Feed (ID 135) | 4× most attrs, 2× serial |
| Main Elevator Pony Motors (ID 143) | 4× serial numbers — 4 separate pony motors |
| Surge Bin 2 (ID 145) | 3× serial |

**Recommended fix:** Create individual equipment records for each motor, or add a `motor_instance` discriminator to the attribute key (e.g. `motor_1_power`, `motor_2_power`). The current state will cause all conflicting values to display simultaneously in the web app.

### ℹ️ LOWER PRIORITY

**C. Duplicate filename: `284595_4101_02.pdf`**  
Two document records (IDs 435, 448) share this filename but have different paths and descriptions. This is probably a filing discrepancy rather than a data error. Suggest checking whether both files are needed or if one is a copy to be removed.

**D. `equipment_locations` table is empty**  
0 rows. Either populate it from `equipment.location_description`, or drop the table to reduce schema noise.

**E. 177 equipment records with NULL `source_document`**  
Most equipment in the topology came from the process schematic. These records should have `source_document = 'Grain Store Process Schematic Rev 1 Sept 21'` set manually or via a targeted update. Consider running:
```sql
UPDATE equipment 
SET source_document = 'Grain Store Process Schematic Rev 1 Sept 21'
WHERE source_document IS NULL;
```
after confirming this is correct for the remaining records.

**F. fire_alarm_zones has no panel_id FK**  
Minor schema gap. All zones belong to the single panel, so no functional impact now. Recommend adding `panel_id INTEGER REFERENCES fire_alarm_panel(id)` in a future migration when/if multiple panels are added.

---

*End of audit report.*
