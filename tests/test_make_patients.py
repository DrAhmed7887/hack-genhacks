"""Tests for data/make_patients.py: offline determinism and CDC NHANES cohort checks."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import make_patients  # noqa: E402
from src import message_guard as g  # noqa: E402
from src import reminders  # noqa: E402


def test_generate_patients_is_deterministic_across_calls():
    run1 = make_patients.generate_patients()
    run2 = make_patients.generate_patients()
    assert run1 == run2


def test_generate_patients_count_and_nhanes_ids():
    patients = make_patients.generate_patients()
    assert len(patients) == make_patients.N_PATIENTS == 578
    ids = [p["patient_id"] for p in patients]
    assert all(pid.startswith("NH-") for pid in ids)
    assert len(set(ids)) == len(ids)  # all unique
    assert "NH-32025" in ids and "NH-31133" in ids


def test_generate_patients_fields_within_allowed_values():
    patients = make_patients.generate_patients()
    for p in patients:
        assert p["age_band"] in make_patients.AGE_BANDS
        assert p["current_med_on_file"] in make_patients.MED_OPTIONS
        assert p["severity"] in make_patients.SEVERITY_OPTIONS
        assert p["asthma_flag"] in ("yes", "no")
        assert p["language"] in make_patients.LANGUAGE_OPTIONS
        sensitised = [s for s in p["sensitised_to"].split("|") if s]
        for sp in sensitised:
            assert sp in make_patients.SPECIES


def test_nhanes_eligibility_and_tier_counts():
    roster = [reminders.patient_from_row(r) for r in make_patients.generate_patients()]
    grass_batch = reminders.build_batch(roster, "grass")
    birch_batch = reminders.build_batch(roster, "birch")
    olive_batch = reminders.build_batch(roster, "olive")
    assert len(grass_batch) == 39
    assert len(birch_batch) == 24
    assert len(olive_batch) == 0  # US NHANES did not assay olive IgE
    by_id = {p.patient_id: p for p in roster}
    tiers = [g.risk_tier(by_id[m.patient_id])[0] for m in grass_batch]
    assert (tiers.count(1), tiers.count(2), tiers.count(3)) == (23, 10, 6)


def test_write_patients_roundtrip(tmp_path):
    patients = make_patients.generate_patients()[:10]
    out_path = tmp_path / "patients.csv"
    make_patients.write_patients(patients, out_path)
    with out_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10
    assert rows[0]["patient_id"] == patients[0]["patient_id"]


def test_write_patients_is_byte_identical_across_runs(tmp_path):
    out1 = tmp_path / "p1.csv"
    out2 = tmp_path / "p2.csv"
    make_patients.write_patients(make_patients.generate_patients(), out1)
    make_patients.write_patients(make_patients.generate_patients(), out2)
    assert out1.read_bytes() == out2.read_bytes()
