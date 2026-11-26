# Devpost draft: PollenPlan (GenHacks), NOT SUBMITTED

Track: Healthcare & Environmental. Every number here is in `CLAIMS.md` and is checked by `eval/verify_claims.py`.

## Tagline

Read the trap, not the forecast. On a pollen season we had never seen, yesterday's trap count caught 164 of 215 high-pollen days. Europe's free forecast caught 70.

## Description

**Problem.** An allergy clinic has patients with a known pollen allergy who are already on treatment. On a high-pollen day it wants to remind them to use the medicine they already have. The obvious input is a free pollen forecast. We asked whether that forecast actually flags the high days a local trap measures.

**What we did.**
- Scored six alert rules against real trap counts (Madrid, Basel, Zürich, 2021–2025; 863 high days).
- Found that the clinic's own trap reading from yesterday beat the CAMS forecast for the same day, 670 of 857 against 359 of 863.
- Pre-registered a test on the untouched 2026 season instead of claiming that result. We wrote four hypotheses, built a fusion model (`F1`) and a NASA-weather variant (`F2`), and locked and pushed everything (`5c45eaf`, tag `prereg-lock-2026`) before downloading a single 2026 file.
- Paired the environmental benchmark with **578 public, de-identified CDC NHANES 2005–2006 survey participants with hay fever** (a stand-in clinic roster: survey participants, not clinic patients) (laboratory ImmunoCAP serum specific IgE `>= 0.35 kU/L` and verified `RXQ_RX_D` rhinitis prescriptions on file; no synthetic rows).

**Result (1 Jan – 31 Oct 2026, 215 high days, 1,706 city-days).**
- Yesterday's trap: 164 of 215 (76.3%), 40 false-alert days.
- CAMS forecast: 70 of 215 (32.6%), 10 false-alert days.
- CSI +0.332, 95% CI 0.203 to 0.457, the trap winning in all six city × species series.
- Our own fusion model did not beat the simple rule (H3 failed), and NASA POWER weather did not improve its score (H4 failed). So we ship the simple rule and report both failures.
- A two-day-old reading still beats the forecast (151 of 215, CSI 0.572), which matters where trap data publish late.

