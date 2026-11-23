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
    # 2023 rows: no prior year at all -> not evaluable -> NaN (never False,
    # per the NaN-consistency fix: NaN = not evaluable, excluded, not a
    # "rule did not fire" result).
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    # 2024 rows: judged against 2023 only
    assert result.iloc[2] == True  # noqa: E712  (2024-01-01, prior share 1.0)
    assert result.iloc[3] == False  # noqa: E712  (2024-01-02, prior share 0.0)


def test_rule_C0_undefined_with_missing_prior_data_is_not_fired():
    # If the only prior-year value for that day-of-year is NaN (missing
    # observed data), C0 cannot compute a share: it must be NaN (not
    # evaluable), never collapsed to False.
    idx = pd.to_datetime(["2023-01-01", "2024-01-01"])
    frame = pd.DataFrame(
        {f"obs_{SPECIES}": [np.nan, 0], f"api_{SPECIES}": [0, 0]}, index=idx
    )
    result = backtest.rule_C0(frame, SPECIES, T)
    assert pd.isna(result.iloc[1])


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


# ---------------------------------------------------------------------------
# Fix 1: season_block_bootstrap_recall must weight resampled seasons by
# draw count (concatenate per-year row slices once per draw), not treat
# the sampled years as a set via years.isin().
# ---------------------------------------------------------------------------

class _FixedDrawRNG:
    """Minimal stand-in for np.random.Generator that always returns the
    same fixed draw from .choice(), so the resampled recall is fully
    hand-computable instead of depending on the real RNG stream."""

    def __init__(self, fixed_draw):
        self._fixed_draw = np.array(fixed_draw)

    def choice(self, a, size=None, replace=True):
        assert len(self._fixed_draw) == size
        return self._fixed_draw


def test_season_block_bootstrap_recall_weights_by_draw_count():
    # Three season-years, one row of ground truth each:
    #   2021: obs_high=True,  alert=True   -> tp=1, events=1 (recall 1.0 alone)
    #   2022: obs_high=True,  alert=False  -> tp=0, events=1 (recall 0.0 alone)
    #   2023: obs_high=True,  alert=True   -> tp=1, events=1 (recall 1.0 alone, never drawn below)
    # Fixed draw = [2021, 2021, 2022] (2021 drawn twice, 2022 once, 2023 never).
    #
    # Correct (weighted by draw count): 2021's row is counted TWICE and
    # 2022's row ONCE in that bootstrap replicate's confusion matrix:
    #   events = 1 + 1 + 1 = 3, tp = 1 + 1 + 0 = 2 -> recall = 2/3.
    # Buggy (years.isin(sample_years), a set-membership mask): the
    # duplicate draw of 2021 collapses back to its rows ONCE, same as a
    # single draw of 2022:
    #   events = 1 + 1 = 2, tp = 1 + 0 = 1 -> recall = 1/2.
    # These two values (2/3 vs 1/2) are different, so this test
    # discriminates the fix from the bug.
    idx = pd.to_datetime(["2021-06-01", "2022-06-01", "2023-06-01"])
    years = idx.year
    obs_high = pd.Series([True, True, True], index=idx)
    alert = pd.Series([True, False, True], index=idx)

    fixed_rng = _FixedDrawRNG([2021, 2021, 2022])
    lo, hi = backtest.season_block_bootstrap_recall(
        obs_high, alert, years, fixed_rng, n_boot=1
    )
    assert lo == pytest.approx(2 / 3)
    assert hi == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# Fix 2: season windows must be derived from TRAINING years only
# (2021-2023), via a 7-day centred rolling mean of the training-years
# mean observed count, clipped to the named-month outer bound.
# ---------------------------------------------------------------------------

