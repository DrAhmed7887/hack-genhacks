# PollenPlan: guide for judges

GenHacks (Devpost), track **Healthcare & Environmental**. Live demo, no account: <https://drahmed7887.github.io/hack-genhacks/>. Code: <https://github.com/DrAhmed7887/hack-genhacks>.

**What it is.** A pre-registered backtest of hay-fever alert rules against real observed pollen counts (Madrid, Basel, Zurich), plus a static demo that turns the result into a nurse-approved reminder batch for a synthetic clinic. **What the result says.** The API's own forecast (rule P2) caught 0.416 of 863 observed high days. Our day rule (R1) caught 0.410. R1 did not beat the API, so the headline is the measured skill, not a better predictor. Every number is traced to its source in [`CLAIMS.md`](CLAIMS.md).

The four criteria below are the verbatim list from the official page (`https://genhacks-open.devpost.com/`, read 19 Nov 2026 and recorded in the project SPEC): four criteria, 25% each.

## 1. Impact (25%): "how well does the project solve a real problem for the people or area its track covers"

| Evidence | Where |
|---|---|
| Problem: hay-fever patients start treatment late because nobody tells them the season began. The first question was whether a simple alert rule beats the forecast it is built on. | `DEVPOST_DRAFT.md` (Problem), `docs/DATA_PLAN.md` §2.5 |
| Scale of the test: 863 observed high-pollen events, 7,373 city-days, 28 city-species-year seasons, six pre-registered rules | `eval/results/backtest.json` → `kill_check.size_check`; `docs/results_table.md` |
| The answer is published even though it is negative: no "beats the API" claim | `kill_check.overall_headline` = `measured_P2_skill_only_no_beats_api_claim`; `README.md` disclaimers |
| Delivery layer: a nurse reviews a draft batch of reminders that name only a medicine class the patient already has on file. Nothing is sent. | `demo/index.html` (`#nurse-console`), `src/reminders.py`, `tests/test_reminders.py` (14 tests) |
| Per-city skill, including the weak cities, so a clinic can see where the alert is unreliable | `docs/results_table.md`; demo results table |

**Honest limits**
- The backtest measures alert quality against observed pollen days. It does not measure fewer symptoms, visits or better adherence. No patient outcome claim.
- Madrid P2 recall is 0.136 for olive (3 of 22) and 0.314 for grass (22 of 70), below the project's own 50% bar. The target user is a Spanish clinic, and the city closest to it is the weakest result.
- Valencia, the demo clinic's city, has no observed counts. It is never scored and carries no accuracy claim.
- The patients are synthetic (N = 200, seed 20261120). Sensitisation and medicine shares are assumptions (`data/DATA_CARD.md` §5). The repo holds no clinician or patient evaluation.
- Thresholds (olive 162, grass 35, birch 30 grains/m³) are single-centre published values, signed 22 Nov 2026 for retrospective use. Not a clinical tool.

## 2. Technical execution (25%): "does it work, and how much did the team build during the hackathon"

