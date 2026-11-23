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


def test_no_invented_message_text():
    """Drafts show only structured fields and the signed safety lines (src/reminders.py)."""
    from src import reminders  # noqa: F401  (import path set by render_site)
    data = json.loads(re.search(r'id="site-data">(.*?)</script>', PAGE, re.S).group(1))
    for d in data["console"]["drafts"]:
        assert set(d["lines"]) <= {reminders.SAFETY_LINE, reminders.ASTHMA_LINE}


def test_wording_guard_same_as_backtest_page():
    """Same forbidden-phrase rule as tests/test_demo.py, applied to the front page."""
    low = PAGE.lower()
    scrubbed = low.replace("do not diagnose anything", "")
    for phrase in ("clinically validated", "diagnos", "recommend treatment"):
        assert phrase not in scrubbed, phrase
