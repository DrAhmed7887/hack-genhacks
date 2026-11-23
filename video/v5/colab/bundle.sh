#!/usr/bin/env bash
# Pack the Remotion project (V5 only: src, public/v5 without 3D frames or music) for Colab notebook B.
# Usage: video/v5/colab/bundle.sh <drive_render_dir>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DST="$1"
cd "$ROOT/video/remotion"
tar --exclude='public/v5/3d' --exclude='public/v5/music' -czf "$DST/remotion_bundle.tgz" \
  package.json package-lock.json remotion.config.ts tsconfig.json src public/v5
ls -la "$DST/remotion_bundle.tgz"
