"""Write the two Colab notebooks for the V5 GPU renders into the Drive render folder.

Run: python3 video/v5/colab/make_notebooks.py <drive_render_dir>
Notebook A renders the Blender trap (Cycles, OptiX). Notebook B renders the Remotion film.
Both read inputs from, and write outputs to, the same Drive folder; no secrets are involved.
"""
import json
import sys
from pathlib import Path

DRIVE_DIR = "/content/drive/MyDrive/Zayed OS/Hackathons/2026-12-genhacks/video/v5_render"


def nb(cells):
    return {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"accelerator": "GPU", "colab": {"gpuType": "L4", "provenance": []},
                         "kernelspec": {"name": "python3", "display_name": "Python 3"}},
            "cells": [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                       "source": c.strip("\n")} if not c.startswith("#md ") else
                      {"cell_type": "markdown", "metadata": {}, "source": c[4:]} for c in cells]}


COMMON = [
    "#md # PollenPlan V5 render ({what})\nRun all. Outputs go to the Drive folder `v5_render/out/`. Disconnect and delete the runtime afterwards.",
    f"""
from google.colab import drive
drive.mount('/content/drive')
import os, time, subprocess
DIR = {DRIVE_DIR!r}
os.makedirs(DIR + '/out', exist_ok=True)
print(open('/proc/meminfo').readline().strip(), os.cpu_count(), 'cpus')
!nvidia-smi --query-gpu=name,memory.total --format=csv
""",
]

BLENDER = COMMON + [
    """
t0 = time.time()
!wget -q https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz -O /content/b.tar.xz && tar -xf /content/b.tar.xz -C /content && mv /content/blender-5.3.0-linux-x64 /content/blender
!apt-get -qq install -y libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 > /dev/null
print('blender ready', round(time.time() - t0), 's')
""",
    """
t0 = time.time()
os.makedirs('/content/trap', exist_ok=True)
cmd = ['/content/blender/blender', '-b', '-P', DIR + '/trap_scene.py', '--', '--out', '/content/trap',
       '--samples', '96', '--device', 'OPTIX']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
n = 0
with open('/content/trap_log.txt', 'w') as log:
    for line in p.stdout:
        log.write(line)
        if 'Saved:' in line:
            n += 1
            if n % 10 == 0 or n == 1:
                print(f'{n} frames, {time.time() - t0:.0f} s', flush=True)
        elif 'GPU' in line or 'Error' in line or 'OptiX' in line:
            print(line.strip()[:200], flush=True)
print('exit', p.wait(), 'frames', n, 'seconds', round(time.time() - t0))
""",
    """
!cd /content/trap && tar -cf "$DIR/out/trap_frames.tar" trap_*.png 2>/dev/null || true
!cp /content/trap_log.txt "$DIR/out/trap_log.txt"
!ls -la "$DIR/out"
print('DONE_TRAP')
""",
]

REMOTION = COMMON + [
    """
t0 = time.time()
!curl -fsSL https://deb.nodesource.com/setup_22.x | bash - > /dev/null && apt-get -qq install -y nodejs > /dev/null
!apt-get -qq install -y ffmpeg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 > /dev/null
!rm -rf /content/remotion && mkdir -p /content/remotion && tar -xzf "$DIR/remotion_bundle.tgz" -C /content/remotion
!cd /content/remotion && npm ci --no-audit --no-fund --loglevel=error && npx remotion browser ensure
!mkdir -p /content/remotion/public/v5/3d/trap && tar -xf "$DIR/out/trap_frames.tar" -C /content/remotion/public/v5/3d/trap
print('remotion ready', round(time.time() - t0), 's')
""",
    """
t0 = time.time()
conc = max(2, os.cpu_count())
def render(gl):
    cmd = (f'cd /content/remotion && npx remotion render src/v5/index.ts FilmV5 out/raw_v5.mp4 '
           f'--concurrency={conc} --gl={gl} --crf=16 --log=info > /content/render_{gl}.log 2>&1')
    rc = subprocess.call(cmd, shell=True)
    print(gl, 'exit', rc, round(time.time() - t0), 's')
    print(''.join(open(f'/content/render_{gl}.log').readlines()[-12:]))
    return rc
rc = render('angle-egl')
if rc != 0:
    rc = render('swangle')
!cp /content/render_*.log "$DIR/out/" 2>/dev/null || true
print('render seconds', round(time.time() - t0))
!cp /content/remotion/out/raw_v5.mp4 "$DIR/out/raw_v5.mp4" && ls -la "$DIR/out"
print('DONE_REMOTION')
""",
]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, cells, what in [("v5_render_A_blender.ipynb", BLENDER, "A: Blender trap, Cycles OptiX"),
                              ("v5_render_B_remotion.ipynb", REMOTION, "B: Remotion film")]:
        cells = [c.replace("{what}", what) for c in cells]
        (out / name).write_text(json.dumps(nb(cells), indent=1))
        print("wrote", out / name)


if __name__ == "__main__":
    main()
