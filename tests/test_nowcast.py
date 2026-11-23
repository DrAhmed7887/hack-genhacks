"""Offline tests for eval/nowcast.py (no network, no 2026 data)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import nowcast as nc  # noqa: E402


def test_logistic_recovers_sign_and_separates():
    rng = np.random.default_rng(0)
    x1 = rng.normal(size=2000)
    y = (rng.random(2000) < 1 / (1 + np.exp(-(2.0 * x1 - 0.5)))).astype(float)
    x = np.column_stack([np.ones_like(x1), x1])
    w = nc.fit_logistic(x, y, c=10.0)
    assert 1.5 < w[1] < 2.5 and -0.8 < w[0] < -0.2


def test_stronger_penalty_shrinks_weights():
    rng = np.random.default_rng(1)
    x1 = rng.normal(size=500)
    y = (x1 > 0).astype(float)
    x = np.column_stack([np.ones_like(x1), x1])
    assert abs(nc.fit_logistic(x, y, 0.01)[1]) < abs(nc.fit_logistic(x, y, 10.0)[1])


def test_conf_counts():
    m = nc.conf(np.array([1, 1, 0, 0], bool), np.array([1, 0, 1, 0], bool))
    assert (m["tp"], m["fp"], m["fn"]) == (1, 1, 1) and m["csi"] == pytest.approx(1 / 3)


def test_model_alert_never_fires_without_yesterdays_reading():
    d = pd.DataFrame({"lag1": [np.nan, 1.0]})
    assert nc.model_alert(d, np.array([0.99, 0.99]), 0.5).tolist() == [False, True]


def test_p0_missing_yesterday_counts_as_no_alert():
    d = pd.DataFrame({"species": ["grass", "grass"], "api": [0.0, 0.0],
                      "obs_prev": [np.nan, 50.0], "c0": [np.nan, True]})
    a = nc.baseline_alerts(d, {"grass": 35})
    assert a["P0"].tolist() == [False, True] and a["C0"].tolist() == [False, True]


def test_bootstrap_identical_rules_give_zero_difference():
    rng = np.random.default_rng(2)
    high = rng.random(200) < 0.2
    alert = rng.random(200) < 0.2
    boot = nc.block_bootstrap([{"high": high, "A": alert, "B": alert.copy()}], np.random.default_rng(3))
    assert np.all(boot["A"] - boot["B"] == 0)


def test_bootstrap_perfect_rule_beats_silent_rule():
    high = np.zeros(140, bool)
    high[30:60] = True
    boot = nc.block_bootstrap([{"high": high, "perfect": high.copy(), "silent": np.zeros(140, bool)}],
                              np.random.default_rng(4))
    assert np.percentile(boot["perfect"] - boot["silent"], 2.5) > 0


def test_features_use_only_past_trap_counts():
    idx = pd.date_range("2021-01-01", "2021-12-31", freq="D")
    obs = pd.Series(np.arange(len(idx), dtype=float), index=idx)
    f = pd.DataFrame({"obs_grass": obs, "api_grass": 1.0, "nasa_t2m_max": 1.0, "nasa_precip": 0.0,
                      "nasa_solar": 1.0, "nasa_ws2m": 1.0}, index=idx)
    d = nc.features(f, "madrid", "grass", 35, [2021])
    day = pd.Timestamp("2021-06-01")
    assert d.loc[day, "lag1"] == pytest.approx(np.log1p(obs[day - pd.Timedelta(days=1)]))
    assert d.loc[day, "lag2"] == pytest.approx(np.log1p(obs[day - pd.Timedelta(days=2)]))
    window = obs[day - pd.Timedelta(days=7): day - pd.Timedelta(days=1)]
    assert d.loc[day, "mean7"] == pytest.approx(np.log1p(window.mean()))


def test_2026_guard_refuses_without_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(nc, "OUT_LOCK", tmp_path / "absent.json")
    with pytest.raises(SystemExit, match="no eval/results/nowcast_lock.json"):
        nc.assert_lock_committed_and_pushed()
