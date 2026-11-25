"""demo/index.html (front page) is generated from the locked 2026 result and never drifts from it."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import render_site  # noqa: E402

PAGE = (ROOT / "demo" / "index.html").read_text()
RES = json.loads((ROOT / "eval" / "results" / "nowcast_2026.json").read_text())


def test_page_is_not_stale():
    assert render_site.main(["--check"]) == 0


def test_headline_numbers_match_result_json():
    p = RES["pooled"]
    assert f'id="trap-hits">{p["P0"]["tp"]}<' in PAGE and f'id="cams-hits">{p["P2"]["tp"]}<' in PAGE
    assert (p["P0"]["tp"], p["P2"]["tp"], p["P0"]["n_events"]) == (164, 70, 215)
    assert f'+{RES["hypotheses"]["H1"]["csi_diff"]:.3f}' in PAGE


def test_failed_hypotheses_are_shown_as_failed():
    assert RES["hypotheses"]["H3"]["passes"] is False and RES["hypotheses"]["H4"]["passes"] is False
    assert PAGE.count('class="chip fail">Failed<') == 2


def test_featured_morning_is_a_real_trap_only_catch():
    data = json.loads(re.search(r'<script type="application/json" id="site-data">(.*?)</script>', PAGE, re.S).group(1))
    f = data["featured"]
    assert f["yesterday"] >= f["threshold"] > f["cams_today"] and f["observed_today"] >= f["threshold"]
    # the values quoted in DEVPOST_DRAFT.md, CLAIMS.md N11 and video/SCRIPT_V5.md
    assert (f["date"], f["yesterday"], f["cams_today"], f["observed_today"]) == ("2026-05-05", 104.0, 19.5, 79.0)
    assert data["console"]["eligible"] == 39 and data["console"]["roster"] == 578


def test_no_invented_message_text():
    """Drafts show only structured fields and the signed safety lines (src/reminders.py)."""
    from src import reminders  # noqa: F401  (import path set by render_site)
    data = json.loads(re.search(r'id="site-data">(.*?)</script>', PAGE, re.S).group(1))
    for d in data["console"]["drafts"]:
        assert set(d["lines"]) <= {reminders.SAFETY_LINE, reminders.ASTHMA_LINE}


def test_wording_guard_same_as_backtest_page():
    """Same forbidden-phrase rule as tests/test_demo.py, applied to the front page and public docs."""
    low = PAGE.lower()
    scrubbed = low.replace("do not diagnose anything", "")
    for phrase in ("clinically validated", "diagnos", "recommend treatment"):
        assert phrase not in scrubbed, phrase
    assert "synthetic" not in (ROOT / "README.md").read_text().lower()
    assert "synthetic patient" not in (ROOT / "JUDGES.md").read_text().lower()
    data = json.loads(re.search(r'<script type="application/json" id="site-data">(.*?)</script>', PAGE, re.S).group(1))
    assert set(data["nowcast_lock"]["cells"]) == {
        "madrid:olive", "madrid:grass", "basel:birch", "basel:grass", "zurich:birch", "zurich:grass"
    }


def _ai():
    return json.loads((ROOT / "eval" / "results" / "ai_layer.json").read_text())


def test_every_recorded_ai_draft_passes_the_gate_and_carries_signed_lines():
    sys.path.insert(0, str(ROOT))
    from src import message_guard as g
    from src.reminders import ASTHMA_LINE, SAFETY_LINE
    a = _ai()
    f = a["featured"]
    assert len(a["drafts"]) == 39
    for d in a["drafts"]:
        opening = d["final"][: d["final"].index(SAFETY_LINE)].strip()
        fx = g.Facts(f["species"], f["yesterday"], f["threshold"], d["medicine"], d["asthma"])
        assert g.check_opening(opening, fx) == [], d["id"]
        assert d["final"].endswith(g.DIRECTIVE) and ((ASTHMA_LINE in d["final"]) == d["asthma"])
    tiers = [d["tier"] for d in a["drafts"]]
    assert tiers == sorted(tiers)


def test_red_team_no_rule_break_reaches_the_nurse():
    sys.path.insert(0, str(ROOT))
    from src import message_guard as g
    from src.reminders import SAFETY_LINE
    a = _ai()
    f = a["featured"]
    med = {d["id"]: (d["medicine"], d["asthma"]) for d in a["drafts"]}
    leaks = 0
    for r in a["red_team"]:
        m, asthma = med[r["patient"]]
        opening = r["final"][: r["final"].index(SAFETY_LINE)].strip()
        leaks += bool(g.check_opening(opening, g.Facts(f["species"], f["yesterday"], f["threshold"], m, asthma)))
    assert leaks == 0 == a["red_team_summary"]["reached_nurse_with_violation"]
    assert len(a["red_team"]) == 40


def test_symptom_questions_were_never_sent_to_the_model():
    for q in _ai()["qa"]:
        if q["route"] == "symptom_router":
            assert q["model_called"] is False
    assert sum(q["route"] == "symptom_router" for q in _ai()["qa"]) >= 3


def test_heldout_red_team_no_rule_break_reaches_the_nurse():
    sys.path.insert(0, str(ROOT))
    from src import message_guard as g
    from src.reminders import SAFETY_LINE
    a = _ai()
    f = a["featured"]
    med = {d["id"]: (d["medicine"], d["asthma"]) for d in a["drafts"]}
    leaks = sum(bool(g.check_opening(h["final"][: h["final"].index(SAFETY_LINE)].strip(),
                                     g.Facts(f["species"], f["yesterday"], f["threshold"], *med[h["patient"]])))
                for h in a["red_team_heldout"])
    assert leaks == 0 == a["red_team_heldout_summary"]["reached_nurse_with_violation"] and len(a["red_team_heldout"]) == 40
