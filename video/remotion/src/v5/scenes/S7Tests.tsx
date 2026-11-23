import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, cue, scene} from '../theme';
import {Paper, Shot, Title, ramp} from '../ui';
import shots from '../../../public/v5/shots/shots.json';

const s = scene('s7');
const ROWS = shots.tests_table.rects.rows;
const Z = 1.86;
const X = 960 - (shots.tests_table.cssW * Z) / 2;
const Y = 300;

/** The real hypothesis table; rows are revealed on their cue, the Failed chips stay. */
export const S7Tests: React.FC = () => {
  const f = useCurrentFrame();
  const at = [0, cue(s, 'tested'), cue(s, 'tested', 0, 0.3), cue(s, 'fusion'), cue(s, 'nasa'), cue(s, 'ship')];
  const kShip = cue(s, 'ship', 0, -0.1);
  const h1 = ROWS[1];
  return (
    <Paper>
      <Title text="We report what lost" sub="four hypotheses, written down before the test" />
      <Shot name="tests_table" x={X} y={Y} zoom={Z} />
      {ROWS.map((r, i) => (
        <div key={i} style={{position: 'absolute', left: X, top: Y + r.y * Z, width: r.w * Z, height: r.h * Z + 1, background: C.paper,
          opacity: 0.94 * (1 - ramp(f, at[i], at[i] + 8))}} />
      ))}
      <div style={{position: 'absolute', left: X - 8, top: Y + h1.y * Z - 6, width: h1.w * Z + 16, height: h1.h * Z + 12,
        border: `4px solid ${C.green}`, borderRadius: 12, opacity: ramp(f, kShip, kShip + 8)}} />
      <div style={{position: 'absolute', left: X, top: Y + (ROWS[5].y + ROWS[5].h) * Z + 40, fontSize: 34, fontWeight: 700, color: C.green,
        opacity: ramp(f, kShip, kShip + 8)}}>We ship H1: yesterday's trap, nothing more.</div>
    </Paper>
  );
};
