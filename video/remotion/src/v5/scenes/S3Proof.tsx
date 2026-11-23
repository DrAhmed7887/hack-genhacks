import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {C, D, F, FPS, cue, scene} from '../theme';
import {Count, Mono, Paper, Title, ramp} from '../ui';

const s = scene('s3');
const P = D.pooled;
const H1 = D.hypotheses.H1;

const COLS = 43;
const ROWS = 5;
const GX = 730;
const GW = 1070;
const PITCH = GW / COLS;

/** 215 high-pollen days as dots, column by column; the first `filled` are solid. */
const DotStrip: React.FC<{y: number; filled: number; color: string; appear: number}> = ({y, filled, color, appear}) => {
  const dots = [];
  for (let i = 0; i < P.events; i++) {
    const col = Math.floor(i / ROWS);
    const row = i % ROWS;
    const on = i < filled;
    dots.push(
      <circle key={i} cx={GX + col * PITCH + PITCH / 2} cy={y + row * PITCH + PITCH / 2} r={on ? 9.5 : 8.5}
        fill={on ? color : 'none'} stroke={on ? color : C.barLight} strokeWidth={on ? 0 : 2.2}
        opacity={appear >= col / COLS ? 1 : 0} />,
    );
  }
  return <>{dots}</>;
};

export const S3Proof: React.FC = () => {
  const f = useCurrentFrame();
  const t215a = cue(s, 'two');
  const t215b = cue(s, 'days');
  const trapA = cue(s, 'one');
  const trapB = cue(s, 'sixty-four', 0, 0.55);
  const camsA = cue(s, 'flagged', 1);
  const camsB = cue(s, 'seventy', 0, 0.45);
  const ciA = cue(s, 'seventy', 0, 1.1);

  const appear = ramp(f, t215a, t215b);
  const trapFill = Math.round(interpolate(f, [trapA, trapB], [0, P.trapHits], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)}));
  const camsFill = Math.round(interpolate(f, [camsA, camsB], [0, P.camsHits], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)}));
  const trapLit = ramp(f, trapA - 8, trapA + 4);
  const camsLit = ramp(f, camsA - 20, camsA - 6);

  const lo = -0.1, hi = 0.5;
  const X = (v: number) => GX + ((v - lo) / (hi - lo)) * GW;
  const ci = ramp(f, ciA, ciA + 22);
  const ciX0 = X(H1.ci[0]);
  const ciX1 = X(H1.ci[1]);

  const row = (y: number, label: string, color: string, lit: number, count: React.ReactNode) => (
    <div style={{position: 'absolute', left: 120, top: y, width: 590, opacity: 0.35 + 0.65 * lit}}>
      <div style={{fontSize: 34, fontWeight: 700, color}}>{label}</div>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 14, marginTop: 2}}>
        <Mono style={{fontSize: 128, fontWeight: 700, color, letterSpacing: -4, lineHeight: 1}}>{count}</Mono>
        <Mono style={{fontSize: 56, fontWeight: 500, color: C.ink2}}>/ {P.events}</Mono>
      </div>
    </div>
  );

  return (
    <Paper>
      <Title at={0} text={<><Mono style={{fontWeight: 700}}><Count to={P.events} a={t215a} b={t215b} /></Mono> high-pollen days</>}
        sub="Madrid · Basel · Zürich · the 2026 season, scored once" />
      {row(272, "Yesterday's trap", C.green, trapLit, <Count to={P.trapHits} a={trapA} b={trapB} />)}
      {row(508, 'CAMS forecast, same day', C.amber, camsLit, <Count to={P.camsHits} a={camsA} b={camsB} />)}
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <DotStrip y={300} filled={trapFill} color={C.green} appear={appear} />
        <DotStrip y={536} filled={camsFill} color={C.amber} appear={appear} />
        {/* CSI difference with its 95% CI, drawn on a number line */}
        <g opacity={ci}>
          <line x1={GX} x2={GX + GW} y1={850} y2={850} stroke={C.rule} strokeWidth={2} />
          <line x1={X(0)} x2={X(0)} y1={812} y2={888} stroke={C.ink2} strokeWidth={2} strokeDasharray="6 6" />
          <rect x={ciX0} y={840} width={(ciX1 - ciX0) * ci} height={20} rx={10} fill={C.ink} />
          <circle cx={X(H1.diff)} cy={850} r={15 * ci} fill={C.paper} stroke={C.ink} strokeWidth={5} />
          <text x={X(0)} y={922} fontFamily={F.mono} fontSize={28} fill={C.ink2} textAnchor="middle">0</text>
          <text x={ciX0} y={922} fontFamily={F.mono} fontSize={28} fill={C.ink2} textAnchor="middle">{H1.ci[0].toFixed(3)}</text>
          <text x={ciX1} y={922} fontFamily={F.mono} fontSize={28} fill={C.ink2} textAnchor="middle">{H1.ci[1].toFixed(3)}</text>
          <text x={X(0) - 18} y={826} fontFamily={F.sans} fontSize={28} fill={C.ink2} textAnchor="end">no difference</text>
        </g>
      </svg>
      <div style={{position: 'absolute', left: 120, top: 778, opacity: ci}}>
        <div style={{fontSize: 30, fontWeight: 700}}>Trap minus forecast, CSI</div>
        <Mono style={{fontSize: 76, fontWeight: 700, letterSpacing: -2}}>+{H1.diff.toFixed(3)}</Mono>
        <div style={{fontSize: 28, color: C.ink2, marginTop: 2}}>95% CI {H1.ci[0].toFixed(3)} to {H1.ci[1].toFixed(3)}</div>
      </div>
    </Paper>
  );
};

export const S3_FRAMES = s.frames;
export const S3_DEBUG = {fps: FPS};