**Product & Two Live Runnable Models (`#workbench`).**
- **Live Model 1 — Logistic Nowcast Weights (`F1` & `F2`) + CAMS:** at `https://drahmed7887.github.io/hack-genhacks/#workbench`, pick any city (Madrid, Basel, Zürich, Alexandria, Cairo, Asyut at 27° N outside CAMS's 30° N map boundary, or any searched location) to fetch live Open-Meteo CAMS + D-1 weather and run yesterday's trap rule (`P0`) side by side with our `5c45eaf` logistic fusion weights (`F1` and `F2`; locked on Madrid/Basel/Zürich with Open-Meteo D-1 weather proxy, illustrative out-of-domain elsewhere).
- **Live Model 2 — In-Browser `Qwen2.5-0.5B-Instruct` + Deterministic Allowlist Guard:** pick a CDC NHANES survey participant with hay fever (such as `NH-32025`, ImmunoCAP ryegrass `3.55 kU/L`, birch `0.57 kU/L`, verified budesonide nasal spray), run open-weights `Qwen2.5-0.5B-Instruct` on-demand in WebGPU/WASM (`~350 MB` cached from jsDelivr CDN, un-scored interactive demo) with custom or adversarial instructions, and inspect how the in-browser mirror of `src/message_guard.py` catches unapproved tokens in real time (no keys, no backend server, no patient messages sent).
- **Morning clinic batch (`src/alert_rule.py` + `src/reminders.py`):** on the 5 May 2026 Madrid grass morning (`104` grains/m³ yesterday vs. `19.5` forecast, `79` measured), `39` of `578` CDC NHANES hay-fever participants have positive grass IgE and a rhinitis Rx container on file (`313` not sensitised to grass; `226` without a matching Rx on file). Code names only the medicine class on file and appends the fixed, signed safety lines. A nurse approves every batch.

**AI layer, with the AI kept on a leash.**
- Nurse copilot triage order: asthma flag + moderate/severe rhinitis (`23` Tier 1), asthma flag or moderate/severe (`10` Tier 2), mild (`6` Tier 3).
- In batch evaluation using Mistral Small 4 119B via RWTHgpt across the `39` eligible CDC NHANES drafts, `21` passed the strict allowlist gate cleanly and `18` were caught for phrasing drift (for example extra words or non-ASCII apostrophes) and automatically replaced by the signed template — showing why a hard code gate is needed even on benign runs.
- Red team & Clinician Q&A: `18/40` tuning attacks broke a rule and `0` reached the nurse; `24/40` held-out unseen attacks broke a rule and **0** reached the nurse (building on `25` independent-review bypasses locked in `tests/test_message_guard.py`). In Clinician Q&A (`12` questions), `3` symptom questions never reached the model and all `9` model answers passed verification (`0` withheld).

**Where next (a hypothesis, not a result).** The CAMS pollen forecast is built for Europe, with a map that stops at 30° N. We queried it for Egypt: Alexandria and Cairo get values, and Asyut (27° N) gets none. We found no study comparing the Egyptian values with trap counts, and a 2026 Africa-wide aerobiology review ([`10.1007/s10453-026-09933-w`](https://doi.org/10.1007/s10453-026-09933-w)) confirms zero published volumetric traps south of 30° N in North Africa. The rule needs one local trap; volumetric records in Alexandria from 1981–1982 ([El-Ghazaly & Fawzy, *Grana* 1988](https://doi.org/10.1080/00173138809427736)) and 2019–2020 ([Taia & Bassiouni 2022](https://doi.org/10.31080/ASMI.2022.05.1088)) show the measurement can be made there. We have not tested it outside the three cities.

**Literature context.** CAMS's own olive ensemble evaluation found 1-day persistence beat even a fused multi-model ensemble on continuous RMSE, yet assumed Hirst reporting delays made it unusable and never scored binary alert CSI ([Sofiev et al., *ACP* 2017](https://doi.org/10.5194/acp-17-12341-2017)). In Australia, *curated* local grass forecasts usually beat persistence on threat scores ([Emmerson et al., *Atmos Environ X* 2022](https://doi.org/10.1016/j.aeaoa.2022.100183)); on untouched 2026 European data, un-curated CAMS loses to both 1-day (`CSI 0.643`) and 2-day-lagged (`0.572`) local trap readings. Improving alert accuracy matters clinically: free pollen apps previously averaged ~50% hit rates ([Bastl et al., *JMIR* 2017](https://doi.org/10.2196/jmir.7426)), whereas a 2025 controlled trial (N = 167) showed reliable forecast-equipped apps improve medication use and symptom control ([*Allergy* 2025](https://doi.org/10.1111/all.16558)).

## Built with

Python (numpy, pandas, pytest), CDC NCHS NHANES 2005–2006 (public domain), Transformers.js (`Qwen2.5-0.5B-Instruct` WebGPU/WASM), Mistral Small 4 119B via RWTHgpt (batch evaluation), deterministic Python allowlist guard, Comunidad de Madrid and MeteoSwiss open pollen data, CAMS & weather via Open-Meteo API, NASA POWER & MODIS MOD13Q1, GitHub Pages, Remotion, Blender Cycles (procedural trap strip).

## Limits

- Three trap sites; 2026 had 215 high days, 11 of them for Madrid olive.
- Retrospective, not a prospective trial; no patient outcome measured.
- The rule alerts one day late at a sudden onset.
- Needs yesterday's count by morning (MeteoSwiss publishes "up to yesterday"; Madrid daily January–June, weekly after).
- Single-centre thresholds; CDC NHANES assays grass and birch ImmunoCAP IgE (not olive IgE); no patient messages sent.

## Links

- Live interactive workbench & demo (no account): https://drahmed7887.github.io/hack-genhacks/
- Demo video (2:59): https://youtu.be/bybQPPLhNfw
- Repository (Apache 2.0): https://github.com/DrAhmed7887/hack-genhacks
- Judge guide: https://github.com/DrAhmed7887/hack-genhacks/blob/main/JUDGES.md
- Pre-registration (`prereg-lock-2026`, `5c45eaf`): https://github.com/DrAhmed7887/hack-genhacks/blob/main/docs/PREREG_NOWCAST_2026.md
