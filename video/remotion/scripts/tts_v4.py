"""Generate V4 narration clips with ElevenLabs (with timestamps).

Usage: ELEVENLABS_API_KEY=... python3 scripts/tts_v4.py s7n s8
Writes public/audio/<id>.mp3 and <id>.alignment.json. Never prints the key.
"""
import base64
import json
import os
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CFG = json.loads((HERE / "vo_v4.json").read_text())
OUT = HERE.parent / "public" / "audio"


def tts(clip_id: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"text": CFG["clips"][clip_id], "model_id": CFG["model_id"], "voice_settings": CFG["voice_settings"]}).encode()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{CFG['voice_id']}/with-timestamps?output_format=mp3_44100_128"
    req = urllib.request.Request(url, data=body, headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    (OUT / f"{clip_id}.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    (OUT / f"{clip_id}.alignment.json").write_text(json.dumps(d["alignment"]))
    print(clip_id, "ok", round(d["alignment"]["character_end_times_seconds"][-1], 2), "s")


if __name__ == "__main__":
    for cid in sys.argv[1:]:
        tts(cid)
