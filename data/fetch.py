#!/usr/bin/env python3
"""PollenPlan data fetch script.

Downloads real, open pollen data and caches small, commit-able derived
CSVs into data/cache/ so that eval/backtest.py can run fully offline
(no network, no key) from a fresh clone.

Sources (see docs/DATA_SOURCES.md and data/DATA_CARD.md for full detail):
  - Open-Meteo Air Quality API (CC BY 4.0): hourly olive_pollen, grass_pollen,
    birch_pollen for Madrid FACF, Basel PBS, Zurich PZH, and Valencia (demo
    only, never scored).
  - MeteoSwiss STAC collection ch.meteoschweiz.ogd-pollen (CC-BY): daily CSVs
    for stations PBS (Basel) and PZH (Zurich), columns kabetud0 (birch) and
    khpoacd0 (grass), 6 UTC - 6 UTC following day, unit No/m3.
  - NASA POWER daily point API (public domain) and NASA ORNL DAAC MODIS
    MOD13Q1 NDVI REST (CC0 / public domain): see data/DATA_CARD.md section 5.
  - Comunidad de Madrid "Histórico de mediciones de polen" (CC BY): yearly
    CSVs 2021-2025 for all traps; filtered here to station FACF and types
    "Olivo" and "Gramíneas".

This script only downloads and caches. It does not compute any alert rule
or metric — that is eval/backtest.py's job, kept separate on purpose.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE_DIR = HERE / "cache"
RAW_DIR = HERE / "raw"  # gitignored scratch space for full raw downloads

START_DATE = "2021-01-01"
END_DATE = "2025-12-31"

# --- Open-Meteo -------------------------------------------------------
OPEN_METEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

CITIES = {
    "madrid_facf": {"lat": 40.4454, "lon": -3.7263, "role": "scored"},
    "basel_pbs": {"lat": 47.5618, "lon": 7.5839, "role": "scored"},
    "zurich_pzh": {"lat": 47.3782, "lon": 8.5656, "role": "scored"},
    "valencia_demo": {"lat": 39.47, "lon": -0.38, "role": "demo_only"},
}

OPEN_METEO_HOURLY_VARS = "olive_pollen,grass_pollen,birch_pollen"

# --- MeteoSwiss ---------------------------------------------------------
METEOSWISS_STATIONS = {
    "pbs": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pbs/ogd-pollen_pbs_d_historical.csv",
    "pzh": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pzh/ogd-pollen_pzh_d_historical.csv",
}
# Confirmed via ogd-pollen_meta_parameters.csv: daily avg 6 UTC - 6 UTC
# following day, unit No/m3.
METEOSWISS_COLUMNS = {
    "birch": "kabetud0",
    "grass": "khpoacd0",
}

# --- Comunidad de Madrid -------------------------------------------------
MADRID_YEAR_URLS = {
    2021: "https://datos.comunidad.madrid/dataset/b0f1e9eb-dfe6-4baf-8167-4fa7a0710509/resource/2615b31b-a74a-4674-89c2-85cf63ee7f42/download/2021.csv",
    2022: "https://datos.comunidad.madrid/dataset/b0f1e9eb-dfe6-4baf-8167-4fa7a0710509/resource/fed85c1e-c5e8-49cf-9985-a39fb10f978c/download/2022.csv",
    2023: "https://datos.comunidad.madrid/dataset/b0f1e9eb-dfe6-4baf-8167-4fa7a0710509/resource/adaaa9ec-196f-417d-80dc-0f9ee1813b3a/download/2023.csv",
    2024: "https://datos.comunidad.madrid/dataset/b0f1e9eb-dfe6-4baf-8167-4fa7a0710509/resource/58005206-9020-4c4e-8cd0-16089760f02f/download/2024.csv",
    2025: "https://datos.comunidad.madrid/dataset/b0f1e9eb-dfe6-4baf-8167-4fa7a0710509/resource/fc197e69-c3fb-4cea-a763-4609d9a66fad/download/2025.csv",
}
MADRID_STATION = "FACF"  # Ciudad Universitaria, lat 40.4454 lon -3.7263
MADRID_TYPE_LABELS = {"olive": "Olivo", "grass": "Gramíneas"}

USER_AGENT = "PollenPlan-hackathon-fetch/0.1 (non-commercial; see docs/DATA_SOURCES.md)"


def _http_get(url: str, timeout: int = 60, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def fetch_open_meteo(force: bool = False) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name, cfg in CITIES.items():
        out_path = CACHE_DIR / f"open_meteo_{name}.csv"
        if out_path.exists() and not force:
            print(f"[open-meteo] cache hit: {out_path.name}")
            continue
        url = (
            f"{OPEN_METEO_URL}?latitude={cfg['lat']}&longitude={cfg['lon']}"
            f"&hourly={OPEN_METEO_HOURLY_VARS}&start_date={START_DATE}"
            f"&end_date={END_DATE}&timezone=UTC"
        )
        print(f"[open-meteo] fetching {name} ...")
        raw = _http_get(url)
        payload = json.loads(raw)
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        olive = hourly.get("olive_pollen", [None] * len(times))
        grass = hourly.get("grass_pollen", [None] * len(times))
        birch = hourly.get("birch_pollen", [None] * len(times))
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["time_utc", "olive_pollen", "grass_pollen", "birch_pollen"])
            for t, o, g, b in zip(times, olive, grass, birch):
                w.writerow([t, o, g, b])
        print(f"[open-meteo] wrote {out_path} ({len(times)} hourly rows)")


def fetch_meteoswiss(force: bool = False) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for station, url in METEOSWISS_STATIONS.items():
        out_path = CACHE_DIR / f"meteoswiss_{station}_daily.csv"
        if out_path.exists() and not force:
            print(f"[meteoswiss] cache hit: {out_path.name}")
            continue
        print(f"[meteoswiss] fetching {station} ...")
        raw = _http_get(url)
        text = raw.decode("iso-8859-1")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        rows_out = []
        for row in reader:
            ts = row["reference_timestamp"]  # DD.MM.YYYY HH:MM
            try:
                day, month, year_time = ts.split(".", 2)
                year = year_time[:4]
            except ValueError:
                continue
            if not (START_DATE[:4] <= year <= END_DATE[:4]):
                continue
            date_iso = f"{year}-{month}-{day}"
            birch = row.get(METEOSWISS_COLUMNS["birch"], "")
            grass = row.get(METEOSWISS_COLUMNS["grass"], "")
            rows_out.append((date_iso, birch, grass))
        rows_out.sort(key=lambda r: r[0])
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date_utc_6_6", "birch_no_m3", "grass_no_m3"])
            w.writerows(rows_out)
        print(f"[meteoswiss] wrote {out_path} ({len(rows_out)} daily rows)")


def fetch_madrid(force: bool = False) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CACHE_DIR / "madrid_facf_daily.csv"
    if out_path.exists() and not force:
        print(f"[madrid] cache hit: {out_path.name}")
        return
    all_rows = []
    for year, url in MADRID_YEAR_URLS.items():
        print(f"[madrid] fetching {year} ...")
        raw = _http_get(url)
        text = raw.decode("iso-8859-1")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        for row in reader:
            if row.get("captador") != MADRID_STATION:
                continue
            tipo = row.get("tipo_polinico", "")
            species = None
            for sp, label in MADRID_TYPE_LABELS.items():
                if tipo == label:
                    species = sp
                    break
            if species is None:
                continue
            fecha = row.get("fecha_lectura", "")  # YYYY/MM/DD HH:MM:SS.fff
            date_part = fecha.split(" ")[0].replace("/", "-")
            value = row.get("granos_de_polen_x_metro_cubico", "")
            all_rows.append((date_part, species, value))
    all_rows.sort(key=lambda r: (r[0], r[1]))
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "species", "grains_m3"])
        w.writerows(all_rows)
    print(f"[madrid] wrote {out_path} ({len(all_rows)} rows, station {MADRID_STATION})")


# --- NASA POWER (daily, point) -----------------------------------------------
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,GWETROOT,WS2M"
NASA_POWER_COLUMNS = [
    ("T2M", "t2m"), ("T2M_MAX", "t2m_max"), ("T2M_MIN", "t2m_min"),
    ("PRECTOTCORR", "prectotcorr"), ("ALLSKY_SFC_SW_DWN", "allsky_sfc_sw_dwn"),
    ("RH2M", "rh2m"), ("GWETROOT", "gwetroot"), ("WS2M", "ws2m"),
]

# --- NASA ORNL DAAC MODIS REST (MOD13Q1, 250 m, 16-day NDVI) --------------------
MODIS_BASE = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
MODIS_START = "2020-12-01"  # include the late-Dec-2020 composite so 1 Jan 2021 has a prior value
MODIS_END = "2025-12-31"
MODIS_BAND = "250m_16_days_NDVI"
MODIS_CHUNK = 10


def fetch_nasa_power(force: bool = False) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name, cfg in CITIES.items():
        out_path = CACHE_DIR / f"nasa_power_{name}.csv"
        if out_path.exists() and not force:
            print(f"[nasa-power] cache hit: {out_path.name}")
            continue
        url = (
            f"{NASA_POWER_URL}?parameters={NASA_POWER_PARAMS}&community=AG"
            f"&longitude={cfg['lon']}&latitude={cfg['lat']}"
            f"&start={START_DATE.replace('-', '')}&end={END_DATE.replace('-', '')}&format=JSON"
        )
        print(f"[nasa-power] fetching {name} ...")
        payload = json.loads(_http_get(url, timeout=120))
        params = payload["properties"]["parameter"]
        dates = sorted(params[NASA_POWER_COLUMNS[0][0]].keys())
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date"] + [c for _, c in NASA_POWER_COLUMNS])
            for d in dates:
                row = [f"{d[:4]}-{d[4:6]}-{d[6:]}"]
                for key, _ in NASA_POWER_COLUMNS:
                    v = params[key].get(d)
                    row.append("" if v is None or float(v) <= -998.5 else v)  # -999 fill -> empty
                w.writerow(row)
        print(f"[nasa-power] wrote {out_path} ({len(dates)} daily rows)")


def fetch_nasa_modis(force: bool = False) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name, cfg in CITIES.items():
        out_path = CACHE_DIR / f"nasa_modis_{name}.csv"
        if out_path.exists() and not force:
            print(f"[nasa-modis] cache hit: {out_path.name}")
            continue
        print(f"[nasa-modis] fetching {name} ...")
        q = f"latitude={cfg['lat']}&longitude={cfg['lon']}"
        avail = json.loads(_http_get(f"{MODIS_BASE}/dates?{q}"))["dates"]
        avail = [d for d in avail if MODIS_START <= d["calendar_date"] <= MODIS_END]
        avail.sort(key=lambda d: d["calendar_date"])
        rows = []
        for i in range(0, len(avail), MODIS_CHUNK):
            chunk = avail[i : i + MODIS_CHUNK]
            url = (
                f"{MODIS_BASE}/subset?{q}&startDate={chunk[0]['modis_date']}"
                f"&endDate={chunk[-1]['modis_date']}&kmAboveBelow=0&kmLeftRight=0&band={MODIS_BAND}"
            )
            payload = json.loads(_http_get(url, timeout=120))
            for rec in payload.get("subset", []):
                val = rec["data"][0]
                ndvi = "" if val <= -2000 else round(val * 0.0001, 6)  # -3000 fill -> empty
                rows.append((rec["calendar_date"], rec["modis_date"], ndvi))
            time.sleep(0.2)
        rows.sort()
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "modis_date", "ndvi"])
            w.writerows(rows)
        print(f"[nasa-modis] wrote {out_path} ({len(rows)} composites, {len(avail)} dates listed)")


def main() -> int:
    force = "--force" in sys.argv
    fetch_open_meteo(force=force)
    fetch_meteoswiss(force=force)
    fetch_madrid(force=force)
    fetch_nasa_power(force=force)
    fetch_nasa_modis(force=force)
    print("Done. Cached files in", CACHE_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
