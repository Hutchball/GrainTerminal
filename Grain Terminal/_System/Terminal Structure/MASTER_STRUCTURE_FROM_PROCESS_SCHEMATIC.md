# Master Terminal Structure

Source drawing:
`Grain Store Process Schematic Rev 1 Sept 21.pdf`

Source path:
`Grain Terminal/Process Schematics/Grain Store Process Schematic Rev 1 Sept 21.pdf`

Status:
First-pass structure extracted from the September 2021 process schematic and cross-checked against existing starter database data.

## Modelling Rule

For every tagged asset:

- `drawing_label` = exact label shown on the drawing
- `canonical_name` = normalized operational name used in the database
- `long_name` = human-readable full name

## Confirmed Abbreviations

| Drawing label | Meaning |
|---|---|
| `RB` | Receiving Belt |
| `RC` | Receiving Conveyor |
| `BB` | Basement Belt |
| `ELV` | Elevator |
| `TH` | Turnhead |
| `UG` | Upper Garner |
| `LG` | Lower Garner |
| `MB` | Mill Bin |
| `GTU` | Gravity Tension Unit |
| `CP` | Compressor |
| `AF` | Aeration Fan |
| `DP` | Dust Plant |
| `RV` | Rotary Valve |
| `MC` | Mill Conveyor |
| `FB` | Feed Belt |
| `SUB` | Substation |
| `LWB` | Lorry Weighback |
| `LWCC` | Lorry Weighback Chain Conveyor |
| `JL` | Junction House Elevator |
| `DCC` | Distribution Chain Conveyor |
| `DC` | Dust Chain Conveyor |
| `SMC` | Soya Mill Conveyor |
| `FE` | Feed Elevator |
| `EP` | Explosion Panel |
| `HS` | Heat Sensor |
| `GB` | Fire Gas Bottles |
| `MRV` | Manual Relief Valve |
| `UG` | Upper Garner |
| `LG` | Lower Garner |

## Area Structure

### 1. Marine And Receiving

- Ship unloader
- Receiving Belt `RB1`
- Receiving Belt `RB2`
- Receiving Conveyor `RC1`
- Receiving Conveyor `RC2`
- Receiving Belt `RB3`
- Receiving Belt `RB4`
- Junction House Elevator `JL1`
- Junction House Elevator `JL2`
- Dust Compaction Units:
  `RB1 DCE`, `RB2 DCE`, `RC1 DCE1`, `RC1 DCE2`, `RB3 DCE`, `RB4 DCE`
- Compressors:
  `CP` symbols plus `COMPRESSORS` room shown separately
- Magnet stations on receiving belts

### 2. Lorry Intake And Weighback

- Lorry intake hopper
- `LWB ELEVATOR`
- `LWCC1`
- `LWCC2`

### 3. Main Elevator / Garner Section

- `SUB 1`
- `SUB 2`
- `UG1`, `UG2`, `UG3`, `UG4`
- `LG1`, `LG2`, `LG3`, `LG4`
- `ELV1`, `ELV2`, `ELV3`, `ELV4`
- `TH1`, `TH2`, `TH3`, `TH4`
- `MB1`, `MB2`
- `DCC (UNUSED)`
- `RC3`
- `RC4`
- `LC1` on drawing
  canonical meaning: `LLCC1`

### 4. Silo Cluster 1

- `RB5`
- `RB6`
- `RB7`
- associated `GTU` units
- Silo Cluster 1 shown as live
- `BB1`
- `BB2`
- `BB3`

### 5. Intermediate Transfer / Turnhead Section

- `TH8`
- `TH9`
- `RB8`
- `RB9`
- last position of tripper shown on drawing
- Bin links:
  `BIN 400A`, `BIN 500`, `BIN 600`

### 6. Silo Cluster 2

- Silo Cluster 2 shown as live
- `BB4`
- `BB5`
- `BB6`
- `BB7`
- `GTU` units
- `SMC`
- `C1`
- Cargills interface connection

### 7. Silo Cluster 3 / Feed / Mill Area

- `TH5`
- `TH6`
- `TH7`
- `UG5`
- `FE1`
- `FB1`
- `FB2`
- `MC1`
- `MC2`
- `MC3`
- `MC4`
- `BB8`
- `BB9`
- `BB10`
- `BB11`
- `BB12`
- bins `1` to `9`
- `HS`, `AF`, `MRV` and related protection / aeration components

### 8. Dust Plant / Silo Basement / Discharge

- `DP1` to `DP6`
- `DP12`
- `DP13`
- `RV1` to `RV13` where shown
- `DC12/13`
- `LGS1`
- `LGS2`
- Vibrating bin discharger
- note on drawing:
  dust filter plant from switchroom 2
- process note:
  from silo 3 basement conveyors

### 9. Lorry Loading

- `LLCC3` above bins `A` to `F`
- loading bins:
  `BIN A`, `BIN B`, `BIN C`, `BIN D`, `BIN E`, `BIN F`
- each with scale and loading chute
- loading bays:
  `A` to `F`

### 10. External / Ancillary Interfaces

- `CARGILLS`
- compressor room / workhouse floor 7
- receiver
- oil separator
- dump hopper
- Peel / DACSA / ADM labels shown on lower-right process area

## Drawing Label Preservation Notes

- `LC1` appears on the drawing but is treated operationally as `LLCC1`
- `LCC3` appears on the drawing but is treated operationally as `LLCC3`
- the database should preserve the original label and add the canonical name separately

## Relationship Notes

- `LLCC1` feeds `LLCC3`
- `LLCC3` runs above lorry loading bins `A` to `F`
- receiving belts and conveyors feed upward through the junction house elevators into the main process route
- turnheads distribute material between silo clusters, basement belts, mill paths, and loadout routes
- `RB8` and `RB9` remain live and are part of the active topology
- `CARGILLS` remains a live external connection and should be retained in the model even if not part of direct operational responsibility
