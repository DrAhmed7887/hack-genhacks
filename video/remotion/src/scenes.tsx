import React from 'react';
import {AbsoluteFill, Loop, OffthreadVideo, staticFile} from 'remotion';
import timeline from './timeline.json';
import {AMBER, CRIMSON, C, FPS, MONO, SANS} from './theme';
import {Cursor, FrameCtx, Hi, Shot, W, appear, box, countTo, ease, fadeIn, pop, useSec, window_} from './ui';

const b = box;
const ctr = (r: {x: number; y: number; w: number; h: number}) => [r.x + r.w / 2, r.y + r.h / 2] as const;
const DUR5A = timeline.scenes.find((s) => s.id === 's5a')!.dur;
const W5B = (p: string, n = 0) => DUR5A + W('s5b', p, n);
const fmt = (n: number) => Math.round(n).toLocaleString('en-US');

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
      <div style={{position: 'absolute', left: 64, top: 56, padding: '10px 22px', borderRadius: 999, background: 'rgba(15,118,110,0.92)', color: '#fff',
        fontFamily: SANS, fontSize: 26, fontWeight: 700, letterSpacing: 0.5, opacity: fadeIn(t, 0.3)}}>Procedural 3D Visual</div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 330, textAlign: 'center', fontFamily: SANS, color: '#fff'}}>
        <div style={{fontSize: 128, fontWeight: 800, letterSpacing: -2, lineHeight: 1.05, ...appear(t, 0.5, 0.7, 40)}}>SPRAYS START TOO LATE?</div>
        <div style={{fontSize: 40, fontWeight: 400, color: '#D5DEE8', marginTop: 34, ...appear(t, W('s1', 'already'), 0.6)}}>
          Already-prescribed nasal sprays · Frozen rules vs raw weather API</div>
      </div>
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
  return (
    <AbsoluteFill>
      <Shot shot="s2_valencia_control" layers={[['s2_valencia_control', 0], ['s2_madrid_grass', tSw + 0.6], ['s2_madrid_approved', tA + 0.9]]} t={t}
        keys={[[0, 960, 1000, 1.2], [tV - 0.4, 960, 1090, 1.55], [tSw - 0.6, 960, 1090, 1.55], [tSw + 0.6, 960, 1100, 1.55], [tN - 0.8, 960, 1100, 1.55],
          [tA - 0.9, 700, 1500, 1.5], [tA, ax + 200, ay - 20, 1.6], [tA + 1.8, lx, ly - 40, 1.6]]}>
        <Hi r={b('s2_valencia_control', 'caveat')} t={t} at={tV} until={tSw - 0.4} dim={false} color={C.warn} />
        <Hi r={{x: 690, y: 1031, w: 828, h: 51}} t={t} at={tH - 0.4} until={tN - 1.0} dim={false} />
        <Cursor t={t} keys={[[tA - 1.0, ax + 420, ay + 160], [tA - 0.1, ax, ay]]} clicks={[tA]} />
        <Hi r={b('s2_madrid_approved', 'audit')} t={t} at={tB + 0.3} pad={8} />
      </Shot>
      <Chip t={t} at={0.4} until={tSw - 0.3} style={{left: 48, bottom: 155}}>Valencia control: 0 drafted</Chip>
      <Chip t={t} at={tSw + 0.2} until={tA - 0.3} bg={C.accent} style={{left: 48, bottom: 155}}>Madrid grass: 42.1 ≥ 35 · 111 drafted / 89 blocked</Chip>
      <Chip t={t} at={tA + 0.3} bg={C.navy} style={{left: 48, bottom: 155}}>Approved → audit log timestamp</Chip>
      <Chip t={t} at={tA + 0.9} bg={C.warn} style={{right: 48, bottom: 225}}>Demo mode: 0 sent externally</Chip>
    </AbsoluteFill>
  );
};

