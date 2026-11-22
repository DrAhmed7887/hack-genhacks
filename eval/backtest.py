#!/usr/bin/env python3
"""PollenPlan pre-registered backtest.

Implements, exactly as written in docs/DATA_PLAN.md section 2.3 (no rule
is added, tuned, or dropped after seeing results, per
.kiro/steering/rules.md):

    P0  Observed(D-1) >= T                         persistence baseline
    P1  API(D-1) >= T                               API persistence
    P2  API(D) >= T                                 the API's own forecast (kill-check baseline)
    R1  mean(API(D-1), API(D)) >= T                 PollenPlan day rule, two-day exposure
    R2  first day of season where max(API(D..D+3)) >= T   onset / pre-peak alert
    C0  day-of-year share of high days in prior years >= 0.5   climatology, no model

Thresholds are read, never edited, from rules/thresholds.json (status
signed 22 Nov 2026). Ground truth:
    Madrid (FACF): olive, grass   -- Comunidad de Madrid, window UNVERIFIED
    Basel  (PBS):  birch, grass   -- MeteoSwiss, 6 UTC - 6 UTC
    Zurich (PZH):  birch, grass   -- MeteoSwiss, 6 UTC - 6 UTC
Valencia is demo-only and is never scored (enforced by simply never being
in CITY_SPECIES below).

Runs fully offline from data/cache/ (no network, no key). Outputs:
    eval/results/backtest.json   (includes "thresholds_status": "signed")
    eval/results/misses.csv
    docs/results_table.md
"""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
CACHE_DIR = REPO_ROOT / "data" / "cache"
RESULTS_DIR = HERE / "results"
DOCS_DIR = REPO_ROOT / "docs"
THRESHOLDS_PATH = REPO_ROOT / "rules" / "thresholds.json"

RNG_SEED = 20261120  # reuse the project seed for the bootstrap, for reproducibility
N_BOOTSTRAP = 2000

YEARS = [2021, 2022, 2023, 2024, 2025]
TRAINING_YEARS = [2021, 2022, 2023]  # DATA_PLAN 2.3: season windows are derived from training years only

# DATA_PLAN 2.3: "Season means: olive Apr-Jun, grass Mar-Jul, birch Mar-Apr,
# as defined from observed data in the training years". These named months
# are the outer bound: the data-driven window (see compute_season_bounds)
# is clipped to fall within them, so a noisy pre/post-season blip in the
# training years can never push the scored season outside the named months.
NAMED_MONTH_BOUNDS = {
    "olive": (4, 1, 6, 30),   # Apr 1 - Jun 30
    "grass": (3, 1, 7, 31),   # Mar 1 - Jul 31
    "birch": (3, 1, 4, 30),   # Mar 1 - Apr 30
}

SEASON_WINDOW_RULE = (
    "Season window = first and last day-of-year, within the named-month "
    "outer bound (olive Apr-Jun, grass Mar-Jul, birch Mar-Apr), where the "
    "training-years (2021-2023) mean of observed daily counts, after a "
    "7-day centred rolling mean (min_periods=1) computed per training "
    "year and then averaged day-of-year across those training years, is "
    ">= 1 grain/m3. Training years only (2021-2023) are used to derive "
    "the window; 2024-2025 are held out and never influence it."
)

# city -> (open_meteo cache file stem, ground-truth kind, ground-truth file(s), species list)
CITY_SPECIES = {
    "madrid": ["olive", "grass"],
    "basel": ["birch", "grass"],
    "zurich": ["birch", "grass"],
}

OPEN_METEO_FILES = {
    "madrid": "open_meteo_madrid_facf.csv",
    "basel": "open_meteo_basel_pbs.csv",
    "zurich": "open_meteo_zurich_pzh.csv",
}

OPEN_METEO_COLUMN = {"olive": "olive_pollen", "grass": "grass_pollen", "birch": "birch_pollen"}

RULE_IDS = ["P0", "P1", "P2", "R1", "C0"]  # day-alert rules scored the same way
ONSET_RULE_IDS = ["R2", "P2", "C0"]  # onset comparison per DATA_PLAN 2.4


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_thresholds() -> dict:
    with THRESHOLDS_PATH.open() as f:
        return json.load(f)


def load_open_meteo_api_daily(city: str) -> pd.DataFrame:
    """Aggregate Open-Meteo hourly data to one daily value per species.

    Madrid: averaging window is UNVERIFIED for the observed ground truth
    (data/DATA_CARD.md section 3), so the API series for Madrid is
    aggregated on plain calendar-day UTC (00:00-23:00) to match the only
    window the ground truth can be interpreted on.

    Basel/Zurich: aggregated on the MeteoSwiss-confirmed 6 UTC - 6 UTC
    (following day) window, so API(D) lines up with Observed(D) exactly
    as MeteoSwiss defines its own daily value (data/DATA_CARD.md section
    2). The reference_timestamp convention (the labelled date is the
    *start* of the 6 UTC-6 UTC window, not its end) was verified live
    against MeteoSwiss's own parameter dictionary and daily data file on
    22 Nov 2026; see data/DATA_CARD.md section 2 for the quoted source
    and URL. The shift-back-6h-then-floor below already implements that
    exact window ([D 06:00 UTC, (D+1) 06:00 UTC) -> D), unchanged by the
    verification.
    """
    path = CACHE_DIR / OPEN_METEO_FILES[city]
    df = pd.read_csv(path)
    df["time_utc"] = pd.to_datetime(df["time_utc"])

    if city == "madrid":
        df["date"] = df["time_utc"].dt.floor("D")
    else:
        # 6 UTC - 6 UTC following day: shift back 6h so the window
        # [D 06:00, D+1 06:00) floors to D.
        df["date"] = (df["time_utc"] - pd.Timedelta(hours=6)).dt.floor("D")

    agg = df.groupby("date").mean(numeric_only=True)
    agg = agg.rename(columns={v: f"api_{k}" for k, v in OPEN_METEO_COLUMN.items()})
    return agg[[f"api_{sp}" for sp in CITY_SPECIES[city]]]


