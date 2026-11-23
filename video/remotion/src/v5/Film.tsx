import React from 'react';
import {AbsoluteFill, Sequence, staticFile} from 'remotion';
import {Audio} from '@remotion/media';
import {C, D, FPS, fontCss} from './theme';
import {Captions, Paper, Progress, Title} from './ui';
import {S3Proof} from './scenes/S3Proof';
import {S5Morning} from './scenes/S5Morning';
import {S2Trap} from './scenes/S2Trap';
import {S1Open} from './scenes/S1Open';
import {S4Season} from './scenes/S4Season';
import {S6Nurse} from './scenes/S6Nurse';
import {S6bAI} from './scenes/S6bAI';
import {S7Tests} from './scenes/S7Tests';
import {S8Map} from './scenes/S8Map';
import {S9Close} from './scenes/S9Close';

const Placeholder: React.FC<{id: string}> = ({id}) => (
  <Paper><Title text={`Scene ${id}`} sub="not built yet" /></Paper>
);

const SCENES: Record<string, React.FC> = {s1: S1Open, s2: S2Trap, s3: S3Proof, s4: S4Season, s5: S5Morning, s6: S6Nurse, s6b: S6bAI, s7: S7Tests, s8: S8Map, s9: S9Close};

export const FilmV5: React.FC<{withSound?: boolean}> = ({withSound = true}) => (
  <AbsoluteFill style={{background: C.paper}}>
    <style>{fontCss}</style>
    {D.scenes.map((s) => {
      const Comp = SCENES[s.id];
      return (
        <Sequence key={s.id} from={s.from} durationInFrames={s.frames} name={s.id}>
          {Comp ? <Comp /> : <Placeholder id={s.id} />}
          {withSound ? (
            <Sequence from={Math.round(s.voiceAt * FPS)} layout="none">
              <Audio src={staticFile(s.audio)} />
            </Sequence>
          ) : null}
        </Sequence>
      );
    })}
    <Captions />
    <Progress />
  </AbsoluteFill>
);
