import {Composition} from 'remotion';
import {Film, TOTAL_FRAMES} from './Film';
export const Root = () => (
  <>
    <Composition id="Film" component={Film} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="FilmSilent" component={Film} defaultProps={{withSound: false}} durationInFrames={TOTAL_FRAMES} fps={30} width={1920} height={1080} />
  </>
);
