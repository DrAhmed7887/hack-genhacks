import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';
import timeline from './timeline.json';
import {DARK, FPS, LIGHT, SANS} from './theme';
import {S1, S2, S3, S4, S5, S6, S7, S8} from './scenes';
import {Sound} from './Sound';
import {OffsetCtx} from './ui';

export const TOTAL_FRAMES = Math.round(timeline.total * FPS);
const F = (s: number) => Math.round(s * FPS);
const X = 10; // pre-overlap fade-in frames: the next scene fades in OVER the previous one, which stays opaque underneath (never black)

// Visual scenes. s5 spans narration slots s5a + s5b; s7 spans s7 + s7n (V4 NASA test).
const VIS: {id: string; narr: string[]; bg: string; C: React.FC}[] = [
  {id: 's1', narr: ['s1'], bg: DARK, C: S1},
  {id: 's2', narr: ['s2'], bg: LIGHT, C: S2},
  {id: 's3', narr: ['s3'], bg: DARK, C: S3},
  {id: 's4', narr: ['s4'], bg: LIGHT, C: S4},
  {id: 's5', narr: ['s5a', 's5b'], bg: DARK, C: S5},
  {id: 's6', narr: ['s6'], bg: LIGHT, C: S6},
  {id: 's7', narr: ['s7', 's7n'], bg: DARK, C: S7},
  {id: 's8', narr: ['s8'], bg: LIGHT, C: S8},
];
const slot = (id: string) => timeline.scenes.find((s) => s.id === id)!;
const starts = VIS.map((v) => F(slot(v.narr[0]).start));
const bounds = [...starts, TOTAL_FRAMES]; // gapless: scene i covers [bounds[i], bounds[i+1])

const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    const faces = [
      new FontFace('Inter', `url(${staticFile('fonts/Inter-400.woff2')})`, {weight: '400'}),
      new FontFace('Inter', `url(${staticFile('fonts/Inter-700.woff2')})`, {weight: '600 800'}),
    ];
    Promise.all(faces.map((f) => f.load())).then((ls) => { ls.forEach((f) => (document.fonts as any).add(f)); continueRender(handle); })
      .catch(() => continueRender(handle));
  }, [handle]);
};

// Pre-overlap fade-in only (no exit fade anywhere). Solid scene background is opaque from the first frame of the fade.
const Scene: React.FC<{bg: string; pre: number; band: boolean; children: React.ReactNode}> = ({bg, pre, band, children}) => {
  const f = useCurrentFrame();
  const o = pre === 0 ? 1 : interpolate(f, [0, pre], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: o, background: bg}}>
      {band && <div style={{position: 'absolute', left: 0, top: 0, right: 0, height: 130, background: '#1C2431', borderBottom: '2px solid #34415A'}} />}
      {children}
    </AbsoluteFill>
  );
};

const Captions: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const cue = timeline.captions.find((c) => t >= c.start && t < c.end);
  if (!cue) return null;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 30, pointerEvents: 'none'}}>
      <div style={{maxWidth: 1600, padding: '10px 28px', borderRadius: 12, background: 'rgba(8,12,18,0.90)', color: '#FFFFFF', fontFamily: SANS,
        fontSize: 38, fontWeight: 700, lineHeight: 1.25, textAlign: 'center', boxShadow: '0 4px 18px rgba(0,0,0,0.35)'}}>{cue.text}</div>
    </AbsoluteFill>
  );
};

const Progress: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', left: 0, bottom: 0, height: 6, width: `${(f / TOTAL_FRAMES) * 100}%`, background: '#0F766E'}} />;
};

export const Film: React.FC<{withSound?: boolean; noCaptions?: boolean}> = ({withSound = true, noCaptions = false}) => {
  useFonts();
  return (
    <AbsoluteFill style={{background: DARK}}>
      {VIS.map((v, i) => {
        const pre = i === 0 ? 0 : X;
        const from = bounds[i] - pre;
        const dur = bounds[i + 1] - bounds[i] + pre;
        return (
          <Sequence key={v.id} from={from} durationInFrames={dur} name={v.id}>
            <Scene bg={v.bg} pre={pre} band={v.bg === DARK && v.id !== 's1'}>
              <OffsetCtx.Provider value={pre / FPS}><v.C /></OffsetCtx.Provider>
            </Scene>
          </Sequence>
        );
      })}
      {timeline.scenes.map((s) => (
        <Sequence key={s.id} from={F(s.start + s.audioAt)} name={`audio-${s.id}`} layout="none"><Audio src={staticFile(`audio/${s.audio}`)} /></Sequence>
      ))}
      {withSound && <Sound />}
      {!noCaptions && <Captions />}
      <Progress />
    </AbsoluteFill>
  );
};
