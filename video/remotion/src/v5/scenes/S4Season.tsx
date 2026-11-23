import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, D, F, cue, scene} from '../theme';
import {Mono, Paper, Shot, Title, ramp} from '../ui';
import shots from '../../../public/v5/shots/shots.json';

const s = scene('s4');
const P = D.pooled;
const R = shots.season_card.rects;
const CROP = {x: 24, y: 58, w: 1000, h: 397};
const Z = 1.88;
const SX = 20, SY = 168;
const rowBox = (labelY: number) => ({y: SY + (labelY - 9 - CROP.y) * Z, h: 36 * Z});

/** Missed high days drawn as hollow boxes, one per day, same size for both methods. */
const Boxes: React.FC<{n: number; x: number; y: number; at: number}> = ({n, x, y, at}) => {
  const f = useCurrentFrame();
  const shown = Math.round(ramp(f, at, at + 14) * n);
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
      {Array.from({length: shown}, (_, i) => (
        <rect key={i} x={x + Math.floor(i / 5) * 27} y={y + (i % 5) * 27} width={20} height={20} rx={3}
          fill="none" stroke={C.red} strokeWidth={2.4} />
      ))}
    </svg>
  );
};

export const S4Season: React.FC = () => {
  const f = useCurrentFrame();
  const kF = cue(s, 'forecast', 0, -0.1);
  const kCut = cue(s, 'trap', 0, -0.35);
  const kT = cue(s, 'fifty-one', 0, -0.2);
  const kWon = cue(s, 'won', 0, -0.1);
  if (f < kCut) {
    const fb = rowBox(R.Forecast.y);
    const fo = ramp(f, kF, kF + 8);
    return (
      <Paper>
        <Title text="Day by day" />
        <Shot name="season_card" x={SX} y={SY} zoom={Z} crop={CROP} />
        <div style={{position: 'absolute', left: SX + 10, top: fb.y, width: CROP.w * Z - 20, height: fb.h, border: `4px solid ${C.amber}`,
          borderRadius: 12, opacity: fo}} />
        <div style={{position: 'absolute', right: 70, top: 96, opacity: fo, fontSize: 40, fontWeight: 700, color: C.amber}}>
          forecast: <Mono>{P.camsMiss}</Mono> high days missed
        </div>
      </Paper>
    );
  }
  const cells = D.cells;
  return (
    <Paper>
      <Title at={0} text="Missed high days" />
      <div style={{position: 'absolute', left: 120, top: 220, fontSize: 34, fontWeight: 700, color: C.amber}}>
        CAMS forecast · <Mono>{P.camsMiss}</Mono> missed
      </div>
      <Boxes n={P.camsMiss} x={120} y={280} at={kCut - 1} />
      <div style={{position: 'absolute', left: 120, top: 470, fontSize: 34, fontWeight: 700, color: C.green, opacity: ramp(f, kT - 6, kT + 4)}}>
        Yesterday's trap · <Mono>{P.trapMiss}</Mono> missed
      </div>
      <Boxes n={P.trapMiss} x={120} y={530} at={kT} />
      <div style={{position: 'absolute', left: 120, top: 700, fontSize: 28, color: C.ink2, width: 760, opacity: ramp(f, kT, kT + 10)}}>
        of {P.events} high-pollen days · one box per missed day, same size for both
      </div>
      {cells.map((c, i) => {
        const at = kWon + i * 12;
        const o = ramp(f, at - 4, at + 6);
        const x = 1010 + (i % 3) * 272;
        const y = 220 + Math.floor(i / 3) * 250;
        return (
          <div key={c.key} style={{position: 'absolute', left: x, top: y, width: 252, height: 226, background: C.card, border: `1px solid ${C.rule}`,
            borderRadius: 16, padding: '18px 20px', boxSizing: 'border-box', opacity: 0.35 + 0.65 * o}}>
            <div style={{fontSize: 28, fontWeight: 700}}>{c.city}</div>
            <div style={{fontSize: 28, color: C.ink2}}>{c.species.toLowerCase()}</div>
            <div style={{marginTop: 12}}><Mono style={{fontSize: 30, fontWeight: 700, color: C.green}}>trap {c.trap}/{c.n}</Mono></div>
            <div><Mono style={{fontSize: 30, fontWeight: 700, color: C.amber}}>fcst {c.cams}/{c.n}</Mono></div>
            <svg width={56} height={56} style={{position: 'absolute', right: 14, top: 14, opacity: o}}>
              <path d="M10 30 L23 43 L46 14" fill="none" stroke={C.ink} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round"
                strokeDasharray={60} strokeDashoffset={60 * (1 - o)} />
            </svg>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 1010, top: 730, opacity: ramp(f, kWon + 5 * 12 + 6, kWon + 5 * 12 + 16)}}>
        <Mono style={{fontSize: 56, fontWeight: 700}}>{D.cellsWon} / {cells.length}</Mono>
        <span style={{fontSize: 30, color: C.ink2, marginLeft: 16}}>cells where the trap had the higher CSI</span>
      </div>
    </Paper>
  );
};
