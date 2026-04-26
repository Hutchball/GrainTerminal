# Existing Data Alignment

This note compares the September 2021 process schematic against the current starter database and web layout.

## Summary

The new process schematic broadly supports the starter data already in the system.
It does not invalidate the existing model, but it shows that the current model is incomplete and contains some duplicate naming.

## Strong Matches

- Receiving section:
  `RB1`, `RB2`, `RC1`, `RC2`, `RB3`, `RB4`
- Receiving dust units:
  `RB1 DCE`, `RB2 DCE`, `RC1 DCE1`, `RC1 DCE2`, `RB3 DCE`, `RB4 DCE`
- Receiving support assets:
  `COMPRESSOR 1`, `COMPRESSOR 2`, magnets
- Junction house elevators
- Silo 1 starter model:
  `BASEMENT BELT 1`, `BASEMENT BELT 2`, `BASEMENT BELT 3`
  `MAIN ELEVATOR 1` to `MAIN ELEVATOR 4`
  `RB5`, `RB6`, `RB7`
- Existing equipment records already include `RB8` and `RB9`

## New Structure Not Yet Modelled Properly

- `TH1` to `TH9`
- `UG1` to `UG5`
- `LG1` to `LG4`
- `ELV1` to `ELV4`
- `SUB 1`, `SUB 2`
- `DCC`
- `RC3`, `RC4`
- `LLCC1`, `LLCC3`
- `LWB ELEVATOR`, `LWCC1`, `LWCC2`
- `BB8` to `BB12`
- `RB10` to `RB12`
- `MC1` to `MC4`
- `FB1`, `FB2`, `FE1`
- loading bins `A` to `F`
- silo clusters 2 and 3 as full process structures
- Cargills and related external process interface

## Existing Naming Problems To Clean Up During Integration

- duplicate style records such as:
  `RB1` and `Receiving Belt RB1`
- mixed junction house naming:
  `JUNCTION HOUSE ELEVATOR 1`
  `Junction House Elevator JH El1`
- spelling inconsistency:
  `BASMENT BELT 2`
- drawing-label inconsistency:
  `LC1` vs operational `LLCC1`

## Recommended Integration Strategy

1. Keep the original drawing labels unchanged in the source layer.
2. Add canonical names for normalized database usage.
3. Rebuild the master topology from the process schematic.
4. Map old starter records onto the new topology.
5. Merge duplicates only after the mapping is reviewed.