def test_compute_season_bounds_ignores_non_training_years():
    # 2021-2023 (training): obs = 0 everywhere, so the rolling mean never
    # reaches 1 grain/m3 inside the named months -> falls back to the
    # named-month outer bound itself.
    # 2024-2025 (held out): obs = 1000 every single day, which WOULD blow
    # the window open to the full year if it were allowed to influence
    # the window. It must be ignored entirely.
    dates = pd.date_range("2021-01-01", "2025-12-31", freq="D")
    obs = pd.Series(0.0, index=dates)
    obs[(dates.year >= 2024)] = 1000.0
    frame = pd.DataFrame({f"obs_{SPECIES}": obs, f"api_{SPECIES}": 0.0}, index=dates)

    bounds = backtest.compute_season_bounds(frame, SPECIES)
    # grass named-month outer bound is Mar 1 - Jul 31 (DATA_PLAN 2.3).
    expected_start = pd.Timestamp(2023, 3, 1).dayofyear
    expected_end = pd.Timestamp(2023, 7, 31).dayofyear
    assert bounds["start_doy"] == expected_start
    assert bounds["end_doy"] == expected_end


def test_compute_season_bounds_rolling_mean_and_named_month_clip():
    # Training years 2021-2023, species "birch" (named months Mar 1 - Apr 30).
    # Put a brief >=1 grain/m3 bump entirely in Feb (before birch's named
    # window) in every training year: the robust rolling-mean rule would
    # otherwise pick it up, but the named-month outer bound must clip it
    # out, since Feb is before Mar 1.
    dates = pd.date_range("2021-01-01", "2023-12-31", freq="D")
    obs = pd.Series(0.0, index=dates)
    for y in [2021, 2022, 2023]:
        bump = pd.date_range(f"{y}-02-10", f"{y}-02-20", freq="D")
        obs.loc[bump] = 5.0  # well above 1 grain/m3, every training year
    frame = pd.DataFrame({"obs_birch": obs, "api_birch": 0.0}, index=dates)

    bounds = backtest.compute_season_bounds(frame, "birch")
    # Since the only >=1 activity is in Feb, outside birch's Mar-Apr
    # named-month bound, the data-driven window has nothing left inside
    # the bound and the rule falls back to the named-month bound itself.
    expected_start = pd.Timestamp(2023, 3, 1).dayofyear
    expected_end = pd.Timestamp(2023, 4, 30).dayofyear
    assert bounds["start_doy"] == expected_start
    assert bounds["end_doy"] == expected_end


def test_season_window_rule_string_present_in_backtest_module():
    # The exact rule must be a fixed string the script can write verbatim
    # into backtest.json (task requirement: "write the exact rule string
    # into backtest.json").
    assert "7-day centred rolling mean" in backtest.SEASON_WINDOW_RULE
    assert "2021-2023" in backtest.SEASON_WINDOW_RULE
    assert backtest.TRAINING_YEARS == [2021, 2022, 2023]


# ---------------------------------------------------------------------------
# Fix 3: kill-check R2 bootstrap (_bootstrap_lead_day_diff) must resample
# season-years (blocks), not individual city-species-year rows.
# ---------------------------------------------------------------------------

def test_bootstrap_lead_day_diff_weights_by_season_year_draw_count():
    # Three onset rows, one per year, each year has exactly one
    # city-species row in this tiny example:
    #   2021: R2_lead=2, P2_lead=0  -> diff = 2
    #   2022: R2_lead=0, P2_lead=4  -> diff = -4
    #   2023: R2_lead=3, P2_lead=1  -> diff = 2   (never drawn below)
    # Fixed draw = [2021, 2021, 2022] (2021's row counted twice, 2022's once).
    # Weighted-by-season-year mean diff = (2 + 2 + (-4)) / 3 = 0.0.
    # A flat per-row bootstrap over the 3 rows (ignoring which year each
    # row belongs to) would instead draw 3 *rows* independently with
    # replacement and could never reproduce this exact multiset from a
    # year-level draw of size 2, showing the two resampling units differ.
    onset_rows = [
        {"city": "basel", "species": "birch", "year": "2021", "R2_lead_days": 2, "P2_lead_days": 0, "C0_lead_days": None},
        {"city": "basel", "species": "birch", "year": "2022", "R2_lead_days": 0, "P2_lead_days": 4, "C0_lead_days": None},
        {"city": "basel", "species": "birch", "year": "2023", "R2_lead_days": 3, "P2_lead_days": 1, "C0_lead_days": None},
    ]
    fixed_rng = _FixedDrawRNG(["2021", "2021", "2022"])
    result = backtest._bootstrap_lead_day_diff(
        onset_rows, "R2_lead_days", "P2_lead_days", fixed_rng, n_boot=1
    )
    assert result["ci95"][0] == pytest.approx(0.0)
    assert result["ci95"][1] == pytest.approx(0.0)
    # Point estimate (over the real, non-resampled data) is unaffected by
    # the bootstrap resampling unit: mean(2, -4, 2) = 0.0.
    assert result["mean_diff"] == pytest.approx(0.0)


