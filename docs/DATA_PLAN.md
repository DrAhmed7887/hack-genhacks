# PollenPlan: DATA_PLAN.md (Phase 0.5, data pack design only; nothing is built or downloaded into a repo)

Written 20 Nov 2026 from `EVIDENCE.md` (rows cited as T1, O3, D1 ...). Thresholds below are **pending Ahmed's sign-off**; code must read them from one config file marked `pending_signoff` until he signs.

## 1. What is real and what is synthetic

| Layer | Real or synthetic | Source | Licence | Used for |
|---|---|---|---|---|
| Observed daily pollen, Madrid | **Real, open** | D1: Comunidad de Madrid Red Palinocam CSVs | CC BY | Ground truth (olive, grass) |
| Observed daily pollen, Basel and Zürich | **Real, open** | D2: MeteoSwiss `ch.meteoschweiz.ogd-pollen` | CC-BY | Ground truth (birch, grass) |
| Modelled pollen, same coordinates | **Real model output** | O1-O2: Open-Meteo Air Quality API (CAMS ENSEMBLE) | CC BY 4.0; free tier non-commercial (O9, O10) | The thing the app alerts on |
| Valencia pollen | Real model output, **no observed archive** (D4) | Open-Meteo | as above | Demo only. No accuracy claim for Valencia. |
| Patient list | **Synthetic, seeded** | `data/make_patients.py` | repo licence chosen at repo creation | The reminder batch the nurse approves |

No patient data of any kind enters the repo, Momen, or any cloud service. Sensitisation shares in the generator are **assumptions**, because the @IT.2020 study says: "this geographical diversity in pollen allergic patients imposes localized clinical guidelines" (PMID 38311961) and gives no Valencia split. They are labelled "illustrative" in the data card and never quoted as epidemiology.

## 2. Backtest design

### 2.1 Unit, cities, period, size
- **Unit:** one city-day for one species (city × species × date). An *event* is a day whose **observed** daily pollen is at or above the signed threshold.
- **Cities (3, all with open observed counts):**
  1. **Madrid**: station FACF Ciudad Universitaria (lat 40.4454, lon -3.7263) primary; mean of FACF, AYTM (Arganzuela), ALER (Salamanca) as sensitivity. Species: olive, grass. Spain, Mediterranean-type season, the closest to the Valencia user.
  2. **Basel** (PBS, lat 47.5618, lon 7.5839). Species: birch, grass.
  3. **Zürich** (PZH, lat 47.3782, lon 8.5656). Species: birch, grass.
  - **Valencia (39.47, -0.38)** is shown in the app and in a replay of Mar-Jun 2025, but is excluded from scoring.
- **Period:** 1 Jan 2021 to 31 Dec 2025. Open-Meteo pollen is non-null from Oct 2020 (O3). Primary analysis uses all five seasons; sensitivity analysis uses 2024-2025 only, because the source of the 2020 to Oct 2023 values is **unverified** (O3).
- **Size (checked, not guessed):** Basel birch observed ≥30 grains/m³ on 18, 27, 26, 26 and 30 days in 2021-2025 (127 events); Basel grass ≥30 on 35, 48, 81, 63, 55 days. Madrid pooled traps 2023-2025: olive ≥162 on 28, 35, 95 trap-days; grass ≥35 on 78, 304, 372 trap-days (D1; single-trap counts to be computed in Phase 1). In-season city-days (Mar-Jul) will be about 150 × 5 years × species × city, well above the n ≥ 100 requirement. **Pre-registered minimum:** at least 100 observed events and at least 1,000 evaluated city-days in total; at least 30 events for any per-city number that is quoted.
- **Alignment:** MeteoSwiss daily = mean 6 UTC to 6 UTC next day (D2); Open-Meteo hourly is aggregated to the same window per station. The Madrid daily file's averaging window is **unverified**; read `descripcion_ampliada_y_diccionario.pdf` (linked on the dataset page) before Phase 1.

### 2.2 Thresholds (from the signed sheet)
Primary evaluation uses the literature thresholds **unchanged** (olive 162, grass 35, birch 30; T1, T2, T4). A secondary run scales the CAMS value with a factor fitted on 2021-2023 and tested on 2024-2025, reported separately and never as the headline. Reason: CAMS is an 11 km grid model and the traps are points, so a systematic offset is expected; the primary run shows the honest, unadjusted skill.

### 2.3 Alert rules compared (all decided before any run; this file is the pre-registration)
| ID | Rule for day D | What it is |
|---|---|---|
| P0 | Observed(D-1) ≥ T | Persistence baseline (what a clinic with a trap sees today) |
| P1 | API(D-1) ≥ T | API persistence (no forecast skill) |
| **P2** | **API(D) ≥ T** | **"The API's own forecast." The kill-check baseline.** The API serves no pollen category (O5), so its own output is the raw value against the clinical threshold. |
| R1 | mean(API(D-1), API(D)) ≥ T | PollenPlan day rule: two-day exposure, motivated by EPOCHAL's lag finding "associations lingered for up to 60 h" (T5). |
| R2 | Onset alert: first day of the season on which max(API(D..D+3)) ≥ T (4-day forecast horizon, O1) | PollenPlan pre-peak alert, the trigger for "start your usual medicine now". |
| C0 | Climatology: day-of-year share of high days in prior years ≥ 0.5 | Calendar-only reminder (no model at all). Tests whether the API adds anything over the calendar. |

Season means: olive Apr-Jun, grass Mar-Jul, birch Mar-Apr, as defined from observed data in the training years (first and last day with ≥ 1 grain/m³ ... exact rule fixed in the script and written to the results JSON).

