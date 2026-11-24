"""V5 narration: one ElevenLabs request per scene, with character timestamps.

Key: env ELEVENLABS_API_KEY (from Keychain by the caller); never printed.
Usage: ELEVENLABS_API_KEY=... python3 video/v5/tts.py [--only s3,s8]
Writes video/remotion/public/v5/vo/<id>.mp3 and <id>.align.json, plus a words file.
"""
import base64, json, os, sys, urllib.request, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "remotion" / "public" / "v5" / "vo"
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "narration.json").read_text())
key = os.environ["ELEVENLABS_API_KEY"]
only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 and sys.argv[1] == "--only" else None
v = cfg["voice"]
scenes = cfg["scenes"]

def words_from_alignment(al):
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, s0 = [], "", None
    for c, a, b in zip(chars, st, en):
        if c.isspace():
            if cur: words.append({"w": cur, "start": s0, "end": prev_end}); cur = ""
            continue
        if not cur: s0 = a
        cur += c; prev_end = b
    if cur: words.append({"w": cur, "start": s0, "end": prev_end})
    return words

for i, s in enumerate(scenes):
    if only and s["id"] not in only:
        continue
    text = s.get("say", s["caption"])
    body = {
        "text": text, "model_id": v["model_id"],
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0,
                           "use_speaker_boost": True, "speed": v["speed"]},
        "previous_text": scenes[i - 1].get("say", scenes[i - 1]["caption"]) if i else None,
        "next_text": scenes[i + 1].get("say", scenes[i + 1]["caption"]) if i + 1 < len(scenes) else None,
    }
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{v['voice_id']}/with-timestamps?output_format=mp3_44100_192",
        data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    (OUT / f"{s['id']}.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    al = d["alignment"]
    (OUT / f"{s['id']}.align.json").write_text(json.dumps({"text": text, "alignment": al, "words": words_from_alignment(al)}, indent=1))
    print(s["id"], "ok", round(al["character_end_times_seconds"][-1], 2), "s")
