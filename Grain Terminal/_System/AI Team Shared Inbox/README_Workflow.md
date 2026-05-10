# PKA Grain Terminal - AI Team Workflow

## How the Team Works

### Important: How agents actually operate

All team members run within the same AI session — Gary is the active agent in every
conversation. When Gary delegates to Ellie or Max, Gary reads that agent's MD file and
adopts their role, expertise, and constraints for that task. This is not automatic —
Paul must ask Gary to involve a specific agent, or Gary must decide to delegate based
on the task type.

For Codex compatibility, these same markdown files are also treated as the source of
truth for any real delegated sub-agent work. That means the workflow stays the same even
if the execution model changes underneath.

To get the best out of the team, address requests to the right person directly:
- *"Ellie — what does drawing DTX-361-AA tell us about MCC1A?"*
- *"Max — what gearbox data do we have for the receiving belt conveyors?"*
- *"Heath — what ATEX zone classification applies to the silo areas?"*
- *"Riley — look up the Siwertell ship unloader maintenance manual online"*
- *"Gary — orchestrate a review of everything in the Incoming folder"*

Gary will always respond, but will adopt the named agent's persona and apply their
specific constraints, knowledge, and output format.

---

### 1. Adding Raw Data

Drop files into the **Incoming** folder (root level of the LEEN project folder):
- PDFs (electrical drawings, manuals, datasheets, reports)
- Photos (equipment, nameplates, issues)
- Maintenance logs (spreadsheets, documents)
- Any other documentation

Then tell Gary (in the chat) what you dropped in and what you want done with it.

---

### 2. How Files Get Routed

Gary reads the Incoming folder and assigns each file to the correct specialist:

| File Type | Assigned To | Destination |
|-----------|-------------|-------------|
| Electrical drawings (DTX, STX, GTX, CTX, etc.) | **Ellie** | `Grain Terminal/Switchrooms/MCCX/` |
| Obsolete electrical drawings | **Ellie** | `Grain Terminal/Obsolete/` |
| Photos (JPG, PNG, HEIC) | **Riley** | `Grain Terminal/Photos/` |
| H&S / safety / ATEX / compliance docs | **Heath** | `Grain Terminal/Compliance/` |
| Maintenance logs / service records | **Adam** | `Grain Terminal/Maintenance Logs/` |
| Manuals / datasheets / handbooks | **Riley** | `Grain Terminal/Manuals/` |
| Equipment specs / nameplates | **Max or Ellie** | `Grain Terminal/Equipment/` |
| Unrecognised items | **Gary** | Asks Paul before routing |

After routing:

- extracted facts must carry a source reference back to the original file
- database updates should be reviewable before they are treated as verified
- portal users should be able to open the original file from each result
- portal users should be able to confirm correctness or raise an issue for review

---

### 3. Folder Structure

```
LEEN/
├── Incoming/                  ← drop new files here, then tell Gary
└── Grain Terminal/
    ├── _System/               ← team files, web app, database (internal)
    │   ├── AI Team/           ← agent definition files
    │   ├── AI Team Shared Inbox/
    │   └── Web App/
    ├── Basement-Receiving/
    ├── Compliance/            ← H&S / ATEX docs (Heath)
    ├── Dust Plants/
    ├── Equipment/             ← equipment docs and specs
    ├── Equipment Register/
    ├── Maintenance Logs/      ← service records (Adam)
    ├── Manuals/               ← equipment manuals (Riley)
    ├── Mill Feed/
    ├── Obsolete/              ← superseded drawings
    ├── Photos/                ← site photos
    ├── Ship Unloader BMH/
    ├── Silo 1 / Silo 2 / Silo 3/
    └── Switchrooms/
        ├── MCC1/ … MCC13/    ← Ellie's electrical drawings
        ├── Scale Room/
        └── SCP/
```

---

### 4. Hiring New Team Members
- Tell **Jenny** (HR) what specialist you need
- Jenny will create a new team member profile in `AI Team/`
- **Gary** will update `Gary_Orchestrator.md` and `TEAM_ROSTER.md`
- **All existing team member MD files** must also be updated to include the new person in their Team table

---
*Last updated: 20 April 2026*
