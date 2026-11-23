#!/usr/bin/env bash
# V5 master: mix the Flow Music bed under the voice (ducked), normalise to -16 LUFS / -1.5 dBTP,
# write the SRT from the approved captions, then run the QC checks and a 1 fps contact sheet.
# Usage: video/v5/master.sh <raw_v5.mp4 from Remotion (voice in)>   (run from the repo root)
set -euo pipefail
RAW="$1"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/video/remotion/out"
BED="$ROOT/video/remotion/public/v5/music/bed.wav"
FINAL="$OUT/PollenPlan_GenHacks_v5_FINAL_1080p.mp4"
mkdir -p "$OUT"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW")
FADE_OUT_AT=$(python3 -c "print(max(0, $DUR - 3.5))")
echo "raw duration ${DUR}s"

# 1. mix: bed at -14 dB, ducked a further ~6 dB under speech, faded in and out
ffmpeg -v error -y -i "$RAW" -i "$BED" -filter_complex "
  [1:a]atrim=0:${DUR},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:d=1.5,afade=t=out:st=${FADE_OUT_AT}:d=3.5[bed];
  [0:a]asplit=2[vo][key];
  [bed][key]sidechaincompress=threshold=0.025:ratio=5:attack=40:release=450[duck];
  [vo][duck]amix=inputs=2:duration=first:normalize=0[mix]" \
  -map 0:v -map "[mix]" -c:v copy -c:a pcm_s16le "$OUT/mix_v5.mov"

# 2. two-pass loudnorm to -16 LUFS integrated, -1.5 dBTP
read -r I TP LRA THRESH OFFSET < <(ffmpeg -hide_banner -i "$OUT/mix_v5.mov" -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 \
  | python3 -c "import sys,json,re; t=sys.stdin.read(); i=t.rindex('{'); d=json.loads(t[i:t.index('}', i)+1]); print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -v error -y -i "$OUT/mix_v5.mov" -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$THRESH:offset=$OFFSET:linear=true,aresample=48000" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 192k "$FINAL"

# 3. SRT from the approved script captions (data.json), absolute times
python3 - "$ROOT/video/remotion/src/v5/data.json" "${FINAL%.mp4}.srt" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
n, out = 0, []
for s in d["scenes"]:
    base = s["from"] / d["fps"]
    for i, c in enumerate(s["captions"]):
        nxt = s["captions"][i + 1]["start"] if i + 1 < len(s["captions"]) else c["end"] + 0.6
        n += 1
        out.append(f"{n}\n{ts(base + c['start'])} --> {ts(base + min(nxt, c['end'] + 0.6) - 0.02)}\n{c['text']}\n")
open(sys.argv[2], "w").write("\n".join(out))
print("srt cues", n)
PY

# 4. QC
echo "== QC =="
ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL" | awk '{printf "duration %.2f s (%d:%05.2f)\n", $1, $1/60, $1%60}'
ffmpeg -hide_banner -i "$FINAL" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|LRA:|Peak:)" | tail -3
echo "-- silences over 4 s (whole mix, -50 dB):"; ffmpeg -hide_banner -i "$FINAL" -af silencedetect=n=-50dB:d=4 -f null - 2>&1 | grep -c silence_start || true
echo "-- voice-only gaps over 4 s:"; ffmpeg -hide_banner -i "$RAW" -af silencedetect=n=-45dB:d=4 -f null - 2>&1 | grep silence_ || echo "none"
echo "-- black frames:"; ffmpeg -hide_banner -i "$FINAL" -vf "blackdetect=d=0.1:pix_th=0.10" -an -f null - 2>&1 | grep blackdetect || echo "none"
ffmpeg -v error -y -i "$FINAL" -vf "fps=1,scale=384:-1,tile=10x18" -frames:v 1 "$OUT/contact_sheet_v5.png"
echo "contact sheet: $OUT/contact_sheet_v5.png"
rm -f "$OUT/mix_v5.mov"