| Evidence | Where |
|---|---|
| Reproduces from a fresh clone, offline: `.venv/bin/python eval/backtest.py` rewrites `eval/results/backtest.json`, `eval/results/misses.csv` and `docs/results_table.md` from `data/cache/`. On 22 Nov 2026 the re-run left `git status` clean for those files. | `eval/backtest.py` (1,285 lines), `data/cache/` (15 files, 5.2 MB) |
| Tests: `.venv/bin/pytest -q` → all pass. At commit `6a9bbb1`: 86 passed (24 hand-worked rule tests, 41 demo-vs-JSON tests, 7 patient-generator tests, 14 reminder-rule tests). The working tree has more tests (112 passed on 22 Nov 2026: 38 backtest rules, 53 demo, 7 patients, 14 reminders). | `tests/` |
| The demo's onset table is generated from the JSON, and a check fails if it is stale: `.venv/bin/python eval/render_demo.py --check` | `eval/render_demo.py` |
| Every public number is mapped to a JSON key and a command; one script verifies them all | `CLAIMS.md` |
| CI on every push (tests + backtest + gitleaks) and auto-deploy to GitHub Pages | `.github/workflows/ci.yml`, `.github/workflows/deploy-pages.yml`; last runs on `main` succeeded (22 Nov 2026) |
| Pre-registration: the rules and kill-check were written before the backtest script entered git (`docs/DATA_PLAN.md` in `705451d`, 18:28; `eval/backtest.py` in `bb879ed`, 19:12, both 22 Nov 2026) | `git log --follow docs/DATA_PLAN.md eval/backtest.py` |
| Data provenance: column meanings and the MeteoSwiss 6 UTC to 6 UTC window were read from the publishers' own dictionaries | `data/DATA_CARD.md` |
| Built during the hackathon: the first commit is 22 Nov 2026, after the 1 Nov start | `git log --reverse` (5 commits at the time of writing) |
| NASA layer: POWER weather/soil (MERRA-2 / CERES) and MODIS MOD13Q1 NDVI (lagged +16 days, strictly causal) cached offline for all 4 cities; rules N1 and N2 calibrated on 2021-2023 only, scored on 2024-2025. Reported with the negative result: N1 (steroid nasal spray priming by thermal accumulation) 21.9 d MAE and 30% hit held-out (70% in-sample) versus 12.5 d and 60% for the prior-year calendar. N2 (prior-day D-1 NASA, no same-day value) raised held-out CSI 0.382 → 0.434 over the API forecast, but a no-NASA control (same scaling every day) scored 0.486, so NASA added no skill; both rules are exploratory, added after the pre-registered backtest | `eval/results/backtest.json["nasa_evaluation"]`, `CLAIMS.md` section K |
| Guard rails: the thresholds file is read-only to the build agents; a pre-tool-use hook configured for the build agent blocks writes to `rules/`, `CLAIMS.md` and `.kiro/` | `rules/thresholds.json`, `scripts/hooks/guard_signed.py`, `.kiro/agents/genhacks-builder.json` |

**Honest limits**
- The N2 gain rests on two held-out years and costs extra false alerts (precision 87.8% → 83.5%); N1 fell from 70% in-sample to 30% held-out (7-28 d window). The kill-check verdict is unchanged: no "beats the API" claim.
- Static GitHub Pages only. There is no server, no database and no real send path. The approve button writes an in-page audit line and nothing else.
- Five seasons per city or fewer, so the confidence intervals are wide (Madrid olive recall CI [0.000, 0.334]).
- R2's +2.88-day lead over P2 (95% CI [+2.64, +3.00]) comes from reading three days of archived forecast, so it is look-ahead by construction. R2 minus climatology is -1.55 days, CI [-7.75, +6.00], which includes zero.
- The Madrid daily averaging window is unverified (`data/DATA_CARD.md` §3). The pre-October-2023 source of Open-Meteo pollen values is unverified.
- CAMS is an 11 km grid model and the traps are points. The unadjusted mismatch is part of the measured result.
- `eval/backtest.py` emits a pandas `FutureWarning` (line ~540). It does not change results and the dependencies are pinned.
- Code was written with AI assistance (listed in `DEVPOST_DRAFT.md`). Every change was human-reviewed, per the draft.

## 3. Creativity (25%)

| Evidence | Where |
|---|---|
| A negative-result-first project: the kill-check is written as a rule before the run, and the outcome is recorded as `kill_check.overall_headline` and the public wording follows it | `docs/DATA_PLAN.md` §2.5; `eval/results/backtest.json` |
| The video and demo show the failures: every one of the 28 seasons is in the onset table, including seasons the early alert missed (R2 and P2 gave no alert in Madrid olive 2024 and 2025, where climatology C0 did fire; R2, P2 and C0 all gave none in Madrid grass 2023) | `demo/index.html` `#onset-table-body`; `docs/results_table.md`; `eval/results/misses.csv` (2,018 missed-day rows) |
| Code decides, a model would only explain: eligibility and message content are deterministic rules with tests, so the nurse screen shows what the code guard filtered out and why | `src/reminders.py`; demo `#nurse-filtered-panel` |
| Climatology (C0) and persistence (P0, P1) baselines test whether the API adds anything over the calendar | `docs/DATA_PLAN.md` §2.3 |

**Honest limits**
- The ideas used (persistence and climatology baselines, bootstrap intervals, a human-approval step) are standard. The novelty is in publishing the negative result and wiring it to the product wording, not in a new model.
- No new forecasting model was built. The project does not claim one.

## 4. Presentation (25%): "demo video and project page"