// ───────── s3 · dark · grid vs traps
export const S3: React.FC = () => {
  const t = useSec();
  const tPeople = W('s3', 'people'), tWe = W('s3', 'we'), tMad = W('s3', 'madrid'), tFive = W('s3', 'five'), tEight = W('s3', 'eight');
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
      {counter(64, `${fmt(countTo(t, tEight, tEight + 1.6, 8076))}`, 'city-days', tEight - 0.2)}
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

// ───────── s5 · dark · proof + silent hold (spans s5a + s5b)
export const S5: React.FC = () => {
  const t = useSec();
  const tApi = W('s5a', 'api'), tOur = W('s5a', 'our'), tIt = W('s5a', 'it'), tSo = W5B('so');
  const card = (x: number, title: string, big: number, n: number, at: number, col: string) => {
    const k = ease(t, at, at + 1.4);
    return (
      <Glass style={{left: x, top: 150, width: 860, height: 400, padding: '30px 40px', borderColor: col, ...appear(t, 0.2, 0.5)}}>
        <div style={{fontSize: 40, fontWeight: 700, color: '#C5D1E0'}}>{title}</div>
        <div style={{fontSize: 190, fontWeight: 800, color: col, lineHeight: 1.05, letterSpacing: -4, marginTop: 6}}>{(big * k).toFixed(1)}%</div>
        <div style={{fontSize: 40, fontWeight: 700, marginTop: 4}}>({fmt(n * k)} / 863)</div>
        <div style={{height: 14, borderRadius: 7, background: '#2B3648', marginTop: 24}}><div style={{height: 14, borderRadius: 7, width: `${big * k}%`, background: col}} /></div>
      </Glass>
    );
  };
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 64, top: 52, fontFamily: SANS, fontSize: 34, fontWeight: 700, color: '#9FB0C5', ...appear(t, 0.2)}}>
        863 high-pollen events · 8,076 city-days · frozen in DATA_PLAN.md before scoring</div>
      {card(64, 'API Forecast (P2)', 41.6, 359, tApi, '#5EEAD4')}
      {card(996, 'Our Rule (R1)', 41.0, 354, tOur, '#93C5FD')}
      {(() => {
        const k = pop(t, tIt);
        return (
          <div style={{position: 'absolute', left: 300, top: 600, width: 1320, padding: '26px 44px', borderRadius: 20, background: AMBER, color: '#1A1203', fontFamily: SANS,
            opacity: Math.min(1, k * 2), transform: `scale(${0.85 + 0.15 * Math.min(1.1, k)}) rotate(${(1 - Math.min(1, k)) * -3}deg)`, boxShadow: '0 16px 40px rgba(217,119,6,0.35)'}}>
            <div style={{fontSize: 50, fontWeight: 800}}>🔒 Claim locked: no “beats the API”</div>
            <div style={{fontSize: 30, fontWeight: 700, marginTop: 6, color: '#3B2603'}}>Frozen in DATA_PLAN.md · 22 Nov 2026</div>
          </div>
        );
      })()}
      <div style={{position: 'absolute', left: 160, top: 826, width: 1600, padding: '20px 36px', borderRadius: 999, background: '#0F766E', color: '#fff', fontFamily: SANS,
        fontSize: 38, fontWeight: 800, textAlign: 'center', ...appear(t, tSo, 0.6, 20)}}>So the app uses API forecast P2 — our work went into delivery</div>
    </AbsoluteFill>
  );
};

