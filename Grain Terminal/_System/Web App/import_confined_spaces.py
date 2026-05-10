"""
import_confined_spaces.py
========================
Imports the Royal Seaforth Grain Terminal Confined Space Register into the
confined_spaces table.

Source document: RSGT Confined Space Register.pdf
Prepared by:     Arco Professional Safety Services Ltd
Survey date:     10 November 2023
Document ref:    Peel Ports Bootle, Rev. 0, November 2023
Imported by:     Heath (H&S specialist, LEEN AI team)

Classification key (CSR '97 ACoP):
  LOW    — Adequate natural ventilation; unobstructed access/egress; no realistic
            specified risk unless conditions change.
  MEDIUM — Access issues; realistic expectation of specified risk; specified risks
            may be introduced by the work activity itself.
  HIGH   — Hazard present that cannot be controlled or eliminated.

Entry requirement key:
  NO_ENTRY_REQUIRED — No known routine entry; retained on register as potential
                      confined space in case circumstances change.
  CONTRACTOR_ONLY   — Entry by approved contractors only; PTW + bespoke RAMS required.
  SITE_TEAM_PTW     — Site maintenance team may enter; PTW + site-specific RAMS required.
  CONTRACTOR_PTW    — Contractor entry; PTW managed by contractor.

Confidence level: VERIFIED for all records — data imported directly from the
Arco survey document without interpretation. Where the survey noted assumptions
due to limited access, this is recorded in the notes field.

Run from inside Grain Terminal/_System/Web App/:
    python3 import_confined_spaces.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db_config import get_connection

SOURCE_DOCUMENT = "RSGT Confined Space Register.pdf (Arco Professional Safety Services, Rev 0, November 2023)"
SOURCE_DATE     = "2023-11-10"
ADDED_BY        = "Heath"

CONFINED_SPACES = [
    {
        "cs_ref": "CS-01",
        "location_name": "Elevator Head Chute",
        "area": "Elevator",
        "classification": "MEDIUM",
        "classification_notes": (
            "Normally not required to enter. Specific Risk Assessment and Method Statement "
            "(RAMS) to be produced for each event. Height exposure is the major hazard."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Oxygen Depletion, Fire / Explosive Atmosphere (Dust), Free Flowing Solids"
        ),
        "additional_risks": (
            "Restricted Access / Egress, Work at Height, Medical Emergency, "
            "Noise, Communications, Non-sparking / non-static tools required"
        ),
        "rescue_arrangements": (
            "Rescue plan proportionate to medium risk. Suitable method for retrieving "
            "casualty required. Standby person at all times."
        ),
        "entry_notes": (
            "Entry required for routine cleaning or chute replacement. Height exposure "
            "to provide access is the major hazard — suitable access platform to be "
            "considered. ATEX compliant electrical equipment required due to potential "
            "fine particulate accumulation. Non-sparking tools to be used."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-02",
        "location_name": "Upper Carrier Top Entry",
        "area": "Conveyor / Carrier",
        "classification": "MEDIUM",
        "classification_notes": (
            "Potential for entry exists. Contractor entry only. Contractor RAMS "
            "to be created for each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion (dust accumulation / ignition), Free Flowing Solids, Medical"
        ),
        "additional_risks": (
            "Access and Egress, Moving Machinery, Free Flowing Solids, Rescue"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors. Robust PTW system with accurate "
            "pre-entry status required. Contractor to submit bespoke RAMS for each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-03",
        "location_name": "Balance Flue",
        "area": "Process / Weighing",
        "classification": "LOW",
        "classification_notes": (
            "Adequate natural ventilation under normal conditions. Risk increases if "
            "work activity introduces ignition sources or disturbs particulate."
        ),
        "entry_requirement": "SITE_TEAM_PTW",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Oxygen Depletion, Heat, Fire / Explosive Atmosphere (Dust)"
        ),
        "additional_risks": (
            "Access and Egress, Rescue, Work at Height, Communication, Hazard Isolation"
        ),
        "rescue_arrangements": (
            "Proportionate to low risk classification. Standby person required."
        ),
        "entry_notes": (
            "De-scale and cleaning required within this space. Non-entry techniques "
            "should be investigated first — ATEX compliant vacuum systems may allow "
            "cleaning from outside the space, potentially eliminating the need for entry. "
            "If entry is unavoidable, PTW and pre-entry atmosphere test required."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-04",
        "location_name": "Scale Entry",
        "area": "Process / Weighing",
        "classification": "MEDIUM",
        "classification_notes": (
            "Bespoke risk controls required. Contractor-managed PTW process. "
            "Contractor controlled access only."
        ),
        "entry_requirement": "CONTRACTOR_PTW",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Heat, Oxygen Depletion, Fire / Explosive Atmosphere (Dust), Entrapment"
        ),
        "additional_risks": (
            "Communication, Access and Egress, Rescue, Work at Height, "
            "Draw-down risk, Housekeeping plan required"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS. "
            "PTW to be managed by contractor."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW process managed "
            "by the contractor. Contractor RAMS required for each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-05",
        "location_name": "Lower Garner Top Entry",
        "area": "Garner / Storage",
        "classification": "MEDIUM",
        "classification_notes": (
            "Historical evidence of entry exists. Contractor entry with bespoke "
            "RAMS approval required."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosive Atmosphere, Heat, Oxygen Depletion, Free Flowing Solids"
        ),
        "additional_risks": "Access and Egress, COSHH",
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors. PTW with accurate pre-entry status "
            "required. Bespoke RAMS to be approved before each entry. Historical "
            "evidence of entry on record."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-06",
        "location_name": "Turnhead",
        "area": "Turnhead / Distribution",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor entry only. Bespoke process and RAMS approval required "
            "before each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Oxygen Depletion, Fire / Explosive Atmosphere, Free Flowing Solids"
        ),
        "additional_risks": (
            "Restricted Access / Egress, Work at Height, Medical Emergency, "
            "Noise, Communications, COSHH"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors. PTW with accurate pre-entry status "
            "required. Bespoke RAMS to be produced for each entry event."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-07",
        "location_name": "FB1 (Feed Belt 1 Boot / Enclosure)",
        "area": "Feed Belt",
        "classification": "LOW",
        "classification_notes": (
            "No known current requirement to enter. Retained on register as a potential "
            "confined space in the event circumstances change."
        ),
        "entry_requirement": "NO_ENTRY_REQUIRED",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Oxygen Depletion, Heat, Fire / Explosive Atmosphere, Free Flowing Solids"
        ),
        "additional_risks": "Medical Emergency, Communication, COSHH",
        "rescue_arrangements": (
            "No current rescue plan required. Should entry become necessary, "
            "a bespoke rescue plan must be produced."
        ),
        "entry_notes": (
            "No known requirement to enter. Retained on register as potential confined "
            "space. SHOULD an entry requirement arise, a bespoke RAMS must be produced "
            "for each entry as needed. PTW required if entry is ever necessary."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-08",
        "location_name": "UG5 (Upper Garner 5)",
        "area": "Upper Garner / Storage",
        "classification": "HIGH",
        "classification_notes": (
            "High risk classification. Contractor only. Bespoke RAMS and approval "
            "required for each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Work at Height, Fire / Explosion (ongoing), Access and Egress, "
            "Medical Emergency"
        ),
        "rescue_arrangements": (
            "High risk — full rescue plan mandatory. Contractor to provide bespoke "
            "rescue arrangements as part of RAMS. Must cover alarm raising, casualty "
            "retrieval, rescue equipment, and trained rescue personnel."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-09",
        "location_name": "Shipping Bins",
        "area": "Shipping / Export",
        "classification": "HIGH",
        "classification_notes": (
            "High risk classification. Contractor only with bespoke RAMS approval."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Free Flowing Solids, Heat"
        ),
        "additional_risks": "Work at Height, Access and Egress, Medical Emergency",
        "rescue_arrangements": (
            "High risk — full rescue plan mandatory. Contractor to provide bespoke "
            "rescue arrangements. Must cover alarm raising, casualty retrieval, "
            "rescue equipment, and trained personnel."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-10",
        "location_name": "Bin Tops (multiple)",
        "area": "Storage Bins",
        "classification": "HIGH",
        "classification_notes": (
            "High risk. Applies to multiple bin top access points. Contractor "
            "only with approved bespoke RAMS."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Work at Height, Fire / Explosion (ongoing), Access and Egress, "
            "Medical Emergency"
        ),
        "rescue_arrangements": (
            "High risk — full rescue plan mandatory. Contractor to provide bespoke "
            "rescue arrangements as part of RAMS for each entry."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry. "
            "Applies to multiple bin top access locations across the terminal."
        ),
        "confidence": "VERIFIED",
        "notes": "Multiple bin tops covered by this register entry.",
    },
    {
        "cs_ref": "CS-11",
        "location_name": "GTU (Grain Transfer Unit)",
        "area": "Grain Transfer",
        "classification": "MEDIUM",
        "classification_notes": (
            "Maintenance team may enter for belt tensioning. Space is restrictive "
            "but not complex in design. Short-duration entries expected."
        ),
        "entry_requirement": "SITE_TEAM_PTW",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion (dust), Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Fire / Explosion (ongoing risk), Emergency plan required"
        ),
        "rescue_arrangements": (
            "Self-rescue is the primary method. Entrant to respond to gas alarm "
            "with sufficient time to evacuate. Rescue arrangements proportionate "
            "to medium risk."
        ),
        "entry_notes": (
            "Entry by maintenance team for belt tensioning. Short-duration entries. "
            "Oxygen depletion has low foreseeability but must be considered. "
            "Heat (positional and ambient) to be managed. Dust accumulation poses "
            "fire / explosion risk — pre-entry cleaning by non-entry techniques preferred "
            "(ATEX-compliant vacuum). Where full clean not achievable, consider "
            "non-sparking tools. Any vacuum used must be ATEX compliant."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-12",
        "location_name": "Lorry Loading Bin Tops",
        "area": "Lorry Loading",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor only. Bespoke RAMS approval required for each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Fire / Explosion (ongoing), Emergency plan required"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-13",
        "location_name": "Mill Bins",
        "area": "Mill / Storage",
        "classification": "MEDIUM",
        "classification_notes": (
            "Routine cleaning and irregular chute repairs may necessitate entry. "
            "Falls risk significant — no ladder access. Offset entry compounds "
            "fall arrest / recovery difficulties."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids (dust), Heat"
        ),
        "additional_risks": (
            "Fire / Explosion (ongoing), Fall from Height (no ladder access), "
            "Emergency plan required"
        ),
        "rescue_arrangements": (
            "Standard tripod / winch may NOT be suitable due to offset entry. "
            "Davit system should be considered to improve fall arrest / recovery. "
            "Contractor to specify suitable rescue provision in RAMS."
        ),
        "entry_notes": (
            "Routine cleaning and chute repairs may require entry. Significant falls "
            "risk — no ladder access available. Offset entry geometry makes standard "
            "tripod / winch arrangement unsuitable; davit system recommended. "
            "Non-entry techniques (ATEX-compliant vacuum) should be used where possible. "
            "Bespoke RAMS required for each entry."
        ),
        "confidence": "VERIFIED",
        "notes": (
            "UNCERTAIN element: offset entry suitability for specific rescue equipment "
            "not confirmed — specialist assessment recommended before first manned entry."
        ),
    },
    {
        "cs_ref": "CS-14",
        "location_name": "Surge Bins",
        "area": "Process / Storage",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor only. Bespoke RAMS approval required for each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Work at Height, Fire / Explosion (ongoing), Access and Egress, "
            "Emergency plan required"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-15",
        "location_name": "Elevator Boot / Elevator Bins",
        "area": "Elevator",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor only. Bespoke RAMS approval required for each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Work at Height, Fire / Explosion (ongoing), Access and Egress, "
            "Emergency plan required"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-16",
        "location_name": "Basement Chute Elevator",
        "area": "Basement",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor only with approved RAMS. PTW with accurate pre-entry status."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Heat"
        ),
        "additional_risks": (
            "Work at Height, Fire / Explosion (ongoing), Access and Egress, "
            "Medical Emergency"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS submission."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Approved RAMS required for each entry."
        ),
        "confidence": "VERIFIED",
        "notes": None,
    },
    {
        "cs_ref": "CS-17",
        "location_name": "Silo 3 Bins",
        "area": "Silo 3",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor only. Bespoke RAMS approval required for each entry. "
            "Toxic atmosphere (H2S) identified as an additional hazard."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Toxic Atmosphere"
        ),
        "additional_risks": (
            "Fire / Explosion (ongoing), Access and Egress, Medical Emergency, H2S"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan. H2S monitoring required. "
            "Rescue equipment must account for toxic atmosphere."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry. "
            "H2S is flagged as an identified risk — gas monitoring mandatory."
        ),
        "confidence": "VERIFIED",
        "notes": "H2S identified as additional hazard. Pre-entry gas monitoring mandatory.",
    },
    {
        "cs_ref": "CS-18",
        "location_name": "BMH (Bucket / Belt Material Handler)",
        "area": "BMH",
        "classification": "MEDIUM",
        "classification_notes": (
            "Contractor only. Bespoke RAMS approval required for each entry."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Toxic Atmosphere"
        ),
        "additional_risks": (
            "Fire / Explosion (ongoing), Emergency plan required, H2S"
        ),
        "rescue_arrangements": (
            "Contractor to provide bespoke rescue plan as part of RAMS. "
            "H2S monitoring required."
        ),
        "entry_notes": (
            "All entries by approved contractors only. PTW with accurate pre-entry "
            "status required. Bespoke RAMS to be approved before each entry."
        ),
        "confidence": "VERIFIED",
        "notes": "H2S identified as additional hazard. Pre-entry gas monitoring mandatory.",
    },
    {
        "cs_ref": "CS-19",
        "location_name": "BMH Filter Box",
        "area": "BMH",
        "classification": "MEDIUM",
        "classification_notes": (
            "Routine entry for filter cleaning / change. Low confined space risk "
            "but complex working position — height exposure with limited space for "
            "traditional fall arrest systems."
        ),
        "entry_requirement": "SITE_TEAM_PTW",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Toxic Atmosphere"
        ),
        "additional_risks": (
            "Fire / Explosion (fine particulate — high explosion risk), "
            "Work at Height, Access and Egress, Medical Emergency, H2S"
        ),
        "rescue_arrangements": (
            "Height specialist assessment recommended — confined space rescue and "
            "height rescue may share the same equipment and solution. "
            "PTW to cover both height and confined space risks."
        ),
        "entry_notes": (
            "Routine entry for filter cleaning / change. Fine particulate presents "
            "elevated fire / explosion risk. Lids removed for maintenance but entrant "
            "may drop below box lip — classified as confined space entry. Height "
            "exposure with little space for traditional temporary fall arrest systems. "
            "Height specialist to assess separately — confined rescue may be addressed "
            "concurrently. PTW required for each entry."
        ),
        "confidence": "VERIFIED",
        "notes": (
            "H2S identified as additional hazard. Height and confined space risks "
            "should be assessed together by a height specialist."
        ),
    },
    {
        "cs_ref": "CS-20",
        "location_name": "BMH Turret",
        "area": "BMH",
        "classification": "MEDIUM",
        "classification_notes": (
            "Routine planned maintenance entry (oils / lubricants). Remote location "
            "adds positional complexity but low confined space risk provided entry "
            "door is secured open."
        ),
        "entry_requirement": "SITE_TEAM_PTW",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Toxic Atmosphere"
        ),
        "additional_risks": (
            "Fire / Explosion (ongoing), H2S, Remote / isolated location"
        ),
        "rescue_arrangements": (
            "Self-rescue considered viable for this space provided entry door is "
            "secured open and gas alarm is worn. Standby person required due to "
            "remote location."
        ),
        "entry_notes": (
            "Entry for routine planned maintenance involving oils / lubricants. "
            "Entry door must be secured in open position before entry. Remove oils / "
            "lubricants to reduce potential for hostile atmosphere. Oxygen depletion "
            "possible if space has been closed for weeks (corrosion). Allow 15–20 "
            "minutes natural ventilation after opening before entry. Space to be kept "
            "free of stored materials — housekeeping a priority as part of entry process."
        ),
        "confidence": "VERIFIED",
        "notes": "H2S identified as additional hazard. Pre-entry gas monitoring mandatory.",
    },
    {
        "cs_ref": "CS-21",
        "location_name": "Main Dust Bins",
        "area": "Dust Plant",
        "classification": "HIGH",
        "classification_notes": (
            "High risk. Entry ONLY by appointed contractors for specific tasks. "
            "Access was not available during the survey — some assumptions made."
        ),
        "entry_requirement": "CONTRACTOR_ONLY",
        "permit_required": 1,
        "atmosphere_testing": 1,
        "specified_risks": (
            "Fire / Explosion, Oxygen Depletion, Free Flowing Solids, Toxic Atmosphere"
        ),
        "additional_risks": (
            "Access and Egress, Fire / Explosion (ongoing), Medical Emergency, H2S"
        ),
        "rescue_arrangements": (
            "High risk — full rescue plan mandatory. Contractor to provide bespoke "
            "rescue arrangements. Must account for toxic atmosphere (H2S) and "
            "confined space retrieval."
        ),
        "entry_notes": (
            "Entry ONLY by appointed contractors for specific tasks such as cleaning. "
            "Contractor management provisions apply. Bespoke RAMS required and approved "
            "before each entry. PTW required."
        ),
        "confidence": "VERIFIED",
        "notes": (
            "H2S identified as additional hazard. Pre-entry gas monitoring mandatory. "
            "Site photo not available — access to bins was not observed during the survey. "
            "Some classification assumptions made based on assessor experience and "
            "information provided on the day (per survey scope statement)."
        ),
    },
]


def run():
    conn = get_connection()
    conn.row_factory = None

    # Check if data already imported
    existing = conn.execute("SELECT COUNT(*) FROM confined_spaces").fetchone()[0]
    if existing > 0:
        print(f"WARNING: confined_spaces already has {existing} rows.")
        answer = input("Re-import? This will DELETE existing records first. [y/N]: ")
        if answer.strip().lower() != "y":
            print("Aborted.")
            conn.close()
            return
        conn.execute("DELETE FROM confined_spaces")
        print(f"  Deleted {existing} existing records.")

    inserted = 0
    flagged = []

    for cs in CONFINED_SPACES:
        conn.execute(
            """
            INSERT INTO confined_spaces (
                cs_ref, location_name, area, classification,
                classification_notes, entry_requirement,
                permit_required, atmosphere_testing,
                specified_risks, additional_risks,
                rescue_arrangements, entry_notes,
                source_document, source_date,
                confidence, added_by, notes
            ) VALUES (
                :cs_ref, :location_name, :area, :classification,
                :classification_notes, :entry_requirement,
                :permit_required, :atmosphere_testing,
                :specified_risks, :additional_risks,
                :rescue_arrangements, :entry_notes,
                :source_document, :source_date,
                :confidence, :added_by, :notes
            )
            """,
            {
                **cs,
                "source_document": SOURCE_DOCUMENT,
                "source_date":     SOURCE_DATE,
                "added_by":        ADDED_BY,
            },
        )
        inserted += 1
        print(f"  ✓ {cs['cs_ref']}: {cs['location_name']} [{cs['classification']}]")
        if cs.get("notes") and "UNCERTAIN" in cs.get("notes", ""):
            flagged.append(cs["cs_ref"])

    conn.commit()
    conn.close()

    print(f"\nImport complete: {inserted} confined spaces imported.")
    if flagged:
        print(f"Entries flagged for review (UNCERTAIN element in notes): {', '.join(flagged)}")
    print("\nConfidence: VERIFIED for all records (directly from Arco survey document).")
    print("Source: RSGT Confined Space Register.pdf, Arco Professional Safety Services, Rev 0, 10 November 2023.")


if __name__ == "__main__":
    run()
