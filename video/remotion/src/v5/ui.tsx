import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, staticFile, useCurrentFrame} from 'remotion';
import {C, D, F, FPS} from './theme';
import shots from '../../public/v5/shots/shots.json';

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const ramp = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

/** Seeded pollen drifting slowly across the paper: deterministic per frame, never over text-critical areas by design (low opacity). */
const rnd = (i: number, k: number) => {
  const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return x - Math.floor(x);
};
export const PollenDrift: React.FC<{n?: number; seed?: number; opacity?: number}> = ({n = 34, seed = 1, opacity = 1}) => {
  const f = useCurrentFrame();
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity, pointerEvents: 'none'}}>
      {Array.from({length: n}, (_, i) => {
        const r = 2.5 + rnd(i, seed) * 6.5;
        const speed = 0.25 + rnd(i, seed + 1) * 0.55;
        const x = ((rnd(i, seed + 2) * 2100 + f * speed) % 2100) - 90;
        const y = rnd(i, seed + 3) * 1080 + Math.sin(f / (40 + rnd(i, seed + 4) * 50) + i) * 22 - f * 0.08 * speed;
        const yy = ((y % 1080) + 1080) % 1080;
        const a = 0.10 + rnd(i, seed + 5) * 0.22;
        return (
          <g key={i} opacity={a}>
            <circle cx={x} cy={yy} r={r} fill="#B9A97A" />
            <circle cx={x - r * 0.3} cy={yy - r * 0.3} r={r * 0.35} fill="#E4D9B6" />
          </g>
        );
      })}
    </svg>
  );
};

export const SceneSeed = React.createContext(1);

/** Paper ground with drifting pollen and a slow camera drift (scale 1 -> 1+drift over the scene). */
export const Paper: React.FC<{children?: React.ReactNode; tone?: string; drift?: number; pollen?: boolean}> = ({
  children, tone = C.paper, drift = 0.025, pollen = true,
}) => {
  const f = useCurrentFrame();
  const seed = React.useContext(SceneSeed);
  const k = 1 + drift * Math.min(1, f / 600);
  return (
    <AbsoluteFill style={{background: tone, fontFamily: F.sans, color: C.ink}}>
      {pollen ? <PollenDrift seed={seed * 7} /> : null}
      <AbsoluteFill style={{transform: `scale(${k})`, transformOrigin: '50% 45%'}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Root-level tape wipe at every scene change: a paper sheet led by a strip of trap tape crosses the frame and covers the cut. */
export const TapeWipes: React.FC = () => {
  const f = useCurrentFrame();
  const H = 9; // frames in, frames out
  const b = D.scenes.slice(1).map((s) => s.from).find((x) => f >= x - H && f < x + H);
  if (b === undefined) return null;
  const t = (f - (b - H)) / (2 * H); // 0..1
  const e = Easing.inOut(Easing.cubic)(t);
  const x = 1920 - e * (1920 + 2200); // leading edge from right to far left
  const W = 2000;
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top: 0, bottom: 0, left: x, width: W, background: C.paper2}}>
        <div style={{position: 'absolute', top: 0, bottom: 0, left: 0, width: 120, background: '#D2CBB9', borderLeft: `3px solid ${C.ink2}`, borderRight: `3px solid ${C.ink2}`}}>
          {Array.from({length: 7}, (_, i) => (
            <div key={i} style={{position: 'absolute', left: 0, right: 0, top: 60 + i * 160, height: 4, background: C.ink, opacity: 0.8}} />
          ))}
        </div>
      </div>
    </div>
  );
};

/** Scene title: top-left, always ≤ 5 words, arrives with a short rise. */
export const Title: React.FC<{text: React.ReactNode; at?: number; sub?: React.ReactNode; x?: number; y?: number}> = ({
  text, at = 0, sub, x = 120, y = 84,
}) => {
  const f = useCurrentFrame();
  const o = ramp(f, at, at + 10);
  return (
    <div style={{position: 'absolute', left: x, top: y, opacity: o, transform: `translateY(${(1 - o) * 14}px)`}}>
      <div style={{fontSize: 68, fontWeight: 800, letterSpacing: -1.5, lineHeight: 1.05}}>
        {typeof text === 'string'
          ? text.split(' ').map((w, i) => {
              const wo = ramp(f, at + i * 3, at + i * 3 + 10);
              return <span key={i} style={{display: 'inline-block', marginRight: '0.26em', opacity: wo, transform: `translateY(${(1 - wo) * 26}px)`}}>{w}</span>;
            })
          : text}
      </div>
      {sub ? <div style={{fontSize: 32, fontWeight: 500, color: C.ink2, marginTop: 14}}>{sub}</div> : null}
    </div>
  );
};

