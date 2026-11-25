# PollenPlan: guide for judges

GenHacks (**Healthcare & Environmental**) · **Live interactive workbench (no account):** <https://drahmed7887.github.io/hack-genhacks/> · **Code:** <https://github.com/DrAhmed7887/hack-genhacks>

**One-line pitch:** On the untouched 2026 pollen season (1,706 city-days; Madrid, Basel, Zürich), **yesterday's local trap count** flagged **164 of 215 high-pollen days (76.3%)** versus **70 (32.6%)** for Europe's CAMS forecast (+0.332 CSI, 95% CI 0.203–0.457), paired with **578 real CDC NHANES allergy patients** and an allowlist-gated nurse console.

## Judging Criteria Evidence

| Criterion (25% each) | Verified Evidence | Where |
|---|---|---|
| **1. Impact** | Real clinical & environmental data: `1,706` 2026 city-days and `7,373` 2021–2025 city-days of real pollen traps plus `578` de-identified CDC NHANES 2005–2006 hay-fever records (`39` grass-eligible: `23` Tier 1, `10` Tier 2, `6` Tier 3). CAMS stops south of 30°N (`Asyut 27°N` returns `null` live). | `eval/results/nowcast_2026.json`, `eval/results/backtest.json`, `data/patients.csv`, `CLAIMS.md` §A/N/F |
| **2. Technical execution** | Locked pre-registration (`5c45eaf`, `prereg-lock-2026`); live in-browser `F1`/`F2` logistic weights (locked on Madrid/Basel/Zürich, illustrative out-of-domain elsewhere) + on-demand `Qwen2.5-0.5B-Instruct` WebGPU/WASM (`~350 MB` CDN, checked by a JS mirror of `src/message_guard.py`) in `#workbench`; offline reproduction (`pytest`, `verify_claims.py`, `render_site.py --check`, `ci.yml`, `deploy-pages.yml`). | `docs/PREREG_NOWCAST_2026.md`, `eval/nowcast.py`, `demo/index.html`, `.github/workflows/` |
| **3. Creativity** | Negative-result-first discipline: fusion (H3) and NASA weather (H4) failed pre-registered tests and were cut, shipping P0. Allowlist guard caught `18/39` routine AI phrasings and `24/40` held-out red-team rule breaks (`0` unsafe drafts reached nurse). | `src/message_guard.py`, `eval/results/ai_layer.json`, `tests/test_message_guard.py` |
| **4. Presentation** | Two live runnable models right below hero on `demo/index.html` (`#workbench`); 2021–25 backtest & nurse console on `demo/backtest.html`; data-driven V5 film built from `eval/results/` with labelled AI voice/music/b-roll. | `demo/index.html`, `demo/backtest.html`, `video/v5/README.md`, `CLAIMS.md` §G |

## Limits

- Retrospective scoring of 3 European trap sites (215 high days in 2026; Madrid olive n=11); no prospective clinical trial or patient outcome measured.
- Persistence alerts 1 day late on sudden bursts and needs yesterday's trap count by morning; thresholds (`162/35/30` grains/m³) are single-centre values signed 22 Nov 2026.
- CDC NHANES 2005–2006 assays ImmunoCAP grass and birch sIgE (`>= 0.35 kU/L`), not olive IgE; no external sends; Valencia is never scored.
- Video link attached at Devpost submission.
