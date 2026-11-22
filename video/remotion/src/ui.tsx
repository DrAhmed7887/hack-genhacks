import React from 'react';
import {Easing, Img, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';
import timeline from './timeline.json';
import boxes from '../public/shots/boxes.json';
import {C, FPS, SANS} from './theme';

export const OffsetCtx = React.createContext(0); // seconds a scene starts before its narration slot (cross-fade)
export const useSec = () => useCurrentFrame() / FPS - React.useContext(OffsetCtx);
export const ease = (t: number, a: number, b: number, from = 0, to = 1, easing = Easing.out(Easing.cubic)) =>
  interpolate(t, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing});
export const fadeIn = (t: number, at: number, d = 0.4) => ease(t, at, at + d);
export const window_ = (t: number, a: number, b: number, d = 0.3) => Math.min(ease(t, a, a + d), 1 - ease(t, b - d, b));
export const appear = (t: number, at: number, d = 0.5, dy = 24): React.CSSProperties => ({
  opacity: ease(t, at, at + d), transform: `translateY(${ease(t, at, at + d, dy, 0)}px)`,
});
export const pop = (t: number, at: number) =>
  spring({frame: Math.round((t - at) * FPS), fps: FPS, config: {damping: 14, stiffness: 170, mass: 0.8}});
export const countTo = (t: number, a: number, b: number, to: number) => ease(t, a, b, 0, to, Easing.out(Easing.quad));

// Scene-local time (s) at which a narrated word starts: the n-th word that begins with `prefix`.
export const wordAt = (tl: any, scene: string, prefix: string, n = 0): number => {
  const s = tl.scenes.find((x: any) => x.id === scene)!;
  const hits = s.words.filter((w: any) => (w[0] as string).toLowerCase().replace(/[^a-z0-9≠-]/g, '').startsWith(prefix.toLowerCase()));
  if (!hits[n]) throw new Error(`word "${prefix}" #${n} not in ${scene}`);
  return hits[n][1] as number;
};
export const W = (scene: string, prefix: string, n = 0) => wordAt(timeline, scene, prefix, n);
// Size of the frame a Shot fills (the teaser's square sits inside a wide frame, so it is not always the video size).
export const FrameCtx = React.createContext({w: 1920, h: 1080});

type Rect = {x: number; y: number; w: number; h: number};
export const box = (shot: string, key: string): Rect => (boxes as any)[shot].targets[key];
export const shotSize = (shot: string) => ({w: (boxes as any)[shot].w as number, h: (boxes as any)[shot].h as number});

// A camera over a real full-page screenshot: keys are [t, centre x, centre y, zoom] in page pixels.
export type Key = [number, number, number, number];
const camAt = (t: number, keys: Key[]) => {
  let [, x, y, z] = keys[0];
  for (let i = 1; i < keys.length; i++) {
    const [ta, xa, ya, za] = keys[i - 1];
    const [tb, xb, yb, zb] = keys[i];
    if (t >= ta) {
      const e = Easing.inOut(Easing.cubic);
      x = ease(t, ta, tb, xa, xb, e); y = ease(t, ta, tb, ya, yb, e); z = ease(t, ta, tb, za, zb, e);
    }
  }
  return {x, y, z};
};
export const ZoomCtx = React.createContext(1);
// layers: [image, from (s)]: later layers cross-fade in over earlier ones (same page coordinates).
export const Shot: React.FC<{shot: string; layers?: [string, number][]; keys: Key[]; t: number; children?: React.ReactNode}> = ({shot, layers, keys, t, children}) => {
  const {x, y, z} = camAt(t, keys);
  const {w, h} = shotSize(shot);
  const fr = React.useContext(FrameCtx);
  const ls = layers ?? [[shot, 0]];
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: C.bg}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h, transformOrigin: '0 0',
        transform: `translate(${fr.w / 2 - x * z}px, ${fr.h / 2 - y * z}px) scale(${z})`}}>
        {ls.map(([img, from], i) => (
          <Img key={i} src={staticFile(`shots/${img}.png`)} style={{position: 'absolute', left: 0, top: 0, opacity: i === 0 ? 1 : fadeIn(t, from, 0.25)}} />
        ))}
        <ZoomCtx.Provider value={z}>{children}</ZoomCtx.Provider>
      </div>
    </div>
  );
};

