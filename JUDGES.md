# PollenPlan: guide for judges

GenHacks (**Healthcare & Environmental**) · **Live interactive demo (no account):** <https://drahmed7887.github.io/hack-genhacks/> · **Code:** <https://github.com/DrAhmed7887/hack-genhacks>

**One-line pitch:** On the untouched 2026 pollen season (1,706 city-days; Madrid, Basel, Zürich), **yesterday's local trap count** flagged **164 of 215 high-pollen days (76.3%)** versus **70 (32.6%)** for Europe's CAMS forecast (+0.332 CSI, 95% CI 0.203–0.457), and a deterministic allowlist gate keeps every AI draft safe before a nurse approves.

## Judging Criteria Evidence

| Criterion (25% each) | Verified Evidence | Where |
|---|---|---|
| **1. Impact** | Pre-registered 2026 result replicated 2021–25 (670/857 vs 359/863). CAMS stops south of 30°N (Asyut 27°N returns `null` live), while a clinic trap works at any latitude. Risk-tiered nurse batch (`9` Tier 1, `58` Tier 2, `44` Tier 3) names only the patient's medicine class on file. | `eval/results/nowcast_2026.json`, `CLAIMS.md` §N, `demo/index.html` (`#workbench`, `#morning`) |
| **2. Technical execution** | Enforced pre-registration lock (`5c45eaf`, `prereg-lock-2026`) pushed before 2026 download; offline reproduction (`backtest.py`, `verify_claims.py`, `render_site.py --check`, `render_demo.py --check`, `pytest`); CI + Pages auto-deploy on `main`. | `docs/PREREG_NOWCAST_2026.md`, `eval/nowcast.py`, `src/alert_rule.py`, `.github/workflows/` |
| **3. Creativity** | Negative-result-first discipline: fusion (H3) and NASA weather (H4) failed pre-registered tests and were cut, shipping P0. Allowlist guard (`src/message_guard.py`) blocked all 21 held-out rule breaks (`0/40` reached nurse); interactive `P022` attack sandbox runs in-browser. | `src/message_guard.py`, `eval/results/ai_layer.json`, `tests/test_message_guard.py` |
| **4. Presentation** | Top-fold 15-second live city CAMS + `<30°N` + trap + `P022` guard sandbox on `demo/index.html`; 2021–25 backtest & nurse console on `demo/backtest.html`; 2:57 data-driven V5 film built from `eval/results/` with labelled AI voice/music/b-roll. | `demo/index.html`, `demo/backtest.html`, `video/v5/README.md`, `CLAIMS.md` §G |

## Limits

- Retrospective scoring of 3 European trap sites (215 high days in 2026; Madrid olive n=11); no prospective clinical trial or patient outcome measured.
- Persistence alerts 1 day late on sudden bursts and needs yesterday's trap count by morning; thresholds (`162/35/30` grains/m³) are single-centre values signed 22 Nov 2026.
- Static GitHub Pages only: synthetic patients (`N = 200`, seed `20261120`), no external sends; Valencia is never scored.
- Video link attached at Devpost submission.