def load_observed_madrid() -> pd.DataFrame:
    path = CACHE_DIR / "madrid_facf_daily.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    wide = df.pivot_table(index="date", columns="species", values="grains_m3", aggfunc="mean")
    wide = wide.rename(columns={sp: f"obs_{sp}" for sp in wide.columns})
    return wide


def load_observed_meteoswiss(station: str) -> pd.DataFrame:
    path = CACHE_DIR / f"meteoswiss_{station}_daily.csv"
    df = pd.read_csv(path, parse_dates=["date_utc_6_6"])
    df = df.rename(
        columns={
            "date_utc_6_6": "date",
            "birch_no_m3": "obs_birch",
            "grass_no_m3": "obs_grass",
        }
    )
    return df.set_index("date")[["obs_birch", "obs_grass"]]


def build_city_frame(city: str) -> pd.DataFrame:
    api = load_open_meteo_api_daily(city)
    if city == "madrid":
        obs = load_observed_madrid()
    elif city == "basel":
        obs = load_observed_meteoswiss("pbs")
    elif city == "zurich":
        obs = load_observed_meteoswiss("pzh")
    else:
        raise ValueError(city)

    full_index = pd.date_range("2021-01-01", "2025-12-31", freq="D")
    frame = pd.DataFrame(index=full_index)
    frame = frame.join(api).join(obs)
    frame.index.name = "date"
    return frame


# ---------------------------------------------------------------------------
# Season definition (DATA_PLAN 2.3 footnote: "first and last day with >= 1
# grain/m3 ... exact rule fixed in the script")
# ---------------------------------------------------------------------------

def compute_season_bounds(frame: pd.DataFrame, species: str) -> dict:
    """Season window derived from TRAINING years only (2021-2023), per
    DATA_PLAN 2.3/2.5: "Season means: olive Apr-Jun, grass Mar-Jul, birch
    Mar-Apr, as defined from observed data in the training years ...
    exact rule fixed in the script and written to the results JSON."

    Rule (see SEASON_WINDOW_RULE, written verbatim into backtest.json):
    for each training year, take a 7-day centred rolling mean of the
    observed daily count (min_periods=1, so edge days near Jan 1/Dec 31
    still get a value from the days actually present); average that
    rolling mean across the training years by day-of-year; the season's
    first/last day-of-year are the first and last day-of-year where that
    training-years mean is >= 1 grain/m3. This data-driven window is then
    clipped to the named-month outer bound for the species (olive
    Apr-Jun, grass Mar-Jul, birch Mar-Apr), so the window can never
    extend past the clinically named months even if the training data is
    noisy right at the edges.

    2024-2025 (the held-out evaluation years) never influence this
    window. Returns DOY bounds (1-366), or (None, None) if there is no
    training-year data at all for this species.
    """
    obs = frame[f"obs_{species}"]
    train_mask = obs.index.year.isin(TRAINING_YEARS)
    train_obs = obs[train_mask]
    if train_obs.notna().sum() == 0:
        return {"start_doy": None, "end_doy": None}

    # 7-day centred rolling mean, computed per training year separately so
    # a rolling window never crosses a year boundary (e.g. Dec of one
    # training year blending into Jan of the next).
    rolling_by_doy: dict[int, list[float]] = {}
    for y in TRAINING_YEARS:
        year_obs = train_obs[train_obs.index.year == y]
        if year_obs.empty:
            continue
        rolled = year_obs.rolling(window=7, center=True, min_periods=1).mean()
        for doy, val in zip(year_obs.index.dayofyear, rolled.values):
            if not np.isnan(val):
                rolling_by_doy.setdefault(int(doy), []).append(float(val))

    if not rolling_by_doy:
        return {"start_doy": None, "end_doy": None}

    mean_by_doy = {doy: sum(vals) / len(vals) for doy, vals in rolling_by_doy.items()}
    active_doys = sorted(doy for doy, m in mean_by_doy.items() if m >= 1.0)

    # Named-month outer bound (DATA_PLAN 2.3), expressed as DOY using a
    # non-leap reference year so Apr 1 / Jun 30 etc. map consistently.
    start_month, start_day, end_month, end_day = NAMED_MONTH_BOUNDS[species]
    bound_start_doy = pd.Timestamp(2023, start_month, start_day).dayofyear
    bound_end_doy = pd.Timestamp(2023, end_month, end_day).dayofyear

    active_doys = [d for d in active_doys if bound_start_doy <= d <= bound_end_doy]

    if not active_doys:
        # Training data never crossed 1 grain/m3 inside the named months:
        # fall back to the named-month outer bound itself so the season
        # is never empty.
        return {"start_doy": bound_start_doy, "end_doy": bound_end_doy}

    return {"start_doy": int(min(active_doys)), "end_doy": int(max(active_doys))}


