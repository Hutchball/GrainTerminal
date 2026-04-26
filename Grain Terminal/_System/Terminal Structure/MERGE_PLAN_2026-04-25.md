# Merge Plan — 25 April 2026

## Purpose

Bring the new process-schematic topology into alignment with the existing equipment
database without losing traceability or creating duplicate assets.

## Current State

- New topology layer in `Web App/data/site_layout.json`
- 9 locations
- 97 first-pass assets
- Existing equipment table/export still contains 73 legacy starter records

## Groups

### Group A — Directly aligned starter records

These already line up well with the new topology and should be mapped, not duplicated:

- `RB1`
- `RB2`
- `RC1`
- `RC2`
- `RB3`
- `RB4`
- `JUNCTION HOUSE ELEVATOR 1`
- `JUNCTION HOUSE ELEVATOR 2`
- `RB1 DCE`
- `RB2 DCE`
- `RC1 DCE1`
- `RC1 DCE2`
- `RB3 DCE`
- `RB4 DCE`
- `COMPRESSOR 1`
- `COMPRESSOR 2`
- `RB5`
- `RB6`
- `RB7`
- `BASEMENT BELT 1`
- `BASEMENT BELT 2`
- `BASEMENT BELT 3`
- `BASEMENT BELT 1, VALVE 1`
- `BASMENT BELT 2, VALVE 1`
- `BASEMENT BELT 3, VALVE 1`
- `MAIN ELEVATOR 1`
- `MAIN ELEVATOR 2`
- `MAIN ELEVATOR 3`
- `MAIN ELEVATOR 4`
- `RB1 MAGNET`
- `RB2 MAGNET`

### Group B — Legacy duplicate naming variants

These look like older or alternate names for already-modelled assets and should be merged
into canonical records after review:

- `Receiving Belt RB1`
- `Receiving Belt RB2`
- `Receiving Chain RC1`
- `Receiving Chain RC2`
- `Junction House Elevator JH El1`
- `Junction House Elevator JH El2`

### Group C — Legitimate equipment still missing from topology layer

These are real assets from drawings or starter records that are not yet represented
explicitly in the process-topology layer:

- `BMH Ship Unloader`
- `Dust Plant 12 - Chain Conveyor`
- `Dust Plant 12 - Elevator`
- `Dust Plant 12 - Fan`
- `Dust Plant 13 - Chain Conveyor`
- `Dust Plant 13 - Elevator`
- `Dust Plant 13 - Fan`
- `Basement Belt Conveyor No 4`
- `Basement Belt Conveyor No 5`
- `Basement Belt Conveyor No 7`
- `Basement Chain Conveyor No 1`
- `Basement Chain Conveyor No 2`
- `Basement Chain Conveyor No 3`
- `Basement Belt Valve 1`
- `Basement Chain Conv 1 Valve 1`
- `Basement Chain Conv 1 Valve 2`
- `Basement Chain Conv 2 Valve 1`
- `Receiving Chain Conveyor 3`
- `Receiving Chain Conveyor 4`
- `Rotary Bin Discharger No 1`
- `Rotary Bin Discharger No 2`
- `Rotary Valve R.V.1`
- `Silo 2 Control Panel`
- `Tripper RB8`
- `Tripper RB9`
- `Receiving Chain Conveyor 3 Valve 1`
- `Receiving Chain Conveyor 4 Valve 1`
- `Receiving Chain Conveyor 4 Valve 2`
- `Receiving Chain Conveyor 4 Valve 3`
- `Receiving Chain Conveyor 4 Valve 4`
- `Tripper Interlock Panel`
- `Tripper No 6`
- `Tripper No 8`
- `Tripper No 9`

### Group D — Naming ambiguity requiring review

- `Junction Tower Elevator J.L.1`
  This may be a true separate asset, or may overlap with the junction house naming family.
  Do not merge automatically.

## Recommended Next Actions

1. Keep Group A as direct mappings into canonical topology-backed records.
2. Fold Group B into canonical records while preserving the legacy names as aliases.
3. Add Group C as second-wave topology assets linked back to drawings.
4. Hold Group D for user review before merge.
