"""Unit tests for eval/backtest.py's alert rule functions.

Expected values are written by hand against the rule definitions in
docs/DATA_PLAN.md section 2.3 *before* checking what the code produces,
on tiny, fully worked-through series. This is meant to catch bugs in the
pre-registered rule implementations independently of the real-data run.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
import backtest  # noqa: E402

T = 10.0
SPECIES = "grass"


def make_frame(obs, api, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(obs), freq="D")
    return pd.DataFrame({f"obs_{SPECIES}": obs, f"api_{SPECIES}": api}, index=idx)


# ---------------------------------------------------------------------------
# P0: Observed(D-1) >= T
# ---------------------------------------------------------------------------

def test_rule_P0_hand_worked_series():
    # obs: D1=5, D2=15, D3=20, D4=3, D5=25
    frame = make_frame(obs=[5, 15, 20, 3, 25], api=[0, 0, 0, 0, 0])
    result = backtest.rule_P0(frame, SPECIES, T)
    expected = [False, False, True, True, False]
    # D1 has no D-1 -> NaN, which is falsy for our purposes but let's check explicitly
    assert pd.isna(result.iloc[0])
    assert list(result.iloc[1:]) == expected[1:]


# ---------------------------------------------------------------------------
# P1: API(D-1) >= T
# ---------------------------------------------------------------------------

def test_rule_P1_hand_worked_series():
    # api: D1=5, D2=8, D3=12, D4=20, D5=25
    frame = make_frame(obs=[0, 0, 0, 0, 0], api=[5, 8, 12, 20, 25])
    result = backtest.rule_P1(frame, SPECIES, T)
    assert pd.isna(result.iloc[0])
    expected = [False, False, True, True]  # for D2..D5
    assert list(result.iloc[1:]) == expected


# ---------------------------------------------------------------------------
# P2: API(D) >= T
# ---------------------------------------------------------------------------

def test_rule_P2_hand_worked_series():
    frame = make_frame(obs=[0, 0, 0, 0, 0], api=[5, 8, 12, 20, 25])
    result = backtest.rule_P2(frame, SPECIES, T)
    expected = [False, False, True, True, True]
    assert list(result) == expected


# ---------------------------------------------------------------------------
# R1: mean(API(D-1), API(D)) >= T
# ---------------------------------------------------------------------------

def test_rule_R1_hand_worked_series():
    # api: D1=5, D2=8, D3=12, D4=20, D5=25
    # D2: mean(5,8)=6.5 < 10 -> False
    # D3: mean(8,12)=10.0 >= 10 -> True
    # D4: mean(12,20)=16.0 >= 10 -> True
    # D5: mean(20,25)=22.5 >= 10 -> True
    frame = make_frame(obs=[0, 0, 0, 0, 0], api=[5, 8, 12, 20, 25])
    result = backtest.rule_R1(frame, SPECIES, T)
    assert pd.isna(result.iloc[0])
    expected = [False, True, True, True]
    assert list(result.iloc[1:]) == expected


# ---------------------------------------------------------------------------
# R2 onset: first in-season day D where max(API(D..D+3)) >= T
# ---------------------------------------------------------------------------

def test_rule_R2_onset_day_hand_worked_series():
    # api: D1=5, D2=5, D3=5, D4=5, D5=15, D6=20
    # D1 window (D1..D4) = [5,5,5,5] max=5 -> no
    # D2 window (D2..D5) = [5,5,5,15] max=15 >= 10 -> fires at D2
    api = [5, 5, 5, 5, 15, 20]
    frame = make_frame(obs=[0] * 6, api=api)
    season_mask = np.ones(6, dtype=bool)
    onset = backtest.rule_R2_onset_day(frame, SPECIES, T, season_mask)
    assert onset == pd.Timestamp("2024-01-02")


def test_rule_R2_onset_day_none_when_never_crosses():
    api = [1, 2, 3, 4, 5, 6]
    frame = make_frame(obs=[0] * 6, api=api)
    season_mask = np.ones(6, dtype=bool)
    onset = backtest.rule_R2_onset_day(frame, SPECIES, T, season_mask)
    assert onset is None


def test_rule_R2_onset_day_respects_season_mask():
    # Even though D1's window would cross T, season_mask excludes D1 and D2.
    api = [20, 20, 20, 20, 20, 20]
    frame = make_frame(obs=[0] * 6, api=api)
    season_mask = np.array([False, False, True, True, True, True])
    onset = backtest.rule_R2_onset_day(frame, SPECIES, T, season_mask)
    assert onset == pd.Timestamp("2024-01-03")


# ---------------------------------------------------------------------------
# P2 onset day (for the onset comparison table)
# ---------------------------------------------------------------------------

def test_p2_onset_day_hand_worked_series():
    # api: D1=5, D2=5, D3=5, D4=5, D5=15, D6=20 -> first day api>=10 is D5
    api = [5, 5, 5, 5, 15, 20]
    frame = make_frame(obs=[0] * 6, api=api)
    season_mask = np.ones(6, dtype=bool)
    onset = backtest.p2_onset_day(frame, SPECIES, T, season_mask)
    assert onset == pd.Timestamp("2024-01-05")


# ---------------------------------------------------------------------------
# C0 climatology: day-of-year share of high days in PRIOR years >= 0.5
# ---------------------------------------------------------------------------

def test_rule_C0_two_years_majority_prior_high():
    # Year 2023 (prior): Jan-01 obs=20 (high, T=10), Jan-02 obs=1 (not high)
    # Year 2024 (evaluated): Jan-01, Jan-02 -- C0 looks only at 2023 as the
    # single prior year for each day-of-year.
    # Expected: 2024-01-01 fires (share of prior-year-high = 1/1 = 1.0 >= 0.5)
    #           2024-01-02 does not fire (share = 0/1 = 0.0 < 0.5)
    idx = pd.to_datetime(["2023-01-01", "2023-01-02", "2024-01-01", "2024-01-02"])
    frame = pd.DataFrame(
        {f"obs_{SPECIES}": [20, 1, 0, 0], f"api_{SPECIES}": [0, 0, 0, 0]}, index=idx
    )
    result = backtest.rule_C0(frame, SPECIES, T)
    # 2023 rows: no prior year at all -> NaN share -> rule does not fire (False)
    assert result.iloc[0] == False  # noqa: E712
    assert result.iloc[1] == False  # noqa: E712
    # 2024 rows: judged against 2023 only
    assert result.iloc[2] == True  # noqa: E712  (2024-01-01, prior share 1.0)
    assert result.iloc[3] == False  # noqa: E712  (2024-01-02, prior share 0.0)


def test_rule_C0_undefined_with_missing_prior_data_is_not_fired():
    # If the only prior-year value for that day-of-year is NaN (missing
    # observed data), C0 cannot compute a share and must not fire.
    idx = pd.to_datetime(["2023-01-01", "2024-01-01"])
    frame = pd.DataFrame(
        {f"obs_{SPECIES}": [np.nan, 0], f"api_{SPECIES}": [0, 0]}, index=idx
    )
    result = backtest.rule_C0(frame, SPECIES, T)
    assert result.iloc[1] == False  # noqa: E712


# ---------------------------------------------------------------------------
# day_alert_metrics: recall / precision / CSI / false-alert-days on a tiny,
# fully hand-counted confusion matrix
# ---------------------------------------------------------------------------

def test_day_alert_metrics_hand_counted():
    # obs_high: T F T T F  (2 events... wait, 3 True: idx0,2,3)
    obs_high = pd.Series([True, False, True, True, False])
    # alert:    T F F T T
    alert = pd.Series([True, False, False, True, True])
    # tp = idx0 (T,T), idx3 (T,T) = 2
    # fp = idx4 (F,T) = 1
    # fn = idx2 (T,F) = 1
    # tn = idx1 (F,F) = 1
    # n_events (obs_high True) = 3
    metrics = backtest.day_alert_metrics(obs_high, alert)
    assert metrics["tp"] == 2
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert metrics["tn"] == 1
    assert metrics["n_events"] == 3
    assert metrics["n_evaluated_days"] == 5
    assert metrics["recall"] == pytest.approx(2 / 3)
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["csi"] == pytest.approx(2 / 4)  # tp / (tp+fp+fn) = 2/4
    assert metrics["false_alert_days"] == 1


def test_day_alert_metrics_excludes_nan_rows_from_denominator():
    # Row 2 has a NaN alert and must be excluded entirely (not counted as
    # a miss, not counted as a false alert).
    obs_high = pd.Series([True, False, True])
    alert = pd.Series([True, False, np.nan])
    metrics = backtest.day_alert_metrics(obs_high, alert)
    assert metrics["n_evaluated_days"] == 2
    assert metrics["n_events"] == 1
    assert metrics["tp"] == 1
    assert metrics["recall"] == pytest.approx(1.0)
