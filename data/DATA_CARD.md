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
- **`reference_timestamp` convention — verified, start of window, not end**
  (re-checked 22 Nov 2026, live `curl` against the published files, see
  shell history; not assumed):
  - Source: `https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/ogd-pollen_meta_parameters.csv`
    (collection-level parameter dictionary) and
    `https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pbs/ogd-pollen_pbs_d_historical.csv`
    (the actual daily data file for Basel).
  - The parameter dictionary's English description for `kabetud0` reads
    verbatim: **"Birch; daily average pollen concentration 6 UTC - 6 UTC
    following day / Betula"**. The German, French and Italian columns say
    the same thing ("6 UTC - 6 UTC Folgetag" / "6 UTC - 6 UTC du jour
    suivant" / "6 UTC - 6 UTC del giorno seguente") — "following day" /
    "Folgetag" / "jour suivant" / "giorno seguente" all describe the
    window's *end*, confirming the window runs forward from the labelled
    day, not backward into it.
  - The actual daily historical CSV confirms this: the first data row is
    `PBS;01.03.1969 00:00;2;0;0;0;0;0;0;;;;;;;` — `reference_timestamp`
    is stamped at `00:00` on the calendar date the row is labelled with,
    and that row's `kabetud0`/`khpoacd0` value is the average over 6 UTC
    on *that same labelled date* through 6 UTC the next calendar day.
  - **Conclusion:** `reference_timestamp` D's `d0` value covers
    `[D 06:00 UTC, (D+1) 06:00 UTC)`. This is the **start** of the
    6 UTC-6 UTC window, not its end. This matches, and confirms, the
    alignment already implemented in `eval/backtest.py`
    (`load_open_meteo_api_daily`): Open-Meteo hourly rows are shifted
    back 6 hours before flooring to a calendar day, so API(D) is built
    from exactly `[D 06:00 UTC, (D+1) 06:00 UTC)`, the same window as
    Observed(D) from MeteoSwiss. No code change was needed; this entry
    records the verification and its source.
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

## 5. NASA Earth-observation layers (POWER + MODIS NDVI)

Added 22 Nov 2026 for the multi-sensor backtest (rules N1, N2 in
`eval/backtest.py`). Fetched by `fetch_nasa_power` / `fetch_nasa_modis` in
`data/fetch.py`; the backtest itself stays offline and reads only the cache.

### 6a. NASA POWER daily point API (weather and root-zone soil)

- **Call shape:** `GET https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,GWETROOT,WS2M&community=AG&longitude=<lon>&latitude=<lat>&start=20210101&end=20251231&format=JSON`
- **Version / sources (from the response header, 22 Nov 2026):** POWER Daily API
  v2.10.5, source native resolution (MERRA-2 based meteorology), `time_standard` LST,
  `fill_value` -999.0.
- **Fields and units:** `T2M`, `T2M_MAX`, `T2M_MIN` (deg C, 2 m), `PRECTOTCORR`
  (mm/day, bias-corrected precipitation), `ALLSKY_SFC_SW_DWN` (MJ/m2/day, all-sky
  surface shortwave downward irradiance), `RH2M` (%), `GWETROOT` (root-zone soil
  wetness, 0-1), `WS2M` (m/s at 2 m).
- **Cache:** `data/cache/nasa_power_<city>.csv`, header
  `date,t2m,t2m_max,t2m_min,prectotcorr,allsky_sfc_sw_dwn,rh2m,gwetroot,ws2m`,
  one row per day 2021-01-01..2025-12-31 (1,826 rows per city), for madrid_facf,
  basel_pbs, zurich_pzh and valencia_demo. `-999` fill values are written as empty
  (NaN in pandas) and never imputed.
- **Caveats:** POWER is a gridded reanalysis/satellite product at coarse
  resolution (about 0.5 deg for MERRA-2 fields), not a station measurement. Its
  day boundary is local solar time (LST), not the 6 UTC-6 UTC window used for
  MeteoSwiss, so alignment with Basel/Zurich pollen days is approximate to within
  a few hours. **Causal use:** N2 on day D reads only prior-day (D-1) POWER
  values (solar, Tmax, precip), never day D (zero same-day hindsight;
  2021-01-01 has no prior day and gets no boost). POWER (MERRA-2) is published
  about 2-3 days late, so a D-1 value may not exist in live operation. Measured
  sensitivity with D-3 predictors, recalibrated (`nasa_evaluation.latency_sensitivity_lag3`):
  held-out 2024-2025 CSI 0.405 and recall 44.4% (versus 0.434 and 47.5% at D-1;
  P2 0.382 and 40.4%). `GWETROOT` is contextual telemetry only, not an N1/N2 input.
- **Licence / citation:** NASA POWER data are publicly available at no cost,
  without restriction on use (public domain; NASA data policy). Cite: "These data
  were obtained from the NASA Langley Research Center (LaRC) POWER Project funded
  through the NASA Earth Science/Applied Science Program."

### 6b. NASA ORNL DAAC MODIS MOD13Q1 (NDVI, 250 m, 16-day composites)

- **Calls:** `GET https://modis.ornl.gov/rst/api/v1/MOD13Q1/dates?latitude=<lat>&longitude=<lon>`
  (available composites), then
  `.../MOD13Q1/subset?latitude=<lat>&longitude=<lon>&startDate=<modis_date>&endDate=<modis_date>&kmAboveBelow=0&kmLeftRight=0&band=250m_16_days_NDVI`
  in chunks of at most 10 composites, 0.2 s apart.
- **Band:** `250m_16_days_NDVI`, scale factor 0.0001, single 250 m pixel at the city
  point (a pixel can be mixed urban/vegetation, so NDVI is a coarse greenness signal).
  Values <= -2000 (fill -3000) are written as empty; otherwise `round(raw * 0.0001, 6)`.
- **Cache:** `data/cache/nasa_modis_<city>.csv`, header `date,modis_date,ndvi`
  (`date` = composite calendar_date, i.e. the composite's first day). Composites
  from 2020-12-01 are kept so 1 Jan 2021 has a prior value.
- **Causal join (exact +16d completion):** a MOD13Q1 composite stamped
  `calendar_date` is built from observations over the following 16 days, so
  `load_nasa_daily` treats it as available only on
  `avail_date = calendar_date + 16 days`, and joins with
  `merge_asof(left_on="date", right_on="avail_date", direction="backward")`.
  Date D therefore sees only composites with `avail_date <= D`; fill-value
  composites are skipped and D keeps the last valid one. This removes the
  16-day lookahead entirely (the +16 d is past the composite window close; it
  does not include any MODIS publication delay). The first composite (2020-12-02) is available on
  2020-12-18, before 2021-01-01, so every 2021 day has a value. NDVI is
  contextual telemetry; N1 and N2 decision rules do not use it.
- **Licence / citation:** ORNL DAAC MODIS web service; MOD13Q1 is a NASA LP DAAC
  product, open data with no use restrictions (CC0 / public domain). Cite: ORNL
  DAAC. 2018. MODIS and VIIRS Land Products Global Subsetting and Visualization
  Tool. ORNL DAAC, Oak Ridge, Tennessee, USA, https://doi.org/10.3334/ORNLDAAC/1379;
  and Didan, K. MOD13Q1 MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN
  Grid V061, NASA LP DAAC, https://doi.org/10.5067/MODIS/MOD13Q1.061.

### 6c. Cache additions

| File | Rows | Columns | Period |
|---|---|---|---|
| `nasa_power_<city>.csv` (4 files) | 1,826 | date + 8 POWER fields | daily 2021-2025 |
| `nasa_modis_<city>.csv` (4 files) | see below | date, modis_date, ndvi | 16-day composites, 2020-12..2025-12 |

## 6. Synthetic patient list (`data/patients.csv`)

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
