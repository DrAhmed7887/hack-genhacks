import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {C, D, F, FPS} from './theme';
import shots from '../../public/v5/shots/shots.json';

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const ramp = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

export const Paper: React.FC<{children?: React.ReactNode; tone?: string}> = ({children, tone = C.paper}) => (
  <AbsoluteFill style={{background: tone, fontFamily: F.sans, color: C.ink}}>{children}</AbsoluteFill>
);

/** Scene title: top-left, always ≤ 5 words, arrives with a short rise. */
export const Title: React.FC<{text: React.ReactNode; at?: number; sub?: React.ReactNode; x?: number; y?: number}> = ({
  text, at = 0, sub, x = 120, y = 84,
}) => {
  const f = useCurrentFrame();
  const o = ramp(f, at, at + 10);
  return (
    <div style={{position: 'absolute', left: x, top: y, opacity: o, transform: `translateY(${(1 - o) * 14}px)`}}>
      <div style={{fontSize: 68, fontWeight: 800, letterSpacing: -1.5, lineHeight: 1.05}}>{text}</div>
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
