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

**NASA layer.** We added NASA POWER (MERRA-2 / CERES: daily T2M, T2M_MAX,
T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN, RH2M, GWETROOT, WS2M) and NASA ORNL
MODIS MOD13Q1 (250 m 16-day NDVI, lagged +16 days for strict causality),
cached offline for all four cities (2021–2025), and tested two extra rules
calibrated on 2021–2023 only. *Negative finding (N1, priming a steroid nasal
spray, an intranasal corticosteroid, 14 days before onset):* thermal
accumulation hit the 7–28 d window 80% in-sample (5.1 d MAE from 14 d) but only
30% on held-out 2024–2025 (n=10 paired rows; 21.5 d MAE), versus 12.5 d
and 60% for the prior-year calendar rule; R2 (Europe's 4-day CAMS pollen forecast) fired
9.7 d after onset (0.0% hit). Warm Feb/Mar springs triggered it before
flowering. *Second negative finding (N2, prior-day D-1 NASA solar/warm/dry
scaling + CAMS, no same-day NASA value):* on held-out 2024–2025 (394 observed
spikes) N2 raised CSI from 0.382 to 0.434 over the API forecast, but a
no-NASA control that scales the forecast the same way on every day scored
0.486 (recall 54.6% vs 47.5%, 48 vs 37 false-alert days). The gain came from
lowering the alert level, not from NASA data. Both rules are exploratory:
they were added after the pre-registered backtest. The kill-check verdict
stays `measured_P2_skill_only_no_beats_api_claim`.

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
