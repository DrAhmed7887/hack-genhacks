import React from 'react';
import {AbsoluteFill, Sequence, staticFile} from 'remotion';
import {Audio} from '@remotion/media';
import {C, D, FPS, fontCss} from './theme';
import {Captions, Paper, Progress, Title} from './ui';
import {S3Proof} from './scenes/S3Proof';
import {S5Morning} from './scenes/S5Morning';
import {S2Trap} from './scenes/S2Trap';

const Placeholder: React.FC<{id: string}> = ({id}) => (
  <Paper><Title text={`Scene ${id}`} sub="not built yet" /></Paper>
);

const SCENES: Record<string, React.FC> = {s2: S2Trap, s3: S3Proof, s5: S5Morning};

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
