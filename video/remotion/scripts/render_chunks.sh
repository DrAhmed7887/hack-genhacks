#!/usr/bin/env bash
# Render the film in video-only chunks (one browser, low memory), render the audio once,
# then join, mux and master to -16 LUFS. Safe on an 8 GB laptop; re-run skips finished chunks.
# Usage (from video/remotion): bash scripts/render_chunks.sh <name>
set -euo pipefail
NAME=${1:-PollenPlan_GenHacks_v4_FINAL_1080p}
TOTAL=$(node -e "const t=require('./src/timeline.json');console.log(Math.round(t.total*30))")
STEP=1000
mkdir -p out/chunks
: > out/chunks/list.txt
i=0
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  f=out/chunks/c$(printf %02d $i).mp4
  if [ ! -s "$f" ]; then
    echo "chunk $i: frames $a-$b"
    npx remotion render src/index.ts Film "$f.part.mp4" --frames=$a-$b --muted --concurrency=1 --crf=18 --log=error
    mv "$f.part.mp4" "$f"
  fi
  echo "file '$(basename "$f")'" >> out/chunks/list.txt
  i=$((i+1))
done
[ -s out/chunks/audio.wav ] || npx remotion render src/index.ts Film out/chunks/audio.wav --codec=wav --log=error
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i out/chunks/list.txt -c copy out/chunks/video.mp4
# two-pass loudness normalisation to -16 LUFS, -1.5 dBTP
ffmpeg -hide_banner -i out/chunks/audio.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2> out/chunks/ln.txt
read I TP LRA TH OFF < <(python3 -c "
import json,re;t=open('out/chunks/ln.txt').read();d=json.loads(t[t.rindex('{'):t.rindex('}')+1])
print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -hide_banner -loglevel error -y -i out/chunks/video.mp4 -i out/chunks/audio.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF:linear=true,alimiter=limit=0.84:level=false" \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest "out/$NAME.mp4"
echo "wrote out/$NAME.mp4"