// ───────── s6 · light · concrete refusal row
export const S6: React.FC = () => {
  const t = useSec();
  const tT = W('s6', 'thirty'), tE = W('s6', 'each'), tN = W('s6', 'not'), tC = tT - 0.9;
  const [px, py] = ctr(b('s6_blocked_guard', 'panel'));
  const [rx, ry] = ctr(b('s6_blocked_guard', 'first_row'));
  return (
    <AbsoluteFill>
      <Shot shot="s6_blocked_guard" t={t}
        keys={[[0, 960, 1180, 1.1], [tC - 0.6, 960, 1180, 1.1], [tC + 0.6, px, py + 40, 1.6], [tE - 1.0, px, py + 40, 1.6], [tE, rx, ry - 20, 1.6]]}>
        <Hi r={b('s6_blocked_guard', 'panel')} t={t} at={tT} until={tE - 0.3} color={CRIMSON} pad={8} />
        <Hi r={b('s6_blocked_guard', 'first_row')} t={t} at={tE + 0.5} pad={8} />
      </Shot>
      <Chip t={t} at={tT - 0.2} bg={CRIMSON} style={{left: 48, bottom: 225, fontSize: 32}}>34 no medicine on file · 55 not sensitised = 89 blocked</Chip>
      <Chip t={t} at={tE + 0.3} bg={C.ink} style={{right: 48, bottom: 225, fontSize: 30}}>P001 · “your intranasal steroid spray” only</Chip>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 155, display: 'flex', justifyContent: 'center', opacity: fadeIn(t, tN - 0.2)}}>
        <div style={{padding: '12px 30px', borderRadius: 999, background: C.accent, color: '#fff', fontFamily: SANS, fontSize: 32, fontWeight: 700}}>
          Thresholds signed 22 Nov 2026 · Not a medical device</div>
      </div>
    </AbsoluteFill>
  );
};

// ───────── s7 · dark · honest limits
export const S7: React.FC = () => {
  const t = useSec();
  const rows: [string, string, number][] = [
    ['1', 'Madrid API P2 recall: 13.6% olive / 31.4% grass (below 50% bar)', W('s7', 'honest') + 0.4],
    ['2', 'R2 pre-peak lead (+2.88d) reflects 3-day forecast look-ahead, not beating C0 (−1.55d)', W('s7', 'pre-peak') - 0.2],
    ['3', 'Valencia: CAMS demo replay only — never scored', W('s7', 'valencia') - 0.2],
  ];
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 120, top: 70, fontFamily: SANS, fontSize: 64, fontWeight: 800, color: '#fff', ...appear(t, 0.2)}}>Honest limits</div>
      {rows.map(([n, txt, at], i) => (
        <Glass key={i} style={{left: 120, top: 210 + i * 220, width: 1680, height: 180, display: 'flex', alignItems: 'center', gap: 36, padding: '0 44px', borderColor: i === 0 ? AMBER : '#34415A', ...appear(t, 0.3 + i * 0.2, 0.5, 20)}}>
          <div style={{flex: '0 0 84px', height: 84, borderRadius: 42, background: AMBER, color: '#1A1203', fontSize: 48, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{n}</div>
          <div style={{fontSize: 42, fontWeight: 700, lineHeight: 1.25, opacity: ease(t, at, at + 0.5, 0.25, 1)}}>{txt}</div>
        </Glass>
      ))}
    </AbsoluteFill>
  );
};

// ───────── s8 · light · close on our measurement
export const S8: React.FC = () => {
  const t = useSec();
  const tZ = W('s8', 'zero'), tE = W('s8', 'eighty'), tN = W('s8', 'ninety'), tO = W('s8', 'open');
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
      {hero(1296, `${fmt(95 * ease(t, tN, tN + 1.0))} / 95`, 'Tests Green', tN, C.navy)}
      <div style={{position: 'absolute', left: 64, top: 570, padding: '14px 34px', borderRadius: 14, background: AMBER, color: '#1A1203', fontFamily: SANS, fontSize: 36, fontWeight: 800, ...appear(t, tN + 0.8, 0.5)}}>
        🔒 Claim Locked (R1 Lost)</div>
      <div style={{position: 'absolute', left: 64, right: 64, top: 690, padding: '22px 36px', borderRadius: 18, background: C.ink, color: '#fff', fontFamily: SANS, ...appear(t, tO - 0.3, 0.6)}}>
        <div style={{fontSize: 34, fontWeight: 700, color: '#9FB0C5'}}>863 events · 8,076 city-days</div>
        <div style={{fontSize: 44, fontWeight: 800, marginTop: 6, color: '#5EEAD4'}}>drahmed7887.github.io/hack-genhacks</div>
        <div style={{fontSize: 34, fontFamily: MONO, marginTop: 6}}>github.com/DrAhmed7887/hack-genhacks</div>
      </div>
    </AbsoluteFill>
  );
};
