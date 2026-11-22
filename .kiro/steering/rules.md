# PollenPlan rules — binding for every agent
- No invented metrics; every number comes from eval/results/*.json produced by eval/backtest.py.
- The backtest is pre-registered in docs/DATA_PLAN.md: rules P0,P1,P2,R1,R2,C0 exactly as written; do not add, tune or drop rules after seeing results.
- rules/thresholds.json is status pending_signoff (not signed by the clinician). Never edit it; read thresholds from it.
- Data: Open-Meteo (CC BY 4.0, non-commercial), Comunidad de Madrid (CC BY), MeteoSwiss (CC-BY), synthetic patients (seed 20261120). Never the Taia unpublished table. Never any real patient data.
- Valencia is demo-only, never scored.
- Static GitHub Pages app (no server). Messages name only a medicine class already on file; nurse approves every batch; nothing is sent.