def in_season_mask(index: pd.DatetimeIndex, bounds: dict) -> np.ndarray:
    if bounds["start_doy"] is None:
        return np.zeros(len(index), dtype=bool)
    doy = index.dayofyear
    return (doy >= bounds["start_doy"]) & (doy <= bounds["end_doy"])


# ---------------------------------------------------------------------------
# Alert rules (DATA_PLAN 2.3) — pre-registered, exact
# ---------------------------------------------------------------------------

def _ge_threshold_preserving_nan(values: pd.Series, threshold: float) -> pd.Series:
    """values >= threshold, but NaN stays NaN instead of collapsing to
    False. This matters for every rule below: a day with no D-1 data (the
    first row) or a genuinely missing API/observed reading must be
    excluded from the evaluation denominator in day_alert_metrics, not
    silently counted as "rule did not fire"."""
    result = values >= threshold
    return result.where(values.notna(), other=np.nan)


def rule_P0(frame: pd.DataFrame, species: str, threshold: float) -> pd.Series:
    """Observed(D-1) >= T."""
    obs_prev = frame[f"obs_{species}"].shift(1)
    return _ge_threshold_preserving_nan(obs_prev, threshold)


def rule_P1(frame: pd.DataFrame, species: str, threshold: float) -> pd.Series:
    """API(D-1) >= T."""
    api_prev = frame[f"api_{species}"].shift(1)
    return _ge_threshold_preserving_nan(api_prev, threshold)


def rule_P2(frame: pd.DataFrame, species: str, threshold: float) -> pd.Series:
    """API(D) >= T."""
    return _ge_threshold_preserving_nan(frame[f"api_{species}"], threshold)


def rule_R1(frame: pd.DataFrame, species: str, threshold: float) -> pd.Series:
    """mean(API(D-1), API(D)) >= T."""
    api = frame[f"api_{species}"]
    api_prev = api.shift(1)
    two_day_mean = pd.concat([api, api_prev], axis=1).mean(axis=1, skipna=False)
    return _ge_threshold_preserving_nan(two_day_mean, threshold)


def rule_C0(frame: pd.DataFrame, species: str, threshold: float) -> pd.Series:
    """Month-day share of high observed days in prior years >= 0.5.

    "Prior years" = years strictly before the evaluated date's year,
    restricted to the 2021-2025 cache. The first year (2021) has no prior
    year, so C0 is undefined (NaN -- not evaluable, excluded from that
    year's evaluation denominator, never coerced to False) for all of
    2021, and for any (year, month-day) whose only prior-year readings
    are themselves missing.

    Matched on (month, day), not day-of-year: day-of-year shifts by one
    for every date after Feb 29 in a leap year relative to a non-leap
    year (e.g. Mar 1 is DOY 60 in 2024 but DOY 60 is Feb 29 in a leap
    year and Mar 1 in a non-leap year), which would silently misalign a
    leap-year Mar 1 reading against a non-leap-year Feb 29 reading one
    day off. (month, day) is calendar-stable across leap and non-leap
    years; Feb 29 itself simply has no match in non-leap prior years and
    is treated like any other month-day with no prior data (NaN).
    """
    obs = frame[f"obs_{species}"]
    is_high = (obs >= threshold).astype(float)
    is_high[obs.isna()] = np.nan
    years = frame.index.year
    month_days = list(zip(frame.index.month, frame.index.day))

    high_by_year_monthday: dict[tuple[int, int, int], float] = {}
    for y in sorted(set(years)):
        yearmask = years == y
        md_for_year = [md for md, keep in zip(month_days, yearmask) if keep]
        vals_for_year = is_high.values[yearmask]
        for (m, d), val in zip(md_for_year, vals_for_year):
            high_by_year_monthday[(y, m, d)] = val

    out = np.full(len(frame), np.nan)
    uniq_years = sorted(set(years))
    for i, (y, (m, d)) in enumerate(zip(years, month_days)):
        prior_vals = [
            high_by_year_monthday.get((py, m, d))
            for py in uniq_years
            if py < y
        ]
        prior_vals = [v for v in prior_vals if v is not None and not np.isnan(v)]
        if not prior_vals:
            continue
        share = sum(prior_vals) / len(prior_vals)
        out[i] = 1.0 if share >= 0.5 else 0.0
    # out holds 1.0 (fired), 0.0 (did not fire), or NaN (not evaluable).
    # Comparing with `== 1.0` would coerce every NaN to False, destroying
    # the "not evaluable" state the rest of the pipeline relies on
    # (day_alert_metrics, climatology_onset_day). Build a nullable boolean
    # series instead so NaN survives as NaN.
    bool_result = pd.Series(np.where(np.isnan(out), np.nan, out == 1.0), index=frame.index)
    return bool_result


