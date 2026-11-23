import React from 'react';
import {AbsoluteFill, Img, Loop, OffthreadVideo, staticFile} from 'remotion';
import film from './data/film_data.json';
import timeline from './timeline.json';
import {AMBER, CRIMSON, C, FPS, MONO, SANS} from './theme';
import {Cursor, FrameCtx, Hi, Shot, W, appear, box, countTo, ease, fadeIn, pop, useSec, window_} from './ui';

const b = box;
const ctr = (r: {x: number; y: number; w: number; h: number}) => [r.x + r.w / 2, r.y + r.h / 2] as const;
const DUR5A = timeline.scenes.find((s) => s.id === 's5a')!.dur;
const W5B = (p: string, n = 0) => DUR5A + W('s5b', p, n);
const DUR7 = timeline.scenes.find((s) => s.id === 's7')!.dur;
const W7N = (p: string, n = 0) => DUR7 + W('s7n', p, n);
const fmt = (n: number) => Math.round(n).toLocaleString('en-US');
const NASA_BLUE = '#93C5FD';
const TEAL = '#5EEAD4';
type Ev = {city: string; species: string; date: string; p2: boolean; r1: boolean};
type Season = {label: string; nasa_lead: number; nasa_hit: boolean; cal_lead: number; cal_hit: boolean};
const EVENTS = (film as any).events as Ev[];
const OLIVE = (film as any).olive as Ev[];
const SEASONS = (film as any).seasons as Season[];

// Screen-space chip (not zoomed).
const Chip: React.FC<{t: number; at: number; until?: number; bg?: string; color?: string; style?: React.CSSProperties; children: React.ReactNode}> =
  ({t, at, until = 999, bg = C.ink, color = '#fff', style, children}) => (
    <div style={{position: 'absolute', padding: '12px 24px', borderRadius: 14, background: bg, color, fontFamily: SANS, fontSize: 30, fontWeight: 700,
      opacity: window_(t, at, until), transform: `translateY(${ease(t, at, at + 0.4, -14, 0)}px)`, boxShadow: '0 10px 28px rgba(20,32,43,0.28)', ...style}}>{children}</div>
  );

const Glass: React.FC<{style?: React.CSSProperties; children: React.ReactNode}> = ({style, children}) => (
  <div style={{position: 'absolute', borderRadius: 18, background: '#1C2431', border: '2px solid #34415A', fontFamily: SANS, color: '#fff',
    boxShadow: '0 12px 30px rgba(0,0,0,0.35)', ...style}}>{children}</div>
);

// ───────── s1 · dark · cold open
export const S1: React.FC = () => {
  const t = useSec();
  return (
    <AbsoluteFill>
      <Loop durationInFrames={120}>
        <OffthreadVideo src={staticFile('media/flow_pollen_hook.mp4')} muted style={{width: 1920, height: 1080, objectFit: 'cover'}} />
      </Loop>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(13,17,23,0.35) 0%, rgba(13,17,23,0.60) 55%, rgba(13,17,23,0.82) 100%)'}} />
      <div style={{position: 'absolute', right: 48, bottom: 120, fontFamily: SANS, fontSize: 28, fontWeight: 700, color: 'rgba(255,255,255,0.6)', opacity: fadeIn(t, 0.3)}}>Procedural 3D visual</div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 330, textAlign: 'center', fontFamily: SANS, color: '#fff'}}>
        <div style={{fontSize: 128, fontWeight: 800, letterSpacing: -2, lineHeight: 1.05, ...appear(t, 0.5, 0.7, 40)}}>SPRAYS START TOO LATE?</div>
        <div style={{fontSize: 40, fontWeight: 400, color: '#D5DEE8', marginTop: 34, ...appear(t, W('s1', 'already'), 0.6)}}>
          Already-prescribed nasal sprays</div>
      </div>
      {(() => {
        const k = pop(t, W('s1', 'say'));
        return (
          <div style={{position: 'absolute', left: 0, right: 0, top: 640, display: 'flex', justifyContent: 'center'}}>
            <div style={{padding: '22px 44px', borderRadius: 20, background: AMBER, color: '#1A1203', fontFamily: SANS, fontSize: 52, fontWeight: 800,
              opacity: Math.min(1, k * 2), transform: `scale(${0.85 + 0.15 * Math.min(1.1, k)}) rotate(${(1 - Math.min(1, k)) * -3}deg)`, boxShadow: '0 16px 40px rgba(217,119,6,0.35)'}}>
              We did: our rule 41.0% vs API 41.6%</div>
          </div>
        );
      })()}
    </AbsoluteFill>
  );
};

