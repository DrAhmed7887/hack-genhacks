"""Trap-first nowcast vs the CAMS pollen forecast (docs/PREREG_NOWCAST_2026.md).

Three modes, run from the repo root with the project venv:

  python eval/nowcast.py            development: leave-one-year-out CV on 2021-2025
                                    for P2, P0, C0, F1, F2 -> eval/results/nowcast_dev.json
  python eval/nowcast.py --lock     also refit F1/F2 on 2021-2025 and write
                                    eval/results/nowcast_lock.json (must be committed
                                    and pushed before any 2026 file is downloaded)
  python eval/nowcast.py --test-2026
                                    score the locked models once on 2026 (1 Jan - 31 Oct)
                                    from data/cache_2026/ -> eval/results/nowcast_2026.json.
                                    Refuses to run unless the lock is committed, pushed,
                                    and this script and data/fetch_2026.py are unchanged
                                    since the lock.

numpy + pandas only (no sklearn). Every feature is known by the morning of D.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest as bt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
OUT_DEV = RESULTS / "nowcast_dev.json"
OUT_LOCK = RESULTS / "nowcast_lock.json"
OUT_TEST = RESULTS / "nowcast_2026.json"
CACHE_2026 = ROOT / "data" / "cache_2026"
FETCH_2026 = ROOT / "data" / "fetch_2026.py"

DEV_YEARS = [2021, 2022, 2023, 2024, 2025]
TEST_START, TEST_END = "2026-01-01", "2026-10-31"
C_GRID = [0.01, 0.1, 1.0, 10.0]
P_GRID = [round(0.2 + 0.05 * i, 2) for i in range(11)]  # 0.20 .. 0.70
F1_COLS = ["lag1", "lag2", "mean7", "api_d", "season_frac", "clim"]  # prereg features 1-4, 6, 7
NASA_COLS = ["n_tmax", "n_precip", "n_solar", "n_wind"]  # NASA POWER D-1 (F2 only)
F2_COLS = F1_COLS + NASA_COLS
CITIES = list(bt.CITY_SPECIES)
BOOT_N, BOOT_BLOCK, BOOT_SEED = 10_000, 7, 20261123


# ---------------------------------------------------------------- features

def features(f: pd.DataFrame, city: str, species: str, threshold: float, clim_years: list[int]) -> pd.DataFrame:
    """One row per day: target, baseline-rule inputs and the F1/F2 features.

    `f` is a city frame as built by backtest.build_city_frame (it may extend
    into 2026). `clim` uses only `clim_years`, never the year being scored."""
    obs, api = f[f"obs_{species}"], f[f"api_{species}"]
    d = pd.DataFrame(index=f.index)
    d["city"], d["species"], d["year"] = city, species, f.index.year
    d["high"] = (obs >= threshold).where(obs.notna())
    d["obs_prev"], d["obs_prev2"] = obs.shift(1), obs.shift(2)
    d["api"] = api
    d["c0"] = bt.rule_C0(f, species, threshold)  # last year's calendar, as in the backtest
    d["lag1"] = np.log1p(obs.shift(1))
    d["lag2"] = np.log1p(obs.shift(2))
    d["mean7"] = np.log1p(obs.shift(1).rolling(7, min_periods=3).mean())
    d["api_d"] = np.log1p(api)
    bounds = bt.compute_season_bounds(f[f.index.year.isin(bt.TRAINING_YEARS)], species)
    span = max(1, bounds["end_doy"] - bounds["start_doy"])
    d["season_frac"] = np.clip((f.index.dayofyear.to_numpy() - bounds["start_doy"]) / span, -0.5, 1.5)
    hi = d["high"][d["year"].isin(clim_years)]
    by_doy = hi.groupby(hi.index.dayofyear).mean().reindex(range(1, 367))
    by_doy = by_doy.rolling(7, center=True, min_periods=1).mean().fillna(0.0)
    d["clim"] = by_doy.reindex(f.index.dayofyear).to_numpy()
    d["n_tmax"], d["n_precip"] = f["nasa_t2m_max"].shift(1), f["nasa_precip"].shift(1)
    d["n_solar"], d["n_wind"] = f["nasa_solar"].shift(1), f["nasa_ws2m"].shift(1)
    return d


def scored_days(d: pd.DataFrame) -> pd.DataFrame:
    """Common day set for every rule: a trap reading on D and a CAMS value for D."""
    return d[d["high"].notna() & d["api"].notna()]


def conf(high, alert) -> dict:
    h, a = np.asarray(high).astype(bool), np.asarray(alert).astype(bool)
    tp, fp, fn = int((h & a).sum()), int((~h & a).sum()), int((h & ~a).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "n_events": int(h.sum()), "n_days": int(len(h)),
            "csi": tp / (tp + fp + fn) if tp + fp + fn else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "precision": tp / (tp + fp) if tp + fp else None}


def baseline_alerts(d: pd.DataFrame, threshold: dict) -> dict[str, np.ndarray]:
    t = d["species"].map(threshold).to_numpy()
    return {"P2": d["api"].to_numpy() >= t,
            "P0": np.nan_to_num(d["obs_prev"].to_numpy(), nan=-1) >= t,  # missing D-1 = no alert
            "C0": pd.array(d["c0"], dtype="boolean").fillna(False).to_numpy(bool)}  # undefined = no alert


def model_alert(d: pd.DataFrame, prob, p_star: float) -> np.ndarray:
    """F1/F2 alert: probability >= p*, and never on a day with no D-1 trap reading."""
    return (np.asarray(prob) >= p_star) & d["lag1"].notna().to_numpy()


# ---------------------------------------------------------------- logistic (numpy)

def design(d: pd.DataFrame, cols: list[str], mu: dict, sd: dict) -> np.ndarray:
    z = pd.DataFrame({c: (d[c] - mu[c]) / sd[c] for c in cols}).fillna(0.0)  # missing -> dev mean
    city = np.stack([(d["city"] == c).to_numpy(float) for c in CITIES[1:]], axis=1)
    return np.hstack([np.ones((len(d), 1)), city, z.to_numpy()])


def standardiser(tr: pd.DataFrame, cols: list[str]) -> tuple[dict, dict]:
    mu = {c: float(tr[c].mean()) for c in cols}
    sd = {c: float(tr[c].std()) or 1.0 for c in cols}
    return mu, sd


def predict(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x @ w, -30, 30)))


def fit_logistic(x: np.ndarray, y: np.ndarray, c: float, iters: int = 100) -> np.ndarray:
    """L2-penalised logistic regression (penalty 1/C, intercept free) by Newton-Raphson."""
    w = np.zeros(x.shape[1])
    pen = np.full(x.shape[1], 1.0 / c)
    pen[0] = 0.0
    for _ in range(iters):
        p = predict(x, w)
        g = x.T @ (p - y) + pen * w
        h = (x * (p * (1 - p))[:, None]).T @ x + np.diag(pen + 1e-9)
        step = np.linalg.solve(h, g)
        w -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


# ---------------------------------------------------------------- development

def dev_frames(clim_years: list[int]) -> dict[str, pd.DataFrame]:
    alert = bt.load_thresholds()["alert"]
    by_sp: dict[str, list[pd.DataFrame]] = {}
    for city, sps in bt.CITY_SPECIES.items():
        f = bt.build_city_frame(city)
        for sp in sps:
            by_sp.setdefault(sp, []).append(features(f, city, sp, alert[sp], clim_years))
    return {sp: pd.concat(fs) for sp, fs in by_sp.items()}


def cv(cols: list[str]) -> dict[float, pd.DataFrame]:
    """Leave-one-year-out CV: out-of-fold probabilities for every C in the grid."""
    oof: dict[float, list[pd.DataFrame]] = {c: [] for c in C_GRID}
    for test_year in DEV_YEARS:
        train_years = [y for y in DEV_YEARS if y != test_year]
        for d in dev_frames(train_years).values():
            tr, te = scored_days(d[d["year"].isin(train_years)]), scored_days(d[d["year"] == test_year])
            if te.empty:
                continue
            mu, sd = standardiser(tr, cols)
            xtr, xte = design(tr, cols, mu, sd), design(te, cols, mu, sd)
            for c in C_GRID:
                w = fit_logistic(xtr, tr["high"].to_numpy(float), c)
                oof[c].append(te.assign(prob=predict(xte, w)))
    return {c: pd.concat(v) for c, v in oof.items()}


def best_on_cv(oof: dict[float, pd.DataFrame]) -> tuple[float, float, dict]:
    best = None
    for c, d in oof.items():
        for p in P_GRID:
            m = conf(d["high"], model_alert(d, d["prob"], p))
            if best is None or (m["csi"] or 0) > (best[2]["csi"] or 0):
                best = (c, p, m)
    return best


def refit(cols: list[str], c: float) -> dict:
    out = {}
    for sp, d in dev_frames(DEV_YEARS).items():
        tr = scored_days(d)
        mu, sd = standardiser(tr, cols)
        w = fit_logistic(design(tr, cols, mu, sd), tr["high"].to_numpy(float), c)
        out[sp] = {"weights": [float(v) for v in w], "mu": mu, "sd": sd,
                   "columns": ["intercept"] + [f"city_{x}" for x in CITIES[1:]] + cols}
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def run_dev(write_lock: bool) -> dict:
    threshold = bt.load_thresholds()["alert"]
    oof1, oof2 = cv(F1_COLS), cv(F2_COLS)
    c1, p1, m1 = best_on_cv(oof1)
    c2, p2, m2 = best_on_cv(oof2)
    days = oof1[c1]
    pooled = {k: conf(days["high"], v) for k, v in baseline_alerts(days, threshold).items()}
    pooled["F1"], pooled["F2"] = m1, m2
    per_cell = {}
    for (city, sp), g in days.groupby(["city", "species"]):
        g2 = oof2[c2][(oof2[c2]["city"] == city) & (oof2[c2]["species"] == sp)]
        per_cell[f"{city}/{sp}"] = {**{k: conf(g["high"], v) for k, v in baseline_alerts(g, threshold).items()},
                                    "F1": conf(g["high"], model_alert(g, g["prob"], p1)),
                                    "F2": conf(g2["high"], model_alert(g2, g2["prob"], p2))}
    out = {"status": "development only (leave-one-year-out CV on 2021-2025; C and p* chosen on the same CV, "
                     "so F1/F2 numbers are optimistic). Not evidence: the evidence is nowcast_2026.json.",
           "prereg": "docs/PREREG_NOWCAST_2026.md", "dev_years": DEV_YEARS,
           "pooled_cv": pooled, "per_cell_cv": per_cell,
           "chosen": {"F1": {"C": c1, "p_star": p1}, "F2": {"C": c2, "p_star": p2}},
           "features": {"F1": F1_COLS, "F2": F2_COLS}}
    RESULTS.mkdir(parents=True, exist_ok=True)
    OUT_DEV.write_text(json.dumps(out, indent=1) + "\n")
    if write_lock:
        lock = {"prereg": "docs/PREREG_NOWCAST_2026.md", "locked_from_git_sha": git("rev-parse", "HEAD"),
                "nowcast_py_sha256": sha256(Path(__file__)), "fetch_2026_py_sha256": sha256(FETCH_2026),
                "test_window": [TEST_START, TEST_END],
                "bootstrap": {"n": BOOT_N, "block_days": BOOT_BLOCK, "seed": BOOT_SEED},
                "F1": {"C": c1, "p_star": p1, "features": F1_COLS, "models": refit(F1_COLS, c1)},
                "F2": {"C": c2, "p_star": p2, "features": F2_COLS, "models": refit(F2_COLS, c2)}}
        OUT_LOCK.write_text(json.dumps(lock, indent=1) + "\n")
    return out


# ---------------------------------------------------------------- 2026 test (runs once)

def assert_lock_committed_and_pushed() -> dict:
    """Pre-registration §6 guard. Raises SystemExit on any failure."""
    if not OUT_LOCK.exists():
        raise SystemExit("no eval/results/nowcast_lock.json: run --lock, commit and push first")
    rel = str(OUT_LOCK.relative_to(ROOT))
    if not git("ls-files", rel):
        raise SystemExit("lock file is not committed")
    if git("status", "--porcelain", rel, "eval/nowcast.py", "data/fetch_2026.py"):
        raise SystemExit("lock, nowcast.py or fetch_2026.py has uncommitted changes")
    added = git("log", "--diff-filter=A", "--format=%H", "--", rel).splitlines()
    if not added:
        raise SystemExit("cannot find the commit that added the lock")
    lock_commit = added[-1]
    if not git("branch", "-r", "--contains", lock_commit):
        raise SystemExit("the lock commit is not on any remote branch: push it first")
    lock = json.loads(OUT_LOCK.read_text())
    if sha256(Path(__file__)) != lock["nowcast_py_sha256"]:
        raise SystemExit("eval/nowcast.py changed since the lock")
    if sha256(FETCH_2026) != lock["fetch_2026_py_sha256"]:
        raise SystemExit("data/fetch_2026.py changed since the lock")
    lock["_lock_commit"] = lock_commit
    return lock


def frame_2021_2026(city: str) -> pd.DataFrame:
    """Development frame plus the 2026 rows from data/cache_2026 (same loaders, same columns)."""
    dev = bt.build_city_frame(city)
    saved = bt.CACHE_DIR
    try:
        bt.CACHE_DIR = CACHE_2026
        api = bt.load_open_meteo_api_daily(city)
        obs = bt.load_observed_madrid() if city == "madrid" else bt.load_observed_meteoswiss(
            {"basel": "pbs", "zurich": "pzh"}[city])
    finally:
        bt.CACHE_DIR = saved
    idx = pd.date_range("2026-01-01", TEST_END, freq="D")
    new = pd.DataFrame(index=idx).join(api).join(obs)
    power = pd.read_csv(CACHE_2026 / f"nasa_power_{bt.NASA_CITY_KEYS[city]}.csv", parse_dates=["date"])
    new = new.join(power.rename(columns=bt.NASA_POWER_RENAME).set_index("date").reindex(idx))
    new["nasa_ndvi"] = np.nan  # not used by any rule in this test
    out = pd.concat([dev, new.reindex(columns=dev.columns)])
    out.index.name = "date"
    return out


def block_bootstrap(cells: list[dict], rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Moving-block bootstrap (7-day blocks) within each city x species 2026 series.

    `cells`: list of {"high": bool[n], "<rule>": bool[n], ...} in date order.
    Returns the pooled CSI per resample for each rule (same resample for every rule)."""
    rules = [k for k in cells[0] if k != "high"]
    tot = {r: np.zeros((BOOT_N, 3)) for r in rules}  # tp, fp, fn
    for cell in cells:
        n = len(cell["high"])
        n_blocks = int(np.ceil(n / BOOT_BLOCK))
        starts = rng.integers(0, max(1, n - BOOT_BLOCK + 1), size=(BOOT_N, n_blocks))
        idx = (starts[:, :, None] + np.arange(BOOT_BLOCK)[None, None, :]).reshape(BOOT_N, -1)[:, :n]
        idx = np.minimum(idx, n - 1)
        h = cell["high"][idx]
        for r in rules:
            a = cell[r][idx]
            tot[r][:, 0] += (h & a).sum(1)
            tot[r][:, 1] += (~h & a).sum(1)
            tot[r][:, 2] += (h & ~a).sum(1)
    return {r: v[:, 0] / np.maximum(1, v.sum(1)) for r, v in tot.items()}


