"""Build the PollenPlan HyperFrames film from timings.json (voice clock) and backtest.json.

Usage: python3 build.py  -> index.html, compositions/*.html, assets/audio/{bed.wav, voice/*.wav}
Every number shown is read from eval/results/backtest.json; every screen is a
screenshot of demo/index.html as it ships. No mock UI, no invented numbers.
"""
import html
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
T = json.loads((HERE / "timings.json").read_text())
SC = {s["id"]: s for s in T["scenes"]}
TOTAL = T["total"]
BT = json.loads((ROOT / "eval" / "results" / "backtest.json").read_text())
assert BT["kill_check"]["overall_headline"] == "measured_P2_skill_only_no_beats_api_claim"
P2 = BT["kill_check"]["check2_beats_api"]["pooled_p2"]["recall"]
R1 = BT["kill_check"]["check2_beats_api"]["pooled_r1"]["recall"]
EVENTS = sum(r["day_rules"]["P2"]["n_events"] for r in BT["results"])
DAYS = sum(r["day_rules"]["P2"]["n_evaluated_days"] for r in BT["results"])
MADRID = {r["species"]: r["day_rules"]["P2"]["recall"] for r in BT["results"] if r["city"] == "madrid"}
ONSET_N = sum(len(r["onset_by_year"]) for r in BT["results"])
INK, MUTED, LINE = "#1D1D1B", "#5D5D58", "#E2E0D8"
RED, REDBG, OK, OKBG, WARN, WARNBG, INFO, INFOBG = "#A4161A", "#FDE8E8", "#1F7A4D", "#E6F3EC", "#9A5B00", "#FDF0DC", "#2B5C9E", "#E7EEF9"
e = html.escape
PYTEST_LINES = (HERE / "assets" / "shots" / "pytest_output.txt").read_text().strip().splitlines()[-2:]
PYTEST_HTML = "<br>".join(e(ln) for ln in PYTEST_LINES)

BASE_CSS = f"""
#root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Inter", sans-serif; color: {INK}; }}
.all {{ position: absolute; inset: 0; }}
.card {{ position: absolute; background: #FFFFFF; border: 1px solid {LINE}; border-radius: 14px;
  box-shadow: 0 18px 40px rgba(29,29,27,0.08); }}
.chip {{ display: inline-block; font-weight: 700; font-size: 28px; line-height: 1; padding: 9px 18px; border-radius: 999px; white-space: nowrap; }}
.bad {{ color: {RED}; background: {REDBG}; }} .ok {{ color: {OK}; background: {OKBG}; }}
.warn {{ color: {WARN}; background: {WARNBG}; }} .info {{ color: {INFO}; background: {INFOBG}; }}
.mono {{ font-family: "JetBrains Mono", monospace; font-variant-ligatures: none; font-feature-settings: "calt" 0, "liga" 0; }}
.muted {{ color: {MUTED}; }}
.hide {{ opacity: 0; }}
.shot {{ display: block; border-radius: 12px; background: #fff; border: 1px solid {LINE}; }}
.title5 {{ font-size: 56px; font-weight: 900; letter-spacing: -0.02em; }}
"""

JS_HELPERS = """
const arrive = (sel, t, from = { y: 28 }) => tl.fromTo(sel, { opacity: 0, ...from }, { opacity: 1, x: 0, y: 0, duration: 0.5, ease: "expo.out" }, t);
const blurIn = (sel, t, d = 0.2) => tl.fromTo(sel, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: d, ease: "expo.out" }, t);
const leave = (sel, t) => tl.to(sel, { opacity: 0, filter: "blur(6px)", duration: 0.25, ease: "power3.in" }, t);
const box = (sel, t, c, bg) => tl.fromTo(sel, { boxShadow: "0 0 0 0px " + c, backgroundColor: "rgba(255,255,255,0)" }, { boxShadow: "0 0 0 4px " + c, backgroundColor: bg, duration: 0.3, ease: "power2.out" }, t);
const stamp = (sel, t) => { tl.set(sel, { opacity: 1 }, t); tl.fromTo(sel, { scale: 1.14 }, { scale: 1, duration: 0.18, ease: "power2.out" }, t); };
const cam = (sel, t, x, y, s, d = 0.8) => tl.to(sel, { x: x, y: y, scale: s, duration: d, ease: "power2.inOut" }, t);
const count = (sel, t, a, b, d, fmt) => { const o = { v: a }; const el = document.querySelector(sel);
  tl.fromTo(o, { v: a }, { v: b, duration: d, ease: "power2.out", onUpdate: () => { el.textContent = fmt(Math.round(o.v)); } }, t); };
"""


