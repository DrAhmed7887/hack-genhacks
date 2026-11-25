"""Check the numbers CLAIMS.md publishes against the committed results.

Two halves: (1) the expected values below must equal `eval/results/backtest.json`
and `rules/thresholds.json`; (2) each of those values, as written in CLAIMS.md,
must appear in CLAIMS.md, so a number edited in the doc alone fails too.
Run from the repo root: `.venv/bin/python eval/verify_claims.py`. Offline, no keys.
"""
import json
d = json.load(open("eval/results/backtest.json"))
t = json.load(open("rules/thresholds.json"))
R = {(r["city"], r["species"]): r["day_rules"] for r in d["results"]}
kc = d["kill_check"]; c2 = kc["check2_beats_api"]
def p2(c, s): return R[(c, s)]["P2"]
checks = {
 "events": kc["size_check"]["total_observed_events_P2_denominator"] == 863,
 "city_days": kc["size_check"]["total_evaluated_city_days_P2_denominator"] == 7373,
 "seasons": sum(len(r["onset_by_year"]) for r in d["results"]) == 28,
 "P2 pooled": (c2["pooled_p2"]["tp"], c2["pooled_p2"]["n_events"], round(c2["pooled_p2"]["recall"], 3), c2["pooled_p2"]["false_alert_days"]) == (359, 863, 0.416, 53),
 "R1 pooled": (c2["pooled_r1"]["tp"], c2["pooled_r1"]["n_events"], round(c2["pooled_r1"]["recall"], 3), c2["pooled_r1"]["false_alert_days"]) == (354, 863, 0.410, 51),
 "pooled P2 tp = sum of cells": sum(p2(*k)["tp"] for k in R) == 359,
 "pooled P2 false alerts = sum of cells": sum(p2(*k)["false_alert_days"] for k in R) == 53,
 "pooled R1 tp = sum of cells": sum(R[k]["R1"]["tp"] for k in R) == 354,
 "pooled R1 false alerts = sum of cells": sum(R[k]["R1"]["false_alert_days"] for k in R) == 51,
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
n1t = ne["N1_pooled"]["train_2021_2023"]["paired_common_rows"]["N1"]
n2 = ne["N2_pooled"]["heldout_2024_2025"]
ctl = ne["no_nasa_control"]
checks.update({
 "K2 N1 in-sample": (n1t["n"], round(n1t["mae_from_14d"], 3), round(n1t["share_in_7_to_28d"], 3)) == (10, 4.8, 0.7),
 "K3 N1 held-out": (n1["n"],) + tuple(round(x, 3) for x in (n1["N1"]["mae_from_14d"], n1["N1"]["share_in_7_to_28d"], n1["C0_14d"]["mae_from_14d"], n1["C0_14d"]["share_in_7_to_28d"])) == (10, 21.9, 0.3, 12.5, 0.6),
 "K4 N2 held-out": (n2["N2"]["n_events"], round(n2["P2"]["csi"], 3), round(n2["N2"]["csi"], 3), n2["P2"]["tp"], n2["N2"]["tp"], n2["P2"]["false_alert_days"], n2["N2"]["false_alert_days"]) == (394, 0.382, 0.434, 159, 187, 22, 37),
 "K8 no-NASA control held-out": (round(ctl["heldout_2024_2025"]["csi"], 3), ctl["heldout_2024_2025"]["tp"], ctl["heldout_2024_2025"]["n_events"], ctl["heldout_2024_2025"]["false_alert_days"], round(ctl["heldout_2024_2025"]["precision"], 3)) == (0.486, 215, 394, 48, 0.817),
 "K9 NASA adds no skill": ctl["nasa_adds_skill_heldout"] is False and ctl["heldout_2024_2025"]["csi"] > n2["N2"]["csi"],
 "K10 exploratory": ne["status"].startswith("exploratory"),
})

nc = json.load(open("eval/results/nowcast_2026.json"))
P, H = nc["pooled"], nc["hypotheses"]
def r3(x): return round(x, 3)
checks.update({
 "N1 2026 scale": (P["P0"]["n_events"], P["P0"]["n_days"]) == (215, 1706),
 "N2 trap": (P["P0"]["tp"], P["P0"]["fp"], r3(P["P0"]["recall"]), r3(P["P0"]["csi"])) == (164, 40, 0.763, 0.643),
 "N3 CAMS": (P["P2"]["tp"], P["P2"]["fp"], r3(P["P2"]["recall"]), r3(P["P2"]["csi"])) == (70, 10, 0.326, 0.311),
 "N4 H1": (r3(H["H1"]["csi_diff"]), [r3(x) for x in H["H1"]["ci95"]], H["H1"]["passes"]) == (0.332, [0.203, 0.457], True),
 "N5 H2-H4": [(r3(H[k]["csi_diff"]), [r3(x) for x in H[k]["ci95"]], H[k]["passes"]) for k in ("H2", "H3", "H4")]
             == [(0.291, [0.176, 0.406], True), (-0.041, [-0.117, 0.028], False), (0.02, [-0.021, 0.064], False)],
 "N6 D-2": (P["P0_D2"]["tp"], r3(P["P0_D2"]["csi"]), [r3(x) for x in H["sensitivity_P0_D2_vs_P2"]["ci95"]]) == (151, 0.572, [0.134, 0.384]),
 "N7 others": [(P[k]["tp"], r3(P[k]["csi"])) for k in ("F1", "F2", "C0")] == [(159, 0.602), (181, 0.622), (118, 0.449)],
 "N8 misses": (P["P2"]["fn"], P["P0"]["fn"]) == (145, 51),
 "N9 all six cells": sum(c["P0"]["csi"] > c["P2"]["csi"] for c in nc["per_cell"].values()) == 6 == len(nc["per_cell"]),
 "N10 2021-2025": (sum(r["day_rules"]["P0"]["tp"] for r in d["results"]), sum(r["day_rules"]["P0"]["tp"] + r["day_rules"]["P0"]["fn"] for r in d["results"])) == (670, 857),
 "N lock commit": nc["lock_commit"].startswith("5c45eaf"),
 "N madrid olive 11 high days": nc["per_cell"]["madrid/olive"]["P0"]["n_events"] == 11,
 "N10b 2021-2025 trap beats forecast in all six series": sum(r["day_rules"]["P0"]["csi"] > r["day_rules"]["P2"]["csi"] for r in d["results"]) == 6 == len(d["results"]),
 "N bootstrap 10,000 x 7-day blocks": (nc["bootstrap"]["n"], nc["bootstrap"]["block_days"]) == (10000, 7),
})

ai_ = json.load(open("eval/results/ai_layer.json"))
_tiers = [sum(x["tier"] == t for x in ai_["drafts"]) for t in (1, 2, 3)]
checks.update({
 "AI1 drafts": (ai_["draft_summary"]["n"], ai_["draft_summary"]["passed_gate"], ai_["draft_summary"]["fell_back"]) == (39, 21, 18),
 "AI2 tiers": _tiers == [23, 10, 6],
 "AI3 red team": (ai_["red_team_summary"]["n"], ai_["red_team_summary"]["model_broke_a_rule"], ai_["red_team_summary"]["reached_nurse_with_violation"]) == (40, 18, 0),
 "AI5 Q&A": (len(ai_["qa"]), sum(q["route"] == "symptom_router" and not q["model_called"] for q in ai_["qa"]), sum(bool(q["violations"]) for q in ai_["qa"])) == (12, 3, 0),
 "AI6 held-out red team": (ai_["red_team_heldout_summary"]["n"], ai_["red_team_heldout_summary"]["model_broke_a_rule"], ai_["red_team_heldout_summary"]["reached_nurse_with_violation"]) == (40, 24, 0),
})

CLAIMS_TEXT = [  # value as CLAIMS.md prints it; each must be present
    "| 863 observed high-pollen events |", "| A2 | 7,373 evaluated city-days", "| 7373 (= " + " + ".join(str(p2(*k)["n_evaluated_days"]) for k in R) + ",",
    "| 28 |", "tp 359, n_events 863", "`kill_check.check2_beats_api.pooled_p2.false_alert_days` | 53 |",
    "tp 354, n_events 863", "`kill_check.check2_beats_api.pooled_r1.false_alert_days` | 51 |",
    " + ".join(str(p2(*k)["false_alert_days"]) for k in R) + " = 53",  # per-cell values from the JSON
    " + ".join(str(R[k]["R1"]["false_alert_days"]) for k in R) + " = 51",
    "N1 MAE 4.8 d from 14 d, 70% in 7-28 d", "N1 21.9 d MAE, 30% hit; C0_14d 12.5 d MAE, 60% hit",
    "P2 CSI 0.382 → N2 0.434", "CSI 0.486; recall 54.6% (215/394); 48 false-alert days; precision 81.7%",
    "`nasa_evaluation.no_nasa_control.nasa_adds_skill_heldout` | `false` |",
    "| n 39, passed 21, fell back 18 |", "| 23 / 10 / 6 |", "| 40, 18, 0 |", "| 12, 3, 0 |", "| 40, 24, 0 |",
    "| 215, 1706 |", "tp 164, fp 40, recall 0.763, csi 0.643", "tp 70, fp 10, recall 0.326, csi 0.311",
    "csi_diff 0.332, ci95 [0.203, 0.457], passes true", "| 145, 51 |", "| 670/857, 359/863 |", "| 104, 19.5, 79 |",
]
_claims_md = open("CLAIMS.md", encoding="utf-8").read()
checks.update({f"CLAIMS.md says: {t[:60]}": t in _claims_md for t in CLAIMS_TEXT})

if __name__ == "__main__":
    for k, v in checks.items():
        print("OK  " if v else "FAIL", k)
    raise SystemExit(0 if all(checks.values()) else 1)