// Highlight inside a Shot (page coordinates): a ring plus a soft dimming of everything else.
export const Hi: React.FC<{r: Rect; t: number; at: number; until?: number; pad?: number; color?: string; dim?: boolean}> = ({r, t, at, until = 999, pad = 10, color = C.accent, dim = true}) => {
  const z = React.useContext(ZoomCtx);
  const o = window_(t, at, until);
  if (o <= 0) return null;
  return (
    <div style={{position: 'absolute', left: r.x - pad, top: r.y - pad, width: r.w + 2 * pad, height: r.h + 2 * pad, borderRadius: 10,
      border: `${4 / z}px solid ${color}`, opacity: o, boxShadow: dim ? `0 0 0 4000px rgba(20,32,43,${0.28 * o})` : undefined, pointerEvents: 'none'}} />
  );
};

// Pointer in page coordinates (keys: [t, x, y]); counter-scaled so it keeps its size when the camera zooms.
export const Cursor: React.FC<{t: number; keys: [number, number, number][]; clicks: number[]}> = ({t, keys, clicks}) => {
  const z = React.useContext(ZoomCtx);
  let x = keys[0][1], y = keys[0][2];
  for (let i = 1; i < keys.length; i++) {
    const [ta, xa, ya] = keys[i - 1];
    const [tb, xb, yb] = keys[i];
    if (t >= ta) { x = ease(t, ta, tb, xa, xb, Easing.inOut(Easing.cubic)); y = ease(t, ta, tb, ya, yb, Easing.inOut(Easing.cubic)); }
  }
  const press = clicks.reduce((m, c) => Math.max(m, t > c && t < c + 0.25 ? 1 - Math.abs(t - c - 0.12) / 0.13 : 0), 0);
  const ring = clicks.map((c) => (t > c && t < c + 0.6 ? (t - c) / 0.6 : -1)).find((v) => v >= 0);
  const vis = ease(t, keys[0][0] - 0.3, keys[0][0]);
  return (
    <div style={{position: 'absolute', left: x, top: y, opacity: vis, zIndex: 50, transform: `scale(${1 / z})`, transformOrigin: '0 0'}}>
      {ring !== undefined && <div style={{position: 'absolute', left: -30 * (0.4 + ring), top: -30 * (0.4 + ring), width: 60 * (0.4 + ring),
        height: 60 * (0.4 + ring), borderRadius: '50%', border: `4px solid rgba(15,118,110,${1 - ring})`}} />}
      <svg width="46" height="46" viewBox="0 0 24 24" style={{transform: `scale(${1 - press * 0.18})`, filter: 'drop-shadow(0 3px 4px rgba(0,0,0,0.35))'}}>
        <path d="M5 3l14 8-6.5 1.5L10 19z" fill="#14202B" stroke="#fff" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

// Screen-space label (not zoomed): a pill in the top-left corner, or anywhere via style.
export const Tag: React.FC<{t: number; at: number; until?: number; children: React.ReactNode; style?: React.CSSProperties; tone?: 'accent' | 'warn' | 'ink'}> = ({t, at, until = 999, children, style, tone = 'accent'}) => {
  const bg = {accent: C.accent, warn: C.warn, ink: C.ink}[tone];
  return (
    <div style={{position: 'absolute', left: 64, top: 56, padding: '14px 26px', borderRadius: 14, background: bg, color: '#fff', fontFamily: SANS,
      fontSize: 34, fontWeight: 700, opacity: window_(t, at, until), transform: `translateY(${ease(t, at, at + 0.4, -16, 0)}px)`,
      boxShadow: '0 10px 30px rgba(20,32,43,0.25)', ...style}}>{children}</div>
  );
};