def test_bootstrap_lead_day_diff_multiple_rows_per_year_move_together():
    # Two city-species rows both in year 2021, one row in year 2022.
    # A year-block bootstrap must draw and duplicate BOTH 2021 rows
    # together, never one without the other.
    onset_rows = [
        {"city": "basel", "species": "birch", "year": "2021", "R2_lead_days": 5, "P2_lead_days": 0, "C0_lead_days": None},
        {"city": "zurich", "species": "birch", "year": "2021", "R2_lead_days": 3, "P2_lead_days": 1, "C0_lead_days": None},
        {"city": "basel", "species": "grass", "year": "2022", "R2_lead_days": 0, "P2_lead_days": 0, "C0_lead_days": None},
    ]
    # Draw 2021 twice and 2022 never: both of 2021's rows appear twice
    # each in that replicate. Row diffs for 2021: basel = 5-0 = 5,
    # zurich = 3-1 = 2 -> replicate diffs = [5, 2, 5, 2], mean = 3.5.
    # Both distinct years (2021, 2022) are present in the input so the
    # function takes the real bootstrap path, not the <2-season-blocks
    # early return.
    fixed_rng = _FixedDrawRNG(["2021", "2021"])
    result = backtest._bootstrap_lead_day_diff(
        onset_rows, "R2_lead_days", "P2_lead_days", fixed_rng, n_boot=1,
    )
    assert result["ci95"][0] == pytest.approx(3.5)
    assert result["ci95"][1] == pytest.approx(3.5)


# ---------------------------------------------------------------------------
# Fix 4: NaN must be treated consistently (not evaluable, excluded,
# never coerced to False) in p2_onset_day, climatology_onset_day,
# rule_R2_onset_day and rule_C0.
# ---------------------------------------------------------------------------

def test_rule_C0_never_returns_false_for_nan_input_row():
    # Rows with no prior-year data at all must stay NaN, not False,
    # anywhere they occur, including beyond just the first year.
    idx = pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"])
    frame = pd.DataFrame(
        {f"obs_{SPECIES}": [np.nan, np.nan, 5], f"api_{SPECIES}": [0, 0, 0]}, index=idx
    )
    result = backtest.rule_C0(frame, SPECIES, T)
    # 2021: no prior year -> NaN.
    assert pd.isna(result.iloc[0])
    # 2022: only prior year (2021) is itself NaN -> still not evaluable -> NaN.
    assert pd.isna(result.iloc[1])
    # 2023: prior years are 2021 (NaN) and 2022 (NaN) -> still NaN.
    assert pd.isna(result.iloc[2])


def test_p2_onset_day_skips_nan_without_firing():
    # api: D1=NaN, D2=NaN, D3=15 (>=T) -- onset must land on D3, a NaN day
    # must never be treated as a crossing (NaN >= T is False in pandas,
    # but it must be *skipped*, not silently treated as "evaluated and
    # did not cross", which matters once season_mask windows change).
    api = [np.nan, np.nan, 15]
    frame = make_frame(obs=[0, 0, 0], api=api)
    season_mask = np.ones(3, dtype=bool)
    onset = backtest.p2_onset_day(frame, SPECIES, T, season_mask)
    assert onset == pd.Timestamp("2024-01-03")


