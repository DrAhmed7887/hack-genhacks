import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {C, D, F, cue, scene} from '../theme';
import {Mono, Paper, Title, ramp} from '../ui';

const s = scene('s2');
export const TRAP_FRAMES = 300; // Blender sequence length (video/v5/blender/trap_scene.py)
// where the unrolled tape sits in the last 3D frame (measured on the rendered frame 300)
export const STRIP = {y0: 396, y1: 696};
const LINE = {y0: 742, y1: 822}; // the strip as the timeline, after it settles
const pad = (n: number) => String(n).padStart(4, '0');
const hhmm = (iso: string) => iso.slice(11, 16);
const day = (iso: string) => {
  const m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][Number(iso.slice(5, 7)) - 1];
  return `${Number(iso.slice(8, 10))} ${m} ${iso.slice(0, 4)}`;
};

const Card: React.FC<{x: number; at: number; step: string; children: React.ReactNode; accent?: string}> = ({x, at, step, children, accent = C.ink}) => {
  const f = useCurrentFrame();
  const o = ramp(f, at, at + 9);
  return (
    <>
      <div style={{position: 'absolute', left: x, top: 330, width: 460, opacity: o, transform: `translateY(${(1 - o) * 18}px)`,
        background: C.card, border: `1px solid ${C.rule}`, borderRadius: 16, padding: '26px 30px', boxShadow: '0 14px 40px rgba(21,32,27,.08)'}}>
        <div style={{fontSize: 28, fontWeight: 700, color: accent}}>{step}</div>
        <div style={{marginTop: 10}}>{children}</div>
      </div>
      <div style={{position: 'absolute', left: x + 40, top: 560, width: 3, height: LINE.y0 - 560, background: C.ink, opacity: o}} />
    </>
  );
};

/** 2a: the 3D trap (Cycles PNG sequence). 2b: the strip becomes the lock timeline. */
export const S2Trap: React.FC = () => {
  const f = useCurrentFrame();
  if (f < TRAP_FRAMES) {
    const tO = ramp(f, cue(s, 'trap'), cue(s, 'trap') + 10) * (1 - ramp(f, TRAP_FRAMES - 40, TRAP_FRAMES - 25));
    return (
      <Paper>
        <Img src={staticFile(`v5/3d/trap/trap_${pad(f + 1)}.png`)} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
        <div style={{opacity: tO}}>
          <Title text="Yesterday's trap" sub="the clinic's own pollen count, read each morning" />
        </div>
      </Paper>
    );
  }
  const g = f - TRAP_FRAMES;
  const settle = interpolate(g, [0, 22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const y0 = STRIP.y0 + (LINE.y0 - STRIP.y0) * settle;
  const y1 = STRIP.y1 + (LINE.y1 - STRIP.y1) * settle;
  const kWrote = cue(s, 'wrote', 0, -0.1);
  const kLocked = cue(s, 'locked', 0, -0.1);
  const kDown = cue(s, 'downloaded', 0, -0.1);
  const kSeason = cue(s, 'twenty', 0, -0.1);
  const hatch = ramp(f, kDown, kDown + 18);
  const LX = 700; // the lock's x on the strip
  return (
    <Paper>
      <Title at={TRAP_FRAMES + 4} text="Locked before the data" />
      {/* the tape, now a timeline */}
      <div style={{position: 'absolute', left: 0, right: 0, top: y0, height: y1 - y0, background: '#DCD6C8', borderTop: `2px solid ${C.ink2}`, borderBottom: `2px solid ${C.ink2}`}} />
      {Array.from({length: 13}, (_, i) => (
        <div key={i} style={{position: 'absolute', left: 70 + i * 148, top: y0, width: 3, height: y1 - y0, background: C.ink, opacity: 0.8}} />
      ))}
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity: hatch}}>
        <defs>
          <pattern id="hatch" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="7" height="14" fill={C.ink} opacity={0.22} />
          </pattern>
        </defs>
        <rect x={LX + 40} y={y0} width={(1380 - LX - 40) * hatch} height={y1 - y0} fill="url(#hatch)" />
        <text x={LX + 60} y={y1 + 50} fontFamily={F.sans} fontSize={30} fontWeight={600} fill={C.ink}>2026 data downloaded after the lock</text>
      </svg>
      <Card x={150} at={kWrote} step="Test written">
        <Mono style={{fontSize: 30}}>{D.lock.prereg.split('/').pop()}</Mono>
        <div style={{fontSize: 28, color: C.ink2, marginTop: 8}}>4 hypotheses, fixed in advance</div>
      </Card>
      <Card x={LX - 40} at={kLocked} step="Model locked and pushed" accent={C.green}>
        <Mono style={{fontSize: 92, fontWeight: 700, letterSpacing: -2, lineHeight: 1}}>{D.lock.short}</Mono>
        <div style={{fontSize: 30, color: C.ink2, marginTop: 10}}>{day(D.lock.time)} · {hhmm(D.lock.time)}</div>
      </Card>
      <Card x={1380} at={kSeason} step="Then scored once">
        <Mono style={{fontSize: 40, fontWeight: 700}}>{D.scored.short} · {hhmm(D.scored.time)}</Mono>
        <div style={{fontSize: 28, color: C.ink2, marginTop: 8}}>on the untouched 2026 season</div>
      </Card>
    </Paper>
  );
};
