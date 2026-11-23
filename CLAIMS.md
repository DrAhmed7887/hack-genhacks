# CLAIMS: every public number and feature claim, with its source

Last verified: 22 Nov 2026, working tree on top of commit `6a9bbb1`. Every number below was read out of `eval/results/backtest.json` (written by `eval/backtest.py`), `rules/thresholds.json`, `data/make_patients.py` or `data/patients.csv`, not typed from memory. The numbers appear in `README.md`, `DEVPOST_DRAFT.md`, `demo/index.html`, `docs/results_table.md` and the video (`video/STORYBOARD.md`, `video/film/script.json`, `video/film/compositions/*.html`).

## How to reproduce from a fresh clone

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python eval/backtest.py              # rewrites eval/results/backtest.json, eval/results/misses.csv, docs/results_table.md from data/cache/ (no network, no key)
.venv/bin/pytest -q                            # all pass. At commit 6a9bbb1: 86 passed; working tree 22 Nov 2026: 112 passed (38 backtest rules, 53 demo, 7 patients, 14 reminders)
.venv/bin/python eval/render_demo.py --check   # exit 0 = the onset table in demo/index.html matches backtest.json
git diff --stat eval/results docs/results_table.md   # empty output = the re-run reproduced the committed results exactly
```

On 22 Nov 2026 the backtest re-run left `git status` clean for `eval/`, `docs/` and `data/`, so the committed results are reproducible.

### Correction, 23 Nov 2026 (independent code review, Codex CLI)

1. **Missing trap readings were scored as "not high" days.** `run_city_species` built `obs_high = obs >= threshold`, which turns a missing reading into `False`, so `day_alert_metrics` (whose docstring already says it counts only days where both sides are defined) scored those days. Now `obs_high` keeps them as NaN. Effect: evaluated city-days 8,076 → 7,373; P2 false-alert days 77 → 53; R1 75 → 51; per-cell precision and CSI change (mostly Madrid grass, which has 310 in-season days with no reading). Recall, the 863 events, every C and D row and the verdict are unchanged.
2. **N1 read same-day temperatures.** Cumulative degree days for an N1 alert on day D included day D's NASA POWER Tmax/Tmin. It now uses values through D-1. Effect: K2 in-sample 80% → 70% in window (MAE 5.1 → 4.8 d); K3 held-out MAE 21.5 → 21.9 d; held-out hit rate unchanged at 30% (calendar 60%).

### One-shot check of every number in the tables below

Run `.venv/bin/python eval/verify_claims.py` from the repo root (offline, no keys). It exits 0 only if every value in sections A–D and K matches the JSON; `tests/test_verify_claims.py` runs it in CI.

Shorthand used in the tables: `BT` = `eval/results/backtest.json`. `cell(city, species)` = the element of `BT.results[]` whose `city` and `species` fields match. `kc` = `BT.kill_check`. Recall values are shown rounded to 3 decimals; the JSON holds the full float.

## A. Scale of the backtest

| # | Claim | Where it appears | Source file and key path | Exact value | Command |
|---|---|---|---|---|---|
| A1 | 863 observed high-pollen events | README, DEVPOST, demo (`#total-events`), video proof scene, `docs/results_table.md` | `BT` → `kill_check.size_check.total_observed_events_P2_denominator` | 863 (= 22 + 70 + 127 + 250 + 140 + 254, the `P2.n_events` of the six cells) | `.venv/bin/python eval/backtest.py` |
| A2 | 7,373 evaluated city-days (corrected 23 Nov 2026 from 8,076, see the correction note) | same | `BT` → `kill_check.size_check.total_evaluated_city_days_P2_denominator` | 7373 (= 1279 + 932 + 1224 + 1315 + 1265 + 1358, the `P2.n_evaluated_days` of the six cells) | same |
| A3 | 28 seasons | DEVPOST, README (onset table), demo onset table, video product scene | `BT` → count of `results[].onset_by_year` entries (Madrid olive 5, Madrid grass 3, Basel birch 5, Basel grass 5, Zurich birch 5, Zurich grass 5). Table rows in `docs/results_table.md` and the demo's `#onset-table-body`. | 28 | `.venv/bin/python eval/render_demo.py --check` and `.venv/bin/pytest -q tests/test_demo.py` (`EXPECTED_ONSET_ROWS = 28`) |
| A4 | Pre-registered size minimum met (>= 100 events, >= 1,000 city-days) | `docs/results_table.md`, demo kill-check | `BT` → `kill_check.size_check.passed`; minimum written in `docs/DATA_PLAN.md` §2.1 | `true` | `.venv/bin/python eval/backtest.py` |
| A5 | 6 rules pre-registered: P0, P1, P2, R1, R2, C0 | README, DEVPOST, video run scene | `BT` → `rules_evaluated`; definitions in `docs/DATA_PLAN.md` §2.3 | `["P0","P1","P2","R1","C0","R2"]` | `.venv/bin/pytest -q tests/test_backtest_rules.py` |
| A6 | Cities scored: Madrid, Basel, Zurich | README, DEVPOST, demo | `BT` → `cities_scored` | `["madrid","basel","zurich"]` | `.venv/bin/python eval/backtest.py` |
| A7 | Backtest period 2021 to 2025; season windows from training years 2021 to 2023 only | demo methodology, `docs/results_table.md` | `BT` → `years`, `training_years`, `season_window_rule` | `[2021..2025]`, `[2021,2022,2023]` | same |

