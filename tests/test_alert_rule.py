from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.alert_rule import trap_alerts  # noqa: E402

ALERT = json.loads((ROOT / "rules" / "thresholds.json").read_text())["alert"]


def test_at_threshold_alerts_below_does_not():
    t = ALERT["grass"]
    assert [a.species for a in trap_alerts({"grass": float(t)}, ALERT)] == ["grass"]
    assert trap_alerts({"grass": t - 0.1}, ALERT) == []


def test_missing_reading_never_alerts():
    assert trap_alerts({"grass": None, "olive": None}, ALERT) == []
    assert trap_alerts({}, ALERT) == []


def test_several_species_can_alert_together():
    got = {a.species for a in trap_alerts({"grass": 80, "olive": 200, "birch": 1}, ALERT)}
    assert got == {"grass", "olive"}


def test_reading_age_limited_to_preregistered_values():
    assert trap_alerts({"birch": 31}, ALERT, reading_age_days=2)[0].reading_age_days == 2
    with pytest.raises(ValueError):
        trap_alerts({"birch": 31}, ALERT, reading_age_days=3)


def test_matches_backtest_rule_p0_on_2026():
    """The product rule is exactly the pre-registered P0 on every scored 2026 day."""
    sys.path.insert(0, str(ROOT / "eval"))
    import nowcast as nc

    res = json.loads((ROOT / "eval" / "results" / "nowcast_2026.json").read_text())
    tp = 0
    for city, species_list in nc.bt.CITY_SPECIES.items():
        f = nc.frame_2021_2026(city)
        for sp in species_list:
            d = nc.scored_days(nc.features(f, city, sp, ALERT[sp], nc.DEV_YEARS))
            d = d[(d.index >= nc.TEST_START) & (d.index <= nc.TEST_END)]
            for _, row in d.iterrows():
                prev = None if row["obs_prev"] != row["obs_prev"] else row["obs_prev"]
                fired = bool(trap_alerts({sp: prev}, {sp: ALERT[sp]}))
                tp += fired and bool(row["high"])
    assert tp == res["pooled"]["P0"]["tp"] == 164
