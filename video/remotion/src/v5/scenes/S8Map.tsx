import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {C, F, cue, scene} from '../theme';
import {Paper, ramp} from '../ui';
import M from '../map.json';

const s = scene('s8');
const place = (n: string) => M.places.find((p) => p.name === n)!;
const LABEL: Record<string, {text: string; dx: number; dy: number; anchor: 'start' | 'end'}> = {
  Madrid: {text: 'Madrid', dx: -18, dy: 10, anchor: 'end'},
  Basel: {text: 'Basel · Zürich', dx: 20, dy: -14, anchor: 'start'},
  Alexandria: {text: 'Alexandria', dx: -22, dy: -8, anchor: 'end'},
  Cairo: {text: 'Cairo', dx: 24, dy: 40, anchor: 'start'},
  Asyut: {text: 'Asyut', dx: 22, dy: 10, anchor: 'start'},
};
const EG = {x: (place('Cairo').x + place('Asyut').x) / 2 + 20, y: (place('Alexandria').y + place('Asyut').y) / 2};

/** Plain line map (Natural Earth 110m), the CAMS domain box, and three Egyptian cities. */
export const S8Map: React.FC = () => {
  const f = useCurrentFrame();
  const kMap = cue(s, 'map', 0, -0.3);
  const k30 = cue(s, 'thirty', 0, -0.1);
  const kSouth = cue(s, 'south', 0, -0.1);
  const kNo = cue(s, 'no', 0, -0.1);
  const kNorth = cue(s, 'north', 1, -0.3);
  const kAlex = cue(s, 'alexandria', 0, -0.1);
  const kCairo = cue(s, 'cairo', 0, -0.1);
  const kChecked = cue(s, 'checked', 0, -0.1);
  const kNeeds = cue(s, 'needs', 0, -0.1);
  const kYet = cue(s, "haven't", 0, -0.1);
  const opt = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const, easing: Easing.inOut(Easing.cubic)};
  // push in on Egypt on "North of it", ease back out a little on "needs only that trap"
  const k = interpolate(f, [kNorth, kNorth + 30, kNeeds, kNeeds + 30], [1, 2.6, 2.6, 2.1], opt);
  const tx = interpolate(f, [kNorth, kNorth + 30], [EG.x, 1260], opt);
  const ty = interpolate(f, [kNorth, kNorth + 30], [EG.y, 560], opt);
  const P = (x: number, y: number) => [(x - EG.x) * k + tx, (y - EG.y) * k + ty] as const;
  const tr = `translate(${tx - EG.x * k},${ty - EG.y * k}) scale(${k})`;
  const land = ramp(f, 0, 14);
  const box = ramp(f, kMap, kMap + 14);
  const line30 = ramp(f, k30, k30 + 18);
  const south = ramp(f, kSouth, kSouth + 14);
  const wideLabels = 1 - ramp(f, kNorth, kNorth + 12);
  const cv = M.cams;
  const mark = (name: string, at: number, kind: string) => {
    const p = place(name);
    const [x, y] = P(p.x, p.y);
    const o = ramp(f, at, at + 10);
    const col = kind === 'tested' ? C.ink : kind === 'unchecked' ? C.amber : C.ink;
    return (
      <g key={name} opacity={o}>
        {kind === 'tested' ? <circle cx={x} cy={y} r={8} fill={C.ink} /> : <circle cx={x} cy={y} r={13} fill={C.paper} stroke={col} strokeWidth={4} />}
        {kind === 'none' ? <line x1={x - 10} y1={y + 10} x2={x + 10} y2={y - 10} stroke={C.ink} strokeWidth={4} /> : null}
        {LABEL[name] ? <text x={x + LABEL[name].dx} y={y + LABEL[name].dy} textAnchor={LABEL[name].anchor} stroke={C.paper} strokeWidth={8} paintOrder="stroke" strokeLinejoin="round" fontFamily={F.sans} fontSize={30} fontWeight={700} fill={col}>{LABEL[name].text}</text> : null}
      </g>
    );
  };
  return (
    <Paper>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="mapclip"><rect x={M.view.x} y={M.view.y} width={M.view.w} height={M.view.h} /></clipPath>
          <pattern id="south" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="3" height="16" fill={C.ink} opacity={0.18} />
          </pattern>
        </defs>
        <g clipPath="url(#mapclip)">
          <g transform={tr}>
            <path d={M.path} fill={C.card} stroke={C.ink} strokeWidth={1.6} vectorEffect="non-scaling-stroke" opacity={land} />
            <rect x={cv.x} y={cv.y} width={cv.w} height={cv.h} fill={C.amber} opacity={0.1 * box} />
            <rect x={cv.x} y={cv.y} width={cv.w} height={cv.h} fill="none" stroke={C.amber} strokeWidth={3} vectorEffect="non-scaling-stroke" opacity={box} />
            <rect x={M.view.x - 2000} y={M.lat30y} width={6000} height={2000} fill="url(#south)" opacity={south} />
            <line x1={M.view.x - 2000} x2={(M.view.x - 2000) + 6000 * line30} y1={M.lat30y} y2={M.lat30y} stroke={C.ink} strokeWidth={4} vectorEffect="non-scaling-stroke" />
          </g>
        </g>
        <rect x={M.view.x} y={M.view.y} width={M.view.w} height={M.view.h} fill="none" stroke={C.rule} strokeWidth={2} />
        <g opacity={wideLabels}>
          {mark('Madrid', kMap, 'tested')}{mark('Basel', kMap + 4, 'tested')}{mark('Zürich', kMap + 4, 'tested')}
        </g>
        <text x={M.view.x + 16} y={P(0, M.lat30y)[1] - 14} stroke={C.paper} strokeWidth={8} paintOrder="stroke" strokeLinejoin="round" fontFamily={F.mono} fontSize={30} fontWeight={700} fill={C.ink} opacity={line30}>30° N</text>
        <text x={M.view.x + 16} y={P(0, M.lat30y)[1] + 44} stroke={C.paper} strokeWidth={8} paintOrder="stroke" strokeLinejoin="round" fontFamily={F.sans} fontSize={30} fontWeight={600} fill={C.ink} opacity={south}>south of the line: no pollen value</text>
        {mark('Asyut', kNo, 'none')}
        {mark('Alexandria', kAlex, 'unchecked')}
        {mark('Cairo', kCairo, 'unchecked')}
        {(() => {
          const [ax, ay] = P(place('Asyut').x, place('Asyut').y);
          const [cx, cy] = P(place('Alexandria').x, place('Alexandria').y);
          return (
            <>
              <text x={ax + 22} y={ay + 46} stroke={C.paper} strokeWidth={8} paintOrder="stroke" strokeLinejoin="round" fontFamily={F.sans} fontSize={30} fill={C.ink2} opacity={ramp(f, kNo, kNo + 10)}>no value</text>
              <text x={cx - 22} y={cy - 48} textAnchor="end" stroke={C.paper} strokeWidth={8} paintOrder="stroke" strokeLinejoin="round" fontFamily={F.sans} fontSize={30} fontWeight={600} fill={C.amber} opacity={ramp(f, kChecked, kChecked + 10)}>values, unchecked</text>
            </>
          );
        })()}
      </svg>
      {/* left column: title, legend, source */}
      <div style={{position: 'absolute', left: 120, top: 84, width: 440}}>
        <div style={{fontSize: 64, fontWeight: 800, letterSpacing: -1.5, lineHeight: 1.04}}>Where the<br />forecast stops</div>
        <div style={{marginTop: 40, fontSize: 28, lineHeight: 1.45, color: C.ink2, opacity: box}}>
          <div><span style={{display: 'inline-block', width: 26, height: 18, border: `3px solid ${C.amber}`, background: 'rgba(180,87,11,.1)', marginRight: 12}} />CAMS forecast area</div>
          <div style={{fontFamily: F.mono, fontSize: 28}}>25° W – 45° E<br />30° N – 72° N</div>
          <div style={{marginTop: 10}}><span style={{display: 'inline-block', width: 14, height: 14, borderRadius: 7, background: C.ink, marginRight: 12}} />tested: Madrid, Basel, Zürich</div>
        </div>
        <div style={{marginTop: 40, fontSize: 34, fontWeight: 700, lineHeight: 1.2, opacity: ramp(f, kNeeds, kNeeds + 10)}}>
          The rule needs one local trap.
        </div>
        <div style={{marginTop: 20, fontSize: 56, fontWeight: 800, letterSpacing: -1, lineHeight: 1.05, opacity: ramp(f, kYet, kYet + 10)}}>
          Not yet tested here.
        </div>
      </div>
      <div style={{position: 'absolute', left: 120, top: 880, width: 440, fontSize: 28, lineHeight: 1.3, color: C.ink2}}>
        Box: CAMS dataset page. Values: our API query, 23 Nov 2026.
      </div>
    </Paper>
  );
};