def loc(scene: str, cue: str) -> float:
    s = SC[scene]
    return round(s["cues"][cue] - s["start"], 3)


def scene_file(sid: str, css: str, body: str, js: str) -> str:
    dur = SC[sid]["dur"] if sid in SC else TOTAL
    return f"""<template>
  <style>{BASE_CSS}{css}</style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    <div id="{sid}-all" class="all clip" data-start="0" data-duration="{dur}" data-track-index="1">
{body}
    </div>
  </div>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});
{JS_HELPERS}
{js}
      window.__timelines["{sid}"] = tl;
    }})();
  </script>
</template>
"""


# ---------- scenes ----------
def claim() -> str:
    s = "claim"
    body = f"""<img src="assets/shots/shot_top.png" style="position:absolute;left:0;top:0;width:1920px" alt="Live PollenPlan demo">
<div id="cl-cap" class="card hide" style="left:120px;top:640px;width:1680px;padding:30px 44px">
  <div id="cl-line1" style="font-size:52px;font-weight:900;letter-spacing:-0.02em">Hay-fever patients miss the season start.</div>
  <div id="cl-line2" class="hide" style="font-size:36px;margin-top:10px">Does a simple alert rule beat the forecast itself? Tested on real pollen counts.</div>
  <div id="cl-chip" class="hide" style="margin-top:16px"><span class="chip info">live demo &middot; no account</span></div></div>"""
    js = f"""arrive("#cl-cap", 0.1, {{ y: 60 }});
blurIn("#cl-line1", {loc(s, 'claim')});
blurIn("#cl-line2", {loc(s, 'stake')});
stamp("#cl-chip", {loc(s, 'screen')});
"""
    return scene_file(s, "", body, js)


def product() -> str:
    s = "product"
    body = f"""<div id="pd-title" class="hide title5" style="position:absolute;left:120px;top:70px">Real counts, real misses.</div>
<div id="pd-tab" class="hide" style="position:absolute;left:120px;top:170px;width:1680px">
  <img src="assets/shots/shot_ptable.png" class="shot" style="width:1680px" alt="P2 results table"></div>
<div id="pd-on" class="hide" style="position:absolute;left:120px;top:170px;width:1680px;height:750px;overflow:hidden;border-radius:12px;background:#fff;border:1px solid {LINE}">
  <img src="assets/shots/shot_onset.png" style="width:1680px" alt="28-season onset table"></div>
<div id="pd-seal" class="hide" style="position:absolute;left:120px;top:950px"><span class="chip ok">pre-registered &middot; {ONSET_N} seasons</span></div>"""
    js = f"""blurIn("#pd-title", 0.1);
arrive("#pd-tab", {loc(s, 'demo')});
leave("#pd-tab", {loc(s, 'onset') - 0.1});
arrive("#pd-on", {loc(s, 'onset')});
stamp("#pd-seal", {loc(s, 'seal')});
"""
    return scene_file(s, "", body, js)


