#!/usr/bin/env bash
# Local fallback render (8 GB Mac): video-only chunks of 1000 frames + one audio-only WAV, joined losslessly.
# Usage: video/v5/render_local.sh   (from the repo root) -> video/remotion/out/raw_v5.mp4
set -euo pipefail
cd "$(dirname "$0")/../remotion"
CHROME=$(ls -d ~/.cache/hyperframes/chrome/chrome-headless-shell/*/chrome-headless-shell-mac-arm64/chrome-headless-shell | head -1)
TOTAL=$(python3 -c "import json;print(json.load(open('src/v5/data.json'))['totalFrames'])")
mkdir -p out/chunks_v5
: > out/chunks_v5/list.txt
for ((a=0; a<TOTAL; a+=1000)); do
  b=$(( a+999 < TOTAL-1 ? a+999 : TOTAL-1 ))
  f=out/chunks_v5/c_$(printf %05d $a).mp4
  if [ ! -s "$f" ]; then
    npx remotion render src/v5/index.ts FilmV5 "$f" --frames=$a-$b --muted --concurrency=4 --crf=16 \
      --browser-executable="$CHROME" --log=error
  fi
  echo "file '$(basename "$f")'" >> out/chunks_v5/list.txt
  echo "chunk $a-$b done $(date +%H:%M:%S)"
done
npx remotion render src/v5/index.ts FilmV5 out/chunks_v5/audio.wav --codec=wav --browser-executable="$CHROME" --log=error
ffmpeg -v error -y -f concat -safe 0 -i out/chunks_v5/list.txt -i out/chunks_v5/audio.wav -map 0:v -map 1:a -c:v copy -c:a pcm_s16le out/raw_v5.mov
ffmpeg -v error -y -i out/raw_v5.mov -c:v copy -c:a aac -b:a 256k out/raw_v5.mp4 && rm out/raw_v5.mov
ffprobe -v error -show_entries format=duration -of csv=p=0 out/raw_v5.mp4
echo RENDER_DONE
