"""Build src/timeline.json for V4 from the V2 timeline plus the regenerated slots.

V2 slots keep their words and captions (shifted in time); slots listed in NEW are
rebuilt from public/audio/<id>.alignment.json. Also writes out/<name>.srt.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
V2 = json.loads((HERE / "timeline_v2.json").read_text())
ORDER = ["s1", "s2", "s3", "s4", "s5a", "s5b", "s6", "s7", "s7n", "s8"]
NEW = {"s3", "s7n", "s8"}
AUDIO_AT, TAIL, MAX_CHARS = 0.35, 0.55, 36


def words_from_alignment(path: pathlib.Path) -> list:
    a = json.loads(path.read_text())
    words, cur, t0, t1 = [], "", None, None
    for ch, s, e in zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                words.append([cur, round(t0 + AUDIO_AT, 3), round(t1 + AUDIO_AT, 3)])
            cur, t0 = "", None
            continue
        if t0 is None:
            t0 = s
        cur, t1 = cur + ch, e
    if cur:
        words.append([cur, round(t0 + AUDIO_AT, 3), round(t1 + AUDIO_AT, 3)])
    return words


def chunk_captions(words: list, offset: float) -> list:
    merged = []
    for w in words:  # glue a lone dash onto the word before it
        if w[0] in ("—", "-") and merged:
            merged[-1] = [merged[-1][0] + " —", merged[-1][1], w[2]]
        else:
            merged.append(w)
    caps, line = [], []
    for w in merged:
        text = " ".join(x[0] for x in line + [w])
        short_end = w[0][-1] in ".;?!" and len(w[0]) <= 9 and len(text) <= MAX_CHARS + 10
        if line and len(text) > MAX_CHARS and not short_end:
            caps.append(line)
            line = []
        line.append(w)
        if w[0][-1] in ".;?!":
            caps.append(line)
            line = []
    if line:
        caps.append(line)
    out = []
    for i, ln in enumerate(caps):
        end = caps[i + 1][0][1] if i + 1 < len(caps) else ln[-1][2]
        out.append({"text": " ".join(x[0] for x in ln), "start": round(offset + ln[0][1], 3), "end": round(offset + max(ln[-1][2], end), 3)})
    return out


def main() -> None:
    old = {s["id"]: s for s in V2["scenes"]}
    scenes, captions, t = [], [], 0.0
    for sid in ORDER:
        if sid in NEW:
            words = words_from_alignment(ROOT / "public" / "audio" / f"{sid}.alignment.json")
            dur = round(words[-1][2] + TAIL, 3)
            captions += chunk_captions(words, t)
        else:
            o = old[sid]
            words, dur = o["words"], o["dur"]
            shift = t - o["start"]
            captions += [{**c, "start": round(c["start"] + shift, 3), "end": round(c["end"] + shift, 3)}
                         for c in V2["captions"] if o["start"] <= c["start"] < o["start"] + o["dur"]]
        scenes.append({"id": sid, "start": round(t, 3), "dur": dur, "audio": f"{sid}.mp3", "audioAt": AUDIO_AT, "words": words})
        t += dur
    tl = {"total": round(t, 3), "scenes": scenes, "captions": captions}
    (ROOT / "src" / "timeline.json").write_text(json.dumps(tl, indent=1))

    def ts(x: float) -> str:
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = "".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n" for i, c in enumerate(captions, 1))
    name = sys.argv[1] if len(sys.argv) > 1 else "PollenPlan_GenHacks_v4_FINAL_1080p"
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / f"{name}.srt").write_text(srt)
    print("total", tl["total"], "s;", len(captions), "captions")


if __name__ == "__main__":
    main()
