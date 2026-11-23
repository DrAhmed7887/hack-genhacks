import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, D, cue, scene} from '../theme';
import {Mono, Paper, ramp} from '../ui';

const s = scene('s9');
const P = D.pooled;

export const S9Close: React.FC = () => {
  const f = useCurrentFrame();
  const kOpen = cue(s, 'open', 0, -0.1);
  const kEvery = cue(s, 'every', 0, -0.1);
  const COLS = 43, PITCH = 24;
  const W = COLS * PITCH;
  return (
    <Paper>
      <div style={{position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center', fontSize: 40, fontWeight: 700}}>
        3 cities · 1 season · a pre-registered test
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: P.events}, (_, i) => {
          const on = i < P.trapHits;
          return <circle key={i} cx={960 - W / 2 + Math.floor(i / 5) * PITCH + PITCH / 2} cy={250 + (i % 5) * PITCH + PITCH / 2} r={on ? 9 : 8}
            fill={on ? C.green : 'none'} stroke={on ? 'none' : C.barLight} strokeWidth={2.2} />;
        })}
      </svg>
      <div style={{position: 'absolute', left: 0, right: 0, top: 410, textAlign: 'center'}}>
        <Mono style={{fontSize: 40, fontWeight: 700, color: C.green}}>{P.trapHits} / {P.events}</Mono>
        <span style={{fontSize: 34, color: C.ink2, marginLeft: 14}}>high-pollen days flagged by yesterday's trap</span>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center', opacity: ramp(f, kOpen, kOpen + 10)}}>
        <div style={{fontSize: 40, fontWeight: 700}}>Open the PollenPlan demo · no setup</div>
        <Mono style={{display: 'block', fontSize: 64, fontWeight: 700, marginTop: 18}}>{D.demoUrl.replace('https://', '')}</Mono>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 790, textAlign: 'center', opacity: ramp(f, kEvery, kEvery + 10)}}>
        <Mono style={{fontSize: 32, color: C.ink2}}>{D.tests} tests · eval/verify_claims.py · lock {D.lock.short}</Mono>
      </div>
    </Paper>
  );
};
