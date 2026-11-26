# PollenPlan: read the trap, not the forecast

**Headline (pre-registered, untouched 2026 season):** on 215 high-pollen days in Madrid, Basel and Zürich (1 Jan – 31 Oct 2026, 1,706 city-days), **yesterday's count from the local pollen trap flagged 164 (76.3%)**. Europe's free CAMS forecast for the same day flagged **70 (32.6%)**. The CSI difference is +0.332, with a 95% CI of 0.203 to 0.457. The model and rules were locked, committed and pushed ([`5c45eaf`](https://github.com/DrAhmed7887/hack-genhacks/commit/5c45eaf)) before any 2026 file was downloaded ([pre-registration](docs/PREREG_NOWCAST_2026.md)); the tag [`prereg-lock-2026`](https://github.com/DrAhmed7887/hack-genhacks/tree/prereg-lock-2026) points at it. Commit IDs changed once, on 23 Nov 2026, when the repository history was rewritten to remove two lines of personal notes; the lock files and their timestamps did not change ([pre-registration §9, deviation 3](docs/PREREG_NOWCAST_2026.md)). A fusion model and a NASA-weather variant did not beat the simple rule, so the product ships the simple rule.

**What this comparison is, in plain words:** "trap beats CAMS" compares *yesterday's measured count* (a persistence rule) with *today's forecast*. It is not one forecast beating another. The rule is **untested outside Madrid, Basel and Zürich**.

**Live demo, no account:** <https://drahmed7887.github.io/hack-genhacks/> · **Demo video:** <https://youtu.be/bybQPPLhNfw> · **Reproduce with no keys:**

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest -q && .venv/bin/python eval/verify_claims.py
```

## What it is

An allergy clinic has patients with a known pollen allergy who are already on treatment. Each morning it needs one answer: is today a high-pollen day, so that these patients should use the medicine already on file? PollenPlan answers that from the clinic's own trap reading for yesterday (`src/alert_rule.py`). It then drafts a reminder for every eligible patient: sensitised to that species, with a medicine on file (`src/reminders.py`). A nurse approves the batch. Nothing is sent without that click. Each draft names only the medicine class on file and carries the signed safety line.

## 2026 result (`eval/results/nowcast_2026.json`)

| Rule | High days flagged | Recall | False-alert days | CSI |
|---|---|---|---|---|
| **Yesterday's trap count (P0, shipped)** | **164 / 215** | **76.3%** | 40 | **0.643** |
| Trap count from two days ago (sensitivity) | 151 / 215 | 70.2% | 49 | 0.572 |
| Fusion model F1 (trap + forecast, logistic) | 159 / 215 | 74.0% | 49 | 0.602 |
| F2 = F1 + NASA POWER weather | 181 / 215 | 84.2% | 76 | 0.622 |
| Last year's calendar (C0) | 118 / 215 | 54.9% | 48 | 0.449 |
| CAMS forecast for the day (P2, the API) | 70 / 215 | 32.6% | 10 | 0.311 |

| Hypothesis (pre-registered) | CSI difference | 95% CI | Result |
|---|---|---|---|
| H1: yesterday's trap beats the forecast | +0.332 | 0.203 to 0.457 | **Passed** |
| H2: fusion model beats the forecast | +0.291 | 0.176 to 0.406 | Passed |
| H3: fusion model beats yesterday's trap | −0.041 | −0.117 to 0.028 | **Failed**, so we ship P0 |
| H4: NASA weather improves the fusion model's score | +0.020 | −0.021 to 0.064 | **Failed**, so NASA is not used |
| Sensitivity: two-day-old reading beats the forecast | +0.261 | 0.134 to 0.384 | Passed |

Yesterday's trap beats the forecast in all six city × species series in 2026. It did the same in 2021–2025, flagging 670 of 857 high days against 359 of 863 for the forecast (`eval/results/backtest.json`). The 2026 test was written to check whether that holds on a season we had not seen.

## AI layer: helps the nurse, never decides

- **Nurse copilot:** the batch uses **578 public, de-identified CDC NHANES 2005–2006 survey participants with hay fever** (a stand-in clinic roster, not clinic patients) (`data/patients.csv`, ImmunoCAP IgE ≥ 0.35 kU/L and verified `RXQ_RX_D` prescriptions; 39 eligible for grass). Ordered by risk: asthma flag and moderate/severe rhinitis first (23), then asthma flag or moderate/severe (10), then mild (6).
- **Reminder drafts & live browser model:** Mistral Small 4 119B via RWTHgpt (`eval/ai_layer.py`) drafted openings for all 39 eligible patients (21 passed the strict allowlist gate, 18 caught for phrasing drift and safely replaced by the signed template, 0 unsafe drafts sent). Inside the live web workbench (`#workbench`), judges can also run **`Qwen2.5-0.5B-Instruct`** on-demand in WebGPU/WASM (`~350 MB` first load from jsDelivr CDN, checked by an in-browser JS mirror of `src/message_guard.py`) alongside live `F1`/`F2` logistic weights (`5c45eaf`; locked on Madrid/Basel/Zürich, illustrative out-of-domain elsewhere).
- **Red team:** see `CLAIMS.md` §AI for every number. Tuning set (20 attacks × 2 patients = 40): 18 model rule breaks, 0 reached the nurse. Held-out set (20 unseen attacks × 2 = 40): 24 model rule breaks, **0** reached the nurse. Independent review caught 25 earlier bypasses (now locked in `tests/test_message_guard.py`).
- **Clinician Q&A:** 12 pre-written questions; 3 symptom questions were routed to the fixed safety line without calling the model, and all 9 model answers passed groundedness checks (`0` withheld).

- **Safety guarantee:** `src/message_guard.py` enforces a deterministic allowlist of exact approved clinical tokens (the species, the two signed numbers, the medicine class on file, and plain phrasing) plus named checks for doses, frequencies, drugs, symptom words, efficacy claims, and links, falling back to the signed template on any violation.

## Where the forecast stops

The CAMS European pollen forecast covers 25° W–45° E and 30° N–72° N ([CAMS dataset page](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts)). Open-Meteo states that its pollen data are "Only available in Europe as provided by CAMS European Air Quality forecast" ([docs](https://open-meteo.com/en/docs/air-quality-api)).

We queried it for Egypt ([`docs/evidence/open_meteo_egypt_coverage_2026-11-23.txt`](docs/evidence/open_meteo_egypt_coverage_2026-11-23.txt)). Alexandria and Cairo, inside the box, get pollen values. Asyut (27° N) gets none.

We found no study comparing those Egyptian values with trap counts. The trap-first rule needs only a local trap. In Alexandria, volumetric trap records from 1981–1982 (El-Ghazaly & Fawzy, *Grana* 1988, [`10.1080/00173138809427736`](https://doi.org/10.1080/00173138809427736)) and May 2019–April 2020 (Taia & Bassiouni, *Acta Scientific Microbiology* 2022, [`10.31080/ASMI.2022.05.1088`](https://doi.org/10.31080/ASMI.2022.05.1088)) show the measurement can be made, while a 2026 continent-wide review confirms zero published volumetric traps south of 30° N in North Africa ([`10.1007/s10453-026-09933-w`](https://doi.org/10.1007/s10453-026-09933-w)). **The rule is not yet tested outside Madrid, Basel and Zürich.**

### Related literature

- **Persistence vs. dispersion ensembles:** In the foundational CAMS olive ensemble evaluation (2014, 62 EAN sites, zero in Africa), 1-day persistence beat even the dynamically fused ensemble on continuous RMSE before decaying at day +2, though binary clinical alert CSI/recall was not evaluated ([Sofiev et al., *ACP* 2017](https://doi.org/10.5194/acp-17-12341-2017)). In Australia's AusPollen verification, *curated* local forecasts usually beat persistence ([Emmerson et al., *Atmos Environ X* 2022](https://doi.org/10.1016/j.aeaoa.2022.100183)); our locked 2026 test shows the inverse for un-curated CAMS ENSEMBLE alerts, where even a 2-day-lagged trap reading (`P0_D2`, CSI `0.572`) outperforms CAMS (`0.311`).
- **Digital alert quality & clinical stakes:** Commercial pollen app hit rates often sit near ~50% ([Bastl et al., *JMIR* 2017](https://doi.org/10.2196/jmir.7426)), whereas a 2025 controlled trial (N = 167) found reliable forecast-equipped allergy apps improved medication use and symptom control ([*Allergy* 2025](https://doi.org/10.1111/all.16558)).

## Limits

- **Scale:** three trap sites, six series, and 215 high days in 2026 (Madrid olive had only 11).
- **Study type:** retrospective scoring of a pre-registered rule, not a prospective trial; no patient outcome was measured.
- **Late onsets & reading delay:** yesterday's count alerts one day late on sudden rises (counted as misses above) and requires yesterday's reading by morning (MeteoSwiss publishes "up to yesterday"; Madrid daily Jan–Jun, weekly after; 2-day lag also beat CAMS).
- **Thresholds:** single-centre published values (`rules/thresholds.json`, signed 22 Nov 2026).
- **Valencia:** the demo clinic's city has no trap counts in this repo; it is **never scored** and carries no accuracy claim.
- **Patient cohort:** 578 de-identified public CDC NHANES 2005–2006 hay-fever participants (`SEQN` IDs, zero PHI); US NHANES assays grass and birch IgE (`>= 0.35 kU/L`), not olive IgE, and nothing is sent externally.

![PollenPlan Workflow](docs/flow.svg)

## What's in this repo

| Component | Description |
|-----------|-------------|
| `docs/PREREG_NOWCAST_2026.md` | Pre-registration: hypotheses, features, lock, endpoints, deviations, review |
| `eval/nowcast.py` | Development CV (`nowcast_dev.json`), `--lock`, and the one-shot `--test-2026` scoring |
| `data/fetch_2026.py` | 2026 download; refuses to run without the committed, pushed lock |
| `eval/results/nowcast_lock.json` · `nowcast_2026.json` | Locked models · the 2026 result |
| `src/alert_rule.py` | The shipped rule (yesterday's trap ≥ signed threshold) |
| `src/reminders.py` | Reminder eligibility and message rules (signed 22 Nov 2026) |
| `demo/index.html` | Front page, written by `eval/render_site.py` (`--check` fails if stale) |
| `demo/backtest.html` | The 2021–2025 backtest page and nurse console, written by `eval/render_demo.py` |
| `eval/backtest.py` · `eval/results/backtest.json` | The 2021–2025 pre-registered backtest |
| `CLAIMS.md` · `JUDGES.md` | Every public number with its source, and the judge guide |
| `rules/thresholds.json` | Alert thresholds (signed 22 Nov 2026) |
| `video/v5/` · `video/remotion/src/v5/` | The demo film, built in code from the result files (see `video/v5/README.md`) |

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
make test                       # the test suite
.venv/bin/python eval/verify_claims.py   # every number in CLAIMS.md against the committed results
python -m http.server 8000 -d demo       # then open http://localhost:8000
```

`make all` re-fetches the open data, rebuilds the CDC NHANES participant table from committed extracts, and re-runs the tests and the backtest. The live page is deployed from `demo/` by `.github/workflows/deploy-pages.yml`.

## Earlier work: the 2021–2025 backtest

Before the 2026 test we scored six rules on 2021–2025 (863 high-pollen days). There, our two-day rule (R1) did not beat the CAMS forecast, and neither NASA rule (POWER weather, MODIS NDVI) beat its own control. We report those as negative results and make no claim for them. The page is `demo/backtest.html`, the method is in `docs/DATA_PLAN.md`, and every number is in `CLAIMS.md` sections A–K.

## Data Attribution

- **Modelled pollen**: Open-Meteo Air Quality API (licence CC BY 4.0; free tier for non-commercial use). Required attribution: [Weather data by Open-Meteo.com](https://open-meteo.com/) and "CAMS European air quality forecasts, ENSEMBLE data".
- **Observed Madrid**: Comunidad de Madrid, Histórico de mediciones de polen (Creative Commons Attribution, CC BY)
- **Observed Basel/Zurich**: Source: MeteoSwiss (CC-BY)
- **Patient cohort**: U.S. CDC NCHS NHANES 2005–2006 public-domain files (`DEMO_D`, `AL_IGE_D`, `AGQ_D`, `RDQ_D`, `MCQ_D`, `RXQ_RX_D`)

## License

[See LICENSE file](LICENSE) for repository license.

---

**This demo is static, retrospective, and limited. Not for medical use.**
