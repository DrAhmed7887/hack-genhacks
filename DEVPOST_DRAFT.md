# Devpost draft — PollenPlan (GenHacks) — NOT SUBMITTED

Track: Healthcare & Environmental. Deadline: 26 Dec 2026 00:00 ET (submit by 24 Dec, Ahmed in Egypt).

## Tagline

Did a hay-fever alert rule beat the forecast itself? We ran the backtest on
3 years of real pollen counts — and published the honest answer.

## Description

**Problem.** Hay-fever patients start treatment late because nobody tells them
the season began. Alerts exist, but nobody checks whether a simple alert rule
beats the raw forecast it is built on.

**What we did.** PollenPlan pre-registered 6 alert rules (persistence, API
persistence, the API's own forecast P2, a 2-day exposure rule R1, a pre-peak
rule R2, climatology C0) and ran them against observed pollen counts in Madrid,
Basel and Zurich — 863 high-pollen events over 8,076 city-days, 28 seasons.

**Result.** The API's own forecast (P2) caught 41.6% of high days. Our day
rule (R1) caught 41.0% — it did not beat the API. So the headline is the
measured skill, and the app is the delivery layer: a clinic-facing briefing
that compares the day's modelled pollen against published-panel thresholds and
drafts reminders for already-prescribed medicine (a nurse approves every batch).

**Honest limits.** Madrid recall is below our own 50% bar (olive 13.6%, grass
31.4%) — flagged as limits. The pre-peak rule fires ~3 days earlier by
construction (it reads 3 days of forecast; archived values may flatter it
live). Thresholds are single-centre published values, status `signed 22 Nov 2026` (CRITERIA_FOR_SIGNOFF rows 1–4 as proposed).
Retrospective analysis; not a clinical tool; no Valencia accuracy claim
(Valencia has no observed counts and is never scored).

**Try it.** Live demo (no account): [DEMO_URL — needs Pages enable + push].
Video (≤3 min): [VIDEO_URL — needs Ahmed's Unlisted upload].

## Built with

Python, pandas, NumPy, pytest, GitHub Pages. AI tools used (per rules):
Kiro CLI (claude-opus-5.5) for demo/test code, Claude (review), Gemini
(checkpoint review) — every merged change human-reviewed; all numbers from
`eval/results/backtest.json`.

## Data attribution

Weather data by Open-Meteo.com (https://open-meteo.com/); CAMS European air
quality forecasts, ENSEMBLE data. Observed Madrid: Comunidad de Madrid,
Histórico de mediciones de polen (CC BY). Observed Basel/Zurich: Source:
MeteoSwiss (CC-BY). Synthetic patients: seeded generator.

## Pre-submit checklist (owner)

- [x] Signed 22 Nov (rows 1–11 as-is, Ahmed's call)
- [ ] Authorize: commit + push + public repo + Pages (Source = GitHub Actions)
- [ ] Upload video Unlisted, check in private window, paste URL above
- [ ] Paste demo URL above, open logged-out in private window
- [ ] Submit by 24 Dec (48 h buffer, in Egypt)
