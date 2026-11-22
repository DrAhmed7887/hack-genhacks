#!/usr/bin/env python3
"""PollenPlan synthetic patient list generator.

Seed 20261120, N = 200, for one fictional clinic ("Clínica Demo",
Valencia). Fields exactly as docs/DATA_PLAN.md section 3. IDs only
(P001...P200), no names, no contact data. No real patient data of any
kind enters this script or its output.

All shares below (age_band, sensitised_to, current_med_on_file, severity,
asthma_flag, language) are assumptions, labelled "illustrative" in
data/DATA_CARD.md, and are never quoted as epidemiology.

Determinism: calling main() twice with the same seed produces an
identical data/patients.csv, byte for byte.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20261120
N_PATIENTS = 200
HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "patients.csv"

AGE_BANDS = ["6-12", "13-17", "18-39", "40-64", "65+"]
AGE_BAND_SHARES = [0.10, 0.10, 0.30, 0.35, 0.15]

SPECIES = ["grass", "olive", "birch"]
SENSITISATION_SHARES = {"grass": 0.70, "olive": 0.45, "birch": 0.05}

MED_OPTIONS = ["none", "oral_antihistamine", "intranasal_steroid", "both"]
MED_SHARES = [0.20, 0.45, 0.20, 0.15]

SEVERITY_OPTIONS = ["mild", "moderate_severe"]
SEVERITY_SHARES = [0.60, 0.40]

ASTHMA_SHARE = 0.25

LANGUAGE_OPTIONS = ["es", "en"]
LANGUAGE_SHARES = [0.70, 0.30]


def generate_patients(seed: int = SEED, n: int = N_PATIENTS) -> list[dict]:
    """Generate the synthetic patient list deterministically.

    Draw order is fixed (age_band, then each species sensitisation in
    SPECIES order, then med, severity, asthma, language) so that the same
    seed always yields the same table regardless of call site.
    """
    rng = np.random.default_rng(seed)
    patients = []
    for i in range(1, n + 1):
        patient_id = f"P{i:03d}"
        age_band = rng.choice(AGE_BANDS, p=AGE_BAND_SHARES)
        sensitised = [
            sp for sp in SPECIES if rng.random() < SENSITISATION_SHARES[sp]
        ]
        med = rng.choice(MED_OPTIONS, p=MED_SHARES)
        severity = rng.choice(SEVERITY_OPTIONS, p=SEVERITY_SHARES)
        asthma = rng.random() < ASTHMA_SHARE
        language = rng.choice(LANGUAGE_OPTIONS, p=LANGUAGE_SHARES)
        patients.append(
            {
                "patient_id": patient_id,
                "age_band": age_band,
                "sensitised_to": "|".join(sensitised),
                "current_med_on_file": med,
                "severity": severity,
                "asthma_flag": "yes" if asthma else "no",
                "language": language,
            }
        )
    return patients


def write_patients(patients: list[dict], out_path: Path = OUT_PATH) -> None:
    fieldnames = [
        "patient_id",
        "age_band",
        "sensitised_to",
        "current_med_on_file",
        "severity",
        "asthma_flag",
        "language",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(patients)


def main() -> int:
    patients = generate_patients()
    write_patients(patients)
    print(f"Wrote {len(patients)} synthetic patients to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
