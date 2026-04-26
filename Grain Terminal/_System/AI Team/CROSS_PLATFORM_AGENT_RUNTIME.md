# Cross-Platform Agent Runtime

This project must stay usable in both Claude-style and Codex-style environments.

## Source Of Truth

The role files in `AI Team/` remain the source of truth for:

- role boundaries
- specialist hand-off rules
- safety constraints
- output expectations

Do not replace those files with tool-specific prompts. Extend them only when the
same rule should apply in both Claude and Codex.

## How Claude Uses The Team

Claude uses the existing pattern already documented elsewhere in this folder:

- Gary is the active front door
- Gary reads the relevant specialist markdown file
- Gary responds in that specialist's role
- the team is prompt-driven, not a real background worker system

## How Codex Uses The Team

Codex can use the same markdown role files in two ways:

1. Single-agent mode:
   Gary remains the front door and Codex adopts the requested specialist role by
   reading that specialist markdown file.

2. Delegated mode:
   Codex can spawn real sub-agents for bounded tasks, but the task brief must be
   derived from the same markdown role files so behaviour stays aligned with Claude.

## Practical Rule

When adding a new specialist:

1. Create the specialist markdown file in `AI Team/`
2. Update `TEAM_ROSTER.md`
3. Update Gary's hand-off table
4. Update any shared workflow docs
5. Avoid adding Codex-only logic that changes the actual business process

## Intake And Processing Model

Target operating model for this project:

1. User drops files into `Incoming/`
2. Gary triages the intake
3. Specialist agents extract structured facts with source references
4. Proposed changes are reviewed against the original file
5. Approved changes are written into the database
6. The web portal exposes every answer with a source link
7. End users can confirm correctness or report an issue
8. Reported issues are reviewed and corrected through the agent workflow

## Current Status

The repository is still at the bare-bones stage:

- markdown team roles exist
- SQLite and JSON export exist
- the portal exists
- provenance and user feedback are being added
- automated intake sorting and approval flows still need more build-out
