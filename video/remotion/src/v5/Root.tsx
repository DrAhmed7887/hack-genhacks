import {Composition} from 'remotion';
import {FilmV5} from './Film';
import {D} from './theme';

export const Root = () => (
  <>
    <Composition id="FilmV5" component={FilmV5} durationInFrames={D.totalFrames} fps={D.fps} width={1920} height={1080} />
    <Composition id="FilmV5Silent" component={FilmV5} defaultProps={{withSound: false}} durationInFrames={D.totalFrames} fps={D.fps} width={1920} height={1080} />
  </>
);