| Evidence | Where |
|---|---|
| Live project page, loads logged-out, HTTP 200 on 22 Nov 2026: <https://drahmed7887.github.io/hack-genhacks/> | `demo/index.html` |
| Video V4 (about 2:43, under the 3:00 cap): real captures of the live page, the 863 observed events as dot grids, the 10 held-out NASA seasons, and the live page's own NASA verdict. Uploaded as an unlisted YouTube or Vimeo link: **not done yet**. | `video/remotion/` (Remotion; `scripts/render_chunks.sh`); narration `video/SCRIPT_V4.md`; claims `CLAIMS.md` §G |
| Devpost text with problem, result, limits, built-with, attribution | `DEVPOST_DRAFT.md` |
| Workflow diagram | `docs/flow.svg` |
| Required attributions are on the page and in the README (Open-Meteo, CAMS, Comunidad de Madrid, MeteoSwiss) | README "Data Attribution"; demo attribution section (`#attribution-modelled`, `#attribution-observed`) |
| Limits are printed on the page, not hidden in the repo | `demo/index.html` "Limits" list; `README.md` |

**Honest limits**
- The video URL is not yet in `DEVPOST_DRAFT.md` (placeholder `[VIDEO_URL — … pending Ahmed's Unlisted upload]`). Nothing is submitted.
- The live site served on 22 Nov 2026 does not yet contain the nurse console (`#nurse-console` is absent from the deployed HTML). It is in the working tree, uncommitted, and appears on the live URL after the next push to `main`.

## Review backlog (dated 22 Nov 2026)

| # | Item | Found | Owner | Status | Where |
|---|---|---|---|---|---|
| 1 | "3 years of real pollen counts" is wrong; data are 2021 to 2025 (5 years, 3 cities). Fixed in `DEVPOST_DRAFT.md` 22 Nov 2026; `video/STORYBOARD.md` line 34 still says three years | 22 Nov 2026 | Ahmed | Done (Devpost); storyboard line open | `DEVPOST_DRAFT.md` line 8, `video/STORYBOARD.md`; `CLAIMS.md` I1 |
| 2 | Video line "Eighty-six tests" becomes stale when the nurse-console tests are committed (112 passed, re-run 22 Nov 2026) | 22 Nov 2026 | Ahmed | Done 23 Nov 2026 (V4 says 117) | `video/film/script.json` (scene `run`), `video/film/compositions/run.html`; `CLAIMS.md` I2 |
| 3 | Upload the video Unlisted, check it in a private window, paste the URL | 22 Nov 2026 | Ahmed | Open | `DEVPOST_DRAFT.md` checklist |
| 4 | Re-check `CLAIMS.md` F9 and F10 against the final HTML: done 22 Nov 2026 (all DOM ids present, `--check` exit 0, 91 passed). **Still open:** push the nurse console so the live URL matches the local demo (live site not updated until the push) | 22 Nov 2026 | Ahmed (push) | F9/F10 re-check Done; push Open | `demo/index.html`, `eval/render_demo.py`, `tests/test_demo.py` |
| 5 | Re-record or re-check the video if the demo page changes visibly (the film captures the page) | 22 Nov 2026 | Ahmed | Open | `video/capture_shots.mjs` |
| 6 | Untracked files in `video/film/` come from a different project ("Clocked": `REVIEW.md`, `SPEC.md`, `assets/site/`, and likely `AGENTS.md`, `CLAUDE.md`). Do not commit them blind. | 22 Nov 2026 | Ahmed | Open | `git status --short video/film` |
| 7 | `DEVPOST_DRAFT.md` "-13.6 LUFS" note was unverified; removed 22 Nov 2026 | 22 Nov 2026 | Ahmed | Done | `CLAIMS.md` G5 |
| 7b | Video line "seasons every rule missed" is true only for Madrid grass 2023 (C0 fired in Madrid olive 2024 and 2025) | 22 Nov 2026 | Ahmed | Done 23 Nov 2026 (V4 narration does not use it) | `video/film/script.json` scene `product`; `CLAIMS.md` I4 |
| 8 | Confirm the "AI tools used" line (tool names and model versions) before submitting | 22 Nov 2026 | Ahmed | Open | `DEVPOST_DRAFT.md` |
| 9 | Madrid daily averaging window unverified (read `descripcion_ampliada_y_diccionario.pdf` for any UTC window) | 20 Nov 2026 | Open question | Open | `data/DATA_CARD.md` §3 |
| 10 | pandas `FutureWarning` in `eval/backtest.py` (~line 540). Results unaffected; fix only with a fresh backtest re-run and diff | 22 Nov 2026 | Low | Open | `eval/backtest.py` |
| 12 | Thresholds signed 22 Nov 2026 and kill-check run | 22 Nov 2026 | Ahmed | Done | `rules/thresholds.json`, `eval/results/backtest.json` |
