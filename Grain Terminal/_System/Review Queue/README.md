# Review Queue

This folder is for follow-up items raised by users of the portal or by the AI team.

## Intended Use

- incorrect answers reported from the web portal
- source-link mismatches
- extracted data that does not match the original drawing or document
- items awaiting manual confirmation before database update

## Current Flow

The standalone portal can export issue reports as JSON files.

Those files can then be:

- reviewed manually by Paul and Codex together
- imported into the database with `Web App/import_feedback.py`
- used as a queue for correction work

## Rule

Nothing should be marked verified in the portal unless it can be traced back to the
original file and survives user spot-checking.
