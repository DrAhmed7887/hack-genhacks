"""Narration for PollenPlan V2: ElevenLabs /with-timestamps -> src/timeline.json + out/PollenPlan_GenHacks_v2_FINAL_1080p.srt."""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "public" / "audio"
CFG = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
TIMELINE = HERE / "src" / "timeline.json"
SRT_PATH = HERE / "out" / "PollenPlan_GenHacks_v2_FINAL_1080p.srt"
LEAD, TAIL = 0.35, 0.55
MAX_CHARS = 54


def _key() -> str:
    k = subprocess.run(
        ["security", "find-generic-password", "-s", "ELEVENLABS_API_KEY", "-w"],
        capture_output=True, text=True,
    ).stdout.strip()
    if not k:
        raise SystemExit("Keychain item ELEVENLABS_API_KEY not found")
    return k


def generate(line: dict, key: str) -> None:
    body = json.dumps({
        "text": line["say"],
        "model_id": CFG["model"],
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": CFG["speed"]},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{CFG['voice']}/with-timestamps?output_format=mp3_44100_128",
        data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    (AUDIO / f"{line['id']}.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    (AUDIO / f"{line['id']}.alignment.json").write_text(json.dumps(d["alignment"]), encoding="utf-8")
    print(f"{line['id']}: {len(line['say'])} chars", file=sys.stderr)


def words(alignment: dict) -> list[list]:
    out, cur, start = [], "", None
    for ch, a, b in zip(
        alignment["characters"],
        alignment["character_start_times_seconds"],
        alignment["character_end_times_seconds"],
    ):
        if ch.isspace():
            if cur:
                out.append([cur, start, end])
            cur, start = "", None
            continue
        if start is None:
            start = a
        cur, end = cur + ch, b
    if cur:
        out.append([cur, start, end])
    disp = CFG.get("display", {})
    for w in out:
        for cand in (w[0], w[0].rstrip(",.;:")):
            if cand in disp:
                w[0] = disp[cand] + w[0][len(cand):]
                break
    return [[w, round(a, 3), round(b, 3)] for w, a, b in out]


def cues(ws: list[list], offset: float) -> list[dict]:
    frases, buf = [], []
    for w in ws:
        buf.append(w)
        if re.search(r"[.;:?!]$", w[0]):
            frases.append(buf)
            buf = []
    if buf:
        frases.append(buf)
    partes = []

    def cortar(f):
        texto = " ".join(x[0] for x in f)
        if len(texto) <= MAX_CHARS or len(f) < 4:
            partes.append(f)
            return
        largos = [len(" ".join(x[0] for x in f[:k])) for k in range(1, len(f))]
        mitad = len(texto) / 2
        k = min(range(1, len(f)), key=lambda k: abs(largos[k - 1] - mitad) - (8 if f[k - 1][0].endswith(",") else 0))
        cortar(f[:k])
        cortar(f[k:])

    for f in frases:
        cortar(f)
    out = [
        {"text": " ".join(x[0] for x in p), "start": round(offset + p[0][1], 3), "end": round(offset + p[-1][2] + 0.15, 3)}
        for p in partes
    ]
    for a, b in zip(out, out[1:]):
        a["end"] = min(a["end"], b["start"])
    return out


def _fmt_srt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_timeline() -> None:
    scenes, captions, t = [], [], 0.0
    for line in CFG["lines"]:
        al = json.loads((AUDIO / f"{line['id']}.alignment.json").read_text(encoding="utf-8"))
        ws = words(al)
        dur = round(LEAD + ws[-1][2] + TAIL + line.get("hold", 0), 3)
        scenes.append({
            "id": line["id"],
            "start": round(t, 3),
            "dur": dur,
            "audio": f"{line['id']}.mp3",
            "audioAt": LEAD,
            "words": [[w, round(a + LEAD, 3), round(b + LEAD, 3)] for w, a, b in ws],
        })
        captions += cues(ws, t + LEAD)
        t += dur
    TIMELINE.parent.mkdir(parents=True, exist_ok=True)
    TIMELINE.write_text(
        json.dumps({"total": round(t, 3), "scenes": scenes, "captions": captions}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    SRT_PATH.parent.mkdir(parents=True, exist_ok=True)
    srt_lines = []
    for i, c in enumerate(captions, 1):
        srt_lines.append(f"{i}\n{_fmt_srt(c['start'])} --> {_fmt_srt(c['end'])}\n{c['text']}\n")
    SRT_PATH.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"timeline: {len(scenes)} scenes, {len(captions)} captions, {t:.1f} s", file=sys.stderr)
    for s in scenes:
        print(f"  {s['id']}: {s['start']:6.1f} s + {s['dur']:5.1f} s", file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--timeline", action="store_true")
    a = ap.parse_args(argv)
    AUDIO.mkdir(parents=True, exist_ok=True)
    if not a.timeline:
        key = _key()
        for line in CFG["lines"]:
            if (a.only and line["id"] == a.only) or (not a.only and not (AUDIO / f"{line['id']}.mp3").exists()):
                generate(line, key)
    build_timeline()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
