# PollenPlan film V4: narration changes from V2 (23 Nov 2026)

V4 = the V2 Director's Cut (128.6 s, approved structure, voice "Daniel", `eleven_multilingual_v2`, speed 1.08) with three changes. Every number below is checked by `eval/verify_claims.py` and by `evidence.py gate` against `eval/results/backtest.json`.

## New slot s7n (inside the dark "Honest limits" scene, after "Valencia is never scored.")

> We also tested NASA POWER weather data on held-out 2024 and 2025. A fourteen-day early warning from NASA temperatures landed in the useful window 30% of the time; last year's calendar did it 60% of the time. A NASA weather rule lifted the alert score from 0.38 to 0.43, but the same rule without NASA scored 0.49. NASA added nothing here, so we claim nothing.

Spoken form (numbers as words for the voice): see `video/remotion/scripts/vo_v4.json`.

On screen: "NASA POWER test · held-out 2024–25 (exploratory)"; two bars (14-day warning in window: NASA 30% vs calendar 60%); three bars (CSI: API forecast 0.382 · NASA rule 0.434 · same rule, no NASA 0.486); verdict chip "NASA adds skill? No".

## Changed slot s3 (scale)

> ... against Madrid, Basel, and Zürich traps — seven thousand three hundred seventy-three city-days.

(V2 said 8,076. The 23 Nov 2026 code review found that days with no trap reading had been counted; see `CLAIMS.md` correction note. On screen: 7,373 in s3, s5 and s8.)

## Changed slot s8 (close)

> Zero unapproved sends, eighty-nine of two hundred filtered out by code, and 117 green tests. Open the live PollenPlan demo today — zero setup required.

(V2 said 95 tests; `pytest -q` = 117 passed on 23 Nov 2026.)

## Not said (fails the evidence gate)

No 14-day alarm claim, no "satellite weather", no orbital or satellite-detection shot, no NASA gain, no MODIS claim (NDVI is cached context only, not an input to N1 or N2).
