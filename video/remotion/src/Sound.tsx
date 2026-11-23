import React from 'react';
import {Audio, Sequence, interpolate, staticFile} from 'remotion';
import timeline from './timeline.json';
import {FPS} from './theme';
import {W} from './ui';

const F = (s: number) => Math.round(s * FPS);
const S = (id: string) => timeline.scenes.find((s) => s.id === id)!.start;
const at = (id: string, word: string, d = 0, n = 0) => S(id) + W(id, word, n) + d;

// Music ducks under speech; the s5 silent hold is ducked too.
const SPEECH = timeline.scenes.map((s) => [s.start + (s.words[0][1] as number), s.start + (s.words[s.words.length - 1][2] as number)] as [number, number]);
const HOLD: [number, number] = [S('s5a') + 12.0, S('s5b') + 0.35];
const UNDER = 0.10, GAP = 0.26, RAMP = 0.35;
const musicVolume = (frame: number) => {
  const t = frame / FPS;
  let v = GAP;
  for (const [a, b] of SPEECH) {
    if (t > a - RAMP && t < b + RAMP) v = Math.min(v, UNDER + (GAP - UNDER) * (t < a ? (a - t) / RAMP : t > b ? (t - b) / RAMP : 0));
  }
  if (t > HOLD[0] && t < HOLD[1]) v = Math.min(v, 0.04);
  return v * interpolate(t, [0, 1.5, timeline.total - 2.5, timeline.total], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};

type Cue = [string, number, number];
const CUES: Cue[] = [
  ...['s2', 's3', 's4', 's5a', 's6', 's7', 's7n', 's8'].map((id) => ['whoosh', S(id) - 0.3, 0.35] as Cue),
  ['click', at('s2', 'switch', -0.1), 0.6],
  ['tick', at('s2', 'hundred'), 0.4],
  ['click', at('s2', 'approves'), 0.8],
  ['chime', at('s2', 'batch'), 0.3],
  ['tick', at('s3', 'five'), 0.4],
  ['tick', at('s3', 'eight'), 0.4],
  ['tick', at('s4', 'frozen'), 0.4],
  ['tick', at('s4', 'twenty-eight', 0, 0), 0.4],
  ['tick', at('s5a', 'api', 0.1, 0), 0.4],
  ['tick', at('s5a', 'our'), 0.4],
  ['click', at('s5a', 'it'), 0.9],
  ['chime', at('s5b', 'so'), 0.4],
  ['tick', at('s6', 'thirty'), 0.4],
  ['tick', at('s7', 'honest', 1.2), 0.3],
  ['tick', at('s7', 'pre-peak'), 0.3],
  ['tick', at('s7', 'valencia'), 0.3],
  ['tick', at('s7n', 'nasa', 0, 1), 0.3],
  ['tick', at('s7n', 'last'), 0.3],
  ['tick', at('s7n', 'score'), 0.3],
  ['tick', at('s7n', 'four', 0, 1), 0.3],
  ['tick', at('s7n', 'without'), 0.3],
  ['click', at('s7n', 'added'), 0.6],
  ['tick', at('s8', 'zero'), 0.4],
  ['tick', at('s8', 'eighty'), 0.4],
  ['tick', at('s8', 'one'), 0.4],
  ['chime', at('s8', 'open'), 0.4],
];

export const Sound: React.FC = () => (
  <>
    <Audio src={staticFile('sfx/music.wav')} volume={musicVolume} />
    {CUES.map(([f, t, vol], i) => (
      <Sequence key={i} from={F(t)} name={`sfx-${f}`} layout="none"><Audio src={staticFile(`sfx/${f}.wav`)} volume={vol} /></Sequence>
    ))}
  </>
);