def rule_R2_onset_day(frame: pd.DataFrame, species: str, threshold: float, season_mask: np.ndarray) -> pd.Timestamp | None:
    """First in-season day D where max(API(D..D+3)) >= T.

    A day whose D..D+3 window is entirely NaN is not evaluable for this
    rule on that day: it neither fires nor counts as "crossed", it is
    simply skipped, exactly like every other NaN handling in this module
    (NaN = not evaluable, excluded, never coerced to True or False).
    """
    api = frame[f"api_{species}"].values
    idx = frame.index
    n = len(api)
    for i in range(n):
        if not season_mask[i]:
            continue
        window = api[i : min(i + 4, n)]
        if not np.any(~np.isnan(window)):
            continue  # window entirely NaN: not evaluable, skip this day
        if np.nanmax(window) >= threshold:
            return idx[i]
    return None


def climatology_onset_day(frame: pd.DataFrame, species: str, c0_alerts: pd.Series, season_mask: np.ndarray) -> pd.Timestamp | None:
    """First in-season day where C0 fires, per year — used as the C0 onset comparator.

    c0_alerts holds True, False, or NaN (not evaluable). ``bool(np.nan)``
    is True in Python, so a naive ``bool(c0_alerts.iloc[i])`` would treat
    every not-evaluable day as "C0 fired". NaN days must be skipped, not
    treated as a fire.
    """
    idx = frame.index
    for i in range(len(idx)):
        if not season_mask[i]:
            continue
        val = c0_alerts.iloc[i]
        if pd.isna(val):
            continue  # not evaluable: skip, never treated as a fire
        if bool(val):
            return idx[i]
    return None


def p2_onset_day(frame: pd.DataFrame, species: str, threshold: float, season_mask: np.ndarray) -> pd.Timestamp | None:
    """First in-season day where API(D) >= T.

    A NaN API reading on a given day is not evaluable: it is skipped
    (never counted as a crossing), matching the NaN convention used
    everywhere else in this module.
    """
    api = frame[f"api_{species}"]
    idx = frame.index
    for i in range(len(idx)):
        if not season_mask[i]:
            continue
        val = api.iloc[i]
        if pd.isna(val):
            continue
        if val >= threshold:
            return idx[i]
    return None


def observed_onset_day(frame: pd.DataFrame, species: str, threshold: float, season_mask: np.ndarray) -> pd.Timestamp | None:
    """First in-season day where Observed(D) >= T.

    A NaN observed reading on a given day is not evaluable: it is
    skipped (never counted as a crossing).
    """
    obs = frame[f"obs_{species}"]
    idx = frame.index
    for i in range(len(idx)):
        if not season_mask[i]:
            continue
        val = obs.iloc[i]
        if pd.isna(val):
            continue
        if val >= threshold:
            return idx[i]
    return None


# ---------------------------------------------------------------------------
# Metrics (DATA_PLAN 2.4)
# ---------------------------------------------------------------------------

def day_alert_metrics(obs_high: pd.Series, alert: pd.Series) -> dict:
    """recall, precision, CSI, false-alert days, counted only over days
    where both observed and alert are defined (not NaN)."""
    valid = obs_high.notna() & alert.notna()
    obs_v = obs_high[valid].astype(bool)
    alert_v = alert[valid].astype(bool)

    tp = int((obs_v & alert_v).sum())
    fp = int((~obs_v & alert_v).sum())
    fn = int((obs_v & ~alert_v).sum())
    tn = int((~obs_v & ~alert_v).sum())
    n_events = int(obs_v.sum())
    n_days = int(valid.sum())

    recall = tp / n_events if n_events > 0 else None
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    csi = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else None

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "n_events": n_events, "n_evaluated_days": n_days,
        "recall": recall, "precision": precision, "csi": csi,
        "false_alert_days": fp,
    }


def season_block_bootstrap_recall(obs_high: pd.Series, alert: pd.Series, years: pd.Index, rng: np.random.Generator, n_boot: int = N_BOOTSTRAP) -> tuple[float | None, float | None]:
    """Bootstrap CI for recall by resampling whole season-years with
    replacement (5 season blocks: 2021-2025).

    A season drawn twice must count its rows twice in the resampled
    confusion matrix. Using ``years.isin(sample_years)`` collapses any
    duplicate draw of the same year back down to one copy of that year's
    rows (set membership, not multiset), which silently removes the
    weighting the block bootstrap is supposed to apply. Instead, each
    draw's year-slice of rows is concatenated explicitly, once per draw,
    so a year drawn twice contributes its rows twice to that bootstrap
    replicate's confusion matrix.
    """
    valid = obs_high.notna() & alert.notna()
    obs_bool_by_year: dict[int, np.ndarray] = {}
    alert_bool_by_year: dict[int, np.ndarray] = {}
    years_arr = np.asarray(years)
    valid_arr = np.asarray(valid)
    obs_arr = obs_high.to_numpy()
    alert_arr = alert.to_numpy()
    uniq_years = sorted(set(years_arr[valid_arr]))
    if len(uniq_years) < 2:
        return (None, None)

    for y in uniq_years:
        yearmask = valid_arr & (years_arr == y)
        obs_bool_by_year[y] = obs_arr[yearmask].astype(bool)
        alert_bool_by_year[y] = alert_arr[yearmask].astype(bool)

    recalls = []
    for _ in range(n_boot):
        sample_years = rng.choice(uniq_years, size=len(uniq_years), replace=True)
        # Concatenate the row-slice for each drawn year once per draw, so a
        # year drawn k times contributes its rows k times (weighted by
        # draw count), not merely once via set membership.
        obs_v = np.concatenate([obs_bool_by_year[y] for y in sample_years])
        alert_v = np.concatenate([alert_bool_by_year[y] for y in sample_years])
        n_events = int(obs_v.sum())
        if n_events == 0:
            continue
        tp = int((obs_v & alert_v).sum())
        recalls.append(tp / n_events)

    if not recalls:
        return (None, None)
    lo, hi = np.percentile(recalls, [2.5, 97.5])
    return (float(lo), float(hi))