// ───────── s2 · light · live product
export const S2: React.FC = () => {
  const t = useSec();
  const tSw = W('s2', 'switch'), tH = W('s2', 'hundred'), tA = W('s2', 'approves'), tB = W('s2', 'batch'), tV = W('s2', 'valencia'), tN = W('s2', 'nurse');
  const [ax, ay] = ctr(b('s2_madrid_approved', 'approve'));
  const [lx, ly] = ctr(b('s2_madrid_approved', 'audit'));
  const kd = b('s2_valencia_control', 'kpi_drafted');
  const KY = b('s2_valencia_control', 'kpis').y + 250; // KPI row high in frame, NASA context panel above it mostly out of shot
  const tD = W('s2', 'deterministic');
  return (
    <AbsoluteFill>
      <Shot shot="s2_valencia_control" layers={[['s2_valencia_control', 0], ['s2_madrid_grass', tSw + 0.6], ['s2_madrid_approved', tA + 0.9]]} t={t}
        keys={[[0, 960, KY, 1.3], [tV - 0.4, 960, KY, 1.55], [tSw - 0.6, 960, KY, 1.55], [tSw + 0.6, 960, KY, 1.55], [tN - 0.8, 960, KY, 1.55],
          [tA - 0.9, 960, (KY + ay) / 2, 1.5], [tA, ax + 200, ay - 20, 1.6], [tA + 1.8, lx, ly - 40, 1.6]]}>
        <Hi r={b('s2_valencia_control', 'caveat')} t={t} at={tV} until={tSw - 0.4} dim={false} color={C.warn} />
        <Hi r={b('s2_madrid_grass', 'kpis')} t={t} at={tH - 0.4} until={tN - 1.0} dim={false} />
        <Cursor t={t} keys={[[tA - 1.0, ax + 420, ay + 160], [tA - 0.1, ax, ay]]} clicks={[tA]} />
        <Hi r={b('s2_madrid_approved', 'audit')} t={t} at={tB + 0.3} pad={8} />
      </Shot>
      <Chip t={t} at={0.4} until={tSw - 0.3} style={{left: 48, bottom: 155}}>Valencia control: 0 drafted</Chip>
      <Chip t={t} at={tSw + 0.2} until={tA - 0.3} bg={C.accent} style={{left: 48, bottom: 155}}>Madrid grass: 42.1 ≥ 35 · 111 drafted / 89 blocked</Chip>
      <Chip t={t} at={tD - 0.1} until={tN} bg={C.navy} style={{left: 48, top: 40, fontSize: 32}}>Trigger in the app: API forecast (P2)</Chip>
      <Chip t={t} at={tA + 0.3} bg={C.navy} style={{left: 48, bottom: 155}}>Approved → audit log timestamp</Chip>
      <Chip t={t} at={tA + 0.9} bg={C.warn} style={{right: 48, bottom: 225}}>Demo mode: 0 sent externally</Chip>
    </AbsoluteFill>
  );
};