Note on A3: "28 seasons" means 28 city × species × year onset rows. It does not mean 28 distinct years.

## B. Pooled recall: P2 (the API's own forecast) versus R1 (PollenPlan day rule)

| # | Claim | Where it appears | Source file and key path | Exact value | Command |
|---|---|---|---|---|---|
| B1 | P2 recall 0.416 (359 of 863) | README, DEVPOST ("41.6%"), demo (`#p2-recall`), video proof scene ("forty-one point six") | `BT` → `kill_check.check2_beats_api.pooled_p2.{tp, n_events, recall}` | tp 359, n_events 863, recall 0.4159907300115875 | `.venv/bin/python eval/backtest.py` |
| B2 | P2 53 false-alert days (was 77 before the 23 Nov 2026 fix) | `docs/results_table.md` kill-check | `BT` → `kill_check.check2_beats_api.pooled_p2.false_alert_days` | 53 | same |
| B3 | R1 recall 0.410 (354 of 863) | README, DEVPOST ("41.0%"), video proof scene ("forty-one") | `BT` → `kill_check.check2_beats_api.pooled_r1.{tp, n_events, recall}` | tp 354, n_events 863, recall 0.4101969872537659 | same |
| B4 | R1 51 false-alert days (was 75 before the 23 Nov 2026 fix) | `docs/results_table.md` kill-check | `BT` → `kill_check.check2_beats_api.pooled_r1.false_alert_days` | 51 | same |
| B5 | R1 does not beat P2 (verdict "No") | README, DEVPOST, demo (`#r1-vs-p2`), video | `BT` → `kill_check.check2_beats_api.r1_beats_p2_pooled_recall_at_equal_or_fewer_false_alerts` | `false` (0.410 < 0.416 on recall; R1 has 2 fewer false-alert days, but recall is lower) | same |
| B6 | Headline: measured P2 skill only | README, DEVPOST, demo, video claim scene | `BT` → `kill_check.overall_headline`; `kill_check.check2_beats_api.passed_beats_api_claim` | `"measured_P2_skill_only_no_beats_api_claim"`; `false` | same |

The pooled tp and false-alert counts equal the sums of the six per-cell values (P2: 3 + 22 + 70 + 100 + 79 + 85 = 359 true positives and 6 + 0 + 13 + 14 + 11 + 9 = 53 false-alert days; R1: 2 + 21 + 70 + 99 + 82 + 80 = 354 and 5 + 1 + 16 + 13 + 8 + 8 = 51). The verification block checks this.

## C. Per-city P2 recall

All values: `BT` → `results[city, species].day_rules.P2`, fields `recall`, `tp`, `n_events`, `recall_ci95`, `false_alert_days`. Command for all rows: `.venv/bin/python eval/backtest.py`. The same rows appear in `docs/results_table.md` and in the demo's P2 table (`#results-table-body`).