# ---------------------------------------------------------------------------
# Main backtest
# ---------------------------------------------------------------------------

def run_city_species(city: str, species: str, threshold: float, rng: np.random.Generator) -> dict:
    frame = build_city_frame(city)
    obs = frame[f"obs_{species}"]
    obs_high = obs >= threshold

    season_bounds = compute_season_bounds(frame, species)
    season_mask = in_season_mask(frame.index, season_bounds)

    day_rules = {}
    c0_alerts_series = None
    for rule_id in RULE_IDS:
        if rule_id == "P0":
            alerts = rule_P0(frame, species, threshold)
        elif rule_id == "P1":
            alerts = rule_P1(frame, species, threshold)
        elif rule_id == "P2":
            alerts = rule_P2(frame, species, threshold)
        elif rule_id == "R1":
            alerts = rule_R1(frame, species, threshold)
        elif rule_id == "C0":
            alerts = rule_C0(frame, species, threshold)
            c0_alerts_series = alerts
        else:
            raise ValueError(rule_id)

        metrics = day_alert_metrics(obs_high, alerts)
        ci_lo, ci_hi = season_block_bootstrap_recall(obs_high, alerts, frame.index.year, rng)
        metrics["recall_ci95"] = [ci_lo, ci_hi]

        # misses: observed high day where this rule did not alert
        valid = obs_high.notna() & alerts.notna()
        alerts_filled = alerts.copy()
        alerts_filled[alerts_filled.isna()] = False
        missed_mask = valid & obs_high.astype(bool) & ~alerts_filled.astype(bool)
        missed_dates = frame.index[missed_mask]
        metrics["_missed_dates"] = [d.strftime("%Y-%m-%d") for d in missed_dates]

        day_rules[rule_id] = metrics

    # Onset comparison per year: R2 vs P2 vs C0, lead days = observed_onset - alert_onset.
    # Years with no observed ground truth at all for this city/species (e.g.
    # Madrid FACF has no grass readings in 2021-2022, see data/DATA_CARD.md)
    # are skipped entirely rather than reporting a meaningless onset.
    onset_by_year = {}
    for y in YEARS:
        year_mask = season_mask & (frame.index.year == y)
        if not year_mask.any():
            continue
        year_full_mask = frame.index.year == y
        if obs[year_full_mask].notna().sum() == 0:
            continue
        obs_onset = observed_onset_day(frame, species, threshold, year_mask)
        r2_onset = rule_R2_onset_day(frame, species, threshold, year_mask)
        p2_onset = p2_onset_day(frame, species, threshold, year_mask)
        c0_onset = climatology_onset_day(frame, species, c0_alerts_series, year_mask) if c0_alerts_series is not None else None

        def lead_days(alert_day):
            if obs_onset is None or alert_day is None:
                return None
            return int((obs_onset - alert_day).days)

        onset_by_year[str(y)] = {
            "observed_onset": obs_onset.strftime("%Y-%m-%d") if obs_onset is not None else None,
            "R2_onset": r2_onset.strftime("%Y-%m-%d") if r2_onset is not None else None,
            "P2_onset": p2_onset.strftime("%Y-%m-%d") if p2_onset is not None else None,
            "C0_onset": c0_onset.strftime("%Y-%m-%d") if c0_onset is not None else None,
            "R2_lead_days": lead_days(r2_onset),
            "P2_lead_days": lead_days(p2_onset),
            "C0_lead_days": lead_days(c0_onset),
            "R2_fired_before_onset": (lead_days(r2_onset) is not None and lead_days(r2_onset) >= 0),
            "R2_missed_season": r2_onset is None and obs_onset is not None,
        }

    return {
        "city": city,
        "species": species,
        "threshold": threshold,
        "season_bounds_doy": season_bounds,
        "day_rules": day_rules,
        "onset_by_year": onset_by_year,
    }


def _pooled_recall_and_false_alerts(results: list[dict], rule_id: str) -> dict:
    """Pool TP/events and false-alert-days across every city-species pair
    for one rule, so the kill-check judges overall skill rather than any
    single lucky city-species row."""
    tp = sum(r["day_rules"][rule_id]["tp"] for r in results)
    events = sum(r["day_rules"][rule_id]["n_events"] for r in results)
    fp = sum(r["day_rules"][rule_id]["false_alert_days"] for r in results)
    recall = tp / events if events > 0 else None
    return {"tp": tp, "n_events": events, "recall": recall, "false_alert_days": fp}


