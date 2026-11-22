# PollenPlan — GenHacks Director's Cut Storyboard (V2.1 — Post Video-Director Opus Critique)

**Target Audience:** GenHacks judges (Healthcare & Environmental track + overall panel: 25% Impact, 25% Technical Execution, 25% Creativity, 25% Presentation).
**Core Single Takeaway:** They froze the rules first, tested their own rule against the weather API, admitted it lost, locked the claim, and built the deterministic human-approval console that actually matters.
**Most Convincing Artifact:** Live kill-check proof (`R1 = 41.0%` vs `P2 = 41.6%` across `863` high-pollen events and `8,076` city-days) paired with the interactive `Trigger: API forecast (P2)` nurse console (`111` eligible grass reminders drafted, `89` blocked by deterministic code, `0` unapproved sends; Valencia control `0` drafted).
**Runtime target:** ~132–140 s (cap 3:00, ≥40 s spare). Alternating Dark (`#0D1117`) ↔ Light (`#F3F5F7`) scenes, Remotion V2 sequential non-overlapping `<Sequence>` blocks, Blender 5.3 3D grid-vs-trap clip, zoomed live Playwright captures, burned-in hand-verified captions, 6 px bottom progress bar.

## 8-Scene Script & Beat Map (video-director B1–B4 & W1–W6 resolved)

### s1 (0–10s, Dark) — Cold Open: The Question & Stake (B1, W1, Polish)
- **Visual:** Procedural 3D pollen drift background (`flow_pollen_hook.mp4`, labelled `Procedural 3D Visual`) + bold title reveal: `SPRAYS START TOO LATE?`. Bottom source chip: `Already-prescribed nasal sprays · Pre-registered rule test`.
- **Voice-over (24 words, ~140 wpm):** "When should a patient restart an already-prescribed pollen spray? And if our own alert rule fails to beat the forecast, would we say so?"

### s2 (10–30s, Light) — Live Product Working in 15s (Control vs Alert + Trigger Label) (B3, W4)
- **Visual:** Live 1920×1080 Playwright capture of `demo/index.html` (`Clínica Demo Nurse Briefing`), zoom on `Trigger: API forecast (P2)` badge. First shows `Valencia · 2025-05-28` control case (`0` drafted — olive 39.6 < 162, grass 12.9 < 35; labelled `Valencia: model replay only, never scored`). Cursor switches dropdown to `Madrid · 2025-05-18` (Grass 42.1 >= 35), clicks **Approve Batch** → timestamped audit log + `Demo mode: nothing leaves the browser`.
- **Voice-over (40 words):** "Open the live demo with zero keys. On Valencia's May twenty-eighth replay, pollen stays below threshold, so zero reminders fire. Switch to Madrid's May eighteenth grass spike: code drafts one hundred eleven reminders, and a nurse approves every batch."

### s3 (30–44s, Dark) — Why We Tested It: 11 km Grid vs Point Traps (Blender 3D, condensed per W2)
- **Visual:** Held Blender 5.3 3D render (`blender_pollen_grid.mp4`): 11 km CAMS grid cube above rooftop Hirst point traps across Madrid, Basel, and Zürich, with labelled single-centre threshold badges (`Olive 162 · PMID 21277516`, `Grass 35 · PMID 20815307`, `Birch 30 · PMID 24247974`) + T5 caveat pill (`EPOCHAL n=396 found no threshold · No safe or unsafe level exists for every person`) + 3-city counter (`8,076 city-days` · `863 events` · `5 years`).
- **Voice-over (30 words):** "Weather APIs model an eleven-kilometre grid; people breathe near point traps. We checked five years of Open-Meteo forecasts against Madrid, Basel, and Zürich traps — eight thousand seventy-six city-days."

### s4 (44–62s, Light) — Frozen Rules & 28-Season Onset Table (condensed per W2)
- **Visual:** Animated SVG node flow (`Open-Meteo CAMS + Madrid/MeteoSwiss` -> `6 Rules Frozen in DATA_PLAN.md` -> `Day Rules P2 vs R1 · Onset R2 vs P2/C0`) + smooth zoomed scan across the 28-season onset table (showing early green rows + missed grey rows like Madrid grass 2023).
- **Voice-over (31 words):** "Six rules were frozen in the repo before scoring: testing day rules P2 against R1, and pre-peak onset R2 against P2 and climatology across twenty-eight seasons — including missed seasons."

### s5 (62–88s, Dark) — The Proof Moment + 2.5s Silent Hold (B3, W2, W3)
- **Visual:** Kinetic comparison: `API Forecast (P2): 41.6% (359 / 863)` vs `Our Rule (R1): 41.0% (354 / 863)`. Amber lock badge (`#D97706`, distinct from S6 red): `Claim locked: no "beats the API"` + small commit reference `DATA_PLAN.md · 22 Nov 2026`. Then animated transition to `So the app uses P2`.
- **Voice-over (38 words + 2.5s hold after "API."):** "Across eight hundred sixty-three high-pollen events, the API forecast caught forty-one point six percent. Our rule caught forty-one point zero. It did not beat the API. [2.5s hold] So the app uses the API forecast, and our work went into what happens next."

### s6 (88–108s, Light) — Concrete Refusal Row & Draft Message (B2, W6)
- **Visual:** Zoomed UI crop onto ONE blocked row (`med_on_file = none` — blocked) alongside ONE drafted row (`P001` / existing medicine class only), with crimson refusal badge (`#B4441A`) showing `34 no med · 55 unsensitised = 89 blocked`, plus pill: `Thresholds signed 22 Nov 2026 · Not a medical device`.
- **Voice-over (36 words):** "Code filters who gets a draft, and a nurse approves every batch. Thirty-four patients without a medicine on file are blocked automatically. Each draft names only the medicine class already on file. Not a medical device."

### s7 (108–122s, Dark) — Honest Limits (W5)
- **Visual:** Clean 3-line limits card: `1. Even API forecast P2 catches only 13.6% Madrid olive / 31.4% grass (below 50% bar)` · `2. R2 pre-peak lead reflects 3-day look-ahead, not beating climatology` · `3. Valencia: demo replay only, never scored`.
- **Voice-over (29 words):** "Honest limits: even the API forecast catches only thirteen point six percent of Madrid olive spikes. Pre-peak lead reflects look-ahead, not beating climatology. Valencia is never scored."

### s8 (122–135s, Light) — Close on Our Measurement (B4)
- **Visual:** Big stat hero cards belonging to US: `0 Unapproved Sends` · `89 / 200 Blocked by Code` · `Claim Locked (R1 Lost)`. Context footer line: `863 events · 8,076 city-days · 91/91 tests green` + `drahmed7887.github.io/hack-genhacks` + `github.com/DrAhmed7887/hack-genhacks`.
- **Voice-over (25 words):** "Zero unapproved sends, eighty-nine of two hundred filtered out by code, and ninety-one green tests. Open the live PollenPlan demo today — zero setup required."
