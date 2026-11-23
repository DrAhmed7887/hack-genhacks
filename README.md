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

## Quick Start

1. Run the backtest to generate results:
   ```bash
   make backtest
   ```

2. Open `demo/index.html` in a browser to see the static demo

3. For a local preview of the Pages site:
   ```bash
   python -m http.server 8000 -d demo
   open http://localhost:8000
   ```

## Setup

### Prerequisites

- Python 3.9+
- `requirements.txt` packages (see below)

### Install Dependencies

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
make all
```

This fetches data, creates synthetic patients, runs tests, and generates backtest results.

### Run Just the Backtest

```bash
make backtest
```

### Run Tests

```bash
make test
```

## Demo Deployment

### GitHub Pages Setup

Pages can publish from a branch only at `/` (root) or `/docs`, not `/demo`. This repo therefore deploys `demo/` with the workflow `.github/workflows/deploy-pages.yml` (`actions/upload-pages-artifact` + `actions/deploy-pages`).

1. Go to your repository's **Settings** > **Pages**
2. Under **Build and deployment** > **Source**, select **GitHub Actions**
3. Push to `main` (or run the `deploy-pages` workflow manually from the **Actions** tab)

Your demo will be available at `https://<username>.github.io/<repo>/`

### Custom Domain (Optional)

Set the custom domain under **Settings** > **Pages** > **Custom domain**, then configure DNS. With an Actions deployment, a `CNAME` file in `demo/` is not used.

## Methodology

### Alert Rules Evaluated

| ID | Rule | Description |
|----|------|-------------|
| P0 | Observed(D-1) ≥ T | Persistence baseline |
| P1 | API(D-1) ≥ T | API persistence |
| **P2** | **API(D) ≥ T** | **API's own forecast (kill-check baseline)** |
| R1 | mean(API(D-1), API(D)) ≥ T | Two-day exposure (PollenPlan day rule) |
| R2 | First in-season day where max(API(D..D+3)) ≥ T | Pre-peak alert |
| C0 | Climatology: prior year share of high days ≥ 0.5 | Calendar-only reminder |

### Cities Scored

| City | Species | Source |
|------|---------|--------|
| Madrid | olive, grass | Comunidad de Madrid (FACF) |
| Basel | birch, grass | MeteoSwiss (PBS) |
| Zurich | birch, grass | MeteoSwiss (PZH) |

