# AGENTS.md

This file provides guidance to Codex (Cowork/Codex) when working in this repository.

---

## Coding Rules

These rules apply to every task in this project unless explicitly overridden.
Bias: caution over speed on non-trivial work. Use judgment on trivial tasks.

## Rule 1 — Think Before Coding
State assumptions explicitly. If uncertain, ask rather than guess.
Present multiple interpretations when ambiguity exists.
Push back when a simpler approach exists.
Stop when confused. Name what's unclear.

## Rule 2 — Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked. No abstractions for single-use code.
Test: would a senior engineer say this is overcomplicated? If yes, simplify.

## Rule 3 — Surgical Changes
Touch only what you must. Clean up only your own mess.
Don't "improve" adjacent code, comments, or formatting.
Don't refactor what isn't broken. Match existing style.

## Rule 4 — Goal-Driven Execution
Define success criteria. Loop until verified.
Don't follow steps. Define success and iterate.
Strong success criteria let you loop independently.

## Rule 5 — Use the model only for judgment calls
Use me for: classification, drafting, summarization, extraction.
Do NOT use me for: routing, retries, deterministic transforms.
If code can answer, code answers.

## Rule 5a — Check utility scripts before doing anything manually
Before reading a large PDF, moving a file, or querying the DB by hand — check the registry first:
`Grain Terminal/_System/AI Team/UTILITY_SCRIPTS.md`

