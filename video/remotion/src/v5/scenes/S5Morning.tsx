import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {C, D, F, cue, scene} from '../theme';
import {Mono, Paper, Shot, ramp} from '../ui';
import shots from '../../../public/v5/shots/shots.json';

const s = scene('s5');
const M = D.featured;
const ROW = shots.morning_cards; // 1048 x 167 css: three cards, 340 wide, 14 gap
const CARD_W = 340;
const GAP = (ROW.cssW - 3 * CARD_W) / 2;
const centre = (i: number) => CARD_W / 2 + i * (CARD_W + GAP);

const OV = {zoom: 1.7, y: 330};
const FOCUS = {zoom: 2.45, y: 300};

export const S5Morning: React.FC = () => {
  const f = useCurrentFrame();
  const k1 = cue(s, "yesterday's", 0, -0.35);
  const k2 = cue(s, 'forecast', 0, -0.2);
  const k3 = cue(s, 'trap', 0, -0.2);
  const kBack = cue(s, 'high', 0, -0.25);

  // camera: overview -> card 1 -> card 2 -> card 3 -> overview with the number line
  const keys = [0, k1, k1 + 14, k2, k2 + 14, k3, k3 + 14, kBack, kBack + 16];
  const ovX = 960 - (ROW.cssW / 2) * OV.zoom;
  const fx = (i: number) => 960 - centre(i) * FOCUS.zoom;
  const xs = [ovX, ovX, fx(0), fx(0), fx(1), fx(1), fx(2), fx(2), ovX];
  const zs = [OV.zoom, OV.zoom, FOCUS.zoom, FOCUS.zoom, FOCUS.zoom, FOCUS.zoom, FOCUS.zoom, FOCUS.zoom, OV.zoom];
  const ys = [OV.y, OV.y, FOCUS.y, FOCUS.y, FOCUS.y, FOCUS.y, FOCUS.y, FOCUS.y, OV.y - 40];
  const opt = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const, easing: Easing.inOut(Easing.cubic)};
  const x = interpolate(f, keys, xs, opt);
  const z = interpolate(f, keys, zs, opt);
  const y = interpolate(f, keys, ys, opt);

  // which card is active (for the dim veil); -1 = none
  const active = f < k1 ? -1 : f < k2 ? 0 : f < k3 ? 1 : f < kBack ? 2 : -1;
  const headO = 1 - ramp(f, k1 - 6, k1 + 8);
  const line = ramp(f, kBack + 8, kBack + 26);

  const lineX0 = 230, lineX1 = 1690, vmax = 120;
  const LX = (v: number) => lineX0 + (v / vmax) * (lineX1 - lineX0);
  const mark = (v: number, color: string, label: string, up: boolean) => (
    <g>
      <circle cx={LX(v)} cy={800} r={13} fill={color} />
      <text x={LX(v)} y={up ? 760 : 862} fontFamily={F.mono} fontSize={30} fontWeight={700} fill={color} textAnchor="middle">{label}</text>
    </g>
  );

  return (
    <Paper>
      <div style={{opacity: headO}}>
        <Shot name="morning_head" x={960 - (shots.morning_head.cssW / 2) * 1.7} y={170} zoom={1.7} shadow={false} />
      </div>
      <Shot name="morning_cards" x={x} y={y} zoom={z} shadow={false} />
      {[0, 1, 2].map((i) => (
        <div key={i} style={{
          position: 'absolute', left: x + (centre(i) - CARD_W / 2) * z - 4, top: y - 4, width: CARD_W * z + 8, height: ROW.cssH * z + 8,
          background: C.paper, opacity: active >= 0 && active !== i ? 0.68 : 0, transition: 'none',
        }} />
      ))}
      <div style={{position: 'absolute', left: 120, top: 92, opacity: 1 - headO - line, fontSize: 36, fontWeight: 600, color: C.ink2}}>
        One morning · Madrid · grass · 5 May 2026
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 790, display: 'flex', justifyContent: 'center', gap: 64, opacity: 1 - line}}>
        {[
          {at: k1, label: "yesterday's trap", v: String(M.yesterday), c: C.green},
          {at: k2, label: 'forecast', v: String(M.cams_today), c: C.amber},
          {at: k3, label: 'measured', v: String(M.observed_today), c: C.ink},
        ].map((st, i) => (
          <div key={i} style={{opacity: ramp(f, st.at + 10, st.at + 22), display: 'flex', alignItems: 'baseline', gap: 14}}>
            <span style={{fontSize: 30, color: C.ink2}}>{st.label}</span>
            <Mono style={{fontSize: 46, fontWeight: 700, color: st.c}}>{st.v}</Mono>
          </div>
        ))}
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity: line}}>
        <line x1={lineX0} x2={lineX1} y1={800} y2={800} stroke={C.rule} strokeWidth={4} />
        <line x1={LX(M.threshold)} x2={LX(M.threshold)} y1={735} y2={865} stroke={C.ink} strokeWidth={3} strokeDasharray="8 7" />
        <text x={LX(M.threshold) - 16} y={730} fontFamily={F.sans} fontSize={28} fill={C.ink2} textAnchor="end">alert line {M.threshold}</text>
        {mark(M.cams_today, C.amber, `forecast ${M.cams_today}`, false)}
        {mark(M.observed_today, C.ink, `measured ${M.observed_today}`, true)}
        {mark(M.yesterday, C.green, `yesterday ${M.yesterday}`, false)}
        <text x={lineX1} y={920} fontFamily={F.sans} fontSize={28} fill={C.ink2} textAnchor="end">grass pollen, grains/m³ · Madrid, 5 May 2026</text>
      </svg>
      <div style={{position: 'absolute', left: 120, top: 120, opacity: line}}>
        <div style={{fontSize: 64, fontWeight: 800, letterSpacing: -1.5}}>A high day, caught</div>
        <Mono style={{fontSize: 30, color: C.ink2}}>the forecast said no; yesterday's trap said yes</Mono>
      </div>
    </Paper>
  );
};