**Valencia** (the app's target city) has no observed ground truth in this repo, is **never scored**, and is excluded from all evaluation; the Clínica Demo console uses a Valencia 2025 CAMS control replay (labelled model output only, never scored).

### Season Definition

Season windows are derived from training years (2021-2023) only:
- First/last day with ≥1 grain/m³ observed pollen
- Clipped to named months (olive Apr-Jun, grass Mar-Jul, birch Mar-Apr)
- 7-day centred rolling mean applied to training-year averages

### Kill-Check (DATA_PLAN 2.5)

1. Observed counts exist for ≥3 cities over ≥1 year
2. **"Alert == the API's own forecast"**: R1 and R2 must beat P2
   - R1 vs P2: recall at equal-or-fewer false-alert days
   - R2 vs P2: mean lead days with bootstrap CI excluding zero
   - R2 vs C0: mean lead days with bootstrap CI excluding zero
3. If P2 recall <50% in Madrid for both species, alert level only lowered with re-sign-off
4. Valencia never scored

**2021–2025 kill-check verdict (R1 only)**: R1 did not beat P2 on pooled recall, so no claim is made for R1. The current headline is the separate, pre-registered 2026 test of P0 (top of this README).

## Results Summary

### Overall Headline

```
measured_P2_skill_only_no_beats_api_claim
```

### Key Metrics

| Metric | Value |
|--------|-------|
| Total events (P2 denominator) | 863 |
| Evaluated city-days | 7373 |
| Pooled P2 recall | 0.416 |
| Pooled R1 recall | 0.410 |
| Madrid olive P2 recall | 0.136 |
| Madrid grass P2 recall | 0.314 |
| R2 vs P2 lead days | +2.88 days (95% CI [+2.64, +3.00]) |
| R2 vs P2 timing | R2 uses API values for D..D+3: fires up to 3 days before P2 by construction, never after (look-ahead, not extra skill; archived D+1..D+3 may beat a live forecast) |
| R2 vs C0 lead days | -1.55 days (95% CI [-7.75, +6.00]) |
| R2 beats C0 (lead days CI excludes zero) | No |

### Madrid Performance

| Species | P2 Recall |
|---------|-----------|
| Olive | 13.6% (below 50% threshold) |
| Grass | 31.4% (below 50% threshold) |

Both Madrid species have P2 recall below 50% → **limits** number per kill-check check3.

## NASA Earth-Observation Layer (POWER + MODIS NDVI)

**Why NASA.** We added NASA POWER (MERRA-2 / CERES: daily `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`, `RH2M`, `GWETROOT`, `WS2M`) and NASA ORNL MODIS `MOD13Q1` (250 m, 16-day `NDVI`, lagged +16 days so a composite is only used once its 16-day window has closed, not counting publication delay; `GWETROOT` and NDVI are contextual telemetry, not N1/N2 decision inputs), cached offline for all four cities (2021-2025). Two extra rules were evaluated, both calibrated on 2021-2023 only and scored on held-out 2024-2025. **They are exploratory:** they were added on 22 Nov 2026, after the pre-registered backtest. All numbers come from `eval/results/backtest.json["nasa_evaluation"]`.

**Bottom line: neither NASA rule beat its control.** N1 lost to a calendar rule; N2's gain over the API forecast came from lowering the alert level, and a no-NASA control that does only that scored higher.

**N1 (negative finding): priming a steroid nasal spray (intranasal corticosteroid) 14 days before onset.** N1 is naive thermal accumulation from 1 January. On the 10 paired held-out rows (2024-2025), R2 (Europe's 4-day CAMS pollen forecast, read as D..D+3) fired 9.7 days *after* onset (0.0% in the 7-28 day window). N1 scored 70% in the 7-28 day window in-sample (2021-2023, 4.8 days MAE from 14 days) but only 30% held-out (2024-2025: 21.9 days MAE) versus 12.5 days MAE and 60% hit for the prior-year calendar rule `C0_14d`. Warm February/March springs triggered N1 early, before olive and grass flowering. N1 is not a usable improvement.

**N2 (negative finding against its control): prior-day (D-1) NASA solar/warm/dry scaling on top of CAMS.** N2 on day D reads only NASA POWER values from D-1 (solar >= train median, Tmax >= train median, precip < 2.0 mm); no same-day NASA value is used (`tests/test_backtest_rules.py` proves invariance). On held-out 2024-2025 (394 observed spikes), CSI rose from 0.382 (P2) to 0.434 (N2, +0.052) and recall from 40.4% to 47.5% (159 to 187 events, including 5 of 8 held-out Madrid olive spikes versus 0 of 8 for P2). The cost is more false-alert days: 22 to 37, precision 87.8% to 83.5%. Pooled 2021-2025 (863 events): CSI 0.392 to 0.454, recall 41.6% to 50.9% (359 to 439), false-alert days 53 to 105. Latency check: NASA POWER (MERRA-2) publishes about 2-3 days late; re-calibrated and re-scored with D-3 predictors, held-out CSI is 0.405, recall 44.4% (175 of 394), 38 false-alert days.

**No-NASA control (added in the 23 Nov 2026 review).** The same scaling applied on every day, with no NASA input and the same training rule (`nasa_evaluation.no_nasa_control`), scored held-out CSI 0.486, recall 54.6% (215 of 394), 48 false-alert days, precision 81.7%; Madrid olive 2 of 8. So the NASA weather condition did not add skill (`nasa_adds_skill_heldout: false`): the N2 gain over P2 is the effect of a lower alert level. The Madrid olive 5-of-8 rests on 8 events and is not a finding.

The legacy kill-check verdict is unchanged (`measured_P2_skill_only_no_beats_api_claim`, because R1 lost to P2). N2 is judged on its own 2021-2023 versus 2024-2025 holdout ledger. Retrospective; two held-out years only.

## Limits & Known Issues

1. **Trap-versus-grid mismatch**: Point measurements vs 11 km grid model
2. **Open-Meteo has no pollen category**: No stated validation; docs call it a forecast, not measurement
3. **Thresholds from single-centre studies**: The newest large panel found no consensus thresholds (T5, DATA_PLAN 2.6)
4. **Only 5 seasons**: Limited statistical power; intervals will be wide
5. **Pre-Oct-2023 API source unverified**: See DATA_PLAN section 2.1
6. **Measures alert quality only**: No data on reduced symptoms, visits, or patient outcomes
7. **Madrid P2 recall below 50%**: Both olive (13.6%) and grass (31.4%) fail this threshold

## Data Attribution

- **Modelled pollen**: Open-Meteo Air Quality API (licence CC BY 4.0; free tier for non-commercial use). Required attribution: [Weather data by Open-Meteo.com](https://open-meteo.com/) and "CAMS European air quality forecasts, ENSEMBLE data".
- **Observed Madrid**: Comunidad de Madrid, Histórico de mediciones de polen (Creative Commons Attribution, CC BY)
- **Observed Basel/Zurich**: Source: MeteoSwiss (CC-BY)
- **Synthetic patients**: Seeded generator (20261120)

## License

[See LICENSE file](LICENSE) for repository license.

---

**This demo is static, retrospective, and limited. Not for medical use.**