| If the task involves… | Use… |
|---|---|
| Reading text from a PDF | `python3 utils/extract_pdf_text.py <file>` → read the .txt |
| Moving a file from Incoming/ | `python3 utils/file_incoming.py <file> <dest> --db` |
| Querying the DB | `sqlite-utils query grain_terminal.db "<SQL>"` (Paul's Mac) or `sqlite3` in bash |

Running a script costs ~50 tokens. Reading a large PDF page-by-page costs thousands. Always script first.

## Rule 6 — Token budgets are not advisory
Per-task: 4,000 tokens. Per-session: 30,000 tokens.
If approaching budget, summarize and start fresh.
Surface the breach. Do not silently overrun.

## Rule 7 — Surface conflicts, don't average them
If two patterns contradict, pick one (more recent / more tested).
Explain why. Flag the other for cleanup.
Don't blend conflicting patterns.

## Rule 8 — Read before you write
Before adding code, read exports, immediate callers, shared utilities.
"Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

## Rule 9 — Tests verify intent, not just behavior
Tests must encode WHY behavior matters, not just WHAT it does.
A test that can't fail when business logic changes is wrong.

## Rule 10 — Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back.
If you lose track, stop and restate.

## Rule 11 — Match the codebase's conventions, even if you disagree
Conformance > taste inside the codebase.
If you genuinely think a convention is harmful, surface it. Don't fork silently.

## Rule 12 — Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.

---

## What this project is

**LEEN — Local Expandable Engineering Network.**

A practical, sellable engineering reference tool. The first deployment is for **engineers and managers working at the Seaforth (Royal Seaforth Dock) Grain Terminal**, operated by Peel Ports in Liverpool. Once proven there, LEEN will be packaged and sold to other industrial companies as a blank product pre-loaded with their own data.

The primary users at any site are on-site personnel: a maintenance engineer needing to know which parts to order before a job, a manager checking what motor is fitted to a conveyor, or a safety officer looking up ATEX zone classifications for an area. The app must be fast, reliable, and correct — wrong information here has real consequences on a live industrial site.

**Core use cases the app must serve well:**
- Look up any piece of equipment by tag (e.g. RB1, ELV3, DP4) and see its full spec — motor, gearbox, rollers, lubrication, belt/bag details
- Find what parts or consumables are needed for a job or motor replacement
- Check site history — drawings, manuals, inspection records, photos
- Access relevant safety data — ATEX zones, DSEAR compliance notes, explosion protection equipment (Fike panels, rotary valves)
- Verify information confidence level — the app clearly flags VERIFIED vs UNCERTAIN data

The system ingests raw documents, drawings, and data files, organises them into a structured SQLite database, and exposes them via a static HTML/JS web portal that works without a server.

The working directory is `/Users/paulhutch/Desktop/PKA Paul/Projects/LEEN/`.

## Design principles

- **Correct over clever** — a wrong answer is worse than no answer; confidence levels must be visible
- **Fast to answer a specific question** — engineers are often standing at a machine; search and lookup must be immediate
- **No server dependency** — the portal is a static file opened locally; keep it that way unless explicitly changing the architecture
- **Lightest efficient outcome** — don't add complexity that doesn't serve the engineers using it

---

## Folder layout

```
LEEN/                           # Root — Local Expandable Engineering Network
├── Grain Terminal/             # First live deployment (Seaforth Grain Terminal)
│   ├── _System/
│   │   ├── AI Team/            # Role definitions for every team member (markdown) — SHIPPED WITH PRODUCT
│   │   ├── Terminal Structure/ # Canonical asset map, alias map, merge plans
│   │   └── Web App/            # All code: DB, Python importers, HTML portal, JS bot
│   └── <area folders>          # e.g. Switchrooms/, Equipment/, Silo 1/, Process Schematics/
└── (future client folders)     # Each new client gets their own folder at this level
```

**Commercial note:** The AI Team agents ship with the product. Site users only access the web portal front-end (`index.html`). The agents, database, and Python scripts are the back-office layer used by Paul and the AI team to maintain data.

All code lives in `Grain Terminal/_System/Web App/`.

---

## Database

**Engine:** SQLite (`grain_terminal.db`) with WAL mode and foreign keys on.
**Planned upgrade path:** PostgreSQL via `db_config.py` (set `DB_TYPE=postgres DATABASE_URL=…`).

All Python scripts import `get_connection()` from `db_config.py` — never call `sqlite3.connect()` directly.

**Core tables:**

| Table | Purpose |
|---|---|
| `equipment` | One row per asset (RB1, ELV2, DP3, …) |
| `equipment_attributes` | Flexible key-value specs (motor kW, gearbox ratio, roller dia, …) |
| `equipment_aliases` | Legacy/drawing names that map to the canonical name |
| `equipment_relationships` | Parent/child links (drives, feeds_into, controlled_by) |
| `equipment_locations` | Physical location (building, floor, grid ref) |
| `documents` | Drawings, manuals, reports — linked to equipment |
| `photos` | Site photos with approval status |
| `verification_feedback` | User-reported corrections from the portal |
| `lubricants` / `equipment_lubricants` | Lubricant register and assignments |
| `equipment_pulleys` / `equipment_gearboxes` | Mechanical sub-registers |

**Confidence levels (mandatory on all attributes):** `VERIFIED` · `LIKELY` · `UNCERTAIN` · `UNKNOWN`

---

## Common commands

All run from inside `Grain Terminal/_System/Web App/`.

```bash
# Initialise a fresh database (destructive — only use on a blank DB)
python3 init_db.py

# Apply additive schema migrations to an existing DB (idempotent)
python3 migrate_schema.py

# Export the DB to JSON files in data/
python3 export_to_json.py

# Embed the JSON data into app.js (run after export_to_json.py)
python3 update_embedded_data.py

# Import specific data sets
python3 import_electrical_motors.py
python3 import_pulleys.py
python3 import_compressors.py
python3 import_fike.py
python3 import_lubricants.py
python3 import_lubricant_assignments.py
python3 import_dust_bags.py
python3 import_asset_list.py

# Apply topology merge (alias/canonical name consolidation)
python3 apply_topology_merge.py

# Tidy equipment canonical names
python3 tidy_equipment_names.py

# Sync equipment aliases
python3 sync_equipment_aliases.py

# Build gearbox register
python3 build_gearbox_register.py
```

**Full refresh after any DB change:**
```bash
python3 export_to_json.py && python3 update_embedded_data.py
```

The web portal is a single static file (`index.html`) with all data embedded in `app.js`. Open `index.html` directly in a browser — no server required.

---

## Web portal architecture

- `index.html` — shell and layout only
- `app.js` — all JS logic plus embedded data constants (`DATA_EQUIPMENT`, `DATA_ATTRS`, etc.)
- `grainbot.js` — floating chatbot widget; read-only; answers from embedded data only; logs change requests in-memory for Paul's approval
- `style.css` — all styles
- `data/` — JSON exports from the DB (regenerated by `export_to_json.py`); embedded into `app.js` by `update_embedded_data.mjs`

The marker `// Port of Liverpool Grain Terminal` in `app.js` is where `update_embedded_data.mjs` splices in the data block. Do not remove it.

---

## Equipment naming conventions

Every asset has three name layers (defined in `Terminal Structure/MASTER_STRUCTURE_FROM_PROCESS_SCHEMATIC.md`):

- `drawing_label` — exact label on the drawing (e.g. `LC1`)
- `canonical_name` — normalised DB name (e.g. `LLCC1`)
- `long_name` — human-readable (e.g. `Lorry Weighback Chain Conveyor 1`)

Canonical abbreviations: `RB` = Receiving Belt, `RC` = Receiving Conveyor, `BB` = Basement Belt, `ELV` = Elevator, `TH` = Turnhead, `UG` = Upper Garner, `LG` = Lower Garner, `DP` = Dust Plant, `RV` = Rotary Valve, `FB` = Feed Belt, `MC` = Mill Conveyor, `FE` = Feed Elevator, `LLCC` = Lorry Loading Chain Conveyor.

---

## Incoming data workflow

1. Paul drops files into `Incoming/` and describes them in chat.
2. **Ask before processing** anything that is not unambiguously classifiable (e.g. an electrical drawing with a clear MCC reference is obvious; an unlabelled spreadsheet is not — ask first).
3. Read the file, route to the correct specialist persona (see AI team below), extract structured facts.
4. Import into the DB, run `export_to_json.py` + `update_embedded_data.mjs`.
5. Move the source file to `Incoming/Processed/` and append an audit entry to the current day's processing log (`Incoming/Processed/YYYY-MM-DD-processing-log.md`).
6. File any organised output (markdown summaries, etc.) into the correct subfolder under `Grain Terminal/`.

---

## AI team personas

When a task requires specialist knowledge, adopt the appropriate persona by reading their role file from `Grain Terminal/_System/AI Team/`. Gary is the default orchestrator and front door.

| Name | Role file | Invoke when… |
|---|---|---|
| Gary | `Gary_Orchestrator.md` | Default — planning, coordination, reporting |
| **Finn** | `Finn_TokenStrategist.md` | **First stop for any large or multi-step task** — plans, scopes, cuts waste before work begins |
| Adam | `Adam_Admin.md` | Filing, document control, intake triage |
| Riley | `Riley_SeniorResearcher.md` | Web research, manufacturer lookups |
| Dave | `Dave_Developer.md` | Web app changes, scripts, data exports |
| Ellie | `Ellie_ElectricalEngineer.md` | Electrical schematics, motor control, PLCs |
| Max | `Max_MechanicalEngineer.md` | Drive trains, gearboxes, conveyor mechanics |
| Heath | `Heath_HealthAndSafety.md` | ATEX zones, DSEAR, HSE compliance |
| Jenny | `Jenny_HR.md` | Adding new team members |

Invoke a specialist by name in chat: *"Ellie, explain drawing DTX-361-AA"*.

**Finn is Gary's internal efficiency layer.** For any large task, Gary routes through Finn first — producing a brief plan with scope, steps, and cuts — before delegating to a specialist. Paul can also invoke Finn directly: *"Finn, plan this before we start."*

---

## Safety-critical rules (non-negotiable)

This is a live working plant. These rules apply to every response, regardless of persona.

- **Never guess** at electrical ratings, safety device settings, ATEX zone classifications, torque settings, pressures, or tolerances.
- **Never fabricate** specifications, part numbers, or procedures.
- **Always cite sources** — document name, date, how to verify.
- **Always state confidence level** on every technical claim: `VERIFIED` / `LIKELY` / `UNCERTAIN` / `UNKNOWN`.
- When in doubt, stop and ask; recommend qualified on-site personnel for safety-critical decisions.
- AI research is reference material only — all safety decisions must be verified by qualified engineers.
