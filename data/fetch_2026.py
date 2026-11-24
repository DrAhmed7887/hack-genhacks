"""Download the untouched 2026 test season (docs/PREREG_NOWCAST_2026.md §3, §6).

Same sources, stations and file formats as data/fetch.py, written to
data/cache_2026/. Refuses to run unless eval/results/nowcast_lock.json is
committed and pushed and the scoring code is unchanged since the lock.

    python data/fetch_2026.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "eval"))

import fetch  # noqa: E402
import nowcast  # noqa: E402

MADRID_2026_URL = ("https://datos.comunidad.madrid/dataset/b0f1e9eb-dfe6-4baf-8167-4fa7a0710509/"
                   "resource/31a5495c-e68b-4f36-8caf-6c48d5150406/download/2026.csv")
METEOSWISS_RECENT = {  # "current year up to yesterday" (MeteoSwiss open-data docs)
    "pbs": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pbs/ogd-pollen_pbs_d_recent.csv",
    "pzh": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pzh/ogd-pollen_pzh_d_recent.csv",
}


def _get_madrid_2026(url: str, **kw) -> bytes:
    """Madrid's 2026.csv is UTF-8 with a BOM; 2021-2025 were ISO-8859-1, which
    fetch.fetch_madrid decodes. Re-encode so the same parser reads it
    (prereg deviation 2: loader only, no scoring change)."""
    return _http_get(url, **kw).decode("utf-8-sig").encode("iso-8859-1")


_http_get = fetch._http_get


def main() -> int:
    lock = nowcast.assert_lock_committed_and_pushed()
    print(f"lock OK (commit {lock['_lock_commit'][:7]}); downloading 2026 ...")
    fetch.CACHE_DIR = nowcast.CACHE_2026
    fetch.START_DATE, fetch.END_DATE = nowcast.TEST_START, nowcast.TEST_END
    fetch.CITIES = {k: v for k, v in fetch.CITIES.items() if v["role"] == "scored"}
    fetch.METEOSWISS_STATIONS = METEOSWISS_RECENT
    fetch.MADRID_YEAR_URLS = {2026: MADRID_2026_URL}
    fetch.fetch_open_meteo(force=True)
    fetch.fetch_meteoswiss(force=True)
    fetch._http_get = _get_madrid_2026
    try:
        fetch.fetch_madrid(force=True)
    finally:
        fetch._http_get = _http_get
    fetch.fetch_nasa_power(force=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
