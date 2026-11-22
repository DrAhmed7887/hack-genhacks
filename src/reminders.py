#!/usr/bin/env python3
"""PollenPlan reminder eligibility and message rules.

Implements DATA_PLAN.md section 3, "Reminder rules (tested by unit tests,
signed 22 Nov 2026)":

  1. A patient is *eligible* only if sensitised to the alerting species
     AND has a medicine on file.
  2. The message may name only the medicine class already on file. It
     never adds a drug, a dose, or a diagnosis.
  3. Every message carries the same fixed safety line (text to be
     signed), and asthma-flag patients also get the asthma-plan line.
  4. A batch is a draft until the nurse presses approve. "Send" writes an
     approved_at row and a log line. Nothing leaves the system.

This module only decides eligibility and assembles the structured message
fields (code decides); it does not call any model and does not send
anything. The "nurse approves every batch" / "nothing is sent" guarantees
in .kiro/steering/rules.md are enforced by there being no send path here
at all.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Signed text (CRITERIA_FOR_SIGNOFF row 9, approved 22 Nov 2026 by Ahmed Zayed),
# per .kiro/steering/rules.md ("rules/thresholds.json is status signed").
SAFETY_LINE = (
    "Pollen levels do not diagnose anything. If you are wheezy or short "
    "of breath, follow your asthma plan or call your clinic; if severe, "
    "call emergency services."
)
ASTHMA_LINE = (
    "You have an asthma flag on file: please follow your own asthma "
    "action plan and seek care if you have breathing difficulty. "
    "Keep your reliever with you."
)

MED_CLASS_LABELS = {
    "none": None,
    "oral_antihistamine": "your oral antihistamine",
    "intranasal_steroid": "your intranasal steroid spray",
    "both": "your oral antihistamine and intranasal steroid spray",
}


@dataclass
class Patient:
    patient_id: str
    age_band: str
    sensitised_to: list[str]
    current_med_on_file: str
    severity: str
    asthma_flag: bool
    language: str


@dataclass
class ReminderMessage:
    patient_id: str
    species: str
    medicine_class: str
    lines: list[str] = field(default_factory=list)


def patient_from_row(row: dict) -> Patient:
    """Build a Patient from a data/patients.csv row (as parsed by csv.DictReader)."""
    raw_sens = row.get("sensitised_to", "") or ""
    sensitised = [s for s in raw_sens.split("|") if s]
    asthma = str(row.get("asthma_flag", "no")).strip().lower() == "yes"
    return Patient(
        patient_id=row["patient_id"],
        age_band=row["age_band"],
        sensitised_to=sensitised,
        current_med_on_file=row["current_med_on_file"],
        severity=row["severity"],
        asthma_flag=asthma,
        language=row["language"],
    )


def is_eligible(patient: Patient, alerting_species: str) -> bool:
    """Rule 1: eligible only if sensitised to the alerting species AND has
    a medicine on file (med on file != "none")."""
    sensitised = alerting_species in patient.sensitised_to
    has_med = patient.current_med_on_file != "none"
    return sensitised and has_med


def build_message(patient: Patient, alerting_species: str) -> ReminderMessage | None:
    """Build the reminder message for one eligible patient.

    Returns None if the patient is not eligible (rule 1). Enforces rule 2
    (name only the medicine class already on file, nothing invented) and
    rule 3 (fixed safety line always present; asthma line added only for
    asthma_flag patients).
    """
    if not is_eligible(patient, alerting_species):
        return None

    medicine_class = MED_CLASS_LABELS.get(patient.current_med_on_file)
    if medicine_class is None:
        # Should be unreachable given is_eligible excludes "none", but
        # guard explicitly rather than silently naming an unknown class.
        return None

    lines = [SAFETY_LINE]
    if patient.asthma_flag:
        lines.append(ASTHMA_LINE)

    return ReminderMessage(
        patient_id=patient.patient_id,
        species=alerting_species,
        medicine_class=medicine_class,
        lines=lines,
    )


def build_batch(patients: list[Patient], alerting_species: str) -> list[ReminderMessage]:
    """Rule 4 framing: this only builds the draft batch. Nothing is sent;
    there is no send function in this module. A caller elsewhere is
    responsible for the nurse-approval step and the approved_at /
    log-line write, which are out of scope for the backtest and tests
    here (no server, no persistence of approvals in this repo)."""
    out = []
    for p in patients:
        msg = build_message(p, alerting_species)
        if msg is not None:
            out.append(msg)
    return out
