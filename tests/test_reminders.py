"""Tests for src/reminders.py: reminder eligibility rules 1-3 from
docs/DATA_PLAN.md section 3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import reminders  # noqa: E402


def make_patient(sensitised_to, med, asthma=False, **kwargs):
    defaults = dict(
        patient_id="P001",
        age_band="18-39",
        current_med_on_file=med,
        severity="mild",
        language="en",
    )
    defaults.update(kwargs)
    return reminders.Patient(
        sensitised_to=sensitised_to, asthma_flag=asthma, **defaults
    )


# ---------------------------------------------------------------------------
# Rule 1: eligible only if sensitised to the alerting species AND has a
# medicine on file.
# ---------------------------------------------------------------------------

def test_rule1_eligible_when_sensitised_and_has_med():
    p = make_patient(["grass"], "oral_antihistamine")
    assert reminders.is_eligible(p, "grass") is True


def test_rule1_ineligible_when_not_sensitised_to_alerting_species():
    p = make_patient(["olive"], "oral_antihistamine")
    assert reminders.is_eligible(p, "grass") is False


def test_rule1_ineligible_when_no_med_on_file():
    p = make_patient(["grass"], "none")
    assert reminders.is_eligible(p, "grass") is False


def test_rule1_ineligible_when_neither_sensitised_nor_med():
    p = make_patient([], "none")
    assert reminders.is_eligible(p, "grass") is False


def test_rule1_sensitised_to_multiple_species_only_matches_alerting_one():
    p = make_patient(["grass", "birch"], "oral_antihistamine")
    assert reminders.is_eligible(p, "grass") is True
    assert reminders.is_eligible(p, "olive") is False


# ---------------------------------------------------------------------------
# Rule 2: the message names only the medicine class already on file, never
# a new drug, dose, or diagnosis.
# ---------------------------------------------------------------------------

def test_rule2_message_names_only_med_on_file_antihistamine():
    p = make_patient(["grass"], "oral_antihistamine")
    msg = reminders.build_message(p, "grass")
    assert msg is not None
    assert msg.medicine_class == reminders.MED_CLASS_LABELS["oral_antihistamine"]
    assert "steroid" not in msg.medicine_class


def test_rule2_message_names_only_med_on_file_steroid():
    p = make_patient(["grass"], "intranasal_steroid")
    msg = reminders.build_message(p, "grass")
    assert msg is not None
    assert msg.medicine_class == reminders.MED_CLASS_LABELS["intranasal_steroid"]
    assert "antihistamine" not in msg.medicine_class


def test_rule2_message_names_both_only_when_both_on_file():
    p = make_patient(["grass"], "both")
    msg = reminders.build_message(p, "grass")
    assert msg is not None
    assert "antihistamine" in msg.medicine_class
    assert "steroid" in msg.medicine_class


def test_rule2_no_message_for_ineligible_patient():
    p = make_patient(["grass"], "none")
    msg = reminders.build_message(p, "grass")
    assert msg is None


# ---------------------------------------------------------------------------
# Rule 3: every message carries the fixed safety line; asthma_flag patients
# also get the asthma-plan line.
# ---------------------------------------------------------------------------

def test_rule3_safety_line_always_present():
    p = make_patient(["grass"], "oral_antihistamine", asthma=False)
    msg = reminders.build_message(p, "grass")
    assert msg is not None
    assert reminders.SAFETY_LINE in msg.lines


def test_rule3_asthma_line_present_only_for_asthma_patients():
    p_asthma = make_patient(["grass"], "oral_antihistamine", asthma=True)
    p_no_asthma = make_patient(["grass"], "oral_antihistamine", asthma=False)

    msg_asthma = reminders.build_message(p_asthma, "grass")
    msg_no_asthma = reminders.build_message(p_no_asthma, "grass")

    assert reminders.ASTHMA_LINE in msg_asthma.lines
    assert reminders.ASTHMA_LINE not in msg_no_asthma.lines
    # safety line still present for both
    assert reminders.SAFETY_LINE in msg_asthma.lines
    assert reminders.SAFETY_LINE in msg_no_asthma.lines


# ---------------------------------------------------------------------------
# build_batch / patient_from_row
# ---------------------------------------------------------------------------

def test_build_batch_only_includes_eligible_patients():
    patients = [
        make_patient(["grass"], "oral_antihistamine", patient_id="P001"),
        make_patient(["olive"], "oral_antihistamine", patient_id="P002"),  # not sensitised to grass
        make_patient(["grass"], "none", patient_id="P003"),  # no med
        make_patient(["grass", "olive"], "both", patient_id="P004"),
    ]
    batch = reminders.build_batch(patients, "grass")
    ids = {m.patient_id for m in batch}
    assert ids == {"P001", "P004"}


def test_patient_from_row_parses_pipe_joined_sensitisation_and_asthma_flag():
    row = {
        "patient_id": "P010",
        "age_band": "40-64",
        "sensitised_to": "grass|olive",
        "current_med_on_file": "both",
        "severity": "moderate_severe",
        "asthma_flag": "yes",
        "language": "es",
    }
    p = reminders.patient_from_row(row)
    assert p.sensitised_to == ["grass", "olive"]
    assert p.asthma_flag is True
    assert p.current_med_on_file == "both"


def test_patient_from_row_empty_sensitisation():
    row = {
        "patient_id": "P011",
        "age_band": "40-64",
        "sensitised_to": "",
        "current_med_on_file": "none",
        "severity": "mild",
        "asthma_flag": "no",
        "language": "en",
    }
    p = reminders.patient_from_row(row)
    assert p.sensitised_to == []
    assert p.asthma_flag is False
