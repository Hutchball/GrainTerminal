# Merge Applied — 25 April 2026

## Summary

The topology/equipment merge plan has been applied to the SQLite database and web
portal exports.

## Applied Changes

- Merged confirmed duplicate starter records into canonical topology records.
- Preserved old starter names as `equipment_aliases`.
- Confirmed `Junction Tower Elevator J.L.1` as `JL1` / Junction House Elevator 1
  per Paul’s clarification.
- Renamed topology-backed records to canonical labels including:
  `JL1`, `JL2`, `BB1` to `BB7`, `BB1_V1` to `BB3_V1`, `ME1` to `ME4`,
  `RC3`, `RC4`, `RB8`, and `RB9`.
- Added missing process-schematic topology assets to the equipment table.
- Added BMH Ship Unloader into the receiving topology layer.
- Regenerated web app JSON exports and refreshed embedded `app.js` data.

## Resulting Counts

- Equipment records: 125
- Equipment aliases: 199
- Documents: 349
- Photos: 3
- Topology locations: 9

## Implementation Files

- `Grain Terminal/_System/Web App/apply_topology_merge.py`
- `Grain Terminal/_System/Web App/update_embedded_data.mjs`
- `Grain Terminal/_System/Web App/data/*.json`
- `Grain Terminal/_System/Web App/app.js`

## Notes

The merge preserved traceability rather than deleting source names outright. Older
labels are retained as aliases so users can still search by historical drawing or
starter-register wording.
