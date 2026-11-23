"""Export the data the V4 film charts, straight from the backtest code.

Writes video/remotion/src/data/film_data.json and fails unless the totals
equal the published results (863 events, P2 359, R1 354; Madrid olive 3/22;
10 paired held-out N1 seasons with 3 NASA hits and 6 calendar hits).
Run from the repo root: .venv/bin/python video/remotion/scripts/export_film_data.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "eval"))
import backtest as bt  # noqa: E402

OUT = ROOT / "video" / "remotion" / "src" / "data" / "film_data.json"


def events() -> list[dict]:
    alert = bt.load_thresholds()["alert"]
    rows = []
    for city, species_list in bt.CITY_SPECIES.items():
        frame = bt.build_city_frame(city)
        for sp in species_list:
            thr = alert[sp]
            obs = frame[f"obs_{sp}"]
            high = (obs >= thr).where(obs.notna())
            p2, r1 = bt.rule_P2(frame, sp, thr), bt.rule_R1(frame, sp, thr)
            valid = high.notna() & p2.notna()
            for day in frame.index[valid & (high == True)]:  # noqa: E712
                rows.append({"city": city, "species": sp, "date": day.strftime("%Y-%m-%d"),
                             "p2": bool(p2[day]), "r1": bool(r1[day]) if r1.notna()[day] else False})
    return rows


def main() -> None:
    ev = events()
    bjson = json.loads((ROOT / "eval" / "results" / "backtest.json").read_text())
    pooled = bjson["kill_check"]["check2_beats_api"]
    n_r1_valid = pooled["pooled_r1"]["n_events"]
    assert len(ev) == 863 == pooled["pooled_p2"]["n_events"], len(ev)
    assert sum(e["p2"] for e in ev) == 359 == pooled["pooled_p2"]["tp"]
    assert sum(e["r1"] for e in ev) == 354 == pooled["pooled_r1"]["tp"], (sum(e["r1"] for e in ev), n_r1_valid)
    olive = [e for e in ev if e["city"] == "madrid" and e["species"] == "olive"]
    assert len(olive) == 22 and sum(e["p2"] for e in olive) == 3

    seasons = []
    for pcs in bjson["nasa_evaluation"]["per_city_species"]:
        for y in ("2024", "2025"):
            row = pcs["N1"]["by_year"].get(y)
            if not row or any(row[r]["lead_days"] is None for r in ("N1", "C0_14d", "R2")):  # paired = all three fired
                continue
            seasons.append({"label": f"{pcs['city'].capitalize()} {pcs['species']} {y}",
                            "nasa_lead": row["N1"]["lead_days"], "nasa_hit": bool(row["N1"]["in_7_to_28d_window"]),
                            "cal_lead": row["C0_14d"]["lead_days"], "cal_hit": bool(row["C0_14d"]["in_7_to_28d_window"])})
    paired = bjson["nasa_evaluation"]["N1_pooled"]["heldout_2024_2025"]["paired_common_rows"]
    assert len(seasons) == paired["n"] == 10, len(seasons)
    assert sum(s["nasa_hit"] for s in seasons) / 10 == paired["N1"]["share_in_7_to_28d"] == 0.3
    assert sum(s["cal_hit"] for s in seasons) / 10 == paired["C0_14d"]["share_in_7_to_28d"] == 0.6

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"events": ev, "olive": olive, "seasons": seasons}, separators=(",", ":")))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(ev)} events, {len(olive)} olive, {len(seasons)} seasons")


if __name__ == "__main__":
    main()