export const Mono: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <span style={{fontFamily: F.mono, fontVariantNumeric: 'tabular-nums', ...style}}>{children}</span>
);

/** A real capture of demo/index.html, placed by its css box and scaled so 1 css px = `zoom` video px. */
type ShotName = keyof typeof shots;
export const Shot: React.FC<{
  name: ShotName; x: number; y: number; zoom: number; opacity?: number; shadow?: boolean;
  crop?: {x: number; y: number; w: number; h: number}; // in css px of the element
}> = ({name, x, y, zoom, opacity = 1, shadow = true, crop}) => {
  const m = shots[name];
  const c = crop ?? {x: 0, y: 0, w: m.cssW, h: m.cssH};
  return (
    <div style={{
      position: 'absolute', left: x, top: y, width: c.w * zoom, height: c.h * zoom, overflow: 'hidden', opacity,
      borderRadius: 14, background: C.card,
      boxShadow: shadow ? '0 1px 0 rgba(21,32,27,.06), 0 18px 50px rgba(21,32,27,.10)' : undefined,
    }}>
      <Img src={staticFile(`v5/shots/${name}.png`)} style={{
        position: 'absolute', left: -c.x * zoom, top: -c.y * zoom, width: m.cssW * zoom, height: m.cssH * zoom,
      }} />
    </div>
  );
};

/** Burned captions from the approved script text, timed by the voice alignment. Root level. */
export const Captions: React.FC = () => {
  const f = useCurrentFrame();
  let text = '';
  for (const s of D.scenes) {
    if (f < s.from || f >= s.from + s.frames) continue;
    const t = (f - s.from) / FPS;
    const c = s.captions.find((x, i) => t >= x.start - 0.05 && (t < (s.captions[i + 1]?.start ?? x.end + 0.6) - 0.05));
    text = c && t < c.end + 0.6 ? c.text : '';
  }
  if (!text) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 34, display: 'flex', justifyContent: 'center'}}>
      <div style={{
        fontFamily: F.sans, fontSize: 36, fontWeight: 600, color: C.ink, background: 'rgba(255,255,255,.92)',
        padding: '10px 26px', borderRadius: 12, border: `1px solid ${C.rule}`, maxWidth: 1500, textAlign: 'center',
      }}>{text}</div>
    </div>
  );
};

export const Progress: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', left: 0, bottom: 0, height: 4, width: `${(f / D.totalFrames) * 100}%`, background: C.ink}} />;
};

/** A count-up number that lands exactly on `to` at frame b. */
export const Count: React.FC<{to: number; a: number; b: number; decimals?: number}> = ({to, a, b, decimals = 0}) => {
  const f = useCurrentFrame();
  const v = interpolate(f, [a, b], [0, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return <>{f >= b ? to.toFixed(decimals) : v.toFixed(decimals)}</>;
};

/** AI b-roll (Gemini Omni via Flow): full-frame, muted, always labelled as AI-generated. */
export const Broll: React.FC<{src: string; opacity?: number; startFrom?: number; scrim?: 'left' | 'center' | 'none'}> = ({
  src, opacity = 1, startFrom = 0, scrim = 'none',
}) => (
  <AbsoluteFill style={{opacity}}>
    <OffthreadVideo src={staticFile(src)} muted startFrom={startFrom} style={{width: 1920, height: 1080, objectFit: 'cover'}} />
    {scrim === 'left' ? <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(246,244,238,.94) 0%, rgba(246,244,238,.80) 42%, rgba(246,244,238,0) 72%)'}} /> : null}
    {scrim === 'center' ? <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, rgba(246,244,238,.86) 0%, rgba(246,244,238,.55) 55%, rgba(246,244,238,.2) 100%)'}} /> : null}
    <div style={{position: 'absolute', right: 36, top: 30, fontFamily: F.sans, fontSize: 28, fontWeight: 600, color: C.ink2,
      background: 'rgba(246,244,238,.88)', padding: '6px 16px', borderRadius: 10}}>AI-generated footage · Gemini Omni (Flow)</div>
  </AbsoluteFill>
);