def run() -> str:
    s = "run"
    chips = "".join(f'<span class="chip info" style="margin-right:14px">{r}</span>' for r in ["P0", "P1", "P2", "R1", "R2", "C0"])
    body = f"""<div id="rn-term" class="card hide mono" style="left:120px;top:120px;width:1680px;padding:30px 40px;font-size:34px;line-height:48px;background:#1D1D1B;color:#E8E6E1;border-color:#1D1D1B">$ python -m pytest -q tests<br>{PYTEST_HTML}</div>
<div id="rn-rules" class="hide" style="position:absolute;left:120px;top:480px;width:1680px">
  <div class="muted" style="font-size:30px;margin-bottom:14px">Six rules, frozen before the run</div>{chips}</div>
<div id="rn-mad" class="card hide" style="left:120px;top:680px;width:1680px;padding:26px 40px;display:flex;gap:36px;align-items:center">
  <span class="chip warn">Yes (limits)</span>
  <span style="font-size:36px">Madrid olive {MADRID['olive']:.3f} &middot; grass {MADRID['grass']:.3f} &mdash; below our own 50% bar, flagged not hidden</span></div>"""
    js = f"""arrive("#rn-term", {loc(s, 'tests') - 0.2}, {{ y: 40 }});
arrive("#rn-rules", {loc(s, 'rules')});
stamp("#rn-mad", {loc(s, 'limits')});
"""
    return scene_file(s, "", body, js)


def proof() -> str:
    s = "proof"
    big = "font-size:120px;font-weight:900;letter-spacing:-0.03em;font-variant-numeric:tabular-nums;line-height:1"
    body = f"""<div id="pf-v" class="hide title5" style="position:absolute;left:120px;top:90px">The verdict.</div>
<div id="pf-stat" class="hide" style="position:absolute;left:120px;top:200px;display:flex;align-items:center;gap:44px">
  <div style="{big};width:520px">{P2:.3f}</div>
  <div style="font-size:36px;line-height:46px">API's own forecast<br><span class="muted">{EVENTS} events &middot; {DAYS:,} city-days</span></div></div>
<div id="pf-r1" class="hide" style="position:absolute;left:120px;top:470px;display:flex;align-items:center;gap:44px">
  <div style="{big};width:520px;color:{MUTED}">{R1:.3f}</div>
  <div style="font-size:36px;line-height:46px">our day rule<br><span id="pf-nobeat" class="chip bad">did not beat the API</span></div></div>
<div id="pf-head" class="hide" style="position:absolute;left:120px;top:760px;display:flex;gap:20px;align-items:center">
  <span class="chip ok">headline: measured skill only</span><span style="font-size:34px">the app is the delivery layer</span></div>"""
    js = f"""blurIn("#pf-v", {loc(s, 'verdict') - 0.2});
arrive("#pf-stat", {loc(s, 'stat') - 0.3});
arrive("#pf-r1", {loc(s, 'no beat') - 0.5});
stamp("#pf-head", {loc(s, 'headline')});
"""
    return scene_file(s, "", body, js)


def limit() -> str:
    s = "limit"
    body = f"""<div id="li-h" class="hide title5" style="position:absolute;left:120px;top:90px">What it doesn't show.</div>
<div id="li-r2" class="card hide" style="left:120px;top:230px;width:1680px;padding:26px 40px">
  <div style="font-size:38px;line-height:50px">Early alert fires ~3 days sooner &mdash; <b>by construction</b>: it reads 3 days of forecast.</div>
  <div class="muted" style="font-size:30px;margin-top:8px">Archived values may flatter it live. +2.88 days is look-ahead, not skill.</div></div>
<div id="li-th" class="card hide" style="left:120px;top:520px;width:1680px;padding:26px 40px">
  <div style="font-size:38px;line-height:50px">Thresholds: published-panel values, <b>signed 22 Nov 2026</b>.</div>
  <div class="muted" style="font-size:30px;margin-top:8px">Single-centre studies. No safe-or-unsafe level exists for every person.</div></div>
<div id="li-nc" class="hide" style="position:absolute;left:120px;top:800px"><span class="chip bad">retrospective &middot; not a medical device</span></div>"""
    js = f"""blurIn("#li-h", {loc(s, 'limit') - 0.2});
arrive("#li-r2", {loc(s, 'lookahead') - 0.3});
arrive("#li-th", {loc(s, 'signed') - 0.3});
stamp("#li-nc", {loc(s, 'disclaimer')});
"""
    return scene_file(s, "", body, js)