// ───────── s3 · dark · grid vs traps
export const S3: React.FC = () => {
  const t = useSec();
  const tPeople = W('s3', 'people'), tWe = W('s3', 'we'), tMad = W('s3', 'madrid'), tFive = W('s3', 'five'), tSeven = W('s3', 'seven');
  const badge = (txt: string, sub: string, at: number, y: number, col: string) => (
    <Glass style={{left: 1160, top: y, width: 696, padding: '18px 26px', ...appear(t, at, 0.5)}}>
      <div style={{fontSize: 40, fontWeight: 800, color: col}}>{txt}</div>
      <div style={{fontSize: 24, color: '#9FB0C5', marginTop: 4}}>{sub}</div>
    </Glass>
  );
  const counter = (x: number, val: string, label: string, at: number) => (
    <Glass style={{left: x, top: 745, width: 330, padding: '18px 10px', textAlign: 'center', ...appear(t, at, 0.5)}}>
      <div style={{fontSize: 66, fontWeight: 800, color: '#5EEAD4', lineHeight: 1}}>{val}</div>
      <div style={{fontSize: 26, color: '#C5D1E0', marginTop: 8}}>{label}</div>
    </Glass>
  );
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 64, top: 110, width: 1040, height: 585, borderRadius: 18, overflow: 'hidden', border: '3px solid #34415A', ...appear(t, 0.2, 0.6, 0)}}>
        <Loop durationInFrames={150}><OffthreadVideo src={staticFile('media/blender_pollen_grid.mp4')} muted style={{width: 1040, height: 585, objectFit: 'cover'}} /></Loop>
      </div>
      <div style={{position: 'absolute', left: 64, top: 52, fontFamily: SANS, fontSize: 32, fontWeight: 700, color: '#9FB0C5', ...appear(t, 0.2)}}>
        11 km model grid vs point traps · Blender 3D</div>
      <div style={{position: 'absolute', left: 1160, top: 52, fontFamily: SANS, fontSize: 32, fontWeight: 700, color: '#9FB0C5', ...appear(t, 1.0)}}>Pre-registered thresholds</div>
      {badge('Olive 162', 'PMID 21277516', 1.5, 110, '#A3E635')}
      {badge('Grass 35', 'PMID 20815307', 2.0, 232, '#5EEAD4')}
      {badge('Birch 30', 'PMID 24247974', 2.5, 354, '#FBBF24')}
      <Glass style={{left: 1160, top: 490, width: 696, padding: '20px 26px', borderColor: AMBER, ...appear(t, tPeople + 0.4, 0.5)}}>
        <div style={{fontSize: 28, fontWeight: 700, color: '#FBBF24'}}>T5 note</div>
        <div style={{fontSize: 30, fontWeight: 700, lineHeight: 1.25, marginTop: 6}}>EPOCHAL n=396 found no threshold</div>
        <div style={{fontSize: 26, color: '#C5D1E0', lineHeight: 1.25, marginTop: 6}}>No safe or unsafe level exists for every person</div>
      </Glass>
      {counter(64, `${fmt(countTo(t, tSeven, tSeven + 1.6, 7373))}`, 'city-days', tSeven - 0.2)}
      {counter(412, `${fmt(countTo(t, tMad, tMad + 1.2, 863))}`, 'events', tMad - 0.2)}
      {counter(760, `${fmt(countTo(t, tFive, tFive + 0.8, 5))}`, 'years', tFive - 0.2)}
    </AbsoluteFill>
  );
};

