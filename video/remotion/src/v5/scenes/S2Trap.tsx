import React from 'react';
import {Img, staticFile, useCurrentFrame} from 'remotion';
import {C, cue, scene} from '../theme';
import {Paper, Title, ramp} from '../ui';

const s = scene('s2');
export const TRAP_FRAMES = 210; // Blender sequence length (video/v5/blender/trap_scene.py)
const pad = (n: number) => String(n).padStart(4, '0');

/** 2a: the 3D trap (Cycles PNG sequence). 2b: the lock timeline (built after style-frame approval). */
export const S2Trap: React.FC = () => {
  const f = useCurrentFrame();
  if (f < TRAP_FRAMES) {
    return (
      <Paper>
        <Img src={staticFile(`v5/3d/trap/trap_${pad(f + 1)}.png`)} style={{position: 'absolute', inset: 0, width: 1920, height: 1080}} />
        <div style={{opacity: ramp(f, cue(s, 'trap'), cue(s, 'trap') + 10)}}>
          <Title text="Yesterday's trap" sub="air in through a slit · pollen sticks to a tape · one band per day" />
        </div>
      </Paper>
    );
  }
  return <Paper><Title text="Locked before the data" sub="(timeline: built after approval)" /></Paper>;
};