def close() -> str:
    s = "close"
    body = f"""<div id="ce-line" class="hide" style="position:absolute;left:160px;top:200px;width:1500px;font-size:80px;font-weight:900;letter-spacing:-0.025em;line-height:92px">
  Measured skill, open code, open data.</div>
<div id="ce-stat" class="hide" style="position:absolute;left:160px;top:470px;display:flex;gap:60px">
  <div><div style="font-size:88px;font-weight:900">{P2:.3f}</div><div class="muted" style="font-size:30px">pooled recall</div></div>
  <div><div style="font-size:88px;font-weight:900">{EVENTS}</div><div class="muted" style="font-size:30px">events</div></div>
  <div><div style="font-size:88px;font-weight:900">{DAYS:,}</div><div class="muted" style="font-size:30px">city-days</div></div></div>
<div id="ce-meta" class="hide" style="position:absolute;left:160px;top:760px">
  <div class="mono" style="font-size:38px">drahmed7887.github.io/hack-genhacks</div>
  <div class="mono" style="font-size:38px;margin-top:14px">github.com/DrAhmed7887/hack-genhacks</div>
  <div class="muted" style="font-size:30px;margin-top:14px">Try the demo now &mdash; no account. Retrospective; not for medical use.</div></div>"""
    js = f"""blurIn("#ce-line", 0.1);
arrive("#ce-stat", {loc(s, 'urls') - 2.5});
arrive("#ce-meta", {loc(s, 'urls')});
"""
    return scene_file(s, "", body, js)


# ---------- captions ----------
def caption_groups() -> list:
    groups = []
    for sc in T["scenes"]:
        cur = []
        for w in sc["words"]:
            cur.append(w)
            if len(cur) >= 6 or re.search(r"[.:;]$", w["text"]) or (w["text"].endswith(",") and len(cur) >= 2):
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
    out = []
    for g in groups:
        out.append({"text": " ".join(w["text"] for w in g), "start": g[0]["start"] - 0.05, "end": g[-1]["end"] + 0.15})
    for a, b in zip(out, out[1:]):
        a["end"] = min(a["end"], b["start"] - 0.01)
    return out