// ───────── s4 · light · frozen rules + onset table
export const S4: React.FC = () => {
  const t = useSec();
  const nodes = [
    {txt: ['Open-Meteo CAMS', '+ Madrid/MeteoSwiss'], at: 0.4, col: C.navy},
    {txt: ['6 Rules Frozen', '(P0..C0)'], at: W('s4', 'frozen'), col: C.accent},
    {txt: ['Day P2 vs R1', 'Onset R2 vs P2/C0'], at: W('s4', 'testing'), col: C.navy},
    {txt: ['Kill-Check Gate'], at: W('s4', 'climatology'), col: C.warn},
  ];
  const NW = 380, GAP = (1792 - 4 * NW) / 3, Y = 40, H = 130;
  const tOn = W('s4', 'pre-peak'), tSeas = W('s4', 'twenty-eight'), tMiss = W('s4', 'missed');
  const res = b('s4_onset_table', 'results'), on = b('s4_onset_table', 'onset');
  return (
    <AbsoluteFill>
      <svg width={1920} height={260} style={{position: 'absolute', left: 0, top: 30}}>
        {nodes.map((n, i) => {
          const x = 64 + i * (NW + GAP);
          const k = pop(t, n.at);
          return (
            <g key={i} opacity={Math.min(1, k * 1.4)} transform={`translate(${x},${Y + 10 * (1 - Math.min(1, k))})`}>
              <rect width={NW} height={H} rx={18} fill="#fff" stroke={n.col} strokeWidth={4} />
              {n.txt.map((l, j) => (
                <text key={j} x={NW / 2} y={n.txt.length === 1 ? H / 2 + 12 : 52 + j * 40} textAnchor="middle" fontFamily={SANS} fontSize={n.txt.length === 1 ? 38 : 30} fontWeight={700} fill={C.ink}>{l}</text>
              ))}
              {i < 3 && (() => {
                const p = ease(t, nodes[i + 1].at - 0.5, nodes[i + 1].at);
                return (
                  <g>
                    <line x1={NW + 8} y1={H / 2} x2={NW + 8 + (GAP - 28) * p} y2={H / 2} stroke={C.muted} strokeWidth={5} />
                    {p > 0.95 && <polygon points={`${NW + GAP - 20},${H / 2 - 12} ${NW + GAP - 4},${H / 2} ${NW + GAP - 20},${H / 2 + 12}`} fill={C.muted} />}
                  </g>
                );
              })()}
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: 64, top: 215, width: 1792, height: 700, borderRadius: 18, overflow: 'hidden', border: `3px solid ${C.line}`, background: '#fff', ...appear(t, 1.0, 0.6, 0)}}>
        <FrameCtx.Provider value={{w: 1792, h: 700}}>
          <Shot shot="s4_onset_table" t={t}
            keys={[[0, 960, res.y + 200, 1.5], [tOn - 1.2, 960, res.y + 200, 1.5], [tOn, 960, on.y + 330, 1.5], [tSeas, 960, on.y + 400, 1.5], [tMiss - 0.3, 960, on.y + 450, 1.5],
              [tMiss + 2.0, 960, on.y + on.h - 330, 1.5]]}>
            <Hi r={res} t={t} at={W('s4', 'testing')} until={tOn - 0.6} dim={false} />
            <Hi r={{x: on.x, y: on.y, w: on.w, h: on.h}} t={t} at={tSeas} until={tMiss + 3} dim={false} color={C.warn} />
          </Shot>
        </FrameCtx.Provider>
      </div>
      <Chip t={t} at={tSeas} bg={C.warn} style={{right: 96, top: 250, fontSize: 28}}>28 seasons (incl. missed Madrid grass 2023)</Chip>
    </AbsoluteFill>
  );
};

// ───────── s5 · dark · proof as 863 real events (spans s5a + s5b)
const GRID_COLS = 48;
const DotGrid: React.FC<{t: number; draw: number; fill: number; rule: 'p2' | 'r1'; col: string}> = ({t, draw, fill, rule, col}) => {
  const caught = EVENTS.filter((e) => e[rule]).length;
  const k = ease(t, fill, fill + 1.4);
  let rank = 0;
  return (
    <svg width={768} height={288}>
      {EVENTS.map((e, i) => {
        const cx = 8 + (i % GRID_COLS) * 16, cy = 8 + Math.floor(i / GRID_COLS) * 16;
        const o = ease(t, draw + ((i % GRID_COLS) / GRID_COLS) * 1.2, draw + ((i % GRID_COLS) / GRID_COLS) * 1.2 + 0.25);
        const on = e[rule] && rank++ < k * caught;
        return <circle key={i} cx={cx} cy={cy} r={6} fill={on ? col : 'none'} stroke={on ? col : '#5A6A82'} strokeWidth={2} opacity={o} />;
      })}
    </svg>
  );
};

export const S5: React.FC = () => {
  const t = useSec();
  const tDraw = W('s5a', 'eight'), tApi = W('s5a', 'caught'), tOur = W('s5a', 'caught', 1), tIt = W('s5a', 'it'), tUses = W5B('uses');
  const panel = (x: number, title: string, big: number, n: number, rule: 'p2' | 'r1', at: number, col: string, dimAt?: number) => {
    const k = ease(t, at, at + 1.4);
    const dim = dimAt === undefined ? 1 : 1 - 0.65 * ease(t, dimAt, dimAt + 0.6);
    return (
      <Glass style={{left: x, top: 150, width: 860, height: 640, borderColor: col, ...appear(t, 0.2, 0.5), opacity: Math.min(ease(t, 0.2, 0.7), dim)}}>
        <div style={{position: 'absolute', left: 46, top: 28, fontSize: 40, fontWeight: 700, color: '#C5D1E0'}}>{title}</div>
        <div style={{position: 'absolute', left: 46, top: 88, display: 'flex', alignItems: 'baseline', gap: 26}}>
          <span style={{fontSize: 150, fontWeight: 800, color: col, lineHeight: 1, letterSpacing: -4}}>{t < at ? '—' : `${(big * k).toFixed(1)}%`}</span>
          <span style={{fontSize: 40, fontWeight: 700, opacity: t < at ? 0 : 1}}>({fmt(n * k)} / 863)</span>
        </div>
        <div style={{position: 'absolute', left: 46, top: 300}}><DotGrid t={t} draw={tDraw} fill={at} rule={rule} col={col} /></div>
        <div style={{position: 'absolute', left: 46, top: 598, fontSize: 28, fontWeight: 700, color: '#9FB0C5', opacity: ease(t, tDraw, tDraw + 0.6)}}>each dot = one observed high-pollen day</div>
      </Glass>
    );
  };
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 64, top: 52, fontFamily: SANS, fontSize: 34, fontWeight: 700, color: '#9FB0C5', ...appear(t, 0.2)}}>
        863 high-pollen events · 7,373 city-days · frozen in DATA_PLAN.md before scoring</div>
      {panel(64, 'API Forecast (P2)', 41.6, 359, 'p2', tApi, TEAL)}
      {panel(996, 'Our Rule (R1)', 41.0, 354, 'r1', tOur, NASA_BLUE, tUses)}
      <div style={{position: 'absolute', left: 64 + 860 - 46 - 330, top: 176, width: 330, padding: '10px 0', borderRadius: 999, background: C.accent, color: '#fff',
        fontFamily: SANS, fontSize: 30, fontWeight: 800, textAlign: 'center', ...appear(t, tUses, 0.5, 10)}}>✓ the app's trigger</div>
      {(() => {
        const k = pop(t, tIt);
        return (
          <div style={{position: 'absolute', left: 300, top: 812, width: 1320, padding: '20px 44px', borderRadius: 20, background: AMBER, color: '#1A1203', fontFamily: SANS,
            opacity: Math.min(1, k * 2), transform: `scale(${0.85 + 0.15 * Math.min(1.1, k)}) rotate(${(1 - Math.min(1, k)) * -3}deg)`, boxShadow: '0 16px 40px rgba(217,119,6,0.35)'}}>
            <div style={{fontSize: 46, fontWeight: 800}}>🔒 Claim locked: no “beats the API”</div>
            <div style={{fontSize: 28, fontWeight: 700, marginTop: 4, color: '#3B2603'}}>Frozen in DATA_PLAN.md · 22 Nov 2026</div>
          </div>
        );
      })()}
    </AbsoluteFill>
  );
};