def test_rule_R2_onset_day_skips_entirely_nan_window():
    # D1's window (D1..D4) is entirely NaN -> not evaluable, must be
    # skipped rather than crashing or firing. D2's window includes a real
    # value >= T, so onset must land on D2.
    api = [np.nan, np.nan, np.nan, np.nan, 15, 20]
    frame = make_frame(obs=[0] * 6, api=api)
    season_mask = np.ones(6, dtype=bool)
    onset = backtest.rule_R2_onset_day(frame, SPECIES, T, season_mask)
    assert onset == pd.Timestamp("2024-01-02")


def test_climatology_onset_day_skips_nan_c0_without_firing():
    # c0_alerts has NaN on D1 (not evaluable) and True on D2. bool(nan) is
    # True in Python, so a naive bool() cast would incorrectly fire on
    # D1; the fix must skip NaN rows instead.
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    frame = make_frame(obs=[0, 0, 0], api=[0, 0, 0], start="2024-01-01")
    c0_alerts = pd.Series([np.nan, True, False], index=idx)
    season_mask = np.ones(3, dtype=bool)
    onset = backtest.climatology_onset_day(frame, SPECIES, c0_alerts, season_mask)
    assert onset == pd.Timestamp("2024-01-02")


# ---------------------------------------------------------------------------
# Fix 5: C0 must match prior years on (month, day), not day-of-year, so a
# leap year doesn't shift every date after Feb 29 by one day relative to
# a non-leap year.
# ---------------------------------------------------------------------------

def test_rule_C0_matches_on_month_day_not_dayofyear_across_leap_year():
    # 2024 is a leap year. DOY 61 is 2024-03-01 but DOY 61 in a non-leap
    # year (e.g. 2025) is 2025-03-02. If C0 matched on day-of-year, the
    # 2025-03-02 evaluated row would incorrectly pick up 2024-03-01's
    # prior value (DOY 61 in both only by coincidence of the leap shift)
    # instead of 2024-03-02's.
    # Prior year 2024 (leap): Mar-01 obs=0 (not high), Mar-02 obs=20 (high, T=10).
    # Evaluated year 2025 (non-leap): Mar-02.
    # Correct (month-day matching): 2025-03-02 is judged against
    # 2024-03-02 (high) -> share = 1/1 = 1.0 -> fires (True).
    # Buggy (day-of-year matching): 2025-03-02 is DOY 61, which in leap
    # 2024 is 2024-03-01 (not high) -> share = 0/1 = 0.0 -> would not fire.
    idx = pd.to_datetime(["2024-03-01", "2024-03-02", "2025-03-02"])
    frame = pd.DataFrame(
        {f"obs_{SPECIES}": [0, 20, 0], f"api_{SPECIES}": [0, 0, 0]}, index=idx
    )
    result = backtest.rule_C0(frame, SPECIES, T)
    assert result.iloc[2] == True  # noqa: E712


# ---------------------------------------------------------------------------
# Fix 6: MeteoSwiss reference_timestamp convention (verified against the
# live parameter dictionary and daily data file, recorded in
# data/DATA_CARD.md) confirms API(D) should be built from
# [D 06:00 UTC, (D+1) 06:00 UTC), which load_open_meteo_api_daily already
# implements via a shift-back-6h-then-floor. This test locks that
# alignment in so it cannot silently drift.
# ---------------------------------------------------------------------------

