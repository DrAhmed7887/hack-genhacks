"""Tests for data/make_patients.py: determinism and basic shape checks."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import make_patients  # noqa: E402


def test_generate_patients_is_deterministic_across_calls():
    run1 = make_patients.generate_patients()
    run2 = make_patients.generate_patients()
    assert run1 == run2


def test_generate_patients_deterministic_with_explicit_seed():
    run1 = make_patients.generate_patients(seed=20261120, n=200)
    run2 = make_patients.generate_patients(seed=20261120, n=200)
    assert run1 == run2


def test_generate_patients_different_seed_differs():
    run1 = make_patients.generate_patients(seed=20261120, n=200)
    run2 = make_patients.generate_patients(seed=1, n=200)
    assert run1 != run2


def test_generate_patients_count_and_ids():
    patients = make_patients.generate_patients()
    assert len(patients) == make_patients.N_PATIENTS
    ids = [p["patient_id"] for p in patients]
    assert ids[0] == "P001"
    assert ids[-1] == f"P{make_patients.N_PATIENTS:03d}"
    assert len(set(ids)) == len(ids)  # all unique


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


def test_write_patients_roundtrip(tmp_path):
    patients = make_patients.generate_patients(seed=1, n=10)
    out_path = tmp_path / "patients.csv"
    make_patients.write_patients(patients, out_path)
    with out_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10
    assert rows[0]["patient_id"] == "P001"


def test_write_patients_is_byte_identical_across_runs(tmp_path):
    out1 = tmp_path / "p1.csv"
    out2 = tmp_path / "p2.csv"
    make_patients.write_patients(make_patients.generate_patients(), out1)
    make_patients.write_patients(make_patients.generate_patients(), out2)
    assert out1.read_bytes() == out2.read_bytes()
