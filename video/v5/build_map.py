"""Scene-8 line map: Natural Earth 1:110m land outlines (public domain), plate carrée,
clipped to the film's view. Writes video/remotion/src/v5/map.json (SVG path + projection).

Run: python3 video/v5/build_map.py <ne_110m_land.geojson>
Source: https://github.com/nvkelso/natural-earth-vector (v5.1.2, geojson/ne_110m_land.geojson)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LON0, LON1, LAT0, LAT1 = -32.0, 58.0, 14.0, 76.0   # view
X0, Y0, PX = 600.0, 96.0, 13.6                    # top-left of the map in the frame, px per degree

# CAMS European air quality forecast domain (dataset page, checked 23 Nov 2026; demo #where)
CAMS = {"west": -25.0, "east": 45.0, "south": 30.0, "north": 72.0}
# city coordinates (decimal degrees)
PLACES = [
    {"name": "Madrid", "lat": 40.42, "lon": -3.70, "kind": "tested"},
    {"name": "Basel", "lat": 47.56, "lon": 7.59, "kind": "tested"},
    {"name": "Zürich", "lat": 47.37, "lon": 8.54, "kind": "tested"},
    {"name": "Alexandria", "lat": 31.20, "lon": 29.92, "kind": "unchecked"},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "kind": "unchecked"},
    {"name": "Asyut", "lat": 27.18, "lon": 31.18, "kind": "none"},
]


def xy(lon, lat):
    return round(X0 + (lon - LON0) * PX, 1), round(Y0 + (LAT1 - lat) * PX, 1)


def main():
    geo = json.loads(Path(sys.argv[1]).read_text())
    parts = []
    for feat in geo["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = poly[0]
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            if max(lons) < LON0 - 5 or min(lons) > LON1 + 5 or max(lats) < LAT0 - 5 or min(lats) > LAT1 + 5:
                continue
            pts = [xy(lo, la) for lo, la in ring]
            parts.append("M" + "L".join(f"{x},{y}" for x, y in pts) + "Z")
    view = {"x": X0, "y": Y0, "w": round((LON1 - LON0) * PX, 1), "h": round((LAT1 - LAT0) * PX, 1)}
    cx0, cy0 = xy(CAMS["west"], CAMS["north"])
    cx1, cy1 = xy(CAMS["east"], CAMS["south"])
    out = {
        "source": "Natural Earth 1:110m land v5.1.2 (public domain)",
        "view": view, "path": " ".join(parts),
        "cams": {**CAMS, "x": cx0, "y": cy0, "w": round(cx1 - cx0, 1), "h": round(cy1 - cy0, 1)},
        "lat30y": xy(0, 30.0)[1],
        "places": [{**p, "x": xy(p["lon"], p["lat"])[0], "y": xy(p["lon"], p["lat"])[1]} for p in PLACES],
    }
    dst = ROOT / "video/remotion/src/v5/map.json"
    dst.write_text(json.dumps(out))
    print("paths", len(parts), "bytes", dst.stat().st_size, "view", view)


if __name__ == "__main__":
    main()