def test_open_meteo_basel_zurich_alignment_matches_verified_6_6_window():
    import pandas as _pd
    hours = _pd.date_range("2024-06-01T00:00:00", periods=30, freq="h")
    df = _pd.DataFrame({
        "time_utc": hours.strftime("%Y-%m-%dT%H:%M"),
        "olive_pollen": 0.0,
        "grass_pollen": [float(h.hour) for h in hours],  # hour-of-day marker
        "birch_pollen": 0.0,
    })
    # A reading at 2024-06-01T06:00 through 2024-06-02T05:00 belongs to
    # the window labelled 2024-06-01 (per the verified
    # "6 UTC - 6 UTC following day" convention); 2024-06-01T00:00-05:00
    # belongs to the PRIOR day's window (2024-05-31).
    df["time_utc"] = _pd.to_datetime(df["time_utc"])
    shifted = (df["time_utc"] - _pd.Timedelta(hours=6)).dt.floor("D")
    first_hour_label = shifted.iloc[0]  # 2024-06-01T00:00 -> labelled day
    hour_six_label = shifted.iloc[6]    # 2024-06-01T06:00 -> labelled day
    assert first_hour_label == _pd.Timestamp("2024-05-31")
    assert hour_six_label == _pd.Timestamp("2024-06-01")


# ---------------------------------------------------------------------------
# NASA POWER + MODIS NDVI: cache integrity, causal NDVI join, and
# training-years-only calibration for N1 and N2.
# ---------------------------------------------------------------------------

NASA_KEYS = ["madrid_facf", "basel_pbs", "zurich_pzh", "valencia_demo"]
POWER_HEADER = ["date", "t2m", "t2m_max", "t2m_min", "prectotcorr",
                "allsky_sfc_sw_dwn", "rh2m", "gwetroot", "ws2m"]


@pytest.mark.parametrize("key", NASA_KEYS)
def test_nasa_power_cache_columns_and_dates(key):
    df = pd.read_csv(backtest.CACHE_DIR / f"nasa_power_{key}.csv", parse_dates=["date"])
    assert list(df.columns) == POWER_HEADER
    assert df["date"].min() == pd.Timestamp("2021-01-01")
    assert df["date"].max() == pd.Timestamp("2025-12-31")
    assert len(df) == 1826
    assert df["date"].is_unique
    # -999 fill values must have been converted to blanks
    assert not (df.drop(columns="date") <= -998).any().any()


@pytest.mark.parametrize("key", NASA_KEYS)
def test_nasa_modis_cache_columns_and_dates(key):
    df = pd.read_csv(backtest.CACHE_DIR / f"nasa_modis_{key}.csv", parse_dates=["date"])
    assert list(df.columns) == ["date", "modis_date", "ndvi"]
    # includes a Dec 2020 composite so 1 Jan 2021 has a prior causal value
    assert df["date"].min() < pd.Timestamp("2021-01-01")
    assert df["date"].min() >= pd.Timestamp("2020-12-01")
    assert df["date"].max() <= pd.Timestamp("2025-12-31")
    assert df["ndvi"].dropna().between(-0.2, 1.0).all()


def test_modis_forward_fill_never_leaks_future_composites():
    """A composite stamped T is usable only from T+16d (avail_date <= D)."""
    lag = pd.Timedelta(days=16)
    for key in NASA_KEYS:
        daily = backtest.load_nasa_daily(key)
        modis = pd.read_csv(backtest.CACHE_DIR / f"nasa_modis_{key}.csv", parse_dates=["date"]).dropna(subset=["ndvi"])
        modis = modis.assign(avail=modis["date"] + lag).sort_values("avail")
        # every filled value equals the latest valid composite with avail <= D
        for d in daily.index[::37]:
            prior = modis[modis["avail"] <= d]
            expected = prior["ndvi"].iloc[-1] if len(prior) else np.nan
            got = daily.loc[d, "nasa_ndvi"]
            assert (np.isnan(expected) and np.isnan(got)) or got == pytest.approx(expected)
        # a composite never appears before its own completion date
        for _, row in modis[modis["avail"] >= "2021-01-02"].iterrows():
            before = row["avail"] - pd.Timedelta(days=1)
            if before in daily.index:
                prev = modis[modis["avail"] <= before]["ndvi"].iloc[-1]
                assert daily.loc[before, "nasa_ndvi"] == pytest.approx(prev)
            if row["avail"] in daily.index:
                assert daily.loc[row["avail"], "nasa_ndvi"] == pytest.approx(row["ndvi"])
    # first composite 2020-12-02 is available 2020-12-18, before 2021-01-01
    first = pd.read_csv(backtest.CACHE_DIR / "nasa_modis_madrid_facf.csv", parse_dates=["date"])["date"].min()
    assert first + lag <= pd.Timestamp("2021-01-01")
    assert not backtest.load_nasa_daily("madrid_facf")["nasa_ndvi"].isna().any()


