# Pre-registration: trap-first nowcast vs the CAMS pollen forecast, untouched 2026 season

**Registered:** 23 Nov 2026, committed before any 2026 pollen or forecast value was downloaded (`data/cache/` held no 2026 row at commit time; check with `git show <this commit>:data/cache`). The git timestamp of this file is the registration time.

**Status:** frozen. Any change after the 2026 data is loaded is reported as a deviation in §9, with the reason.

## 1. Question

On a day D, does a clinic that reads its local pollen trap do better than Europe's free CAMS pollen forecast at flagging a high-pollen day (observed daily mean ≥ the signed threshold), so the nurse can tell already-treated patients to use their medicine?

Background from the pre-registered 2021–2025 backtest (`eval/results/backtest.json`, 863 high-pollen days, Madrid / Basel / Zurich): yesterday's trap count (P0) caught 78.2% of high days (CSI 0.643); the CAMS forecast for the same day (P2) caught 41.6% (CSI 0.392); last year's calendar (C0) 60.0% (CSI 0.457). That comparison was in the registered rule set but not in the registered kill-check, so it is treated here as a hypothesis to replicate, not as a result.

## 2. Hypotheses

- **H1 (replication):** P0 beats P2 on 2026 (pooled CSI difference > 0, 95% CI excludes 0).
- **H2 (fusion):** the locked fusion model F1 beats P2 on 2026 (same test).
- **H3 (fusion vs persistence):** F1 beats P0 on 2026 (same test). If H3 fails, the product ships P0, the simpler rule.
- **H4 (NASA, fair test):** F2 = F1 + prior-day NASA POWER weather beats F1 on 2026. If not, NASA is not used.

## 3. Data

| Role | Years | Source |
|---|---|---|
| Development (model choice, may be looked at freely) | 2021–2025 | the files already in `data/cache/` |
| **Test (loaded once, after the lock in §6)** | **2026 (1 Jan – 31 Oct)** | Comunidad de Madrid, Histórico de mediciones de polen, resource `2026.csv` (station FACF, same as development); MeteoSwiss `ogd-pollen_pbs_d_recent.csv` / `_pzh_` (Basel PBS, Zurich PZH); Open-Meteo air-quality archive (CAMS European ENSEMBLE) for the same coordinates; NASA POWER daily for the same coordinates |

Same cities, species, thresholds (`rules/thresholds.json`, signed 22 Nov 2026: olive 162, grass 35, birch 30 grains/m³, daily mean), season windows (from 2021–2023, unchanged) and loaders as `eval/backtest.py`. Valencia is never scored. A missing trap reading on day D excludes day D; a missing D-1 reading makes P0/F1/F2 undefined that day and the day counts against them (no alert).

## 4. Rules compared on 2026

- **P2** — CAMS forecast for day D ≥ threshold (the API, as in the backtest).
- **P0** — observed trap count on D-1 ≥ threshold.
- **C0** — last year's calendar rule, as in the backtest.
- **F1** — logistic regression per species (pooled over cities, city as a fixed effect), predicting high(D) from exactly these features, all known by the morning of D:
  1. log1p(observed D-1), 2. log1p(observed D-2), 3. log1p(mean observed D-7..D-1), 4. log1p(CAMS forecast for D), 5. log1p(CAMS forecast for D+1), 6. day-of-season scaled 0–1, 7. share of prior development years that were high on this calendar day (climatology).
  Alert when predicted probability ≥ p*, with p* chosen in development (§5).
- **F2** — F1 + NASA POWER D-1 features: T2M_MAX, PRECTOTCORR, ALLSKY_SFC_SW_DWN, WS2M (standardised on development years).

No other model families are tried on 2026.

## 5. Development protocol (2021–2025 only)

- Leave-one-year-out cross-validation: fit on 4 years, score the 5th, rotate.
- Choose L2 strength C from {0.01, 0.1, 1, 10} and p* from {0.2, 0.25, …, 0.7} to maximise pooled CV CSI.
- Then refit F1 (and F2) on all of 2021–2025 with the chosen C and p*.
- Report the CV numbers for P0, P2, C0, F1, F2 as development results (not evidence).

## 6. Lock

Before any 2026 file is downloaded, commit `eval/results/nowcast_lock.json` with: the git SHA of the code, the F1/F2 coefficients, C, p*, feature means/SDs, and a SHA-256 of the scoring script. The 2026 download script refuses to run if that file is absent.