def _bootstrap_lead_day_diff(onset_rows: list[dict], key_a: str, key_b: str, rng: np.random.Generator, n_boot: int = N_BOOTSTRAP) -> dict:
    """Season-block bootstrap on mean(lead_days[key_a] - lead_days[key_b]).

    Resamples whole season-years (blocks) with replacement -- each draw
    picks a year, and every city-species-year onset row for that year is
    included for that draw -- not individual city-species-year rows
    independently. Per DATA_PLAN 2.5 the bootstrap unit is the season
    (5 blocks: 2021-2025), matching season_block_bootstrap_recall; a row
    is a city-species-year cell, so a flat per-row bootstrap would treat
    e.g. Madrid-olive-2024 and Basel-birch-2024 as independent draws when
    they are not: both come from the same climate year. Returns the point
    estimate and a 95% CI; "excludes zero" means the whole interval is on
    one side of 0.
    """
    paired_by_year: dict[str, list[tuple[float, float]]] = {}
    for row in onset_rows:
        if row[key_a] is None or row[key_b] is None:
            continue
        paired_by_year.setdefault(row["year"], []).append((row[key_a], row[key_b]))

    uniq_years = sorted(paired_by_year.keys())
    all_pairs = [p for year in uniq_years for p in paired_by_year[year]]
    if not all_pairs:
        return {"mean_diff": None, "ci95": [None, None], "excludes_zero": False, "n_pairs": 0}

    diffs = np.array([a - b for a, b in all_pairs], dtype=float)
    point_estimate = float(diffs.mean())

    if len(uniq_years) < 2:
        # Not enough season blocks to bootstrap across; report the point
        # estimate with no CI rather than a fabricated single-block interval.
        return {
            "mean_diff": point_estimate,
            "ci95": [None, None],
            "excludes_zero": False,
            "n_pairs": len(all_pairs),
        }

    boot_means = []
    for _ in range(n_boot):
        sample_years = rng.choice(uniq_years, size=len(uniq_years), replace=True)
        # Concatenate each drawn year's pairs once per draw, so a year
        # drawn twice contributes its rows twice (weighted by draw count).
        boot_pairs = [p for year in sample_years for p in paired_by_year[year]]
        boot_diffs = np.array([a - b for a, b in boot_pairs], dtype=float)
        boot_means.append(boot_diffs.mean())
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    excludes_zero = bool(lo > 0 or hi < 0)
    return {
        "mean_diff": point_estimate,
        "ci95": [float(lo), float(hi)],
        "excludes_zero": excludes_zero,
        "n_pairs": len(all_pairs),
    }