### 2.4 Metrics (in the user's terms)
- **Day alerts (P0, P1, P2, R1, C0):** recall of observed high days (caught / all), false-alert days per season (alert fatigue), precision, critical success index. Missed high days listed by date, city, species. Bootstrap CI by season blocks (5 seasons, so intervals will be wide; reported as such).
- **Onset (R2 vs C0 and P2):** lead days = observed first high day minus alert day. Count of seasons where the alert fired before the observed onset, and of seasons missed.
- **Outputs:** `eval/results/backtest.json`, `eval/results/misses.csv`, `docs/results_table.md`, all produced by one script, re-run from a fresh clone with the API responses cached in `data/cache/` (no key, no network).

### 2.5 Kill-check (from IDEAS, written as a rule)
1. **Observed counts exist for ≥ 3 cities over ≥ 1 year, openly downloadable today:** passed on 20 Nov (Madrid D1; Basel and Zürich D2). The circularity risk named in the Opus scoring is closed.
2. **"Alert == the API's own forecast":** R1 and R2 are compared with P2. **If R1 does not beat P2 on recall at equal-or-fewer false-alert days, or R2 does not beat both P2 and C0 on lead days, with a season-bootstrap interval that excludes zero, then no "beats the API" claim is made.** The headline becomes the measured P2 skill ("the CAMS-based alert caught X of Y observed high days in Madrid") and the app is described as a delivery and plan layer, not a better predictor.
3. **If P2 recall at the clinical threshold is below 50% in Madrid for both olive and grass:** the app's alert level is lowered by the Phase 1 calibration (section 2.2) only with Ahmed's re-sign-off; otherwise the headline is a "limits" number and the video says so.
4. **Valencia:** never scored. If the video shows Valencia, the caption says "model output, not validated against counts in this city".

### 2.6 Known limits to print under "Limits" in the README
- Trap-versus-grid mismatch (point vs 11 km); olive and grass are heterogeneous inside a city.
- Open-Meteo has no pollen category (O5) and no stated validation of its pollen fields; the docs call it a forecast, not a measurement (O6).
- Thresholds come from single-centre studies, and the newest large panel found none (T5).
- Five seasons per city; pre-Oct-2023 API source unverified (O3).
- Backtest measures alert quality, not reduced symptoms or visits.

## 3. Synthetic patient list (seeded)

`data/make_patients.py`, seed `20261120`, N = 200 patients for one fictional clinic ("Clínica Demo", Valencia). Output `data/patients.csv` plus `DATA_CARD.md`. IDs only (`P001`...), no names, no contact data.

| Field | Values and generation |
|---|---|
| `patient_id` | `P001` to `P200` |
| `age_band` | 6-12, 13-17, 18-39, 40-64, 65+ with shares fixed in the card |
| `sensitised_to` | subset of {olive, grass, birch}; shares **assumed** (e.g. grass 70%, olive 45%, birch 5%) and labelled illustrative (PMID 38311961: grass allergen ranks among the top three sensitisers at every centre; profiles otherwise differ by city) |
| `current_med_on_file` | none / oral antihistamine / intranasal steroid / both, assumed shares |
| `severity` | mild / moderate-severe (assumed) |
| `asthma_flag` | yes/no (assumed 25%); drives the red-flag line in the message |
| `language` | es / en |

**Reminder rules (tested by unit tests, all pending sign-off):**
1. A patient is *eligible* only if sensitised to the alerting species **and** has a medicine on file.
2. The message may name only the medicine **class already on file**. It never adds a drug, a dose or a diagnosis.
3. Every message carries the same fixed safety line (text to be signed), and asthma-flag patients also get the asthma-plan line.
4. A batch is a draft until the nurse presses approve. "Send" writes an `approved_at` row and a log line. **Nothing leaves the system.**

The AI step (Momen AI action) turns structured fields into a short bilingual message; it receives no free text from patients and its output is validated against rules 1-3 by code (code decides, the model explains). The batch count on the approve screen ("12 reminders waiting") is computed from `patients.csv`, not by the model.

## 4. Open-Meteo calls (3 cities plus Valencia, one long call each, cached; far below the free limits in O10)
Calls are made once by the data script and cached; the hackathon repo's reproduce command reads the cache.

`GET https://air-quality-api.open-meteo.com/v1/air-quality?latitude=<lat>&longitude=<lon>&hourly=olive_pollen,grass_pollen,birch_pollen&start_date=2021-01-01&end_date=2025-12-31&timezone=UTC`
The long-span call was accepted in the 20 Nov test (O4). Attribution lines for README and app: "Weather data by Open-Meteo.com" and "CAMS European air quality forecasts, ENSEMBLE data" (O9). Observed data attribution: Comunidad de Madrid (CC BY) and "Source: MeteoSwiss" (D1, D2).

## 5. Licence checklist (done 20 Nov)
| Dataset | Licence found | Where read | Open item |
|---|---|---|---|
| Open-Meteo Air Quality API | CC BY 4.0; free tier non-commercial | licence and terms pages (via subagent, quotes in EVIDENCE O9, O10) | Ahmed's no-monetisation rule already fits |
| Comunidad de Madrid pollen history | Creative Commons Attribution | dataset page text | Exact CC version not stated on the page; cite as "Creative Commons Attribution" |
| MeteoSwiss pollen | CC-BY | STAC collection field | Confirm the attribution string on the MeteoSwiss page when the README is written |
| Euskadi pollen | UNVERIFIED | — | Not needed; do not use unless checked |

## 6. Hours (stated once, from the IDEAS estimate, adjusted for this plan)
Data scripts and cache about 2 h; backtest script, results and misses list about 2 h; synthetic generator and data card about 1 h. These sit inside the 4.5 h build and 2 h eval of IDEAS; Momen build, film and submit are separate. Total estimate unchanged at about 9 h; the backtest has more moving parts than IDEAS assumed, so treat the top of the range as likely.