## 7. Endpoints

- **Primary:** pooled CSI on 2026 high days, F1 − P2 and P0 − P2 (H1, H2).
- **Uncertainty:** moving-block bootstrap over days within each city × species season (block 7 days, 10,000 resamples, fixed seed 20261123); 95% percentile CI of the CSI difference. A hypothesis passes only if the CI excludes 0.
- **Secondary:** recall and false-alert days per rule; per-city CSI; P0 with a two-day lag (D-2) as a sensitivity check for late trap publication.

## 8. Kill rule and what gets said

- If H1 fails: no "trap beats forecast" claim; the 2021–2025 P0 result is reported as retrospective only.
- If H2 fails: F1 is not shipped or claimed.
- Whatever the outcome, all four hypotheses and all rules in §4 are reported with their numbers.
- Operational claim ("a clinic can read yesterday's count by the morning") is made per city only with a cited source for that network's publication delay; otherwise the D-2 sensitivity result is the one quoted.

## 9. Deviations

1. **23 Nov 2026, before any 2026 data was loaded: feature 5 (CAMS forecast for D+1) is dropped from F1 and F2.** The archived Open-Meteo value for D+1 is stitched from a later forecast run, so on the morning of D it would not be known in that form: the same look-ahead documented for R2 in the backtest. F1 keeps features 1–4, 6 and 7.

2. **23 Nov 2026, after the first 2026 download, before any scoring: Madrid loader encoding.** Madrid's `2026.csv` is UTF-8 with a byte-order mark; 2021–2025 were ISO-8859-1. The BOM renamed the `captador` column, so the first download kept 0 FACF rows. `data/fetch_2026.py` now re-encodes that one file before the unchanged parser reads it. No 2026 value had been scored; `eval/nowcast.py`, the models, C and p* are unchanged. Because the lock holds the SHA-256 of `fetch_2026.py`, the lock was rewritten with only that hash and `locked_from_git_sha` changed (the F1/F2 blocks are byte-identical; checked by diffing the two lock files).

3. **23 Nov 2026, after scoring: commit IDs changed (no change to the test).** The repository history was rewritten to remove two lines of personal notes from `JUDGES.md` and `DEVPOST_DRAFT.md`. Every commit got a new ID; file contents other than those two lines, and all author and commit timestamps, are unchanged. The lock commit is now `5c45eaf` (was `6ac1700`), committed 2026-11-23 10:54:53 +0100, and the scoring commit is `23bff19` (was `7588b26`). The recorded IDs in `eval/results/nowcast_lock.json` (`locked_from_git_sha`) and `eval/results/nowcast_2026.json` (`lock_commit`) were updated to the new IDs; no other field changed. The tag `prereg-lock-2026` points at `5c45eaf`.

## 10. Lock record

23 Nov 2026, before any 2026 file was downloaded (`data/cache_2026/` did not exist): `eval/results/nowcast_lock.json` written by `eval/nowcast.py --lock`. Chosen on development CV: F1 C = 10, p* = 0.45; F2 C = 10, p* = 0.30. Development CV (optimistic, not evidence), pooled CSI: P2 0.392 · C0 0.407 · P0 0.639 · F1 0.667 · F2 0.673 (`eval/results/nowcast_dev.json`). Implementation notes, fixed at lock: C0 undefined (no prior-year reading) counts as no alert; F1/F2 never alert on a day with no D-1 trap reading; the bootstrap resamples 7-day blocks within each city × species 2026 series (1 Jan–31 Oct). The 2026 download (`data/fetch_2026.py`) and the scoring (`eval/nowcast.py --test-2026`) refuse to run unless this lock is committed, pushed, and both scripts are byte-identical to their locked SHA-256.

**Independent review after scoring (23 Nov 2026, code-reviewer agent): no result-changing bug.** Checked: no feature moves when 2026 values from D onward are perturbed; all six rules share the same 1,706 scored days; P2 equals `backtest.rule_P2` exactly; the bootstrap is paired across rules. Known guard limits, none of which affected this run: the guard checks that the commit first adding the lock is pushed, not the latest lock content (561ce5b is pushed); `eval/backtest.py` and `rules/thresholds.json` are not hashed (neither changed between 5c45eaf and the scoring commit); "scored once" is a convention, since `--test-2026` can be rerun (it was run once, commit 23bff19).
