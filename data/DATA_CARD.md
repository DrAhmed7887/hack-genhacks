# PollenPlan data card

Written from files actually downloaded and inspected (via `curl` and
`data/fetch.py`) on 22 Nov 2026. Every column name, unit, and window below
was read out of the source file or its published data dictionary, not
assumed. See `docs/DATA_PLAN.md` for the backtest design and
`docs/DATA_SOURCES.md` for the full evidence table (D1, D2, O1-O10).

## 1. Open-Meteo Air Quality API (modelled, CAMS ENSEMBLE)

- **Call shape (confirmed live):**
  `GET https://air-quality-api.open-meteo.com/v1/air-quality?latitude=<lat>&longitude=<lon>&hourly=olive_pollen,grass_pollen,birch_pollen&start_date=2021-01-01&end_date=2025-12-31&timezone=UTC`
- **Response:** JSON, `hourly.time` (ISO8601, UTC) and one array per
  variable, unit `"Grains/m³"` as given in `hourly_units`.
- **Cities fetched:** Madrid FACF (40.4454, -3.7263), Basel PBS (47.5618,
  7.5839), Zürich PZH (47.3782, 8.5656), Valencia (39.47, -0.38, **demo
  only, never scored** per `.kiro/steering/rules.md`).
- **Cache:** `data/cache/open_meteo_<city>.csv`, columns
  `time_utc,olive_pollen,grass_pollen,birch_pollen`, one row per hour,
  43,824 rows per city (2021-01-01T00:00 to 2025-12-31T23:00).
- **Licence:** CC BY 4.0, free tier non-commercial. Attribution required:
  "Weather data by Open-Meteo.com", CAMS citation "CAMS European air
  quality forecasts, ENSEMBLE data."

## 2. MeteoSwiss `ch.meteoschweiz.ogd-pollen` (observed, ground truth for Basel/Zürich)

- **Discovery:** STAC item IDs for Basel and Zürich are literally `pbs` and
  `pzh` in `https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen/items`.
  Each item's `assets` list the daily historical CSV:
  `https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/<station>/ogd-pollen_<station>_d_historical.csv`.
  This file already extends through 2025-12-31, so no separate `_recent.csv`
  was needed for the 2021-2025 backtest period.
- **Raw columns (inspected directly):**
  `station_abbr;reference_timestamp;kaalnud0;kabetud0;kacoryd0;kafagud0;kafraxd0;kaquerd0;khpoacd0;kaalnud1;kabetud1;kacoryd1;kafagud1;kafraxd1;kaquerd1;khpoacd1`
  — semicolon-delimited, `reference_timestamp` as `DD.MM.YYYY HH:MM`.
- **Column meaning (confirmed from the collection's own data dictionary,
  `ogd-pollen_meta_parameters.csv`, ISO-8859-1 encoded):**
  - `kabetud0` = "Birch; daily average pollen concentration 6 UTC - 6 UTC
    following day / Betula", unit `No/m³`, datatype Integer, granularity D.
  - `khpoacd0` = "Grasses; daily average pollen concentration 6 UTC - 6 UTC
    following day / Poaceae", unit `No/m³`, datatype Integer, granularity D.
  - The `...d1` variants are the midnight-aligned (0 UTC - 0 UTC) version of
    the same measurement and are **not used** — the backtest aligns
    Open-Meteo to the `d0` (6 UTC - 6 UTC) window to match MeteoSwiss, per
    `docs/DATA_PLAN.md` §2.1.
- **Cache:** `data/cache/meteoswiss_<station>_daily.csv`, columns
  `date_utc_6_6,birch_no_m3,grass_no_m3`, filtered to 2021-01-01..2025-12-31.
  PBS: 1,574 rows. PZH: 1,612 rows. (Some dates missing a value for one or
  both species; left blank, not imputed.)
- **Licence:** STAC `license` field is `CC-BY`. Attribution "Source:
  MeteoSwiss".

## 3. Comunidad de Madrid "Histórico de mediciones de polen" (observed, ground truth for Madrid)

- **Discovery:** `datos.gob.es/catalogo/...` returned HTTP 503 on every
  attempt (including with a browser user-agent, retried 3 times); this
  looks like a WAF or outage on that host, not a dataset problem. The same
  dataset is served directly by the comunidad.madrid CKAN API, which
  worked on the first try:
  `https://datos.comunidad.madrid/api/3/action/package_search?q=polen`
  → dataset `mediciones_polen_historico` (id
  `b0f1e9eb-dfe6-4baf-8167-4fa7a0710509`), one CSV resource per year
  1993-2026, plus a dictionary document
  `descripcion_ampliada_y_diccionario.pdf`.
