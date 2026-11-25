"""Build video/remotion/src/v5/data.json: every on-screen number and every cue.

Numbers come from eval/results/nowcast_2026.json and eval/results/ai_layer.json
(and the site-data blob that demo/index.html draws from, for the daily strip).
Timings come from the ElevenLabs alignment files written by video/v5/tts.py.
Nothing here is typed by hand except layout pads.

Run: python3 video/v5/build_data.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VO = ROOT / "video" / "remotion" / "public" / "v5" / "vo"
OUT = ROOT / "video" / "remotion" / "src" / "v5" / "data.json"
FPS = 30

LEAD = 0.15     # silence before the voice in each scene (s)
TAIL = 0.45     # silence after the voice in each scene (s)
EXTRA_TAIL = {"s3": 1.8, "s8": 1.3, "s9": 2.2}   # holds: CI bar, "Not yet tested here", end card (<180s total cap)

# caption display text differs from spoken text only for numbers spoken as words
DISPLAY = [  # longest first
    ("twenty twenty-six", "2026"), ("Two hundred fifteen", "215"), ("one hundred sixty-four", "164"),
    ("one hundred forty-five", "145"), ("one hundred and four", "104"), ("Thirty-nine of five hundred seventy-eight", "39 of 578"),
    ("nineteen point five", "19.5"), ("seventy-nine", "79"), ("flagged seventy.", "flagged 70."), ("fifty-one", "51"),
    ("forty times", "40 times"), ("twenty-four times", "24 times"), ("thirty degrees north", "30° north"),
]


def audio_seconds(mp3: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def show(text: str) -> str:
    for k, v in DISPLAY:
        text = text.replace(k, v)
    return text


def caption_chunks(words: list[dict], max_chars: int = 62) -> list[dict]:
    """One caption per sentence; a long sentence splits once, at the comma (else the word) nearest its middle."""
    sentences, cur = [], []
    for w in words:
        cur.append(w)
        if w["w"][-1] in ".?!":
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)

    def split(ws: list[dict]) -> list[list[dict]]:
        if len(show(" ".join(x["w"] for x in ws))) <= max_chars or len(ws) < 4:
            return [ws]
        total = len(show(" ".join(x["w"] for x in ws)))
        best, best_score = None, 1e9
        for k in range(2, len(ws) - 1):
            left = len(show(" ".join(x["w"] for x in ws[:k])))
            score = abs(left - total / 2) - (12 if ws[k - 1]["w"].endswith((",", ":")) else 0)
            if score < best_score:
                best, best_score = k, score
        return split(ws[:best]) + split(ws[best:])

    res = []
    for sent in sentences:
        for c in split(sent):
            res.append({"text": show(" ".join(x["w"] for x in c)), "start": c[0]["start"], "end": c[-1]["end"]})
    return res


def main() -> None:
    nc = json.loads((ROOT / "eval/results/nowcast_2026.json").read_text())
    ai = json.loads((ROOT / "eval/results/ai_layer.json").read_text())
    html = (ROOT / "demo/index.html").read_text()
    site = json.loads(re.search(r'<script type="application/json" id="site-data">(.*?)</script>', html, re.S).group(1))
    narr = json.loads((ROOT / "video/v5/narration.json").read_text())

    scenes, t = [], 0.0
    for s in narr["scenes"]:
        sid = s["id"]
        al = json.loads((VO / f"{sid}.align.json").read_text())
        dur_audio = audio_seconds(VO / f"{sid}.mp3")
        dur = LEAD + dur_audio + TAIL + EXTRA_TAIL.get(sid, 0.0)
        frames = round(dur * FPS)
        words = [{"w": w["w"], "start": round(w["start"] + LEAD, 3), "end": round(w["end"] + LEAD, 3)} for w in al["words"]]
        scenes.append({
            "id": sid, "from": round(t * FPS), "frames": frames, "voiceAt": LEAD,
            "audio": f"v5/vo/{sid}.mp3", "audioSeconds": round(dur_audio, 3),
            "words": words, "captions": caption_chunks(words),
        })
        t += frames / FPS
    total = sum(s["frames"] for s in scenes)

    pooled = nc["pooled"]
    cells = []
    for c in site["cells"]:
        pc = nc["per_cell"][c["key"]]
        assert pc["P0"]["tp"] == c["trap_hits"] and pc["P2"]["tp"] == c["cams_hits"], c["key"]
        cells.append({"key": c["key"], "city": c["city"], "species": c["species"], "threshold": c["threshold"],
                      "n": pc["P0"]["n_events"], "trap": pc["P0"]["tp"], "cams": pc["P2"]["tp"],
                      "trapCsi": pc["P0"]["csi"], "camsCsi": pc["P2"]["csi"]})
    mg = next(c for c in site["cells"] if c["key"] == "madrid/grass")

    data = {
        "fps": FPS, "totalFrames": total, "scenes": scenes,
        "lock": {"sha": nc["lock_commit"], "short": nc["lock_commit"][:7], "prereg": nc["prereg"]},
        "pooled": {
            "events": pooled["P0"]["n_events"], "days": pooled["P0"]["n_days"],
            "trapHits": pooled["P0"]["tp"], "trapMiss": pooled["P0"]["fn"], "trapFalse": pooled["P0"]["fp"],
            "camsHits": pooled["P2"]["tp"], "camsMiss": pooled["P2"]["fn"], "camsFalse": pooled["P2"]["fp"],
        },
        "hypotheses": {k: {"diff": v["csi_diff"], "ci": v["ci95"], "passes": v["passes"]}
                       for k, v in nc["hypotheses"].items() if k.startswith("H")},
        "cells": cells,
        "cellsWon": sum(1 for c in cells if c["trapCsi"] > c["camsCsi"]),
        "madridGrass": {"threshold": mg["threshold"], "days": mg["days"]},
        "featured": ai["featured"],
        "batch": {"roster": site["console"]["roster"], "eligible": ai["draft_summary"]["n"],
                  "passedGate": ai["draft_summary"]["passed_gate"]},
        "redTeam": {"n": ai["red_team_heldout_summary"]["n"],
                    "broke": ai["red_team_heldout_summary"]["model_broke_a_rule"],
                    "reached": ai["red_team_heldout_summary"]["reached_nurse_with_violation"]},
    }
    # lock and scoring commits, straight from git
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    sha = nc["lock_commit"]
    data["lock"]["time"] = git("log", "-1", "--format=%cI", sha)
    data["lock"]["subject"] = git("log", "-1", "--format=%s", sha)
    scored = git("log", "--format=%h|%cI|%s", f"{sha}..HEAD", "--grep", "score the locked")
    sh, st, ss = scored.splitlines()[-1].split("|", 2)
    data["scored"] = {"short": sh, "time": st, "subject": ss}
    # test count and the demo URL, from the repo itself
    py = Path(os.environ.get("PYTHON", ROOT / ".venv/bin/python"))
    py = py if py.exists() else Path(sys.executable)
    coll = subprocess.run([str(py), "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True, text=True).stdout
    data["tests"] = int(re.search(r"(\d+) tests? collected", coll).group(1))
    data["demoUrl"] = re.search(r"<(https://[^>]+github\.io/[^>]+)>", (ROOT / "README.md").read_text()).group(1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"tests {data['tests']} url {data['demoUrl']} lock {data['lock']['time']} scored {data['scored']}")
    print(f"total {total} frames = {total / FPS:.2f} s; cells won {data['cellsWon']}/6")
    for s in scenes:
        print(f"  {s['id']:4s} from {s['from'] / FPS:6.2f}s  {s['frames'] / FPS:5.2f}s")


if __name__ == "__main__":
    main()
