# PollenPlan rules — binding for every agent
- No invented metrics; every number comes from eval/results/*.json produced by eval/backtest.py.
- The backtest is pre-registered in docs/DATA_PLAN.md: rules P0,P1,P2,R1,R2,C0 exactly as written; do not add, tune or drop rules after seeing results.
- rules/thresholds.json is status signed (signed 22 Nov 2026 by Ahmed Zayed). Never edit it; read thresholds from it.
- Data: Open-Meteo (CC BY 4.0, non-commercial), Comunidad de Madrid (CC BY), MeteoSwiss (CC-BY), public de-identified CDC NHANES 2005–2006 survey participants (SEQN IDs only; replaced the seed-20261120 synthetic roster on 25 Nov 2026). Never the Taia unpublished table. Never any real patient data.
- Valencia is demo-only, never scored.
- Static GitHub Pages app (no server). Messages name only a medicine class already on file; nurse approves every batch; nothing is sent.
