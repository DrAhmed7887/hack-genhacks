# Devpost draft: PollenPlan (GenHacks), NOT SUBMITTED

Track: Healthcare & Environmental. Deadline: 26 Dec 2026 06:00 Valencia (submit by 24 Dec). Every number here is in `CLAIMS.md` §N and is checked by `eval/verify_claims.py`.

## Tagline

Read the trap, not the forecast. On a pollen season we had never seen, yesterday's trap count caught 164 of 215 high-pollen days. Europe's free forecast caught 70.

## Description

**Problem.** An allergy clinic has patients with a known pollen allergy who are already on treatment. On a high-pollen day it wants to remind them to use the medicine they already have. The obvious input is a free pollen forecast. We asked whether that forecast actually flags the high days a local trap measures.

**What we did.**
- Scored six alert rules against real trap counts (Madrid, Basel, Zürich, 2021–2025; 863 high days).
- Found that the clinic's own trap reading from yesterday beat the CAMS forecast for the same day, 670 of 857 against 359 of 863.
- Pre-registered a test on the untouched 2026 season instead of claiming that result. We wrote four hypotheses, built a fusion model and a NASA-weather variant, and locked and pushed everything before downloading a single 2026 file.

**Result (1 Jan – 31 Oct 2026, 215 high days, 1,706 city-days).**
- Yesterday's trap: 164 of 215 (76.3%), 40 false-alert days.
- CAMS forecast: 70 of 215 (32.6%), 10 false-alert days.
- CSI +0.332, 95% CI 0.203 to 0.457, the trap winning in all six city × species series.
- Our own fusion model did not beat the simple rule (H3 failed), and NASA POWER weather did not improve its score (H4 failed). So we ship the simple rule and report both failures.
- A two-day-old reading still beats the forecast, which matters where trap data publish late.

**Product.**
- Each morning the clinic's trap reading for yesterday goes into `src/alert_rule.py`.
- `src/reminders.py` drafts a reminder only for patients sensitised to that species who already have a medicine on file. Each draft names only that medicine class and carries a fixed, signed safety line.
- A nurse approves the batch. Nothing is sent without that click.
- The demo replays a real morning: Madrid, 5 May 2026. Yesterday's grass count was 104, the forecast said 19.5, and the trap measured 79. The demo drafts 111 reminders for 200 synthetic patients.

**AI layer, with the AI kept on a leash.**
- A nurse copilot orders the batch by risk: asthma flag plus moderate/severe rhinitis first.
- An AI model (Qwen on RWTHgpt, free, offline, synthetic patients) drafts each reminder opening. Code rejects any dose, frequency, drug name, symptom words, efficacy claim, link or unexplained number, and it appends the signed safety lines itself.
- We attacked it 40 times: the model broke a rule 12 times, and none of those drafts reached the nurse. The first run let 2 efficacy claims through. We fixed the rule, added both sentences to the tests and re-ran.
- Clinician Q&A answers only from that morning's facts. Symptom questions never reach the model.

**Where next (a hypothesis, not a result).** The CAMS pollen forecast is built for Europe, with a map that stops at 30° N. We queried it for Egypt: Alexandria and Cairo get values, and Asyut (27° N) gets none. We found no study comparing the Egyptian values with trap counts. The rule needs one local trap, and a one-year trap study in Alexandria (2019–20) shows the measurement can be made there. We have not tested it outside the three cities.

## Built with

Python (numpy, pandas), Comunidad de Madrid and MeteoSwiss open pollen data, CAMS via Open-Meteo, NASA POWER, GitHub Pages, Remotion.

## Limits

- Three trap sites; 2026 had 215 high days, 11 of them for Madrid olive.
- Retrospective, not a prospective trial; no patient outcome measured.
- The rule alerts one day late at a sudden onset.
- Needs yesterday's count by morning (MeteoSwiss publishes "up to yesterday"; Madrid daily January–June, weekly after).
- Single-centre thresholds; synthetic patients.

## Links

Demo: https://drahmed7887.github.io/hack-genhacks/ · Code: https://github.com/DrAhmed7887/hack-genhacks · Pre-registration: docs/PREREG_NOWCAST_2026.md
