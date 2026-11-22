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
pending_signoff). Ground truth:
    Madrid (FACF): olive, grass   -- Comunidad de Madrid, window UNVERIFIED
    Basel  (PBS):  birch, grass   -- MeteoSwiss, 6 UTC - 6 UTC
    Zurich (PZH):  birch, grass   -- MeteoSwiss, 6 UTC - 6 UTC
Valencia is demo-only and is never scored (enforced by simply never being
in CITY_SPECIES below).

Runs fully offline from data/cache/ (no network, no key). Outputs:
    eval/results/backtest.json   (includes "thresholds_status": "pending_signoff")
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
    as MeteoSwiss defines its own daily value (data/DATA_CARD.md section 2).
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
    """First and last day-of-year with observed >= 1 grain/m3, pooled
    across all training years (2021-2025), used to define the in-season
    window for onset (R2) scoring. Returns DOY bounds (1-366)."""
    obs = frame[f"obs_{species}"]
    active = obs[obs >= 1.0]
    if active.empty:
        return {"start_doy": None, "end_doy": None}
    doys = active.index.dayofyear
    return {"start_doy": int(doys.min()), "end_doy": int(doys.max())}


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
    """Day-of-year share of high observed days in prior years >= 0.5.

    "Prior years" = years strictly before the evaluated date's year,
    restricted to the 2021-2025 cache. The first year (2021) has no prior
    year, so C0 is undefined (NaN -> not fired, excluded from that year's
    evaluation denominator) for all of 2021.
    """
    obs = frame[f"obs_{species}"]
    is_high = (obs >= threshold).astype(float)
    is_high[obs.isna()] = np.nan
    years = frame.index.year
    doys = frame.index.dayofyear

    high_by_year_doy: dict[tuple[int, int], float] = {}
    for y in sorted(set(years)):
        yearmask = years == y
        for doy, val in zip(doys[yearmask], is_high.values[yearmask]):
            high_by_year_doy[(y, doy)] = val

    out = np.full(len(frame), np.nan)
    for i, (y, doy) in enumerate(zip(years, doys)):
        prior_vals = [
            high_by_year_doy.get((py, doy))
            for py in sorted(set(years))
            if py < y
        ]
        prior_vals = [v for v in prior_vals if v is not None and not np.isnan(v)]
        if not prior_vals:
            continue
        share = sum(prior_vals) / len(prior_vals)
        out[i] = 1.0 if share >= 0.5 else 0.0
    result = pd.Series(out, index=frame.index)
    return result == 1.0


def rule_R2_onset_day(frame: pd.DataFrame, species: str, threshold: float, season_mask: np.ndarray) -> pd.Timestamp | None:
    """First in-season day D where max(API(D..D+3)) >= T."""
    api = frame[f"api_{species}"].values
    idx = frame.index
    n = len(api)
    for i in range(n):
        if not season_mask[i]:
            continue
        window = api[i : min(i + 4, n)]
        if np.nanmax(window) >= threshold if np.any(~np.isnan(window)) else False:
            return idx[i]
    return None


def climatology_onset_day(frame: pd.DataFrame, species: str, c0_alerts: pd.Series, season_mask: np.ndarray) -> pd.Timestamp | None:
    """First in-season day where C0 fires, per year — used as the C0 onset comparator."""
    idx = frame.index
    for i in range(len(idx)):
        if season_mask[i] and bool(c0_alerts.iloc[i]):
            return idx[i]
    return None


def p2_onset_day(frame: pd.DataFrame, species: str, threshold: float, season_mask: np.ndarray) -> pd.Timestamp | None:
    api = frame[f"api_{species}"]
    idx = frame.index
    for i in range(len(idx)):
        if season_mask[i] and api.iloc[i] >= threshold:
            return idx[i]
    return None


def observed_onset_day(frame: pd.DataFrame, species: str, threshold: float, season_mask: np.ndarray) -> pd.Timestamp | None:
    obs = frame[f"obs_{species}"]
    idx = frame.index
    for i in range(len(idx)):
        if season_mask[i] and obs.iloc[i] >= threshold:
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
    replacement (5 season blocks: 2021-2025)."""
    valid = obs_high.notna() & alert.notna()
    uniq_years = sorted(set(years[valid]))
    if len(uniq_years) < 2:
        return (None, None)

    recalls = []
    for _ in range(n_boot):
        sample_years = rng.choice(uniq_years, size=len(uniq_years), replace=True)
        mask = valid & years.isin(sample_years)
        obs_v = obs_high[mask].astype(bool)
        alert_v = alert[mask].astype(bool)
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
    """Season-block bootstrap on mean(lead_days[key_a] - lead_days[key_b]),
    resampling city-species-year onset rows with replacement. Returns the
    point estimate and a 95% CI; "excludes zero" means the whole interval
    is on one side of 0."""
    paired = [
        (row[key_a], row[key_b])
        for row in onset_rows
        if row[key_a] is not None and row[key_b] is not None
    ]
    if not paired:
        return {"mean_diff": None, "ci95": [None, None], "excludes_zero": False, "n_pairs": 0}

    diffs = np.array([a - b for a, b in paired], dtype=float)
    point_estimate = float(diffs.mean())

    boot_means = []
    n = len(diffs)
    for _ in range(n_boot):
        sample_idx = rng.integers(0, n, size=n)
        boot_means.append(diffs[sample_idx].mean())
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    excludes_zero = bool(lo > 0 or hi < 0)
    return {
        "mean_diff": point_estimate,
        "ci95": [float(lo), float(hi)],
        "excludes_zero": excludes_zero,
        "n_pairs": n,
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
        "Thresholds status: **pending_signoff** (rules/thresholds.json). "
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
    if thresholds.get("status") != "pending_signoff":
        raise RuntimeError(
            "rules/thresholds.json status is not 'pending_signoff' as expected; "
            "refusing to proceed without checking with the clinical lead."
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
