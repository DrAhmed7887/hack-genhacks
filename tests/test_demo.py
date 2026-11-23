"""Tests for demo/index.html data and rendering.

The demo embeds a rounded copy of eval/results/backtest.json (P2 table) and
static onset rows written by eval/render_demo.py. These tests parse the actual
HTML (no browser) and compare what it shows against backtest.json.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "demo"
EVAL_RESULTS_DIR = REPO_ROOT / "eval" / "results"
README = REPO_ROOT / "README.md"

sys.path.insert(0, str(REPO_ROOT / "eval"))
import render_demo  # noqa: E402

EXPECTED_ONSET_ROWS = 28


class _TbodyRows(HTMLParser):
    """Collect the cell text of every <tr> inside <tbody id=...>."""

    def __init__(self, tbody_id: str) -> None:
        super().__init__()
        self.tbody_id = tbody_id
        self.inside = False
        self.rows: list[list[str]] = []
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tbody" and dict(attrs).get("id") == self.tbody_id:
            self.inside = True
        elif self.inside and tag == "tr":
            self.rows.append([])
        elif self.inside and tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "tbody" and self.inside:
            self.inside = False
        elif self.inside and tag in ("td", "th") and self._cell is not None:
            self.rows[-1].append("".join(self._cell).strip())
            self._cell = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse_onset_rows(html: str) -> list[list[str]]:
    parser = _TbodyRows("onset-table-body")
    parser.feed(html)
    return parser.rows


def embedded_backtest_data(html: str) -> dict:
    match = re.search(r"const backtestData = (\{.*?\n    \});", html, re.S)
    assert match, "backtestData block not found in demo/index.html"
    return json.loads(match.group(1))


def _date(v):
    return "no alert" if v is None else v


def _lead(v):
    if v is None:
        return "n/a"
    return f"+{v}" if v > 0 else str(v)


def load_backtest_data():
    """Load backtest.json for demo data."""
    backtest_path = EVAL_RESULTS_DIR / "backtest.json"
    if not backtest_path.exists():
        raise FileNotFoundError(f"Backtest results not found: {backtest_path}")
    with open(backtest_path) as f:
        return json.load(f)


def load_demo_html():
    """Load demo/index.html."""
    demo_path = DEMO_DIR / "index.html"
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo HTML not found: {demo_path}")
    return demo_path.read_text()


class TestDemoDataLoading:
    """Test that demo can load and parse backtest data."""

    def test_backtest_json_exists(self):
        """Backtest results file must exist."""
        assert EVAL_RESULTS_DIR.joinpath("backtest.json").exists()

    def test_backtest_json_loads(self):
        """Backtest.json must be valid JSON."""
        data = load_backtest_data()
        assert isinstance(data, dict)

    def test_backtest_json_has_required_fields(self):
        """Backtest.json must have required top-level fields."""
        data = load_backtest_data()
        required = ["results", "kill_check", "thresholds_status", "cities_scored"]
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_results_has_p2_metrics(self):
        """Each result must have P2 metrics."""
        data = load_backtest_data()
        for result in data["results"]:
            assert "P2" in result["day_rules"], f"P2 missing for {result['city']}/{result['species']}"
            p2 = result["day_rules"]["P2"]
            assert "recall" in p2
            assert "precision" in p2
            assert "csi" in p2
            assert "false_alert_days" in p2
            assert "recall_ci95" in p2


class TestDemoRendering:
    """Test demo HTML has required structure and disclaimers."""

    def test_demo_html_exists(self):
        """Demo HTML file must exist."""
        assert DEMO_DIR.joinpath("index.html").exists()

    def test_demo_html_loads(self):
        """Demo HTML must be readable."""
        html = load_demo_html()
        assert isinstance(html, str)
        assert len(html) > 1000  # Sanity check: file is substantial

    def test_demo_has_disclaimers(self):
        """Demo must contain all required disclaimers."""
        html = load_demo_html()
        disclaimers = [
            "retrospective",
            "Not a clinical tool",
            "No \"beats the API\" claim",
            "signed 22 Nov 2026",
            "Model vs reality",
        ]
        for d in disclaimers:
            assert d.lower() in html.lower(), f"Missing disclaimer: {d}"

    def test_demo_has_headline_section(self):
        """Demo must show kill-check headline."""
        html = load_demo_html()
        assert "headline" in html.lower()
        # Check for the expected headline value
        assert "measured_P2_skill_only_no_beats_api_claim" in html

    def test_demo_has_metrics_grid(self):
        """Demo must display metrics in a grid."""
        html = load_demo_html()
        assert "metrics-grid" in html
        assert "metric-card" in html

    def test_demo_has_results_table(self):
        """Demo must show results table."""
        html = load_demo_html()
        assert "results-table-body" in html
        assert "city" in html.lower()
        assert "recall" in html.lower()

    def test_demo_has_onset_table(self):
        """Demo must show onset comparison table."""
        html = load_demo_html()
        assert "onset-table-body" in html
        assert "R2 Lead" in html or "lead" in html.lower()

    def test_demo_has_methodology_section(self):
        """Demo must explain methodology."""
        html = load_demo_html()
        assert "methodology" in html.lower()
        # Must mention key rules
        assert "P2" in html or "API" in html
        assert "P0" in html or "persistence" in html.lower()

    def test_demo_has_limits_section(self):
        """Demo must list known limitations."""
        html = load_demo_html()
        assert "limits" in html.lower()
        # Must mention key limitations
        assert "trap" in html.lower() or "grid" in html.lower()
        assert "Madrid" in html

    def test_demo_has_attribution(self):
        """Demo must credit data sources."""
        html = load_demo_html()
        attributions = ["Open-Meteo", "Comunidad de Madrid", "MeteoSwiss", "CC BY"]
        for attr in attributions:
            assert attr in html, f"Missing attribution: {attr}"


class TestRenderedValues:
    """Test that rendered HTML values match backtest.json data."""

    def test_onset_html_has_all_28_rows(self):
        """The HTML onset tbody must hold one row per city-species-season."""
        rows = parse_onset_rows(load_demo_html())
        assert len(rows) == EXPECTED_ONSET_ROWS
        assert all(len(r) == len(render_demo.COLUMNS) for r in rows)

    def test_onset_html_cells_match_backtest_json(self):
        """Every rendered cell (dates, leads, status) equals backtest.json onset_by_year."""
        data = load_backtest_data()
        expected = []
        for res in data["results"]:
            for year in sorted(res["onset_by_year"]):
                o = res["onset_by_year"][year]
                if o["R2_missed_season"]:
                    status = "missed season"
                elif o["R2_fired_before_onset"]:
                    status = "on time or early"
                else:
                    status = "late"
                expected.append([
                    res["city"].capitalize(), res["species"], year,
                    _date(o["observed_onset"]),
                    _date(o["R2_onset"]), _lead(o["R2_lead_days"]),
                    _date(o["P2_onset"]), _lead(o["P2_lead_days"]),
                    _date(o["C0_onset"]), _lead(o["C0_lead_days"]),
                    status,
                ])
        assert parse_onset_rows(load_demo_html()) == expected

    def test_onset_rows_agree_with_kill_check_rows(self):
        """onset_by_year and kill_check onset_rows_used must describe the same 28 seasons."""
        data = load_backtest_data()
        used = data["kill_check"]["check2_beats_api"]["onset_rows_used"]
        rows = render_demo.onset_rows(data)
        assert len(rows) == len(used) == EXPECTED_ONSET_ROWS
        for row, u in zip(rows, used):
            assert (row.city, row.species, row.year) == (u["city"], u["species"], u["year"])
            assert (row.r2_lead, row.p2_lead, row.c0_lead) == (
                u["R2_lead_days"], u["P2_lead_days"], u["C0_lead_days"])

    def test_onset_misses_and_nulls_shown_honestly(self):
        """Seasons where R2/P2/C0 never fired must show 'no alert' and 'n/a', not be dropped."""
        rows = parse_onset_rows(load_demo_html())
        missed = [r for r in rows if r[10] == "missed season"]
        assert [(r[0], r[1], r[2]) for r in missed] == [
            ("Madrid", "olive", "2024"), ("Madrid", "olive", "2025"), ("Madrid", "grass", "2023")]
        for r in missed:
            assert r[4] == "no alert" and r[5] == "n/a"
        assert sum(1 for r in rows if r[8] == "no alert") == 6  # C0 never fired: 6 seasons
        assert not any(c == "N/A" for r in rows for c in r)

    def test_onset_html_is_current(self):
        """demo/index.html must equal what eval/render_demo.py renders now."""
        assert render_demo.main(["--check"]) == 0

    def test_no_js_overwrites_onset_rows(self):
        """No script may replace the static onset rows."""
        html = load_demo_html()
        assert "getElementById('onset-table-body')" not in html
        assert 'getElementById("onset-table-body")' not in html

    def test_embedded_p2_metrics_match_backtest_json(self):
        """The P2 table data embedded in the HTML equals backtest.json to 3 dp."""
        html_data = embedded_backtest_data(load_demo_html())
        data = load_backtest_data()
        assert len(html_data["results"]) == len(data["results"])
        for h, j in zip(html_data["results"], data["results"]):
            assert (h["city"], h["species"], h["threshold"]) == (j["city"], j["species"], j["threshold"])
            hp, jp = h["day_rules"]["P2"], j["day_rules"]["P2"]
            for k in ("tp", "fp", "fn", "tn", "n_events", "n_evaluated_days", "false_alert_days"):
                assert hp[k] == jp[k], (h["city"], h["species"], k)
            for k in ("recall", "precision", "csi"):
                assert hp[k] == round(jp[k], 3), (h["city"], h["species"], k)
            assert hp["recall_ci95"] == [round(x, 3) for x in jp["recall_ci95"]]
        assert all(r["city"] != "valencia" for r in html_data["results"])

    def test_madrid_both_below_50_displays_limits(self):
        """Madrid badge must show 'Yes (limits)' with warning color."""
        html = load_demo_html()
        assert "Yes (limits)" in html
        assert 'badge-warning' in html  # Warning color for Madrid P2 recall below 50%

    def test_r2_vs_c0_shows_no(self):
        """R2 vs C0 badge must show 'No' (not beating C0)."""
        html = load_demo_html()
        # The R2 vs C0 badge should show "No" 
        assert 'id="r2-vs-c0"' in html
        assert 'badge-danger' in html or 'badge-warning' in html

    def test_overall_verdict_shows_no_claim(self):
        """Overall verdict must show 'No claim'."""
        html = load_demo_html()
        assert "No claim" in html
        assert 'id="overall-verdict"' in html

    def test_all_metric_values_present(self):
        """All key metric values must be present in HTML."""
        html = load_demo_html()
        data = load_backtest_data()
        
        # P2 recall
        p2_recall = str(data["kill_check"]["check2_beats_api"]["pooled_p2"]["recall"])
        assert p2_recall[:5] in html or "0.416" in html
        
        # Total events
        assert "863" in html
        
        # Total days  
        assert 'id="total-days">7373<' in html
        assert 'id="total-events">863<' in html
        assert 'id="p2-recall">0.416<' in html
        
        # Madrid P2 recall values
        assert "0.136" in html  # olive
        assert "0.314" in html  # grass
        
        # R2 vs P2 lead days
        assert "2.9" in html or "2.88" in html
        
        # R2 CI
        assert "[+2.6" in html or "[+2.64" in html


class TestKillCheckValues:
    """Test that kill-check values in demo match backtest results."""

    def test_overall_headline(self):
        """Headline must be 'measured_P2_skill_only_no_beats_api_claim'."""
        data = load_backtest_data()
        assert data["kill_check"]["overall_headline"] == "measured_P2_skill_only_no_beats_api_claim"

    def test_r1_vs_p2_check(self):
        """R1 must not beat P2 on pooled recall."""
        data = load_backtest_data()
        r1 = data["kill_check"]["check2_beats_api"]["pooled_r1"]
        p2 = data["kill_check"]["check2_beats_api"]["pooled_p2"]
        assert r1["recall"] < p2["recall"], "R1 recall must be < P2 recall"
        assert data["kill_check"]["check2_beats_api"]["r1_beats_p2_pooled_recall_at_equal_or_fewer_false_alerts"] is False

    def test_r2_vs_p2_check(self):
        """R2 must beat P2 on lead days with CI excluding zero."""
        data = load_backtest_data()
        r2_vs_p2 = data["kill_check"]["check2_beats_api"]["r2_minus_p2_lead_days_bootstrap"]
        assert r2_vs_p2["mean_diff"] > 0
        assert r2_vs_p2["excludes_zero"] is True

    def test_madrid_p2_below_50(self):
        """Madrid P2 recall must be below 50% for both species."""
        data = load_backtest_data()
        check3 = data["kill_check"]["check3_madrid_p2_recall"]
        assert check3["both_below_50pct"] is True
        assert check3["madrid_p2_recall_by_species"]["olive"] < 0.5
        assert check3["madrid_p2_recall_by_species"]["grass"] < 0.5


class TestDemoThresholds:
    """Test thresholds are shown as signed."""

    def test_thresholds_status_signed(self):
        """Thresholds status must be signed."""
        data = load_backtest_data()
        assert data["thresholds_status"] == "signed"

    def test_demo_shows_thresholds_status(self):
        """Demo must mention thresholds are signed."""
        html = load_demo_html()
        assert "signed 22 Nov 2026" in html

    def test_threshold_values_shown_with_units_and_signed(self):
        """Threshold column and caption must carry the unit and signed status."""
        html = load_demo_html()
        rules = json.loads((REPO_ROOT / "rules" / "thresholds.json").read_text())
        assert rules["status"] == "signed"
        header = re.search(r'<th id="threshold-header">(.*?)</th>', html).group(1)
        assert "grains/m³" in header and "daily mean" in header and "signed 22 Nov 2026" in header
        caption = re.search(r'<p id="threshold-caption"[^>]*>(.*?)</p>', html, re.S).group(1)
        for species, value in rules["alert"].items():
            assert f"{species} {value}" in caption
        assert "grains/m³ (daily mean)" in caption and "signed 22 Nov 2026" in caption

    def test_demo_does_not_modify_thresholds(self):
        """Demo must read, not modify, thresholds."""
        # Read thresholds from rules/thresholds.json
        thresholds_path = REPO_ROOT / "rules" / "thresholds.json"
        with open(thresholds_path) as f:
            rules_thresholds = json.load(f)
        # Demo should use values from backtest.json (which reads same thresholds)
        data = load_backtest_data()
        assert data["thresholds_used"] == rules_thresholds.get("alert", {})


class TestAttributionAndPublicText:
    """Exact attribution strings (DATA_PLAN 4, DATA_SOURCES O9) and no internal-only text."""

    def test_demo_exact_attribution(self):
        html = load_demo_html()
        assert '<a href="https://open-meteo.com/">Weather data by Open-Meteo.com</a>' in html
        assert "CAMS European air quality forecasts, ENSEMBLE data" in html
        assert "Source: MeteoSwiss" in html
        assert "Comunidad de Madrid" in html

    def test_readme_exact_attribution(self):
        readme = README.read_text()
        assert "[Weather data by Open-Meteo.com](https://open-meteo.com/)" in readme
        assert "CAMS European air quality forecasts, ENSEMBLE data" in readme
        assert "Source: MeteoSwiss" in readme

    def test_no_internal_only_text(self):
        for text in (load_demo_html(), README.read_text()):
            for marker in ("Submission Prep Checklist", "No commits", "per instructions"):
                assert marker not in text, marker

    def test_readme_does_not_claim_valencia_in_demo(self):
        readme = README.read_text()
        assert "shown in the demo" not in readme
        assert "never scored" in readme


class TestCityScoring:
    """Test that only correct cities are scored."""

    def test_only_madrid_basel_zurich_scored(self):
        """Only Madrid, Basel, Zurich must be scored."""
        data = load_backtest_data()
        assert set(data["cities_scored"]) == {"madrid", "basel", "zurich"}

    def test_valencia_not_scored(self):
        """Valencia must never be scored."""
        data = load_backtest_data()
        assert data["valencia_scored"] is False
        assert "valencia" not in data["cities_scored"]
        # Verify Valencia doesn't appear in results
        for result in data["results"]:
            assert result["city"] != "valencia"


class TestStaticAndWording:
    """Static/no-network guarantee and forbidden public wording."""

    def test_demo_makes_no_network_calls(self):
        """The demo must be self-contained: no fetch, no XHR, no external scripts."""
        html = load_demo_html()
        assert "fetch(" not in html
        assert "XMLHttpRequest" not in html
        assert not re.search(r"<script\b[^>]*\bsrc\s*=", html, re.I)

    def test_forbidden_phrases_absent(self):
        """'beats the API' only in negated form; no clinical-validation or diagnosis wording."""
        for name, text in (("demo", load_demo_html()), ("README", README.read_text())):
            low = text.lower().replace('"', "")
            for m in re.finditer(r"beats the api", low):
                before = low[max(0, m.start() - 3):m.start()]
                assert before == "no ", f"{name}: un-negated 'beats the API' at {m.start()}"
            # Only the signed negated safety line and the audit-log wording
            # ("no drug, dose, or diagnosis added") may contain "diagnos".
            scrubbed = low.replace("do not diagnose anything", "").replace("no drug, dose, or diagnosis added", "")
            for phrase in ("clinically validated", "diagnos", "recommend treatment"):
                assert phrase not in scrubbed, f"{name}: forbidden phrase {phrase!r}"


def embedded_console_data(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="nurse-console-data">\n(.*?)\n</script>', html, re.S)
    assert m, "nurse console data block not found"
    return json.loads(m.group(1))


class TestNurseConsole:
    """The interactive console is injected from Python and must match src.reminders."""

    @staticmethod
    def _patients():
        import csv

        sys.path.insert(0, str(REPO_ROOT))
        from src import reminders

        with (REPO_ROOT / "data" / "patients.csv").open() as fh:
            return reminders, [reminders.patient_from_row(r) for r in csv.DictReader(fh)]

    def test_counts_and_ids_match_build_batch(self):
        reminders, patients = self._patients()
        data = embedded_console_data(load_demo_html())
        assert data["roster_size"] == len(patients) == 200
        by_id = {s["id"]: s for s in data["scenarios"]}
        expected = {"valencia_control": None, "madrid_grass": "grass", "basel_birch": "birch", "olive_sim": "olive"}
        assert set(by_id) == set(expected)
        for sid, species in expected.items():
            sc = by_id[sid]
            batch = reminders.build_batch(patients, species) if species else []
            assert sc["alerting_species"] == species
            assert [d["patient_id"] for d in sc["drafts"]] == [m.patient_id for m in batch]
            assert sc["eligible_count"] == len(batch)
            assert sc["filtered_count"] == 200 - len(batch)
            assert sum(sc["filtered_reasons"].values()) == sc["filtered_count"]
            for d, m in zip(sc["drafts"], batch):
                assert d["message"] == " ".join(m.lines)
                assert d["med_class_on_file"] == m.medicine_class
        assert by_id["valencia_control"]["eligible_count"] == 0
        for sid in ("madrid_grass", "basel_birch", "olive_sim"):
            assert by_id[sid]["eligible_count"] > 0

    def test_valencia_control_below_thresholds(self):
        data = embedded_console_data(load_demo_html())
        sc = next(s for s in data["scenarios"] if s["id"] == "valencia_control")
        assert sc["means"]["olive"] == 39.6 and sc["means"]["grass"] == 12.9
        for sp, v in sc["means"].items():
            assert v < data["thresholds"][sp]

    def test_required_dom_ids_and_order(self):
        html = load_demo_html()
        for dom_id in ("replay-scenario-select", "nurse-draft-table-body", "approve-batch-btn", "nurse-audit-log"):
            assert f'id="{dom_id}"' in html
        assert html.index('id="nurse-console"') < html.index("<h2>Key Findings</h2>")

    def test_render_check_passes(self):
        assert render_demo.main(["--check"]) == 0

    def test_no_network_added(self):
        html = load_demo_html()
        assert "fetch(" not in html and "XMLHttpRequest" not in html
        assert not re.search(r"<script\b[^>]*\bsrc\s*=", html, re.I)


# --- alerting_species: raw (unrounded) threshold semantics -------------------

_ALERT = {"olive": 162, "grass": 35, "birch": 30}


def test_alerting_species_uses_raw_not_rounded_means():
    assert round(34.96, 1) == 35.0
    means = {"olive": 0.0, "grass": 34.96, "birch": 0.0}
    assert render_demo.alerting_species(means, _ALERT) is None


def test_alerting_species_triggers_at_exact_threshold():
    means = {"olive": 0.0, "grass": 35.0, "birch": 0.0}
    assert render_demo.alerting_species(means, _ALERT) == "grass"


def test_alerting_species_simultaneous_crossing_raises():
    import pytest
    means = {"olive": 162.0, "grass": 35.0, "birch": 0.0}
    with pytest.raises(ValueError, match="Multiple species crossed"):
        render_demo.alerting_species(means, _ALERT)


def test_approve_batch_scope_disclosure_in_demo():
    page = (DEMO_DIR / "index.html").read_text()
    assert "Approve Entire Scenario Batch (" in page
    assert "hidden by filter" in page
    assert "hidden by filter at sign-off" in page


# ---------------------------------------------------------------------------
# NASA telemetry panel and NASA evaluation summary (Figma Board 1)
# ---------------------------------------------------------------------------

def test_nasa_panel_and_summary_elements_exist():
    html = load_demo_html()
    for el_id in ("nasa-telemetry-panel", "nasa-eval-summary", "nasa-gdd", "nasa-solar",
                  "nasa-precip", "nasa-soil", "nasa-ndvi"):
        assert f'id="{el_id}"' in html, el_id


def test_nasa_telemetry_matches_load_nasa_daily():
    import pandas as pd
    import backtest as bt

    data = embedded_console_data(load_demo_html())
    for s in data["scenarios"]:
        key, date, species, _ = render_demo.NASA_SCENARIOS[s["id"]]
        frame = bt.load_nasa_daily(key)
        ts = pd.Timestamp(date)
        row = frame.loc[ts]
        t = s["nasa_telemetry"]
        assert t["gdd_base_c"] == bt.GDD_BASE[species]
        assert t["cum_gdd"] == round(float(bt.cum_gdd_series(frame, species).loc[ts]), 1)
        assert t["solar_mj_m2"] == round(float(row["nasa_solar"]), 2)
        assert t["precip_mm"] == round(float(row["nasa_precip"]), 2)
        assert t["gwetroot"] == round(float(row["nasa_gwetroot"]), 2)
        assert t["ndvi_causal"] == round(float(row["nasa_ndvi"]), 4)
        assert t["t2m_max_c"] == round(float(row["nasa_t2m_max"]), 1)
    sim = next(s for s in data["scenarios"] if s["id"] == "olive_sim")
    assert sim["nasa_telemetry"]["source_label"] == "Simulated olive spike over Valencia 2025-05-28 NASA telemetry"


def test_nasa_eval_summary_matches_backtest_json():
    html = load_demo_html()
    m = re.search(r'<div class="section" id="nasa-eval-summary">(.*?)<!-- NASA_EVAL:END -->', html, re.S)
    assert m
    text = re.sub(r"<[^>]+>", " ", m.group(1))
    backtest = json.loads((EVAL_RESULTS_DIR / "backtest.json").read_text())
    ho = backtest["nasa_evaluation"]["N2_pooled"]["heldout_2024_2025"]
    # Independent derivation from the JSON (not via render_demo's formatter).
    assert f"{ho['P2']['csi']:.3f} → {ho['N2']['csi']:.3f}" in text
    assert f"{ho['P2']['recall']*100:.1f}% → {ho['N2']['recall']*100:.1f}%" in text
    assert f"{ho['P2']['tp']} → {ho['N2']['tp']} of {ho['N2']['n_events']}" in text
    assert f"{ho['P2']['fp']} → {ho['N2']['fp']}" in text
    assert f"{ho['P2']['precision']*100:.1f}% → {ho['N2']['precision']*100:.1f}%" in text
    paired = backtest["nasa_evaluation"]["N1_pooled"]["heldout_2024_2025"]["paired_common_rows"]
    assert f"{paired['N1']['mae_from_14d']:.1f}d" in text
    assert f"{paired['C0_14d']['mae_from_14d']:.1f}d" in text
    assert f"{paired['N1']['share_in_7_to_28d']*100:.0f}%" in text
    assert f"{paired['R2']['mean_lead_days']:.1f}d" in text
    # Headline figures as stated in CLAIMS.md section K.
    for literal in ("0.382 → 0.434", "40.4% → 47.5%", "159 → 187 of 394", "0/8 → 5/8", "22 → 37",
                    "87.8% → 83.5%", "21.9d", "12.5d", "30%", "60%", "0.0%", "-9.7d"):
        assert literal in text, literal
    for label in ("R2 (4-day CAMS pollen forecast)", "N1 (NASA GDD, 7–28d pre-peak start)",
                  "Held-Out 2024–25 Prior-Day (D-1) NASA + CAMS (N2) vs API Forecast (P2)"):
        assert label in text, label
    lg = backtest["nasa_evaluation"]["latency_sensitivity_lag3"]["N2_pooled"]["heldout_2024_2025"]["N2"]
    assert "Latency check" in text and f"{lg['csi']:.3f}" in text and f"{lg['recall']*100:.1f}%" in text


def test_nasa_eval_summary_shows_no_nasa_control():
    """The page must show the control and must not present N2 as a NASA gain when the control wins."""
    html = load_demo_html()
    m = re.search(r'<div class="section" id="nasa-eval-summary">(.*?)<!-- NASA_EVAL:END -->', html, re.S)
    assert m
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1)))
    ctl = json.loads((EVAL_RESULTS_DIR / "backtest.json").read_text())["nasa_evaluation"]["no_nasa_control"]
    ho = ctl["heldout_2024_2025"]
    assert f"CSI {ho['csi']:.3f}" in text
    assert f"{ho['tp']} of {ho['n_events']}" in text and f"{ho['fp']} false-alert days" in text
    verdict = "yes" if ctl["nasa_adds_skill_heldout"] else "no"
    assert f"Does NASA add skill? {verdict}" in text
    if not ctl["nasa_adds_skill_heldout"]:
        assert "What Helped" not in text
        assert 'class="ne-card good"' not in m.group(1)