| # | City, species | Threshold used | P2 recall | tp / events | P2 false-alert days | Where it appears |
|---|---|---|---|---|---|---|
| C1 | Madrid, olive | 162 | 0.136 (0.13636...) | 3 / 22 | 6 | README, DEVPOST ("13.6%"), demo (`#madrid-olive-recall`), video run scene |
| C2 | Madrid, grass | 35 | 0.314 (0.31428...) | 22 / 70 | 15 | README, DEVPOST ("31.4%"), demo (`#madrid-grass-recall`), video run scene |
| C3 | Basel, birch | 30 | 0.551 | 70 / 127 | 22 | `docs/results_table.md`, demo table |
| C4 | Basel, grass | 35 | 0.400 | 100 / 250 | 14 | same |
| C5 | Zurich, birch | 30 | 0.564 | 79 / 140 | 11 | same |
| C6 | Zurich, grass | 35 | 0.335 | 85 / 254 | 9 | same |
| C7 | Madrid, both species below 50% ("Yes (limits)") | n/a | olive 0.136, grass 0.314 | n/a | n/a | README, DEVPOST, demo (`#madrid-both-below`), video. Source: `BT` → `kill_check.check3_madrid_p2_recall.{madrid_p2_recall_by_species, both_below_50pct}` (`true`) |

The Madrid confidence intervals are wide: olive `recall_ci95` = [0.000, 0.334], grass = [0.000, 0.364]. These are season-block bootstrap intervals over only 3 to 5 seasons, so no per-city number in table C is a precise estimate.

## D. Onset-lead claims (R2 pre-peak alert)

| # | Claim | Where it appears | Source file and key path | Exact value | Command |
|---|---|---|---|---|---|
| D1 | R2 minus P2 = +2.88 days, 95% CI [+2.64, +3.00] | README, demo (`#r2-vs-p2`), video limit scene ("three days sooner") | `BT` → `kill_check.check2_beats_api.r2_minus_p2_lead_days_bootstrap.{mean_diff, ci95, excludes_zero, n_pairs}` | 2.88, [2.64, 3.0], `true`, 25 pairs | `.venv/bin/python eval/backtest.py` |
| D2 | R2 minus C0 = -1.55 days, 95% CI [-7.75, +6.00]; CI includes zero, so R2 does not beat climatology | README, demo (`#r2-vs-c0`) | `BT` → `kill_check.check2_beats_api.r2_minus_c0_lead_days_bootstrap.{mean_diff, ci95, excludes_zero, n_pairs}` | -1.55, [-7.75, 6.0], `false`, 20 pairs | same |
| D3 | D1 is look-ahead by construction, not extra skill | README, DEVPOST, demo (`#r2-lookahead-note`), video limit scene | Rule R2 = first in-season day with max(API(D..D+3)) >= T, `docs/DATA_PLAN.md` §2.3. P2 reads API(D) only, so R2 can fire up to 3 days earlier and never later. | design fact, no number | `.venv/bin/pytest -q tests/test_backtest_rules.py -k R2` |
| D4 | Per-season lead days (28 rows) | demo `#onset-table-body`, `docs/results_table.md` | `BT` → `results[].onset_by_year[year].{R2_lead_days, P2_lead_days, C0_lead_days}` | see file | `.venv/bin/python eval/render_demo.py --check` |

## E. Signed thresholds and the signature

