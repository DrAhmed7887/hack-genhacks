#!/usr/bin/env python3
"""PollenPlan CDC NHANES 2005-2006 allergy cohort builder.

Replaces illustrative synthetic rows with real, de-identified public-domain
CDC NCHS NHANES 2005-2006 participants (zero PHI, SEQN respondent IDs only):

  - Cohort: RIDAGEYR >= 6, doctor/health-professional confirmed hay fever
    (AGQ010 == 1), with complete ImmunoCAP serum specific IgE (kU/L) in AL_IGE_D.
  - Sensitisation (standard ImmunoCAP cut-off >= 0.35 kU/L):
      * grass: LBXIG5 (ryegrass) >= 0.35 OR LBXIG2 (Bermuda grass) >= 0.35
      * birch: LBXIT3 (birch) >= 0.35
      * olive: not assayed by US NHANES (never imputed or invented)
  - Medicine on file (verified Rx containers in RXQ_RX_D):
      * intranasal_steroid: FLUTICASONE/MOMETASONE/BUDESONIDE/TRIAMCINOLONE/
        BECLOMETHASONE/FLUNISOLIDE NASAL
      * oral_antihistamine: oral cetirizine, desloratadine, loratadine,
        fexofenadine, levocetirizine, chlorpheniramine, brompheniramine,
        diphenhydramine, hydroxyzine (excluding nasal/ophthalmic/topical forms)
      * both / none
  - Clinical flags:
      * asthma_flag: yes if MCQ010 == 1 else no
      * severity: moderate_severe if AGQ030 == 1 (12m hay-fever episode) or
        RDQ070 == 1 (12m wheeze) else mild

Usage:
  .venv/bin/python data/make_patients.py           # offline build from cached cohort CSV
  .venv/bin/python data/make_patients.py --fetch   # refresh cache CSV from ww.cdc.gov
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE_CSV = HERE / "cache" / "nhanes_2005_2006_hayfever_cohort.csv"
MANIFEST_JSON = HERE / "cache" / "nhanes_2005_2006_manifest.json"
OUT_PATH = HERE / "patients.csv"

NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2005/DataFiles"
NHANES_TABLES = ("AL_IGE_D", "DEMO_D", "MCQ_D", "AGQ_D", "RDQ_D", "RXQ_RX_D")
IGE_THRESHOLD = 0.35

N_PATIENTS = 578
AGE_BANDS = ["6-12", "13-17", "18-39", "40-64", "65+"]
SPECIES = ["grass", "birch"]
MED_OPTIONS = ["none", "oral_antihistamine", "intranasal_steroid", "both"]
SEVERITY_OPTIONS = ["mild", "moderate_severe"]
LANGUAGE_OPTIONS = ["en"]

NASAL_STEROIDS = frozenset({
    "FLUTICASONE NASAL",
    "MOMETASONE NASAL",
    "BUDESONIDE NASAL",
    "TRIAMCINOLONE NASAL",
    "BECLOMETHASONE NASAL",
    "FLUNISOLIDE NASAL",
})
ORAL_AH_TERMS = (
    "CETIRIZINE",
    "DESLORATADINE",
    "LORATADINE",
    "FEXOFENADINE",
    "LEVOCETIRIZINE",
    "CHLORPHENIRAMINE",
    "BROMPHENIRAMINE",
    "DIPHENHYDRAMINE",
    "HYDROXYZINE",
)


def _is_oral_antihistamine(drug_upper: str) -> bool:
    if any(bad in drug_upper for bad in ("NASAL", "OPHTHALMIC", "TOPICAL")):
        return False
    return any(term in drug_upper for term in ORAL_AH_TERMS)


def _age_band(age_years: float) -> str:
    age = int(age_years)
    if age <= 12:
        return "6-12"
    if age <= 17:
        return "13-17"
    if age <= 39:
        return "18-39"
    if age <= 64:
        return "40-64"
    return "65+"


def fetch_nhanes_cohort(
    cache_csv: Path = CACHE_CSV,
    manifest_json: Path = MANIFEST_JSON,
    timeout: int = 30,
) -> dict:
    """Download public CDC NHANES 2005-2006 .XPT files and cache the de-identified cohort."""
    import pandas as pd

    hashes: dict[str, dict] = {}
    frames: dict[str, pd.DataFrame] = {}
    for name in NHANES_TABLES:
        url = f"{NHANES_BASE}/{name}.xpt"
        req = urllib.request.Request(url, headers={"User-Agent": "PollenPlan-Research/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        hashes[name] = {
            "url": url,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        frames[name] = pd.read_sas(io.BytesIO(raw), format="xport")

    rx = frames["RXQ_RX_D"][["SEQN", "RXDDRUG"]].copy()
    rx["RXDDRUG"] = rx["RXDDRUG"].apply(
        lambda x: x.decode("latin1").strip().upper() if isinstance(x, (bytes, bytearray)) else str(x).strip().upper()
    )
    rx["SEQN_INT"] = rx["SEQN"].astype(int)
    rx_incs = set(rx[rx["RXDDRUG"].isin(NASAL_STEROIDS)]["SEQN_INT"])
    rx_oah = set(rx[rx["RXDDRUG"].apply(_is_oral_antihistamine)]["SEQN_INT"])

    rx_names_by_seqn: dict[int, list[str]] = {}
    for _, row in rx.iterrows():
        d = row["RXDDRUG"]
        if d in NASAL_STEROIDS or _is_oral_antihistamine(d):
            rx_names_by_seqn.setdefault(int(row["SEQN_INT"]), []).append(d)

    ige = frames["AL_IGE_D"][["SEQN", "LBXIG5", "LBXIG2", "LBXIT3"]]
    demo = frames["DEMO_D"][["SEQN", "RIDAGEYR"]]
    mcq = frames["MCQ_D"][["SEQN", "MCQ010"]]
    agq = frames["AGQ_D"][["SEQN", "AGQ010", "AGQ030"]]
    rdq = frames["RDQ_D"][["SEQN", "RDQ070"]]

    df = (
        ige.merge(demo, on="SEQN")
        .merge(mcq, on="SEQN", how="left")
        .merge(agq, on="SEQN", how="left")
        .merge(rdq, on="SEQN", how="left")
    )
    df = df[(df["RIDAGEYR"] >= 6) & (df["AGQ010"] == 1)].dropna(subset=["LBXIG5", "LBXIG2", "LBXIT3"])
    df = df.sort_values("SEQN").copy()

    cache_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "seqn",
        "age_years",
        "rye_grass_ige_kul",
        "bermuda_grass_ige_kul",
        "birch_ige_kul",
        "asthma_mcq010",
        "hayfever_12m_agq030",
        "wheeze_12m_rdq070",
        "has_nasal_steroid_rx",
        "has_oral_antihistamine_rx",
        "rx_drugs_seen",
    ]
    rows_written = 0
    with cache_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for _, r in df.iterrows():
            seqn = int(r["SEQN"])
            rx_seen = sorted(set(rx_names_by_seqn.get(seqn, [])))
            w.writerow(
                {
                    "seqn": seqn,
                    "age_years": int(r["RIDAGEYR"]),
                    "rye_grass_ige_kul": round(float(r["LBXIG5"]), 2),
                    "bermuda_grass_ige_kul": round(float(r["LBXIG2"]), 2),
                    "birch_ige_kul": round(float(r["LBXIT3"]), 2),
                    "asthma_mcq010": int(r["MCQ010"] == 1) if pd.notna(r["MCQ010"]) else 0,
                    "hayfever_12m_agq030": int(r["AGQ030"] == 1) if pd.notna(r["AGQ030"]) else 0,
                    "wheeze_12m_rdq070": int(r["RDQ070"] == 1) if pd.notna(r["RDQ070"]) else 0,
                    "has_nasal_steroid_rx": int(seqn in rx_incs),
                    "has_oral_antihistamine_rx": int(seqn in rx_oah),
                    "rx_drugs_seen": "|".join(rx_seen),
                }
            )
            rows_written += 1

    manifest = {
        "source": "CDC NCHS NHANES 2005-2006 (public domain, de-identified SEQN)",
        "selection_rule": "RIDAGEYR >= 6 AND AGQ010 == 1 AND complete LBXIG5/LBXIG2/LBXIT3",
        "ige_cutoff_kul": IGE_THRESHOLD,
        "olive_note": "Olea europaea IgE not assayed in US NHANES 2005-2006",
        "n_rows": rows_written,
        "xpt_sources": hashes,
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def generate_patients(cache_csv: Path = CACHE_CSV) -> list[dict]:
    """Build the clinic roster deterministically offline from the cached CDC NHANES CSV."""
    if not cache_csv.is_file():
        raise FileNotFoundError(
            f"Missing {cache_csv}. Re-run with --fetch (network required once) to cache public NHANES files."
        )
    patients: list[dict] = []
    with cache_csv.open(newline="", encoding="utf-8") as fh:
        rows = sorted(csv.DictReader(fh), key=lambda r: int(r["seqn"]))
    for r in rows:
        seqn = int(r["seqn"])
        grass_pos = (float(r["rye_grass_ige_kul"]) >= IGE_THRESHOLD) or (
            float(r["bermuda_grass_ige_kul"]) >= IGE_THRESHOLD
        )
        birch_pos = float(r["birch_ige_kul"]) >= IGE_THRESHOLD
        sensitised = []
        if grass_pos:
            sensitised.append("grass")
        if birch_pos:
            sensitised.append("birch")

        has_ns = int(r["has_nasal_steroid_rx"]) == 1
        has_oah = int(r["has_oral_antihistamine_rx"]) == 1
        if has_ns and has_oah:
            med = "both"
        elif has_ns:
            med = "intranasal_steroid"
        elif has_oah:
            med = "oral_antihistamine"
        else:
            med = "none"

        asthma = int(r["asthma_mcq010"]) == 1
        severe = (int(r["hayfever_12m_agq030"]) == 1) or (int(r["wheeze_12m_rdq070"]) == 1)
        patients.append(
            {
                "patient_id": f"NH-{seqn}",
                "age_band": _age_band(float(r["age_years"])),
                "sensitised_to": "|".join(sensitised),
                "current_med_on_file": med,
                "severity": "moderate_severe" if severe else "mild",
                "asthma_flag": "yes" if asthma else "no",
                "language": "en",
            }
        )
    return patients


def load_nhanes_metadata(cache_csv: Path = CACHE_CSV) -> dict[str, dict]:
    """Return laboratory ImmunoCAP IgE (kU/L) and observed Rx drugs keyed by NH-<SEQN>."""
    out: dict[str, dict] = {}
    with cache_csv.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pid = f"NH-{int(r['seqn'])}"
            out[pid] = {
                "seqn": int(r["seqn"]),
                "age_years": int(r["age_years"]),
                "rye_grass_ige_kul": float(r["rye_grass_ige_kul"]),
                "bermuda_grass_ige_kul": float(r["bermuda_grass_ige_kul"]),
                "birch_ige_kul": float(r["birch_ige_kul"]),
                "rx_drugs_seen": [d for d in (r.get("rx_drugs_seen") or "").split("|") if d],
            }
    return out


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fetch", action="store_true", help="Fetch CDC NHANES 2005-2006 .XPT files first")
    args = ap.parse_args(argv)
    if args.fetch:
        m = fetch_nhanes_cohort()
        print(f"Cached {m['n_rows']} NHANES participants to {CACHE_CSV}")
    patients = generate_patients()
    write_patients(patients)
    print(f"Wrote {len(patients)} CDC NHANES patients to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