def kill_check(results: list[dict], rng: np.random.Generator) -> dict:
    """DATA_PLAN 2.5, applied mechanically to the measured numbers above.

    All comparisons are pooled across every scored city-species pair (and,
    for onset, every city-species-year with a valid observed onset), not
    evaluated on any single favourable row, so the verdict reflects
    overall skill rather than a result that would flip under a different
    pre-registration draw.
    """
    verdict = {}

    # 1. Observed counts exist for >= 3 cities over >= 1 year, openly downloadable.
    verdict["check1_observed_counts_exist"] = {
        "passed": True,
        "note": "Madrid (D1), Basel and Zurich (D2) observed counts downloaded and cached; see data/DATA_CARD.md.",
    }

    # Pre-registered minimum size check (DATA_PLAN 2.1): >=100 events, >=1000 evaluated city-days total.
    total_events = sum(r["day_rules"]["P2"]["n_events"] for r in results)
    total_days = sum(r["day_rules"]["P2"]["n_evaluated_days"] for r in results)
    verdict["size_check"] = {
        "total_observed_events_P2_denominator": total_events,
        "total_evaluated_city_days_P2_denominator": total_days,
        "passed": total_events >= 100 and total_days >= 1000,
    }

    # 2. "Alert == the API's own forecast": R1 vs P2 on recall at equal-or-fewer
    #    false-alert days; R2 vs both P2 and C0 on lead days with a
    #    season-bootstrap interval excluding zero. Both judged on pooled
    #    numbers across all scored city-species pairs, per DATA_PLAN 2.5.
    pooled_r1 = _pooled_recall_and_false_alerts(results, "R1")
    pooled_p2 = _pooled_recall_and_false_alerts(results, "P2")
    r1_beats_p2_pooled = bool(
        pooled_r1["recall"] is not None
        and pooled_p2["recall"] is not None
        and pooled_r1["recall"] > pooled_p2["recall"]
        and pooled_r1["false_alert_days"] <= pooled_p2["false_alert_days"]
    )

    onset_rows = []
    for r in results:
        for year, onset in r["onset_by_year"].items():
            onset_rows.append({
                "city": r["city"], "species": r["species"], "year": year,
                "R2_lead_days": onset["R2_lead_days"],
                "P2_lead_days": onset["P2_lead_days"],
                "C0_lead_days": onset["C0_lead_days"],
            })

    r2_vs_p2 = _bootstrap_lead_day_diff(onset_rows, "R2_lead_days", "P2_lead_days", rng)
    r2_vs_c0 = _bootstrap_lead_day_diff(onset_rows, "R2_lead_days", "C0_lead_days", rng)
    r2_beats_p2_pooled = bool(r2_vs_p2["mean_diff"] is not None and r2_vs_p2["mean_diff"] > 0 and r2_vs_p2["excludes_zero"])
    r2_beats_c0_pooled = bool(r2_vs_c0["mean_diff"] is not None and r2_vs_c0["mean_diff"] > 0 and r2_vs_c0["excludes_zero"])

    verdict["check2_beats_api"] = {
        "pooled_r1": pooled_r1,
        "pooled_p2": pooled_p2,
        "r1_beats_p2_pooled_recall_at_equal_or_fewer_false_alerts": r1_beats_p2_pooled,
        "r2_minus_p2_lead_days_bootstrap": r2_vs_p2,
        "r2_minus_c0_lead_days_bootstrap": r2_vs_c0,
        "r2_beats_p2_on_lead_days_with_ci_excluding_zero": r2_beats_p2_pooled,
        "r2_beats_c0_on_lead_days_with_ci_excluding_zero": r2_beats_c0_pooled,
        "onset_rows_used": onset_rows,
        "note": (
            "Per DATA_PLAN 2.5 rule 2: if R1 does not beat P2 on pooled "
            "recall at equal-or-fewer false-alert days, or R2 does not "
            "beat both P2 and C0 on mean lead days with a season-block "
            "bootstrap interval (resampling city-species-year onset rows) "
            "that excludes zero, then no 'beats the API' claim is made. "
            "The headline becomes the measured P2 skill."
        ),
        "passed_beats_api_claim": bool(r1_beats_p2_pooled and r2_beats_p2_pooled and r2_beats_c0_pooled),
    }

    # 3. P2 recall at the clinical threshold below 50% in Madrid for both olive and grass?
    madrid_p2 = {r["species"]: r["day_rules"]["P2"]["recall"] for r in results if r["city"] == "madrid"}
    madrid_below_50 = all(
        (v is not None and v < 0.5) for v in madrid_p2.values()
    ) if madrid_p2 else False
    verdict["check3_madrid_p2_recall"] = {
        "madrid_p2_recall_by_species": madrid_p2,
        "both_below_50pct": madrid_below_50,
        "note": (
            "If true, DATA_PLAN 2.5 rule 3 requires the app's alert level "
            "be lowered only with Ahmed's re-sign-off; otherwise the "
            "headline is reported as a 'limits' number."
        ),
    }

    # 4. Valencia never scored.
    verdict["check4_valencia_never_scored"] = {
        "passed": True,
        "note": "Valencia is excluded from CITY_SPECIES and never appears in results.",
    }

    verdict["overall_headline"] = (
        "beats_the_api" if verdict["check2_beats_api"]["passed_beats_api_claim"]
        else "measured_P2_skill_only_no_beats_api_claim"
    )

    return verdict


def write_misses_csv(results: list[dict]) -> None:
    out_path = RESULTS_DIR / "misses.csv"
    rows = []
    for r in results:
        for rule_id, metrics in r["day_rules"].items():
            for date_str in metrics["_missed_dates"]:
                rows.append({
                    "city": r["city"],
                    "species": r["species"],
                    "rule": rule_id,
                    "date": date_str,
                    "threshold": r["threshold"],
                })
    rows.sort(key=lambda x: (x["city"], x["species"], x["rule"], x["date"]))
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["city", "species", "rule", "date", "threshold"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} missed-day rows to {out_path}")