| # | Claim | Where it appears | Source file and key path | Exact value | Command |
|---|---|---|---|---|---|
| E1 | Alert thresholds olive 162, grass 35, birch 30 grains/m³ (daily mean) | README, demo, DEVPOST, video | `rules/thresholds.json` → `alert.{olive, grass, birch}`; echoed in `BT` → `thresholds_used` | 162, 35, 30 | `.venv/bin/pytest -q tests/test_demo.py` (TestDemoThresholds) |
| E2 | Grass watch level 20 | `rules/thresholds.json` only. It is not used by the backtest or shown as a result. | `rules/thresholds.json` → `watch.grass`; source label `sources.grass_watch` = "T3 Warsaw" | 20 | `.venv/bin/python -c "import json;print(json.load(open('rules/thresholds.json'))['watch'])"` |
| E3 | Status "signed", signed 22 Nov 2026 by Ahmed Zayed | README, DEVPOST, demo, video limit scene ("signed off") | `rules/thresholds.json` → `status`, `signed_by`, `note`; `BT` → `thresholds_status`, `thresholds_note` | `"signed"`, `"Ahmed Zayed"`, note starts "Signed 22 Nov 2026 by Ahmed Zayed: CRITERIA_FOR_SIGNOFF rows 1-4 as proposed (EVIDENCE T1-T4). Single-centre values; retrospective use only." | `.venv/bin/python eval/backtest.py` (the script reads thresholds from this file) |
| E4 | Threshold provenance (single-centre studies) | README limits | `rules/thresholds.json` → `sources` | olive "T1 Ciudad Real n=20", grass "T2 Ciudad Real n=27", birch "T4 Clermont-Ferrand n=61", grass_watch "T3 Warsaw" | read the file |

The signed thresholds are single-centre published values. The newest large panel found none (`docs/DATA_PLAN.md` §2.6). They are for retrospective use, not clinical guidance.

## F. Synthetic patients and reminder rules

| # | Claim | Where it appears | Source file and key path | Exact value | Command |
|---|---|---|---|---|---|
| F1 | N = 200 synthetic patients | `data/DATA_CARD.md`, `docs/DATA_PLAN.md` §3, demo (if shown) | `data/make_patients.py` → `N_PATIENTS`; `data/patients.csv` (header + 200 rows, IDs `P001` to `P200`) | 200 | `.venv/bin/pytest -q tests/test_make_patients.py`; `wc -l data/patients.csv` prints 201 (header + 200) |
| F2 | Seed 20261120, deterministic | `data/DATA_CARD.md` | `data/make_patients.py` → `SEED` | 20261120; same seed gives identical output | `.venv/bin/pytest -q tests/test_make_patients.py` |
| F3 | No real patient data; IDs only, no names or contact data | `data/DATA_CARD.md`, README | `data/patients.csv` header: `patient_id,age_band,sensitised_to,current_med_on_file,severity,asthma_flag,language` | 7 columns, none identifying | `head -1 data/patients.csv` |
| F4 | Sensitisation, medicine, asthma shares are assumptions, not epidemiology | `data/DATA_CARD.md` §5 | `data/DATA_CARD.md` §5 table | grass 70%, olive 45%, birch 5%; asthma 25%, labelled "illustrative" | read the file |
| F5 | Eligible only if sensitised to the alerting species and a medicine is on file | `docs/DATA_PLAN.md` §3 rule 1 | `src/reminders.py` → `is_eligible` | rule | `.venv/bin/pytest -q tests/test_reminders.py` (the `test_rule1_*` tests) |
| F6 | Message names only the medicine class already on file | `docs/DATA_PLAN.md` §3 rule 2 | `src/reminders.py` → `MED_CLASS_LABELS`, `build_message` | rule | same (`test_rule2_*`) |
| F7 | Fixed safety line on every message; asthma line only for asthma-flag patients | `docs/DATA_PLAN.md` §3 rule 3 | `src/reminders.py` → `SAFETY_LINE`, `ASTHMA_LINE`, `build_message` | rule | same (`test_rule3_*`) |
| F8 | Nurse approves every batch; nothing is sent | README disclaimers, DEVPOST, video | `src/reminders.py` has `build_batch` (a draft list) and no send, network or persistence code. | design fact | `grep -nE "requests\|urllib\|smtplib\|socket\|http" src/reminders.py` prints nothing (exit 1) |
| F9 | Demo nurse console: roster 200, "Sent Externally" 0, approve freezes the batch and appends an in-page audit line, nothing leaves the page | `demo/index.html` section `#nurse-console` (`#kpi-roster`, `#kpi-sent`, `#approve-batch-btn`, `#nurse-audit-log`, `#nurse-trigger-rule`). Re-checked 22 Nov 2026: all seven DOM ids are present once each in the final HTML. | draft data in the generated `#nurse-console-data` JSON block written by `eval/render_demo.py`; `kpi-sent` is set to the constant 0 in the page script; vanilla JS over embedded JSON, no network call | roster 200 (see F1), sent 0. Replay drafts/blocked (from `console_data()`): Valencia control 0/200, Madrid grass 111/89, Basel birch 17/183, olive simulation 67/133. Trigger badge `#nurse-trigger-rule` = "Trigger: API forecast (P2)" | `.venv/bin/python eval/render_demo.py --check`; `.venv/bin/pytest -q tests/test_demo.py` |
| F10 | Valencia replay in the console is "model output, demo replay only, never scored against ground truth" | `demo/index.html` `#nurse-caveat` | same rule as `docs/DATA_PLAN.md` §2.5 rule 4 | caption text; `#nurse-caveat` also says "Demo mode: approval is logged in-page; nothing leaves the browser." (re-checked 22 Nov 2026) | read the page |