def _synthetic_nasa_frame():
    idx = pd.date_range("2021-01-01", "2025-12-31", freq="D")
    doy = idx.dayofyear.values
    tmax = 10 + 15 * np.sin((doy - 100) / 365 * 2 * np.pi) + (idx.year.values - 2021) * 0.3
    obs = np.where((doy >= 90) & (doy <= 150), 50.0, 0.0)
    api = np.where((doy >= 92) & (doy <= 148), 30.0, 1.0)
    return pd.DataFrame({
        "obs_grass": obs, "api_grass": api,
        "nasa_t2m_max": tmax, "nasa_t2m_min": tmax - 8, "nasa_t2m": tmax - 4,
        "nasa_precip": (doy % 7 == 0) * 6.0, "nasa_solar": 15 + 5 * np.sin(doy / 58.0),
        "nasa_gwetroot": 0.5, "nasa_ndvi": 0.4,
    }, index=idx)


def test_n1_n2_calibration_ignores_heldout_years():
    base = _synthetic_nasa_frame()
    mutated = base.copy()
    held = mutated.index.year >= 2024
    for col in ["obs_grass", "api_grass", "nasa_t2m_max", "nasa_t2m_min", "nasa_precip", "nasa_solar", "nasa_ndvi", "nasa_gwetroot"]:
        mutated.loc[held, col] = np.random.default_rng(0).uniform(0, 1000, held.sum())
    thr = 10.0
    assert backtest.calibrate_n1(base, "grass", thr) == backtest.calibrate_n1(mutated, "grass", thr)
    assert backtest.calibrate_n2(base, "grass", thr) == backtest.calibrate_n2(mutated, "grass", thr)
    assert backtest.calibrate_n1(base, "grass", thr)["train_years_used"] == [2021, 2022, 2023]


def test_n1_gdd_target_is_median_of_training_cum_gdd_at_minus_14d():
    frame = _synthetic_nasa_frame()
    calib = backtest.calibrate_n1(frame, "grass", 10.0)
    cum = backtest.cum_gdd_series(frame, "grass")
    vals = [cum.loc[pd.Timestamp(y, 1, 1) + pd.Timedelta(days=89 - 14)] for y in (2021, 2022, 2023)]
    assert calib["gdd_target"] == pytest.approx(float(np.median(vals)))


def test_rule_N2_washout_and_nan_handling():
    # N2 reads PRIOR-day NASA values: row i uses the NASA fields of row i-1.
    idx = pd.date_range("2024-04-01", periods=5, freq="D")
    f = pd.DataFrame({
        "api_grass": [8.0, 8.0, 8.0, 8.0, np.nan],
        "nasa_precip": [0.0, 0.0, 0.0, 6.0, 0.0],
        "nasa_solar": [20.0, 5.0, 20.0, 20.0, 20.0],
        "nasa_t2m_max": [25.0, 25.0, 25.0, 25.0, 25.0],
    }, index=idx)
    res = backtest.rule_N2(f, "grass", 10.0, 1.5, True, 10.0, 15.0)
    assert res.iloc[0] == False  # no prior day (NaN) -> no boost, unscaled 8 < 10  # noqa: E712
    assert res.iloc[1] == True   # prior day dry, sunny, warm: 8*1.5=12 >= 10  # noqa: E712
    assert res.iloc[2] == False  # prior day not sunny -> no boost  # noqa: E712
    assert res.iloc[3] == True   # prior day dry/sunny/warm -> boost  # noqa: E712
    assert pd.isna(res.iloc[4])  # NaN API stays NaN


