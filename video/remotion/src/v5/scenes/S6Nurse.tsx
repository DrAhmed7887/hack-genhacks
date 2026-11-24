import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {C, cue, scene} from '../theme';
import {Broll, Paper, Shot, Title, ramp} from '../ui';
import shots from '../../../public/v5/shots/shots.json';

const s = scene('s6');
const B = shots.console_bar.rects;
const DR = shots.draft_first.rects;
const HEAD = B['Nurse copilot · 111 of 200 synthetic patients, highest risk first'];
const NOTHING = B['Nothing is sent from this page.'];

/** A callout: a thin ink line from a point on the capture to a label on the right. */
export const Callout: React.FC<{x1: number; y1: number; x2: number; y2: number; at: number; color?: string; children: React.ReactNode}> = ({x1, y1, x2, y2, at, color = C.ink, children}) => {
  const f = useCurrentFrame();
  const o = ramp(f, at, at + 10);
  return (
    <>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity: o}}>
        <path d={`M${x1},${y1} L${x2 - 20},${y2}`} stroke={color} strokeWidth={3} fill="none" />
        <circle cx={x1} cy={y1} r={7} fill={color} />
      </svg>
      <div style={{position: 'absolute', left: x2, top: y2 - 26, opacity: o, fontSize: 40, fontWeight: 700, color, maxWidth: 1920 - x2 - 80, lineHeight: 1.15}}>{children}</div>
    </>
  );
};

export const S6Nurse: React.FC = () => {
  const f = useCurrentFrame();
  const kEach = cue(s, 'each', 0, -0.2);
  const kMed = cue(s, 'medicine', 1, -0.1);
  const kAdds = cue(s, 'adds', 0, -0.1);
  const kNurse = cue(s, 'a', 1, -0.3);
  const kApp = cue(s, 'approves', 0, 0.1);
  const kNothing = cue(s, 'nothing', 0, -0.1);

  if (f < kEach) {
    const Z = 3.3;
    return (
      <Paper>
        <Broll src="v5/flow/clinic_desk.mp4" scrim="center" />
        <Title text="The morning batch" />
        <Shot name="console_bar" x={960 - (HEAD.w * Z) / 2 - 16} y={420} zoom={Z} shadow={false}
          crop={{x: HEAD.x - 4, y: HEAD.y - 4, w: HEAD.w + 8, h: HEAD.h + 10}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center', fontSize: 30, color: C.ink2,
          opacity: ramp(f, cue(s, 'synthetic', 0, 0), cue(s, 'synthetic', 0, 0.4))}}>
          synthetic patients only · no real patient data
        </div>
      </Paper>
    );
  }
  if (f < kNurse) {
    const Z = 2.05, X = 200, Y = 116;
    const RX = X + shots.draft_first.cssW * Z + 10;
    const med = DR['your intranasal steroid spray'];
    const safety = DR['block:Pollen levels do not diagnose anything.'];
    const u = ramp(f, kMed, kMed + 12);
    return (
      <Paper>
        <Shot name="draft_first" x={X} y={Y} zoom={Z} />
        <div style={{position: 'absolute', left: X + med.x * Z, top: Y + (med.y + med.h) * Z + 1, width: med.w * Z * u, height: 5, background: C.green, borderRadius: 3}} />
        <Callout at={kMed} color={C.green} x1={RX} y1={Y + (med.y + med.h / 2) * Z} x2={990} y2={Y + (med.y + med.h / 2) * Z}>
          only the medicine<br />already on file
        </Callout>
        <div style={{position: 'absolute', left: X - 22, top: Y + safety.y * Z, width: 8, height: safety.h * Z * ramp(f, kAdds, kAdds + 14), background: C.ink, borderRadius: 4}} />
        <Callout at={kAdds} x1={RX} y1={Y + (safety.y + safety.h / 2) * Z} x2={990} y2={Y + (safety.y + safety.h / 2) * Z}>
          the signed safety line,<br />added by code
        </Callout>
      </Paper>
    );
  }
  const Z = 3.2;
  const clicked = f >= kApp;
  const btn = clicked ? shots.approve_after : shots.approve_btn;
  const bx = 960 - (btn.cssW * Z) / 2, by = 380;
  // cursor glides to the button, presses on "approves"
  const cx = interpolate(f, [kNurse, kApp - 4], [1560, 960 + 40], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const cy = interpolate(f, [kNurse, kApp - 4], [860, by + 80], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const ring = interpolate(f, [kApp, kApp + 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const NZ = 3.0;
  return (
    <Paper>
      <Title text="A nurse approves" />
      <Shot name={clicked ? 'approve_after' : 'approve_btn'} x={bx} y={by} zoom={Z} shadow={false} />
      {f >= kApp && f < kApp + 14 ? (
        <div style={{position: 'absolute', left: cx - 40 * (1 + ring), top: cy - 40 * (1 + ring), width: 80 * (1 + ring), height: 80 * (1 + ring),
          borderRadius: '50%', border: `4px solid ${C.ink}`, opacity: 1 - ring}} />
      ) : null}
      <svg width={64} height={64} style={{position: 'absolute', left: cx, top: cy, opacity: 1 - ramp(f, kApp + 20, kApp + 30)}}>
        <path d="M4 2 L4 46 L16 35 L25 56 L34 52 L25 32 L42 32 Z" fill={C.ink} stroke="#fff" strokeWidth={3} strokeLinejoin="round" />
      </svg>
      <div style={{opacity: ramp(f, kNothing, kNothing + 10)}}>
        <Shot name="console_bar" x={960 - (NOTHING.w * NZ) / 2} y={660} zoom={NZ} shadow={false}
          crop={{x: NOTHING.x - 3, y: NOTHING.y - 3, w: NOTHING.w + 6, h: NOTHING.h + 8}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 750, textAlign: 'center', fontSize: 28, color: C.ink2}}>the demo page, as built</div>
      </div>
    </Paper>
  );
};