F8 caveat: the module docstring says the approve step and the `approved_at` log are outside the scope of `src/reminders.py`. "0 external sends" is true because no code path in the repo can send. `#kpi-sent` is a fixed 0, not a measured count of sends. F9 and F10 were re-checked against the final HTML on 22 Nov 2026 (DOM ids present, `render_demo.py --check` exit 0, 91 passed).

## G. Video claims (`video/film/renders/film_2026-11-22_21-15-36.mp4`)

| # | Claim | Source | Command |
|---|---|---|---|
| G1 | Duration 2:16 | `ffprobe` duration 136.3 s | `ffprobe -v error -show_entries format=duration -of csv=p=0 video/film/renders/film_2026-11-22_21-15-36.mp4` |
| G2 | "Eighty-six tests, green" | `pytest -q` summary line. 86 passed at commit `6a9bbb1`, which is the state the video was filmed on. Re-run on 22 Nov 2026 after the final console edits: `pytest -q` = 112 passed (`tests/test_demo.py` grew from 41 to 53 tests with the nurse console, threshold-boundary and NASA telemetry tests; `tests/test_backtest_rules.py` has 38). | `PY=$PWD/.venv/bin/python; git worktree add /tmp/pp 6a9bbb1 && (cd /tmp/pp && $PY -m pytest -q tests)`; run on 22 Nov 2026 gives 86 passed. Remove with `git worktree remove --force /tmp/pp`. |
| G3 | "863 events, 7,373 city-days", "41.6" / "41", "13.6" / "31.4", "+2.88" | rows A1, A2, B1, B3, C1, C2, D1 above | `.venv/bin/python eval/verify_claims.py` |
| G4 | "Six rules, frozen before the run" | row A5. `docs/DATA_PLAN.md` first entered git in `705451d` (22 Nov 2026 18:28 +0100); `eval/backtest.py` first entered in `bb879ed` (19:12 +0100). Git order shows the plan came first. It cannot prove nobody looked at results in between. | `git log --follow --format='%h %ad %s' --date=iso docs/DATA_PLAN.md eval/backtest.py` |
| G5 | "-13.6 LUFS" note: removed from `DEVPOST_DRAFT.md` on 22 Nov 2026 (unverified). Re-measure with `ffmpeg -i <mp4> -af ebur128 -f null -` before any re-use. | see left |

## H. Claims this project does NOT make