def test_rule_N2_washout_uses_prior_day_precip():
    idx = pd.date_range("2024-04-01", periods=3, freq="D")
    f = pd.DataFrame({
        "api_grass": [20.0, 20.0, 20.0],
        "nasa_precip": [6.0, 0.0, 0.0],
        "nasa_solar": [20.0] * 3,
        "nasa_t2m_max": [25.0] * 3,
    }, index=idx)
    res = backtest.rule_N2(f, "grass", 10.0, 1.0, True, 10.0, 15.0)
    assert res.iloc[1] == False  # prior day 6 mm -> washed out despite API 20  # noqa: E712
    assert res.iloc[2] == True   # prior day dry  # noqa: E712


def test_rule_N2_invariant_to_same_day_nasa_power():
    """Zero same-day hindsight: mutating NASA POWER on day D cannot change N2(D)."""
    base = _synthetic_nasa_frame()
    solar_med, tmax_med = 17.0, 12.0
    ref = backtest.rule_N2(base, "grass", 10.0, 2.0, True, solar_med, tmax_med)
    rng = np.random.default_rng(1)
    for d in rng.choice(np.arange(1, len(base)), size=60, replace=False):
        mutated = base.copy()
        for col in ("nasa_solar", "nasa_t2m_max", "nasa_precip"):
            mutated.iloc[d, mutated.columns.get_loc(col)] = rng.uniform(-50, 500)
        out = backtest.rule_N2(mutated, "grass", 10.0, 2.0, True, solar_med, tmax_med)
        assert out.iloc[d].__eq__(ref.iloc[d]) or (pd.isna(out.iloc[d]) and pd.isna(ref.iloc[d]))
        # and the mutation DOES matter for day D+1 for at least some rows (sanity checked below)
    flipped = 0
    for d in range(1, len(base) - 1, 7):
        mutated = base.copy()
        mutated.iloc[d, mutated.columns.get_loc("nasa_precip")] = 100.0
        out = backtest.rule_N2(mutated, "grass", 10.0, 2.0, True, solar_med, tmax_med)
        flipped += int(out.iloc[d + 1] != ref.iloc[d + 1])
    assert flipped > 0


def test_no_nasa_control_ignores_nasa_inputs_and_equals_scaled_api():
    """The control is API(D) x k on every day: NASA columns cannot change it, washout is ignored."""
    base = _synthetic_nasa_frame()
    ref = backtest.rule_N2(base, "grass", 10.0, 2.0, True, 17.0, 12.0, use_nasa=False)
    mutated = base.copy()
    for col in ("nasa_solar", "nasa_t2m_max", "nasa_precip"):
        mutated[col] = np.random.default_rng(2).uniform(-50, 500, len(mutated))
    out = backtest.rule_N2(mutated, "grass", 10.0, 2.0, True, 17.0, 12.0, use_nasa=False)
    pd.testing.assert_series_equal(ref, out)
    expected = backtest._ge_threshold_preserving_nan(base["api_grass"] * 2.0, 10.0)
    pd.testing.assert_series_equal(ref, expected)


def test_no_nasa_control_with_k1_equals_p2():
    base = _synthetic_nasa_frame()
    control = backtest.rule_N2(base, "grass", 10.0, 1.0, False, 0.0, 0.0, use_nasa=False)
    pd.testing.assert_series_equal(control, backtest.rule_P2(base, "grass", 10.0), check_names=False)


def test_no_nasa_control_calibration_ignores_heldout_years():
    base = _synthetic_nasa_frame()
    mutated = base.copy()
    held = mutated.index.year >= 2024
    for col in ("obs_grass", "api_grass"):
        mutated.loc[held, col] = np.random.default_rng(3).uniform(0, 1000, held.sum())
    a = backtest.calibrate_n2(base, "grass", 10.0, use_nasa=False)
    b = backtest.calibrate_n2(mutated, "grass", 10.0, use_nasa=False)
    assert (a["k"], a["washout"]) == (b["k"], b["washout"])
    assert a["washout"] is False