- **Raw columns (inspected directly, 2025.csv):**
  `captador;fecha_lectura;tipo_polinico;granos_de_polen_x_metro_cubico`
  — semicolon-delimited, ISO-8859-1 encoded, CRLF line endings,
  `fecha_lectura` as `YYYY/MM/DD HH:MM:SS.fff` (time part always
  `00:00:00.000`).
- **Column meaning (from the dictionary PDF, page 2 table):**
  - `captador`: sampler/trap identifier. Station used here: **FACF**
    (Ciudad Universitaria, lat 40.4454, lon -3.7263 — matches the
    Open-Meteo Madrid coordinate exactly).
  - `fecha_lectura` (timestamp): "Momento temporal en que se hizo el
    muestreo" ("the time at which the sampling was done").
  - `tipo_polinico` (text): pollen type. Exact Spanish labels used in the
    file, confirmed by listing unique values: `Olivo` (olive), `Gramíneas`
    (grass), plus 23 others (Abedul/birch, Aliso, Artemisia, etc.).
  - `granos_de_polen_x_metro_cubico` (numeric): "Medida resultado del
    muestreo, en granos de polen por metro cúbico" (grains of pollen per
    cubic metre).
- **Daily averaging window: UNVERIFIED.** The dictionary PDF states
  sampling is manual and daily ("Las muestras son recogidas diariamente de
  forma manual") but gives no UTC start/end time for the 24 h window,
  unlike the explicit "6 UTC - 6 UTC" wording MeteoSwiss publishes. Per
  `docs/DATA_PLAN.md` §2.1 this is recorded here as **unverified** and the
  Madrid leg of the backtest is run on calendar-day alignment only; no UTC
  window claim is made for Madrid.
- **Cache:** `data/cache/madrid_facf_daily.csv`, columns
  `date,species,grains_m3`, filtered to station FACF and
  species ∈ {olive, grass}, years 2021-2025. 2,922 rows (2 species × ~1,461
  calendar days, one row per species per day).
- **Licence:** dataset page text "Creative Commons Attribution" (CC BY),
  confirmed via the CKAN `license_title` field returned by the API.

## 4. Cache summary

| File | Rows | Columns | Period |
|---|---|---|---|
| `open_meteo_madrid_facf.csv` | 43,824 | time_utc, olive_pollen, grass_pollen, birch_pollen | hourly 2021-01-01..2025-12-31 |
| `open_meteo_basel_pbs.csv` | 43,824 | same | same |
| `open_meteo_zurich_pzh.csv` | 43,824 | same | same |
| `open_meteo_valencia_demo.csv` | 43,824 | same | same (demo only, never scored) |
| `meteoswiss_pbs_daily.csv` | 1,574 | date_utc_6_6, birch_no_m3, grass_no_m3 | daily 2021-2025 |
| `meteoswiss_pzh_daily.csv` | 1,612 | date_utc_6_6, birch_no_m3, grass_no_m3 | daily 2021-2025 |
| `madrid_facf_daily.csv` | 2,922 | date, species, grains_m3 | daily 2021-2025 |

Total cache size: 4.8 MB, 181,411 lines, all committed to `data/cache/`.
Reproduce with `make fetch` (or `.venv/bin/python data/fetch.py`); the
backtest itself reads only from `data/cache/` and makes no network calls.

## 5. Synthetic patient list (`data/patients.csv`)

Generated by `data/make_patients.py`, seed `20261120`, N = 200, fields per
`docs/DATA_PLAN.md` §3. No real patient data of any kind. The following
shares are **illustrative assumptions**, not epidemiology, and are never
quoted as clinical fact (PMID 38311961 gives no Valencia-specific split):

| Field | Illustrative shares used |
|---|---|
| `age_band` | 6-12: 10%, 13-17: 10%, 18-39: 30%, 40-64: 35%, 65+: 15% |
| `sensitised_to` | grass 70%, olive 45%, birch 5% (independent draws, a patient may be sensitised to 0-3 species) |
| `current_med_on_file` | none 20%, oral antihistamine 45%, intranasal steroid 20%, both 15% |
| `severity` | mild 60%, moderate-severe 40% |
| `asthma_flag` | yes 25%, no 75% |
| `language` | es 70%, en 30% |

All shares are independent Bernoulli/categorical draws from
`numpy.random.default_rng(20261120)`; re-running `make data` reproduces the
identical `data/patients.csv` byte-for-byte.