| # | Not claimed | Why, with source |
|---|---|---|
| H1 | **No "beats the API" claim.** R1 recall 0.410 is below P2 recall 0.416 and R2 versus C0 has a CI that includes zero. | `kill_check.check2_beats_api.passed_beats_api_claim` = `false`; `docs/DATA_PLAN.md` §2.5 rule 2 |
| H2 | **No Valencia accuracy claim.** Valencia has no observed counts, is never scored, and appears in no result row. Any Valencia view is "model output, not validated against counts in this city". | `BT` → `valencia_scored` = `false`; `docs/DATA_PLAN.md` §2.5 rule 4; `data/cache/open_meteo_valencia_demo.csv` is demo input only |
| H3 | **No patient outcome claim.** The backtest measures alert quality against observed pollen days. It does not measure fewer symptoms, fewer visits or better adherence. The patients are synthetic. | `docs/DATA_PLAN.md` §2.6 last bullet; `data/DATA_CARD.md` §5 |
| H4 | **No ARIA day recommendation.** The project does not recommend when to start treatment under the ARIA guideline and does not name any new drug or dose. Messages repeat a medicine class already on file. Thresholds are signed single-centre research values. | `rules/thresholds.json` → `note` ("retrospective use only"); `src/reminders.py` rule 2 |
| H5 | Not a clinical tool or medical device. | README disclaimers, demo disclaimers |
| H6 | R2's +2.88-day lead is not evidence of better skill. It comes from reading D..D+3 of archived forecast values. A live forecast may do worse. | row D3 |
| H7 | Madrid is not shown as acceptable. Both species are below the project's own 50% bar. | row C7 |
| H8 | Per-city numbers are not precise. Five seasons or fewer per city give wide intervals. | row C1/C2 CIs; `docs/DATA_PLAN.md` §2.6 |
| H9 | Madrid daily averaging window is **unverified** (MeteoSwiss window is verified 6 UTC to 6 UTC). No UTC-alignment claim is made for Madrid. | `data/DATA_CARD.md` §3 |
| H10 | The pre-October-2023 source of Open-Meteo pollen values is unverified. | `docs/DATA_PLAN.md` §2.6 |

## K. NASA POWER + MODIS layer (rules N1, N2)

All values: `BT` → `nasa_evaluation`; reproduce with `.venv/bin/python eval/backtest.py` (offline, reads `data/cache/nasa_*.csv`). Calibration on 2021-2023 only; held-out 2024-2025.

