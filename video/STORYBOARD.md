# PollenPlan — GenHacks video storyboard (150 s, cap 3:00, 5 s spare)

Follows `Hackathons/WINNING_VIDEO_RECIPE.md` v2 beat sheet. Every number below is
from `eval/results/backtest.json` / `docs/results_table.md` (verified 22 Nov:
863 events, 8,076 city-days, P2 0.416, R1 0.410, Madrid olive 0.136 / grass 0.314,
R2−P2 +2.88 [+2.64, +3.00], R2−C0 −1.55). No medical claims; thresholds shown as
`signed 22 Nov 2026` wherever values appear. No face; voice-over on screen.

1. **0–10 s Claim** (captioned demo screen, frame 1): "Hay-fever patients miss
   the season start. We tested whether a simple alert rule beats the forecast
   itself — on real pollen counts." On-screen: headline card
   `measured_P2_skill_only_no_beats_api_claim`.
2. **10–30 s Product** (live demo page, scrolling): the P2 results table
   (Madrid / Basel / Zurich, olive / grass / birch) and the 28-season onset
   table. 5-word title: "Real counts, real misses."
3. **30–95 s Run** (terminal + demo): `pytest` green (86 tests), then the
   pre-registered backtest path P0/P1/P2/R1/R2/C0 → results table. Madrid
   olive 13.6%, grass 31.4% shown with the "Yes (limits)" badge. 5-word
   titles per scene; waits cut.
4. **95–120 s Proof** (stat card, spoken + on screen): "Pooled API recall 0.416
   over 863 events and 8,076 city-days. Our day rule scored 0.410 — it did not
   beat the API, so the headline is the measured skill." Repeat on end card.
5. **110–135 s Limit** (failing cases on screen): Madrid below 50% both
   species; R2's +2.88-day lead is look-ahead by construction (reads D..D+3,
   archived values may beat a live forecast); thresholds signed 22 Nov 2026;
   retrospective analysis, not a clinical tool. One sentence each, no apology.
6. **135–150 s Close**: stat card (0.416 / 863 / 8,076), demo URL + repo link,
   "try it, no account."

## Voice-over draft (~370 words, one line per scene; timestamps drive cuts)

- "Hay-fever patients miss the season start — treatment starts late."
- "PollenPlan asked a hard question first: does a simple alert rule beat the
  forecast itself? We tested it on three years of real pollen counts."
- "Madrid, Basel, Zurich. Olive, grass, birch. Twenty-eight seasons, every
  onset on screen — including the seasons every rule missed."
- "Eighty-six tests green. Six rules, pre-registered before the run."
- "The verdict: the API's own forecast caught 41.6 percent of high days across
  863 events. Our rule caught 41.0. It did not beat the API."
- "So the headline is the measured skill — and the app is the delivery layer."
- "Madrid stays honest: 13.6 and 31.4 percent, below our own bar. Flagged as
  limits, not hidden."
- "The early alert fires three days sooner — by construction: it reads three
  days of forecast. Archived values may flatter it live."
- "Thresholds are published-panel values, signed off 22 November 2026.
  Retrospective. Not a medical device."
- "Measured skill, open code, open data. Try the demo now."

## Filming notes

- Capture: `capture.mjs` retargeted at local `demo/index.html` (1920×1080) +
  terminal `pytest`/`backtest` run on seeded state. Must run 10× from reset.
- Proof overlays copy numbers from `eval/results/backtest.json` only.
- Sign-off rows 1–11 approved as-is 22 Nov; numbers locked. Remaining for filming: demo URL (needs Pages enable + push).
- Upload Unlisted + private-window check are Ahmed's (recipe step 9).
