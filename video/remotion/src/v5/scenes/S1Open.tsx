import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, D, F, cue, scene} from '../theme';
import {Broll, Paper, ramp} from '../ui';

const s = scene('s1');
const days = D.madridGrass.days as [string, number, number, number, number, number][];
const T = D.madridGrass.threshold;

/** Cold open: the title is readable on frame 0; the real 2026 Madrid grass counts draw under it. */
export const S1Open: React.FC = () => {
  const f = useCurrentFrame();
  const X0 = 120, X1 = 1800, BASE = 900, H = 330;
  const vmax = Math.max(...days.map((d) => d[1]));
  const bw = (X1 - X0) / days.length;
  const Y = (v: number) => BASE - (v / vmax) * H;
  const clipOut = cue(s, 'is', 0, 0.2);             // the meadow gives way to the real counts on "Is today..."
  const drawA = clipOut + 6, drawB = cue(s, 'have', 0, 0.2);
  const shown = ramp(f, drawA, drawB) * days.length;
  const lineO = ramp(f, cue(s, 'high-pollen', 0, -0.2), cue(s, 'high-pollen', 0, 0.3));
  return (
    <Paper>
      <Broll src="v5/flow/meadow.mp4" scrim="left" opacity={1 - ramp(f, clipOut - 6, clipOut + 12)} />
      <div style={{position: 'absolute', left: 120, top: 96}}>
        <div style={{fontSize: 30, fontWeight: 700, letterSpacing: 2.5, color: C.green, textTransform: 'uppercase'}}>PollenPlan</div>
        <div style={{fontSize: 128, fontWeight: 800, letterSpacing: -4, lineHeight: 0.98, marginTop: 14}}>
          Read the trap,<br />not the forecast.
        </div>
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        {days.map((d, i) => {
          const p = Math.min(1, Math.max(0, shown - i));
          if (p <= 0) return null;
          const h = (BASE - Y(d[1])) * p;
          return <rect key={i} x={X0 + i * bw + 2} y={BASE - h} width={bw - 4} height={h} rx={2}
            fill={d[1] >= T ? C.bar : C.barLight} />;
        })}
        <g opacity={lineO}>
          <line x1={X0} x2={X1} y1={Y(T)} y2={Y(T)} stroke={C.ink} strokeWidth={2.5} strokeDasharray="10 8" />
          <text x={X0} y={Y(T) - 14} fontFamily={F.sans} fontSize={28} fill={C.ink2}>alert line {T} grains/m³</text>
        </g>
        <text x={X0} y={BASE + 44} fontFamily={F.sans} fontSize={28} fill={C.ink2} opacity={ramp(f, drawA, drawA + 12)}>Madrid · grass pollen · each bar is one day of 2026, read from the trap</text>
      </svg>
    </Paper>
  );
};
