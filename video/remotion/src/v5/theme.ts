import {staticFile} from 'remotion';
import data from './data.json';

export const D = data;
export const FPS = data.fps;

export const C = {
  paper: '#F6F4EE',
  paper2: '#EDEAE1',
  card: '#FFFFFF',
  ink: '#15201B',
  ink2: '#4A544F',
  mute: '#8A8F86',
  rule: '#D8D3C6',
  bar: '#9E9885',
  barLight: '#D6D1C4',
  green: '#16794A',
  greenSoft: '#DCEFE3',
  amber: '#B4570B',
  amberSoft: '#F8E6D6',
  red: '#A33A2F',
};

export const F = {
  sans: "'InterV5', Inter, system-ui, sans-serif",
  mono: "'JBMonoV5', 'JetBrains Mono', ui-monospace, monospace",
};

export const fontCss = `
@font-face { font-family: 'InterV5'; src: url('${staticFile('v5/fonts/Inter-var.woff2')}') format('woff2'); font-weight: 100 900; font-display: block; }
@font-face { font-family: 'JBMonoV5'; src: url('${staticFile('v5/fonts/JetBrainsMono-var.woff2')}') format('woff2'); font-weight: 100 800; font-display: block; }
`;

export type Scene = (typeof data.scenes)[number];
export const scene = (id: string): Scene => {
  const s = data.scenes.find((x) => x.id === id);
  if (!s) throw new Error('no scene ' + id);
  return s;
};

/** Frame (inside a scene) at which the n-th occurrence of a spoken word starts. */
export const cue = (s: Scene, word: string, nth = 0, offset = 0): number => {
  const hits = s.words.filter((w) => w.w.toLowerCase().replace(/[^a-z0-9'-]/g, '') === word.toLowerCase());
  if (!hits[nth]) throw new Error(`cue '${word}'#${nth} not in ${s.id}`);
  return Math.round((hits[nth].start + offset) * FPS);
};