def captions() -> str:
    gs = caption_groups()
    body = "".join(f'<div id="cap-{i}" class="cg"><span>{e(g["text"])}</span></div>' for i, g in enumerate(gs))
    js = ""
    for i, g in enumerate(gs):
        js += (f'tl.fromTo("#cap-{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.08 }}, {g["start"]:.3f});'
               f'tl.to("#cap-{i}", {{ opacity: 0, duration: 0.08 }}, {g["end"] - 0.08:.3f});'
               f'tl.set("#cap-{i}", {{ opacity: 0, visibility: "hidden" }}, {g["end"]:.3f});\n')
    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; font-family: "Inter", sans-serif; }}
    .cg {{ position: absolute; left: 0; right: 0; bottom: 64px; text-align: center; opacity: 0; }}
    .cg span {{ display: inline-block; background: rgba(29,29,27,0.86); color: #fff; font-size: 40px; font-weight: 700;
      line-height: 54px; padding: 8px 22px; border-radius: 10px; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
    <div id="captions-all" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1" data-layout-allow-caption-zone>{body}</div>
  </div>
  <script>(function () {{ const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["captions"] = tl; }})();</script>
</template>
"""


# ---------- audio ----------
SFX = [  # (file, scene, cue or None, offset, volume)
    ("whoosh_a", "claim", "screen", -0.05, 0.4), ("pop", "product", "seal", 0.0, 0.45),
    ("pop", "run", "tests", 0.0, 0.45), ("pop", "run", "limits", 0.0, 0.45),
    ("pop", "proof", "stat", 0.0, 0.45), ("stamp", "proof", "headline", 0.03, 0.7),
    ("pop", "limit", "disclaimer", 0.0, 0.45), ("whoosh_b", "close", "urls", -0.1, 0.35),
]


def sh(args: list) -> None:
    subprocess.run(args, check=True)


def prep_audio() -> None:
    vdir = HERE / "assets" / "audio" / "voice"
    for sc in T["scenes"]:
        src, dst = vdir / f"{sc['id']}.mp3", vdir / f"{sc['id']}.wav"
        sh(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "48000", str(dst)])
    # music bed: -16 LUFS, 0.14 under voice, dip under the limit scene, lift at proof, fade out
    dip0, dip1 = SC["limit"]["start"], SC["close"]["start"]
    nums = SC["proof"]["start"]
    vol = (f"if(lt(t,{dip0}),if(lt(t,{nums}),0.14,0.17),if(lt(t,{dip0 + 0.8}),0.17-0.10*(t-{dip0})/0.8,"
           f"if(lt(t,{dip1}),0.07,if(lt(t,{dip1 + 0.8}),0.07+0.07*(t-{dip1})/0.8,0.14))))")
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(HERE / "assets/audio/raw/music.mp3"), "-af",
         f"loudnorm=I=-16:TP=-1.5:LRA=11,volume='{vol}':eval=frame,apad,afade=t=out:st={TOTAL - 3}:d=3,atrim=0:{TOTAL}",
         "-ar", "48000", str(HERE / "assets/audio/bed.wav")])


def media_len(path: pathlib.Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return round(float(out) - 0.005, 3)


def audio_tags() -> str:
    tags = [f'<audio id="bed" class="clip" src="assets/audio/bed.wav" data-start="0" data-duration="{media_len(HERE / "assets/audio/bed.wav")}" data-track-index="20" data-volume="1"></audio>']
    for sc in T["scenes"]:
        tags.append(f'<audio id="vo-{sc["id"]}" class="clip" src="assets/audio/voice/{sc["id"]}.wav" data-start="{sc["voice_at"]}" '
                    f'data-duration="{media_len(HERE / "assets/audio/voice" / (sc["id"] + ".wav"))}" data-track-index="21" data-volume="1"></audio>')
    for i, (f, sid, cue, off, v) in enumerate(SFX):
        t = round(SC[sid]["cues"][cue] + off, 3)
        tags.append(f'<audio id="sfx-{i}" class="clip" src="assets/audio/raw/sfx_{f}.mp3" data-start="{t}" data-duration="{media_len(HERE / "assets/audio/raw" / ("sfx_" + f + ".mp3"))}" '
                    f'data-track-index="{22 + i % 3}" data-volume="{v}"></audio>')
    return "\n      ".join(tags)


def main() -> None:
    comp = HERE / "compositions"
    comp.mkdir(exist_ok=True)
    builders = {"claim": claim, "product": product, "run": run, "proof": proof, "limit": limit, "close": close}
    hosts = []
    for k, (sid, fn) in enumerate(builders.items()):
        (comp / f"{sid}.html").write_text(fn())
        sc = SC[sid]
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{sc["start"]}" '
                     f'data-duration="{sc["dur"]}" data-track-index="{1 + k % 2}" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 2"></div>')
    (comp / "captions.html").write_text(captions())
    hosts.append(f'<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" '
                 f'data-duration="{TOTAL}" data-track-index="4" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index: 4"></div>')
    prep_audio()
    nl = "\n      "
    (HERE / "index.html").write_text(f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #F6F5F1; }}
      #root {{ width: 100%; height: 100%; position: relative; }}
      #ground {{ position: absolute; inset: 0; background: #F6F5F1; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="ground" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="0" style="z-index: 0"></div>
      {nl.join(hosts)}
      {audio_tags()}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
    print("built", len(builders), "scenes,", TOTAL, "s")


if __name__ == "__main__":
    main()