// ───────── s6 · light · concrete refusal row
export const S6: React.FC = () => {
  const t = useSec();
  const tT = W('s6', 'thirty'), tE = W('s6', 'each'), tC = tT - 0.9;
  const [px, py] = ctr(b('s6_blocked_guard', 'panel'));
  const [rx, ry] = ctr(b('s6_blocked_guard', 'first_row'));
  const KY6 = b('s6_blocked_guard', 'kpis').y + 250;
  return (
    <AbsoluteFill>
      <Shot shot="s6_blocked_guard" t={t}
        keys={[[0, 960, KY6, 1.4], [tC - 0.6, 960, KY6, 1.4], [tC + 0.6, px, py + 40, 1.6], [tE - 1.0, px, py + 40, 1.6], [tE, rx, ry - 20, 1.6]]}>
        <Hi r={b('s6_blocked_guard', 'panel')} t={t} at={tT} until={tE - 0.3} color={CRIMSON} pad={8} />
        <Hi r={b('s6_blocked_guard', 'first_row')} t={t} at={tE + 0.5} pad={8} />
      </Shot>
      <Chip t={t} at={tT - 0.2} bg={CRIMSON} style={{left: 48, bottom: 225, fontSize: 32}}>34 no medicine on file · 55 not sensitised = 89 blocked</Chip>
      <Chip t={t} at={tE + 0.3} bg={C.ink} style={{right: 48, bottom: 225, fontSize: 30}}>P001 · “your intranasal steroid spray” only</Chip>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 155, display: 'flex', justifyContent: 'center', opacity: fadeIn(t, tE - 0.2)}}>
        <div style={{padding: '12px 30px', borderRadius: 999, background: C.accent, color: '#fff', fontFamily: SANS, fontSize: 32, fontWeight: 700}}>
          Thresholds signed 22 Nov 2026 · Not a medical device</div>
      </div>
    </AbsoluteFill>
  );
};

