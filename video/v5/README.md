# PollenPlan demo film (V5)

A 2:57 film built in code. Every number on screen is read from the repo's result files at build time, and every product screen is a real capture of `demo/index.html`.

## Pipeline

| Step | File | What it does |
|---|---|---|
| Narration | `narration.json`, `tts.py` | The script from `video/SCRIPT_V5.md`, voiced with ElevenLabs (with word timestamps). Key read from the `ELEVENLABS_API_KEY` env var. |
| Data | `build_data.py` | Reads `eval/results/nowcast_2026.json`, `eval/results/ai_layer.json`, the demo's site data and git (lock and scoring commits), and writes `video/remotion/src/v5/data.json` with every number and scene cue. |
| Screens | `capture.mjs` | Playwright captures of `demo/index.html` at 3×, plus the boxes of the text and rows that callouts point to. |
| Map | `build_map.py` | Natural Earth 1:110m land outlines (public domain) and the CAMS forecast domain box. |
| 3D | `blender/trap_scene.py` | A procedural pollen trap whose tape unrolls into the film's timeline strip (Blender Cycles). |
| Film | `video/remotion/src/v5/` | The Remotion composition `FilmV5`. |
| Render | `render_local.sh` or `colab/` | Chunked local render, or Colab notebooks for the GPU 3D render and the film. |
| Master | `master.sh` | Music under the voice, loudness to −16 LUFS, captions (SRT), QC checks and a contact sheet. |

## Rebuild

```bash
node video/v5/capture.mjs
python3 video/v5/build_data.py
blender -b -P video/v5/blender/trap_scene.py -- --out video/remotion/public/v5/3d/trap
video/v5/render_local.sh
video/v5/master.sh video/remotion/out/raw_v5.mp4
```

## AI-generated material in the film

- Voice: ElevenLabs.
- Music: Google Flow Music.
- Three short b-roll clips (a meadow, a clinic desk, pollen in light): Gemini Omni via Google Flow, each labelled on screen as AI-generated footage.

No AI imagery of people or of app screens is used. The data, charts and product screens are not AI-generated.