def write_results_table_md(results: list[dict], kc: dict, thresholds: dict) -> None:
    out_path = DOCS_DIR / "results_table.md"
    lines = [
        "# PollenPlan backtest results",
        "",
        "Generated by `eval/backtest.py` from cached data in `data/cache/`. "
        f"Thresholds status: **{thresholds.get('status')}** (rules/thresholds.json). "
        "Numbers here are exactly what the script computed; see "
        "`eval/results/backtest.json` for the full machine-readable output "
        "and `eval/results/misses.csv` for every missed observed high day.",
        "",
        "## Day-alert rules (P0, P1, P2, R1, C0)",
        "",
        "| City | Species | Threshold | Rule | Recall | 95% CI | Precision | CSI | False-alert days | Events | Evaluated days |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    def fmt(x):
        if x is None:
            return "n/a"
        if isinstance(x, float):
            return f"{x:.3f}"
        return str(x)

    for r in results:
        for rule_id in RULE_IDS:
            m = r["day_rules"][rule_id]
            ci = m["recall_ci95"]
            ci_str = f"[{fmt(ci[0])}, {fmt(ci[1])}]" if ci[0] is not None else "n/a"
            lines.append(
                f"| {r['city']} | {r['species']} | {r['threshold']} | {rule_id} | "
                f"{fmt(m['recall'])} | {ci_str} | {fmt(m['precision'])} | {fmt(m['csi'])} | "
                f"{m['false_alert_days']} | {m['n_events']} | {m['n_evaluated_days']} |"
            )

    lines += [
        "",
        "## Onset (R2 vs P2 vs C0), lead days = observed first high day minus alert day",
        "",
        "| City | Species | Year | Observed onset | R2 onset | R2 lead days | P2 onset | P2 lead days | C0 onset | C0 lead days |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        for year, o in r["onset_by_year"].items():
            lines.append(
                f"| {r['city']} | {r['species']} | {year} | {o['observed_onset']} | "
                f"{o['R2_onset']} | {fmt(o['R2_lead_days'])} | {o['P2_onset']} | "
                f"{fmt(o['P2_lead_days'])} | {o['C0_onset']} | {fmt(o['C0_lead_days'])} |"
            )

    def fmt_ci(ci):
        if ci is None or ci[0] is None:
            return "n/a"
        return f"[{fmt(ci[0])}, {fmt(ci[1])}]"

    lines += [
        "",
        "## Kill-check verdict (DATA_PLAN 2.5)",
        "",
        f"- Check 1 (observed counts exist): **{kc['check1_observed_counts_exist']['passed']}**",
        f"- Pre-registered size minimum (>=100 events, >=1000 evaluated city-days): **{kc['size_check']['passed']}** "
        f"(events={kc['size_check']['total_observed_events_P2_denominator']}, "
        f"days={kc['size_check']['total_evaluated_city_days_P2_denominator']})",
        f"- Check 2, pooled R1 recall {fmt(kc['check2_beats_api']['pooled_r1']['recall'])} "
        f"vs pooled P2 recall {fmt(kc['check2_beats_api']['pooled_p2']['recall'])} "
        f"(false-alert days R1={kc['check2_beats_api']['pooled_r1']['false_alert_days']}, "
        f"P2={kc['check2_beats_api']['pooled_p2']['false_alert_days']}): "
        f"R1 beats P2 = **{kc['check2_beats_api']['r1_beats_p2_pooled_recall_at_equal_or_fewer_false_alerts']}**",
        f"- Check 2, R2 minus P2 mean lead days = {fmt(kc['check2_beats_api']['r2_minus_p2_lead_days_bootstrap']['mean_diff'])}, "
        f"95% CI {fmt_ci(kc['check2_beats_api']['r2_minus_p2_lead_days_bootstrap']['ci95'])}: "
        f"R2 beats P2 = **{kc['check2_beats_api']['r2_beats_p2_on_lead_days_with_ci_excluding_zero']}**",
        f"- Check 2, R2 minus C0 mean lead days = {fmt(kc['check2_beats_api']['r2_minus_c0_lead_days_bootstrap']['mean_diff'])}, "
        f"95% CI {fmt_ci(kc['check2_beats_api']['r2_minus_c0_lead_days_bootstrap']['ci95'])}: "
        f"R2 beats C0 = **{kc['check2_beats_api']['r2_beats_c0_on_lead_days_with_ci_excluding_zero']}**",
        f"- Check 2 overall ('beats the API' claim allowed): **{kc['check2_beats_api']['passed_beats_api_claim']}**",
        f"- Check 3 (Madrid P2 recall below 50% for both olive and grass): "
        f"**{kc['check3_madrid_p2_recall']['both_below_50pct']}** "
        f"(olive={fmt(kc['check3_madrid_p2_recall']['madrid_p2_recall_by_species'].get('olive'))}, "
        f"grass={fmt(kc['check3_madrid_p2_recall']['madrid_p2_recall_by_species'].get('grass'))})",
        f"- Check 4 (Valencia never scored): **{kc['check4_valencia_never_scored']['passed']}**",
        "",
        f"**Overall headline: `{kc['overall_headline']}`**",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    thresholds = load_thresholds()
    if thresholds.get("status") not in ("pending_signoff", "signed"):
        raise RuntimeError(
            "rules/thresholds.json status is not 'pending_signoff' or 'signed' "
            "as expected; refusing to proceed without checking with the clinical lead."
        )

    rng = np.random.default_rng(RNG_SEED)

    results = []
    for city, species_list in CITY_SPECIES.items():
        for species in species_list:
            threshold = thresholds["alert"][species]
            results.append(run_city_species(city, species, threshold, rng))

    kc = kill_check(results, rng)

    # Strip internal helper fields before writing JSON (misses go to their own CSV)
    results_public = []
    for r in results:
        r2 = json.loads(json.dumps(r, default=str))
        for rule_id in r2["day_rules"]:
            r2["day_rules"][rule_id].pop("_missed_dates", None)
        results_public.append(r2)

    output = {
        "thresholds_status": thresholds.get("status"),
        "thresholds_used": thresholds.get("alert"),
        "thresholds_note": thresholds.get("note"),
        "years": YEARS,
        "training_years": TRAINING_YEARS,
        "season_window_rule": SEASON_WINDOW_RULE,
        "season_window_named_month_bounds": {
            sp: f"{bound[0]:02d}-{bound[1]:02d} to {bound[2]:02d}-{bound[3]:02d}"
            for sp, bound in NAMED_MONTH_BOUNDS.items()
        },
        "cities_scored": list(CITY_SPECIES.keys()),
        "valencia_scored": False,
        "rules_evaluated": RULE_IDS + ["R2"],
        "results": results_public,
        "kill_check": kc,
    }

    out_json = RESULTS_DIR / "backtest.json"
    out_json.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {out_json}")

    write_misses_csv(results)
    write_results_table_md(results, kc, thresholds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
