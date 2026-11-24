# PollenPlan film V5: script (23 Nov 2026), APPROVED by Ahmed 23 Nov 2026 ("approve all")

Built from scratch around the pre-registered 2026 result. V4 and earlier are retired. Target length is about 2:20, under the 3:00 cap. Every number comes from `eval/results/nowcast_2026.json` (CLAIMS.md §N) and is mapped in `research/public_claims_v5.jsonl` before render. Visuals are real captures of `demo/index.html` plus motion graphics drawn from the same JSON. No AI imagery of people or screens.

| # | Time | Narration (voice) | On screen |
|---|---|---|---|
| 1 | 0:00–0:12 | Every morning in pollen season, an allergy clinic asks one question. Is today a high-pollen day, so our patients should use the medicine they already have? | Title in the first second: **Read the trap, not the forecast.** Below it, a dawn-coloured season strip draws itself. |
| 2 | 0:12–0:32 | Most tools answer with a forecast. We asked a simpler source: the clinic's own pollen trap, read yesterday. And we tested it the hard way. We wrote the test down, locked the model, and pushed it before we downloaded a single day of the 2026 season. | The lock commit `6ac1700` with its timestamp, then "2026 download" stamped after it. The chips read: pre-registered · 4 hypotheses · locked before data. |
| 3 | 0:32–0:58 | Two hundred fifteen high-pollen days in Madrid, Basel and Zürich. Yesterday's trap flagged one hundred sixty-four of them. Europe's free CAMS forecast for the same day flagged seventy. | Two counters race up: **164 / 215** (trap, green) against **70 / 215** (forecast, amber). Then a 215-dot grid fills in. CSI +0.332, 95% CI 0.203 to 0.457. |
| 4 | 0:58–1:16 | Day by day it looks like this. The forecast missed one hundred forty-five high days. The trap missed fifty-one, and it won in every city and every species. | A real capture of the season strips, panning across Madrid grass (forecast 1/36 against trap 29/36), then the six-cell grid with 6/6 ticks. |
| 5 | 1:16–1:36 | One real morning: Madrid, fifth of May. Yesterday's grass count was one hundred and four. The forecast for that day said nineteen point five, below the alert line. The trap that day measured seventy-nine. A high day. | The three "morning" cards, zoomed: 104 → alert; 19.5 → no alert; 79 → high day. |
| 6 | 1:36–1:56 | So the clinic drafts reminders. One hundred eleven of two hundred synthetic patients, each sensitised to grass with a medicine on file. Code names only the medicine already on file and adds the signed safety line. A nurse approves. Nothing is sent without that click. | Nurse batch capture: the drafts, then the approve button pressed. "Nothing is sent without that click." |
| 7 | 1:56–2:12 | We also tested ideas of our own. A fusion model didn't beat the simple trap rule. NASA weather didn't improve the score. So we ship the simple rule, and we say so. | Hypothesis table capture: H1 and H2 Passed; H3 and H4 Failed (red chips held on screen). |
| 8 | 2:12–2:28 | The forecast's map stops at thirty degrees north. South of that line, across most of Africa, it gives no pollen value at all. North of it, in Alexandria and Cairo, it does give numbers, and we found no one who has checked them against a trap. This rule needs only that trap. We haven't tested it there yet. That's next. | A map line at 30° N with the CAMS box shaded. Asyut is marked "no value". Alexandria and Cairo are marked "values, unchecked". The words "Not yet tested here". |
| 9 | 2:26–2:36 | Three cities, one season, a pre-registered test, and every number checks itself. Open the PollenPlan demo. No setup needed. | Close: the demo URL, "137 tests · verify_claims.py · lock 6ac1700". |

## Rules for the cut

- Proof goes in the first 60 s. Scenes 2–3 carry the lock and the headline.
- One idea per scene. Titles are five words or fewer. No text under 28 px at 1080 p.
- Real captures of `demo/index.html` only. Motion graphics are drawn from `nowcast_2026.json`.
- The map in scene 8 is a plain line drawing (domain box from the CAMS dataset page), not satellite imagery.
- Loudness target is −16 LUFS, with no silence over 4 s, a contact sheet, and frames checked at full size.

## Not said (fails the evidence gate or the clinical rules)

- "Clinically validated", "prevents symptoms", "fewer visits", or any patient-outcome claim.
- "Works in Egypt or Africa." The film says only that the rule needs one trap and is not yet tested there.
- Any treatment advice beyond "use the medicine they already have". The pre-season steroid guideline quote is unverified (ARIA full text not read).
- Any NASA gain.

## Signed by Ahmed, 23 Nov 2026 ("approve all": both items below)

- **Scene 1 wording:** "so our patients should use the medicine they already have." This is the same intent as the signed message rules (DATA_PLAN §3): the message names only the medicine class on file.
- **Scene 8 wording, corrected 23 Nov after review:** the earlier draft said Egypt had no forecast. That was wrong: Alexandria (31.2° N) and Cairo (30.0° N) sit inside the CAMS box and get values. The script now says only what WR1 (the domain) and WR6/WR7 (our API query: Alexandria and Cairo get values, Asyut none) support. "We found no one who has checked them against a trap" is a negative search result, not a survey of the field.

## Amendment A1 (23 Nov 2026), APPROVED by Ahmed 23 Nov 2026 ("Approve A1"): AI layer scene 6b, inserted after scene 6 (about +16 s, total about 2:52)

| # | Time | Narration (voice) | On screen |
|---|---|---|---|
| 6b | +0:16 | An AI model writes each reminder, and code checks every word. No dose, no drug name, no symptom advice, and the signed safety lines are added by code, not the model. We then attacked it forty times with attacks it had never seen. The model broke a rule twenty-one times. None of those reached the nurse. | Nurse copilot capture (batch ordered by risk, "Review first" badges), then the red-team table with its Blocked chips, then the counter: 40 held-out attacks · 21 broke a rule · 0 reached the nurse. |
