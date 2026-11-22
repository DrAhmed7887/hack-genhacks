# Devpost draft — PollenPlan (GenHacks) — NOT SUBMITTED

Track: Healthcare & Environmental. Deadline: 26 Dec 2026 00:00 ET (submit by 24 Dec, Ahmed in Egypt).

## Tagline

Did a hay-fever alert rule beat the forecast itself? We ran the backtest on
5 years of real pollen counts (2021–2025) — and published the honest answer.

## Description

**Problem.** Hay-fever patients may miss the start of the pollen season. Alerts exist, but nobody checks whether a simple alert rule
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

**Try it.** Live demo (no account): https://drahmed7887.github.io/hack-genhacks/.
The interactive Clínica Demo Nurse Briefing & Batch Approval Console is live on
the same GitHub Pages URL: Valencia control drafts 0 reminders, Madrid
grass drafts 111 and blocks 89 by code, the nurse sign-off writes an in-page audit
log, and there are 0 external sends (nothing leaves the browser).
Video: [VIDEO_URL — Remotion V2 + Blender 3D + Figma + ElevenLabs Director's Cut, ~/Downloads/To-Upload/PollenPlan_GenHacks_v2_FINAL_1080p.mp4]

## Built with

Python, pandas, NumPy, pytest, GitHub Pages, Playwright; Figma, Blender 3D,
Remotion, ElevenLabs, FFmpeg. AI workflow: Claude CLI (Sonnet 4.5 / Opus 4.5),
Kiro CLI, Codex/GPT-6.1-Sol (cross-family review), Gemini 4 Hydrogen (evidence
review) — every change human-reviewed against `CRITERIA_FOR_SIGNOFF.md`; all
numbers from `eval/results/backtest.json` and `eval/render_demo.py`.

## Data attribution

Weather data by Open-Meteo.com (https://open-meteo.com/); CAMS European air
quality forecasts, ENSEMBLE data. Observed Madrid: Comunidad de Madrid,
Histórico de mediciones de polen (CC BY). Observed Basel/Zurich: Source:
MeteoSwiss (CC-BY). Synthetic patients: seeded generator.

## Pre-submit checklist (owner)

- [x] Signed 22 Nov (rows 1–11 as-is, Ahmed's call)
- [x] Committed on `main` + pushed + public + Pages live (CI + deploy green 22 Nov)
- [ ] Upload video Unlisted, check in private window, paste URL above
- [ ] Paste demo URL above, open logged-out in private window
- [ ] Submit by 24 Dec (48 h buffer, in Egypt)