| # | Claim | Source key path | Exact value |
|---|---|---|---|
| K1 | NASA POWER fields (T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN, RH2M, GWETROOT, WS2M) and MODIS MOD13Q1 250 m 16-day NDVI cached for all 4 cities, 2021-2025; NDVI used only from `calendar_date + 16 days` | `data/DATA_CARD.md` §5; `load_nasa_daily` | 4 + 4 cache files |
| K2 | N1 (steroid nasal spray priming 14 days before onset), in-sample fit 2021-2023, paired rows | `nasa_evaluation.N1_pooled.train_2021_2023.paired_common_rows` | n=10, N1 MAE 4.8 d from 14 d, 70% in 7-28 d (in-sample fit, not evidence of skill) |
| K3 | N1 held-out 2024-2025, paired rows | `N1_pooled.heldout_2024_2025.paired_common_rows` | n=10; N1 21.9 d MAE, 30% hit; C0_14d 12.5 d MAE, 60% hit; R2 (Europe's 4-day CAMS pollen forecast) mean lead -9.7 d, 0.0% hit |
| K4 | N2 held-out 2024-2025; N2 on day D uses prior-day (D-1) NASA POWER only | `N2_pooled.heldout_2024_2025` | 394 events; P2 CSI 0.382 → N2 0.434 (+0.052); recall 40.4% → 47.5% (159 → 187); false-alert days 22 → 37; precision 87.8% → 83.5% |
| K5 | N2 pooled 2021-2025 | `N2_pooled.all_evaluable` | 863 events; CSI 0.392 → 0.454; recall 41.6% → 50.9% (359 → 439); false-alert days 53 → 105 |
| K6 | Madrid olive held-out spikes caught | `per_city_species[madrid/olive].N2.splits.heldout_2024_2025` | N2 5/8, P2 0/8 (N2 has 4 false-alert days there) |
| K6b | N2 latency sensitivity: D-3 NASA POWER (MERRA-2 publishes ~2-3 days late), recalibrated | `latency_sensitivity_lag3.N2_pooled` | held-out CSI 0.405, recall 44.4% (175/394), 38 false-alert days; pooled CSI 0.429, recall 48.7%; Madrid olive 5/8 with 2 false-alert days |
| K7 | Legacy kill-check verdict unchanged | `kill_check` | `measured_P2_skill_only_no_beats_api_claim` |
| K8 | No-NASA control, held-out 2024-2025 (API × k every day, no NASA input, k chosen on 2021-2023 by the N2 rule) | `nasa_evaluation.no_nasa_control.heldout_2024_2025` | CSI 0.486; recall 54.6% (215/394); 48 false-alert days; precision 81.7% |
| K9 | NASA adds skill over its control, held-out | `nasa_evaluation.no_nasa_control.nasa_adds_skill_heldout` | `false` |
| K10 | Status of N1 and N2 | `nasa_evaluation.status` | exploratory, added 22 Nov 2026 after the pre-registered backtest |

Not claimed: N1 is a negative result (worse than the calendar rule out-of-sample). N2 is also a negative result: it beats the API forecast (K4) but loses to the no-NASA control (K8, K9), so no NASA contribution is claimed. Madrid olive 5/8 (K6) rests on 8 events.

## I. Wording that does not match the source (open items)

| # | Where | Text | What the source says | Suggested fix |
|---|---|---|---|---|
| I1 | `DEVPOST_DRAFT.md` line 8 (tagline) and `video/STORYBOARD.md` voice-over draft | "3 years of real pollen counts" / "three years of real pollen counts" | `BT` → `years` is 2021 to 2025, five seasons. Only the training window is three years. | **Fixed in `DEVPOST_DRAFT.md` 22 Nov 2026** ("5 years of real pollen counts (2021–2025)"); still open in `video/STORYBOARD.md` line 34 (draft voice-over). Change to "5 years" or "three cities". The shipped video script (`video/film/script.json`) says "real pollen counts" and is not affected. |
| I2 | Video "Eighty-six tests, green" | Hard-coded count | The committed state has 86 tests; the working tree already has 112. Once the nurse-console tests are committed, the video line is wrong. | Either re-cut the line to the final count or change it to "tests green". Re-run `pytest -q` before the final upload. |
| I3 | `DEVPOST_DRAFT.md` "AI tools used" line | Names tools and model versions | Not verifiable from the repo. | Owner confirms before submitting. |
| I4 | Video script and `video/STORYBOARD.md` | "including the seasons every rule missed" | `BT` → `results[].onset_by_year`: only Madrid grass 2023 has no onset from R2, P2 and C0. In Madrid olive 2024 and 2025, R2 and P2 gave none but C0 fired (2024-05-21, 2025-05-21). | Say "seasons the early alert missed", or name Madrid grass 2023. |

## J. Data and attribution claims

| # | Claim | Source | Command |
|---|---|---|---|
| J1 | Observed Madrid: Comunidad de Madrid, CC BY (exact CC version not stated by the publisher) | `data/DATA_CARD.md` §3, `docs/DATA_PLAN.md` §5 | `data/cache/madrid_facf_daily.csv` (2,922 rows) |
| J2 | Observed Basel and Zurich: MeteoSwiss, CC-BY, daily mean 6 UTC to 6 UTC | `data/DATA_CARD.md` §2 | `data/cache/meteoswiss_pbs_daily.csv` (1,574 rows), `data/cache/meteoswiss_pzh_daily.csv` (1,612 rows) |
| J3 | Modelled: Open-Meteo Air Quality API, CAMS ENSEMBLE, CC BY 4.0, free tier non-commercial | `data/DATA_CARD.md` §1 | `data/cache/open_meteo_*.csv` (43,824 hourly rows each) |
| J4 | Never used: the Taia unpublished table, any real patient data | repo rules, `data/DATA_CARD.md` | `ls data/cache` lists the seven files above plus eight NASA files (`nasa_power_*`, `nasa_modis_*`) |
| J6 | NASA POWER (public domain, NASA LaRC POWER Project) and ORNL DAAC MODIS MOD13Q1 (NASA LP DAAC, open data) | `data/DATA_CARD.md` §5 | `data/cache/nasa_*.csv` |
| J5 | The backtest reads only `data/cache/`, no network | `data/DATA_CARD.md` §4 | `.venv/bin/python eval/backtest.py` works offline |
