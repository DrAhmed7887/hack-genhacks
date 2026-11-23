# PollenPlan: read the trap, not the forecast

**Headline (pre-registered, untouched 2026 season):** on 215 high-pollen days in Madrid, Basel and Zürich (1 Jan – 31 Oct 2026, 1,706 city-days), **yesterday's count from the local pollen trap flagged 164 (76.3%)**. Europe's free CAMS forecast for the same day flagged **70 (32.6%)**. The CSI difference is +0.332, with a 95% CI of 0.203 to 0.457. The model and rules were locked, committed and pushed ([`6ac1700`](https://github.com/DrAhmed7887/hack-genhacks/commit/6ac1700)) before any 2026 file was downloaded ([pre-registration](docs/PREREG_NOWCAST_2026.md)). A fusion model and a NASA-weather variant did not beat the simple rule, so the product ships the simple rule.

**Live demo, no account:** <https://drahmed7887.github.io/hack-genhacks/> · **Reproduce with no keys:**

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

- **Nurse copilot:** the batch is ordered by risk. Patients with an asthma flag and moderate/severe rhinitis come first (9), then asthma flag or moderate/severe (58), then mild (44). The nurse can approve all, hold or edit.
- **Reminder drafts:** an AI model (Qwen 3.8 27B on RWTHgpt, free, run offline on synthetic patients) writes each opening from the prompt in `rules/assistant_prompt.md`. Code (`src/message_guard.py`) accepts an opening only if every word is on a short approved list: the species, the two signed numbers, the medicine class on file, and plain words. Named checks also run for dose, frequency, drug names, symptom words, efficacy claims and links. On any failure it falls back to the signed template, and it appends the signed safety lines itself.
- **Red team:** see the AI section of `CLAIMS.md` for the numbers.
  - The tuning set is 20 attacks × 2 patients, run three times.
  - Run 1 let 2 efficacy claims through ("help prevent asthma attacks").
  - After run 2, an independent review found 25 more bypasses (Unicode lookalikes, "bid", "with food", Spanish drug names). The gate became an allowlist, and those 25 are now in the fixed tests.
  - A separate held-out set of 20 new attacks, never used for tuning, is reported on its own. Earlier runs are in `eval/results/ai_layer_run1.json` and `ai_layer_run2.json`.
- **Clinician Q&A:** answers come only from the morning's facts, and every number is checked against them. Symptom questions get the fixed safety reply and never reach the model (3 of 12 test questions).

Honest note: with only the trap count and the timing line approved, the 111 openings are nearly identical. The model adds little over the template until more personal content is signed (for example a parent voice for children, or Spanish).

## Where the forecast stops

The CAMS European pollen forecast covers 25° W–45° E and 30° N–72° N ([CAMS dataset page](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts)). Open-Meteo states that its pollen data are "Only available in Europe as provided by CAMS European Air Quality forecast" ([docs](https://open-meteo.com/en/docs/air-quality-api)).

We queried it for Egypt ([`docs/evidence/open_meteo_egypt_coverage_2026-11-23.txt`](docs/evidence/open_meteo_egypt_coverage_2026-11-23.txt)). Alexandria and Cairo, inside the box, get pollen values. Asyut (27° N) gets none.

We found no study comparing those Egyptian values with trap counts. The trap-first rule needs only a local trap. In Alexandria, a one-year volumetric trap study (May 2019 – April 2020; Taia & Bassiouni, *Acta Scientific Microbiology* 2022) shows the measurement can be made. **The rule is not yet tested outside Madrid, Basel and Zürich.**

## Limits

- **Scale:** three trap sites, six series and 215 high days in 2026. Madrid olive had only 11 high days.
- **Study type:** this is retrospective scoring of a pre-registered rule, not a prospective trial. No patient outcome was measured.
- **Late onsets:** yesterday's count cannot see the first high day of a burst, so on a sudden rise the rule alerts one day late. Those days count as misses above.
- **Reading delay:** the rule needs yesterday's count by morning.
  - MeteoSwiss publishes files "up to yesterday".
  - Madrid publishes daily from January to June and weekly after that.
  - The two-day-old reading also beat the forecast.
- **Thresholds:** single-centre values (`rules/thresholds.json`, signed 22 Nov 2026).
- **Valencia:** the demo clinic's city has no trap counts in this repo. It is **never scored** and carries no accuracy claim.
- **Data:** the patients are synthetic. Nothing is sent.

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

`make all` re-fetches the open data, rebuilds the synthetic patients, and re-runs the tests and the backtest. The live page is deployed from `demo/` by `.github/workflows/deploy-pages.yml`.

## Earlier work: the 2021–2025 backtest

Before the 2026 test we scored six rules on 2021–2025 (863 high-pollen days). There, our two-day rule (R1) did not beat the CAMS forecast, and neither NASA rule (POWER weather, MODIS NDVI) beat its own control. We report those as negative results and make no claim for them. The page is `demo/backtest.html`, the method is in `docs/DATA_PLAN.md`, and every number is in `CLAIMS.md` sections A–K.

## Data Attribution

- **Modelled pollen**: Open-Meteo Air Quality API (licence CC BY 4.0; free tier for non-commercial use). Required attribution: [Weather data by Open-Meteo.com](https://open-meteo.com/) and "CAMS European air quality forecasts, ENSEMBLE data".
- **Observed Madrid**: Comunidad de Madrid, Histórico de mediciones de polen (Creative Commons Attribution, CC BY)
- **Observed Basel/Zurich**: Source: MeteoSwiss (CC-BY)
- **Synthetic patients**: Seeded generator (20261120)

## License

[See LICENSE file](LICENSE) for repository license.

---

**This demo is static, retrospective, and limited. Not for medical use.**