// ───────── s7 · dark · honest limits
export const S7: React.FC = () => {
  const t = useSec();
  const tN = W7N('we') - 0.2;               // phase 2: NASA test (narration slot s7n)
  const tC = W7N('rule') - 0.8;             // phase 3: CSI bars
  const tT = W7N('nine') + 0.5;             // phase 4: the live page's own verdict
  const out1 = 1 - ease(t, tN - 0.4, tN);
  const tCatch = W('s7', 'catches'), tThirteen = W('s7', 'thirteen'), tPre = W('s7', 'pre-peak'), tVal = W('s7', 'valencia');

  // Phase 1 · row 1: the 22 observed Madrid olive spike days, in date order (gap between years)
  let gaps = 0;
  const olive = OLIVE.map((e, i) => {
    if (i > 0 && e.date.slice(0, 4) !== OLIVE[i - 1].date.slice(0, 4)) gaps++;
    return {x: 70 + i * 56 + gaps * 18, caught: e.p2};
  });
  const oliveFill = ease(t, tThirteen, tThirteen + 0.8);
  const small = (n: string, txt: string, at: number, top: number) => (
    <Glass style={{left: 120, top, width: 1680, height: 150, display: 'flex', alignItems: 'center', gap: 36, padding: '0 44px', ...appear(t, at, 0.5, 20), opacity: Math.min(ease(t, at, at + 0.5), out1)}}>
      <div style={{flex: '0 0 84px', height: 84, borderRadius: 42, background: AMBER, color: '#1A1203', fontSize: 48, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{n}</div>
      <div style={{fontSize: 42, fontWeight: 700, lineHeight: 1.25}}>{txt}</div>
    </Glass>
  );

  // Phase 2 · ten held-out seasons: when each rule fired relative to the trap onset
  const PX = 480 / 56, ONSET_X = 920, xOf = (lead: number) => Math.max(440, Math.min(1400, ONSET_X - lead * PX));
  const tFour = W7N('fourteen'), tEarly = W7N('early'), tNasa = W7N('nasa', 1), tUseful = W7N('useful'),
    tThirty = W7N('thirty'), tLast = W7N('last'), tSixty = W7N('sixty');
  const o2 = window_(t, tN, tC, 0.4), o3 = window_(t, tC, tT, 0.4), o4 = ease(t, tT, tT + 0.5);
  const rowY = (i: number) => 240 + i * 64;
  const bar = (label: string, value: string, frac: number, col: string, at: number, top: number) => (
    <div style={{position: 'absolute', left: 44, top, width: 1592, height: 58, display: 'flex', alignItems: 'center', gap: 24, ...appear(t, at, 0.5, 12)}}>
      <div style={{flex: '0 0 470px', fontSize: 34, fontWeight: 700, color: '#D5DEE8'}}>{label}</div>
      <div style={{height: 46, width: 900 * frac * ease(t, at, at + 0.9), background: col, borderRadius: 10}} />
      <div style={{fontSize: 40, fontWeight: 800, color: '#fff', fontFamily: MONO}}>{value}</div>
    </div>
  );
  const tile = (title: string, glyph: React.ReactNode, pct: number, at: number, top: number, col: string) => (
    <div style={{position: 'absolute', left: 1450, top, width: 360, height: 300, borderRadius: 18, background: '#1C2431', border: `2px solid ${col}`, padding: '22px 26px', ...appear(t, at - 0.3, 0.5, 14)}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 14, fontSize: 30, fontWeight: 700, color: '#D5DEE8'}}>{glyph}{title}</div>
      <div style={{fontSize: 96, fontWeight: 800, color: col, lineHeight: 1.1, marginTop: 14}}>{t < at ? '—' : `${Math.round(pct * ease(t, at, at + 0.8))}%`}</div>
      <div style={{fontSize: 28, fontWeight: 700, color: '#9FB0C5'}}>in the useful window</div>
    </div>
  );
  return (
    <AbsoluteFill style={{fontFamily: SANS, color: '#fff'}}>
      {/* ── phase 1: honest limits ── */}
      <div style={{position: 'absolute', left: 120, top: 70, fontSize: 64, fontWeight: 800, ...appear(t, 0.2), opacity: Math.min(ease(t, 0.2, 0.7), out1)}}>Honest limits</div>
      <Glass style={{left: 120, top: 190, width: 1680, height: 380, ...appear(t, 0.3, 0.5, 20), opacity: Math.min(ease(t, 0.3, 0.8), out1), borderColor: AMBER}}>
        <div style={{position: 'absolute', left: 44, top: 30, display: 'flex', alignItems: 'center', gap: 24}}>
          <div style={{width: 64, height: 64, borderRadius: 32, background: AMBER, color: '#1A1203', fontSize: 38, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>1</div>
          <div style={{fontSize: 36, fontWeight: 800}}>Madrid olive spike days · API forecast (P2)</div>
        </div>
        <svg width={1400} height={120} style={{position: 'absolute', left: 0, top: 150}}>
          {olive.map((d, i) => (
            <circle key={i} cx={d.x} cy={60} r={23} fill={d.caught && oliveFill > 0 ? TEAL : 'none'} fillOpacity={d.caught ? oliveFill : 0}
              stroke={d.caught && oliveFill > 0.5 ? TEAL : '#5A6A82'} strokeWidth={3} opacity={ease(t, tCatch + i * 0.03, tCatch + i * 0.03 + 0.25)} />
          ))}
        </svg>
        <div style={{position: 'absolute', left: 44, top: 290, fontSize: 30, fontWeight: 700, color: '#9FB0C5', opacity: ease(t, tCatch, tCatch + 0.6)}}>each circle = one observed spike day · filled = the forecast caught it</div>
        <div style={{position: 'absolute', right: 50, top: 110, textAlign: 'right'}}>
          <div style={{fontSize: 96, fontWeight: 800, color: TEAL, lineHeight: 1}}>{t < tThirteen ? '—' : `${(13.6 * oliveFill).toFixed(1)}%`}</div>
          <div style={{fontSize: 32, fontWeight: 700, color: '#D5DEE8', marginTop: 10, opacity: oliveFill}}>grass: 31.4%</div>
        </div>
      </Glass>
      {small('2', 'Pre-peak lead reflects look-ahead, not beating climatology', tPre - 0.2, 600)}
      {small('3', 'Valencia: CAMS demo replay only — never scored', tVal - 0.2, 780)}

      {/* ── phase 2-4: NASA POWER test ── */}
      {t >= tN - 0.4 && (
        <div style={{position: 'absolute', left: 120, top: 46, ...appear(t, tN, 0.5)}}>
          <span style={{fontSize: 60, fontWeight: 800}}>NASA POWER test</span>
          <span style={{fontSize: 34, fontWeight: 700, color: '#9FB0C5', marginLeft: 28}}>held-out 2024–25 · exploratory</span>
        </div>
      )}
      {o2 > 0 && (
        <AbsoluteFill style={{opacity: o2}}>
          <div style={{position: 'absolute', left: 120, top: 138, fontSize: 30, fontWeight: 700, color: '#9FB0C5', opacity: ease(t, tN + 0.2, tN + 0.7)}}>
            14-day early warning vs the real trap onset · 10 seasons</div>
          <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}}>
            <rect x={xOf(28)} y={220} width={xOf(7) - xOf(28)} height={10 * 64 + 10} fill={TEAL} opacity={0.15 * ease(t, tEarly, tEarly + 0.6)} />
            <text x={(xOf(28) + xOf(7)) / 2} y={214} textAnchor="middle" fontSize={28} fontWeight={700} fill={TEAL} opacity={ease(t, tEarly, tEarly + 0.6)}>useful window</text>
            <line x1={ONSET_X} y1={220} x2={ONSET_X} y2={220 + 650 * ease(t, tFour, tFour + 0.5)} stroke="#fff" strokeWidth={3} />
            <text x={ONSET_X + 10} y={214} fontSize={28} fontWeight={700} fill="#fff" opacity={ease(t, tFour, tFour + 0.5)}>trap onset</text>
            <text x={450} y={910} fontSize={28} fontWeight={700} fill="#9FB0C5" opacity={ease(t, tFour, tFour + 0.5)}>← earlier</text>
            <text x={1390} y={910} textAnchor="end" fontSize={28} fontWeight={700} fill="#9FB0C5" opacity={ease(t, tFour, tFour + 0.5)}>later →</text>
            {SEASONS.map((s, i) => {
              const y = rowY(i) + 22, rowO = ease(t, tN + 0.3 + i * 0.06, tN + 0.3 + i * 0.06 + 0.3);
              const nIn = ease(t, tNasa + i * 0.08, tNasa + i * 0.08 + 0.25), nDim = s.nasa_hit ? 1 : 1 - 0.55 * ease(t, tUseful, tUseful + 0.4);
              const cIn = ease(t, tLast + i * 0.08, tLast + i * 0.08 + 0.25), cRing = s.cal_hit ? ease(t, tSixty, tSixty + 0.4) : 0;
              const cx = xOf(s.cal_lead);
              return (
                <g key={i} opacity={rowO}>
                  <text x={120} y={y + 10} fontSize={30} fontWeight={700} fill="#D5DEE8">{s.label}</text>
                  <line x1={440} y1={y} x2={1400} y2={y} stroke="#2B3648" strokeWidth={2} />
                  <circle cx={xOf(s.nasa_lead)} cy={y - 9} r={13} fill={NASA_BLUE} opacity={nIn * nDim}
                    stroke="#fff" strokeWidth={s.nasa_hit ? 4 * ease(t, tUseful, tUseful + 0.4) : 0} />
                  <rect x={cx - 11} y={y + 3} width={22} height={22} fill="#D5DEE8" opacity={cIn} transform={`rotate(45 ${cx} ${y + 14})`}
                    stroke="#fff" strokeWidth={4 * cRing} />
                </g>
              );
            })}
          </svg>
          {tile('NASA temperature clock', <svg width={26} height={26}><circle cx={13} cy={13} r={12} fill={NASA_BLUE} /></svg>, 30, tThirty, 240, NASA_BLUE)}
          {tile("Last year's calendar", <svg width={26} height={26}><rect x={5} y={5} width={16} height={16} fill="#D5DEE8" transform="rotate(45 13 13)" /></svg>, 60, tSixty, 570, '#D5DEE8')}
        </AbsoluteFill>
      )}
      {o3 > 0 && (
        <Glass style={{left: 120, top: 175, width: 1680, height: 345, opacity: o3}}>
          <div style={{position: 'absolute', left: 44, top: 26, fontSize: 36, fontWeight: 800}}>Alert score (CSI) · higher is better</div>
          {bar('API forecast alone', '0.382', 0.382 / 0.5, '#5A6672', tC + 0.4, 105)}
          {bar('+ NASA weather rule', '0.434', 0.434 / 0.5, NASA_BLUE, W7N('four', 1), 180)}
          {bar('Same rule, no NASA', '0.486', 0.486 / 0.5, C.accent, W7N('without'), 255)}
        </Glass>
      )}
      {o4 > 0 && (
        <div style={{position: 'absolute', left: 120, top: 170, width: 1680, height: 700, borderRadius: 18, background: '#fff', border: '3px solid #34415A', opacity: o4,
          boxShadow: '0 12px 30px rgba(0,0,0,0.35)'}}>
          <div style={{position: 'absolute', left: 40, top: 26, fontSize: 30, fontWeight: 700, color: C.muted}}>live page · NASA Layer: What We Tested</div>
          <Img src={staticFile('shots/s7_tile_csi.png')} style={{position: 'absolute', left: 160, top: 90, height: 380}} />
          <Img src={staticFile('shots/s7_tile_control.png')} style={{position: 'absolute', left: 1000, top: 90, height: 380}} />
          <div style={{position: 'absolute', left: 0, right: 0, top: 520, display: 'flex', justifyContent: 'center'}}>
            <div style={{position: 'relative', padding: 14, borderRadius: 16,
              boxShadow: `0 0 0 ${6 * ease(t, W7N('nothing'), W7N('nothing') + 0.4)}px ${C.accent}`}}>
              <Img src={staticFile('shots/s7_tile_verdict.png')} style={{display: 'block', height: 110}} />
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ───────── s8 · light · close on our measurement
export const S8: React.FC = () => {
  const t = useSec();
  const tZ = W('s8', 'zero'), tE = W('s8', 'eighty'), tN = W('s8', 'one'), tO = W('s8', 'open');
  const hero = (x: number, big: string, label: string, at: number, col: string) => (
    <div style={{position: 'absolute', left: x, top: 150, width: 560, height: 380, borderRadius: 24, background: '#fff', border: `4px solid ${col}`, fontFamily: SANS, textAlign: 'center',
      boxShadow: '0 16px 40px rgba(20,32,43,0.14)', ...appear(t, at, 0.5, 30)}}>
      <div style={{fontSize: 118, fontWeight: 800, color: col, lineHeight: 1, marginTop: 90, letterSpacing: -2, whiteSpace: 'nowrap'}}>{big}</div>
      <div style={{fontSize: 40, fontWeight: 700, color: C.ink, marginTop: 24}}>{label}</div>
    </div>
  );
  const kZ = ease(t, tE, tE + 1.2);
  return (
    <AbsoluteFill>
      {hero(64, '0', 'Unapproved Sends', tZ, C.accent)}
      {hero(680, `${fmt(89 * kZ)} / 200`, 'Blocked by Code', tE, CRIMSON)}
      {hero(1296, `${fmt(117 * ease(t, tN, tN + 1.0))} / 117`, 'Tests Green', tN, C.navy)}
      <div style={{position: 'absolute', left: 64, top: 570, padding: '14px 34px', borderRadius: 14, background: AMBER, color: '#1A1203', fontFamily: SANS, fontSize: 36, fontWeight: 800, ...appear(t, tO - 0.2, 0.5)}}>
        🔒 Claim Locked (R1 Lost)</div>
      <div style={{position: 'absolute', left: 64, right: 64, top: 690, padding: '22px 36px', borderRadius: 18, background: C.ink, color: '#fff', fontFamily: SANS, ...appear(t, tO - 0.3, 0.6)}}>
        <div style={{fontSize: 34, fontWeight: 700, color: '#9FB0C5'}}>863 events · 7,373 city-days</div>
        <div style={{fontSize: 44, fontWeight: 800, marginTop: 6, color: '#5EEAD4'}}>drahmed7887.github.io/hack-genhacks</div>
        <div style={{fontSize: 34, fontFamily: MONO, marginTop: 6}}>github.com/DrAhmed7887/hack-genhacks</div>
      </div>
    </AbsoluteFill>
  );
};