TEST_RULES = ("P2", "P0", "C0", "F1", "F2", "P0_D2")
HYPOTHESES = {"H1": ("P0", "P2"), "H2": ("F1", "P2"), "H3": ("F1", "P0"), "H4": ("F2", "F1"),
              "sensitivity_P0_D2_vs_P2": ("P0_D2", "P2")}


def run_test_2026() -> dict:
    lock = assert_lock_committed_and_pushed()
    threshold = bt.load_thresholds()["alert"]
    rows, cells, per_cell = [], [], {}
    for city, sps in bt.CITY_SPECIES.items():
        f = frame_2021_2026(city)
        for sp in sps:
            d = features(f, city, sp, threshold[sp], DEV_YEARS)
            d = scored_days(d[(d.index >= TEST_START) & (d.index <= TEST_END)])
            if d.empty:
                continue
            alerts = baseline_alerts(d, threshold)
            alerts["P0_D2"] = np.nan_to_num(d["obs_prev2"].to_numpy(), nan=-1) >= threshold[sp]
            for name in ("F1", "F2"):
                m = lock[name]["models"][sp]
                prob = predict(design(d, lock[name]["features"], m["mu"], m["sd"]), np.array(m["weights"]))
                alerts[name] = model_alert(d, prob, lock[name]["p_star"])
            high = d["high"].to_numpy(bool)
            per_cell[f"{city}/{sp}"] = {k: conf(high, v) for k, v in alerts.items()}
            cells.append({"high": high, **{k: np.asarray(alerts[k], bool) for k in TEST_RULES}})
            rows.append(pd.DataFrame({"high": high, **{k: np.asarray(alerts[k], bool) for k in TEST_RULES}}))
    all_days = pd.concat(rows)
    pooled = {k: conf(all_days["high"], all_days[k]) for k in TEST_RULES}
    boot = block_bootstrap(cells, np.random.default_rng(BOOT_SEED))
    hyps = {}
    for hid, (a, b) in HYPOTHESES.items():
        lo, hi = np.percentile(boot[a] - boot[b], [2.5, 97.5])
        hyps[hid] = {"rule": a, "vs": b, "csi_diff": pooled[a]["csi"] - pooled[b]["csi"],
                     "ci95": [float(lo), float(hi)], "passes": bool(lo > 0)}
    out = {"status": "pre-registered test, scored once", "prereg": "docs/PREREG_NOWCAST_2026.md",
           "lock_commit": lock["_lock_commit"], "test_window": [TEST_START, TEST_END],
           "pooled": pooled, "hypotheses": hyps, "per_cell": per_cell,
           "bootstrap": {"n": BOOT_N, "block_days": BOOT_BLOCK, "seed": BOOT_SEED}}
    OUT_TEST.write_text(json.dumps(out, indent=1) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Trap-first nowcast vs CAMS (pre-registered)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--lock", action="store_true", help="also write the lock file")
    g.add_argument("--test-2026", action="store_true", help="score the locked models on 2026 (once)")
    args = ap.parse_args(argv)
    if args.test_2026:
        out = run_test_2026()
        print(json.dumps({"pooled": out["pooled"], "hypotheses": out["hypotheses"]}, indent=1))
        return 0
    out = run_dev(args.lock)
    print(json.dumps({k: {"csi": round(v["csi"], 3), "recall": round(v["recall"], 3), "fp": v["fp"]}
                      for k, v in out["pooled_cv"].items()}, indent=1))
    print("chosen", out["chosen"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
