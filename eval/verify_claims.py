"""Check every number in CLAIMS.md against the committed results.

Run from the repo root: `.venv/bin/python eval/verify_claims.py`. Offline, no keys.
Exits 0 only if every value matches `eval/results/backtest.json` and `rules/thresholds.json`.
"""
import json
d = json.load(open("eval/results/backtest.json"))
t = json.load(open("rules/thresholds.json"))
R = {(r["city"], r["species"]): r["day_rules"] for r in d["results"]}
kc = d["kill_check"]; c2 = kc["check2_beats_api"]
def p2(c, s): return R[(c, s)]["P2"]
checks = {
 "events": kc["size_check"]["total_observed_events_P2_denominator"] == 863,
 "city_days": kc["size_check"]["total_evaluated_city_days_P2_denominator"] == 8076,
 "seasons": sum(len(r["onset_by_year"]) for r in d["results"]) == 28,
 "P2 pooled": (c2["pooled_p2"]["tp"], c2["pooled_p2"]["n_events"], round(c2["pooled_p2"]["recall"], 3), c2["pooled_p2"]["false_alert_days"]) == (359, 863, 0.416, 77),
 "R1 pooled": (c2["pooled_r1"]["tp"], c2["pooled_r1"]["n_events"], round(c2["pooled_r1"]["recall"], 3), c2["pooled_r1"]["false_alert_days"]) == (354, 863, 0.410, 75),
 "pooled P2 tp = sum of cells": sum(p2(*k)["tp"] for k in R) == 359,
 "pooled P2 false alerts = sum of cells": sum(p2(*k)["false_alert_days"] for k in R) == 77,
 "pooled R1 tp = sum of cells": sum(R[k]["R1"]["tp"] for k in R) == 354,
 "pooled R1 false alerts = sum of cells": sum(R[k]["R1"]["false_alert_days"] for k in R) == 75,
 "madrid olive": (p2("madrid","olive")["tp"], p2("madrid","olive")["n_events"], round(p2("madrid","olive")["recall"], 3)) == (3, 22, 0.136),
 "madrid grass": (p2("madrid","grass")["tp"], p2("madrid","grass")["n_events"], round(p2("madrid","grass")["recall"], 3)) == (22, 70, 0.314),
 "basel birch": round(p2("basel","birch")["recall"], 3) == 0.551,
 "basel grass": round(p2("basel","grass")["recall"], 3) == 0.400,
 "zurich birch": round(p2("zurich","birch")["recall"], 3) == 0.564,
 "zurich grass": round(p2("zurich","grass")["recall"], 3) == 0.335,
 "R2-P2": (c2["r2_minus_p2_lead_days_bootstrap"]["mean_diff"], c2["r2_minus_p2_lead_days_bootstrap"]["ci95"]) == (2.88, [2.64, 3.0]),
 "R2-C0": (c2["r2_minus_c0_lead_days_bootstrap"]["mean_diff"], c2["r2_minus_c0_lead_days_bootstrap"]["ci95"]) == (-1.55, [-7.75, 6.0]),
 "no beats-the-API claim": c2["passed_beats_api_claim"] is False and kc["overall_headline"] == "measured_P2_skill_only_no_beats_api_claim",
 "valencia not scored": d["valencia_scored"] is False and "valencia" not in d["cities_scored"] and all(r["city"] != "valencia" for r in d["results"]),
 "thresholds": t["status"] == "signed" and t["alert"] == {"olive": 162, "grass": 35, "birch": 30} and t["watch"] == {"grass": 20} and d["thresholds_used"] == t["alert"],
 "signed note": "22 Nov 2026" in t["note"] and t["signed_by"] == "Ahmed Zayed",
 "rules": d["rules_evaluated"] == ["P0", "P1", "P2", "R1", "C0", "R2"],
}
ne = d["nasa_evaluation"]
n1 = ne["N1_pooled"]["heldout_2024_2025"]["paired_common_rows"]
n2 = ne["N2_pooled"]["heldout_2024_2025"]
ctl = ne["no_nasa_control"]
checks.update({
 "K3 N1 held-out": (n1["n"], n1["N1"]["mae_from_14d"], n1["N1"]["share_in_7_to_28d"], n1["C0_14d"]["mae_from_14d"], n1["C0_14d"]["share_in_7_to_28d"]) == (10, 21.5, 0.3, 12.5, 0.6),
 "K4 N2 held-out": (n2["N2"]["n_events"], round(n2["P2"]["csi"], 3), round(n2["N2"]["csi"], 3), n2["P2"]["tp"], n2["N2"]["tp"], n2["P2"]["false_alert_days"], n2["N2"]["false_alert_days"]) == (394, 0.382, 0.434, 159, 187, 22, 37),
 "K8 no-NASA control held-out": (round(ctl["heldout_2024_2025"]["csi"], 3), ctl["heldout_2024_2025"]["tp"], ctl["heldout_2024_2025"]["n_events"], ctl["heldout_2024_2025"]["false_alert_days"], round(ctl["heldout_2024_2025"]["precision"], 3)) == (0.486, 215, 394, 48, 0.817),
 "K9 NASA adds no skill": ctl["nasa_adds_skill_heldout"] is False and ctl["heldout_2024_2025"]["csi"] > n2["N2"]["csi"],
 "K10 exploratory": ne["status"].startswith("exploratory"),
})

if __name__ == "__main__":
    for k, v in checks.items():
        print("OK  " if v else "FAIL", k)
    raise SystemExit(0 if all(checks.values()) else 1)
