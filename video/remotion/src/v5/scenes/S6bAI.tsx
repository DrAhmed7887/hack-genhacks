import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C, D, F, cue, scene} from '../theme';
import {Count, Mono, Paper, Shot, Title, ramp} from '../ui';
import {Callout} from './S6Nurse';
import shots from '../../../public/v5/shots/shots.json';

const s = scene('s6b');
const DR = shots.draft_first.rects;
const ROWS = shots.safety_table.rects.rows;
const RT = D.redTeam;

const Strike: React.FC<{at: number; children: React.ReactNode}> = ({at, children}) => {
  const f = useCurrentFrame();
  const o = ramp(f, at, at + 8);
  const k = ramp(f, at + 6, at + 14);
  return (
    <div style={{position: 'relative', display: 'inline-block', opacity: o, marginRight: 18, marginBottom: 14, padding: '10px 22px', borderRadius: 999,
      border: `2px solid ${C.ink}`, fontSize: 34, fontWeight: 700, background: C.card}}>
      {children}
      <div style={{position: 'absolute', left: 14, right: 14, top: '50%', height: 4, background: C.red, transform: `scaleX(${k})`, transformOrigin: 'left'}} />
    </div>
  );
};

export const S6bAI: React.FC = () => {
  const f = useCurrentFrame();
  const kAI = cue(s, 'ai', 0, -0.2);
  const kCode = cue(s, 'code', 0, -0.1);
  const kDose = cue(s, 'dose', 0, -0.15);
  const kDrug = cue(s, 'drug', 0, -0.15);
  const kSym = cue(s, 'symptom', 0, -0.15);
  const kAdded = cue(s, 'added', 0, -0.1);
  const kWe = cue(s, 'we', 0, -0.25);
  const kBroke = cue(s, 'the', 2, -0.25);
  if (f < kWe) {
    const Z = 2.05, X = 200, Y = 116;
    const RX = X + shots.draft_first.cssW * Z + 10;
    const ai = DR['block:Grass pollen measured'];
    const safety = DR['block:Pollen levels do not diagnose anything.'];
    return (
      <Paper>
        <Shot name="draft_first" x={X} y={Y} zoom={Z} />
        <div style={{position: 'absolute', left: X - 22, top: Y + ai.y * Z, width: 8, height: ai.h * Z * ramp(f, kAI, kAI + 12), background: C.ink, borderRadius: 4}} />
        <Callout at={kAI} x1={RX} y1={Y + (ai.y + ai.h / 2) * Z} x2={990} y2={Y + (ai.y + ai.h / 2) * Z}>
          an AI model writes this
        </Callout>
        <div style={{position: 'absolute', left: 990, top: Y + (ai.y + ai.h / 2) * Z + 34, fontSize: 32, color: C.ink2, opacity: ramp(f, kCode, kCode + 10)}}>
          code checks every word against an approved list
        </div>
        <div style={{position: 'absolute', left: 990, top: 440, width: 860}}>
          <Strike at={kDose}>dose</Strike>
          <Strike at={kDrug}>drug name</Strike>
          <Strike at={kSym}>symptom advice</Strike>
        </div>
        <div style={{position: 'absolute', left: X - 22, top: Y + safety.y * Z, width: 8, height: safety.h * Z * ramp(f, kAdded, kAdded + 14), background: C.green, borderRadius: 4}} />
        <Callout at={kAdded} color={C.green} x1={RX} y1={Y + (safety.y + safety.h * 0.75) * Z} x2={990} y2={Y + (safety.y + safety.h * 0.75) * Z}>
          signed safety lines:<br />added by code, not the model
        </Callout>
      </Paper>
    );
  }
  if (f < kBroke) {
    const Z = 1.86;
    const head = ROWS[0];
    const held = ROWS.filter((r) => r.text.includes('(held out)')).slice(0, 3);
    const y0 = held[0].y, y1 = held[held.length - 1].y + held[held.length - 1].h;
    return (
      <Paper>
        <Title text="We attacked our own AI" />
        <Shot name="safety_table" x={960 - (head.w * Z) / 2} y={220} zoom={Z} crop={{x: 0, y: head.y, w: head.w, h: head.h}} shadow={false} />
        <Shot name="safety_table" x={960 - (head.w * Z) / 2} y={220 + head.h * Z} zoom={Z} crop={{x: 0, y: y0, w: head.w, h: y1 - y0}} shadow={false} />
        <div style={{position: 'absolute', left: 64, top: 230 + (head.h + y1 - y0) * Z + 20, fontSize: 28, color: C.ink2}}>
          rows from the held-out attack table on the demo page
        </div>
      </Paper>
    );
  }
  const k40 = cue(s, 'the', 2, -0.25);
  const k21 = cue(s, 'twenty-four', 0, -0.1);
  const k0 = cue(s, 'none', 0, -0.1);
  const big = (n: number, at: number, label: string, size: number) => (
    <div style={{opacity: ramp(f, at, at + 8), textAlign: 'center', width: 520}}>
      <Mono style={{fontSize: size, fontWeight: 700, letterSpacing: -4, lineHeight: 1}}><Count to={n} a={at} b={at + 12} /></Mono>
      <div style={{fontSize: 36, fontWeight: 600, color: C.ink2, marginTop: 18}}>{label}</div>
    </div>
  );
  return (
    <Paper>
      <Title text="Held-out attacks" sub="new attacks, never used to tune the gate" />
      <div style={{position: 'absolute', left: 100, right: 100, top: 360, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
        {big(RT.n, k40, 'held-out attacks', 170)}
        {big(RT.broke, k21, 'times the model broke a rule', 170)}
        {big(RT.reached, k0, 'reached the nurse', 250)}
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 800, textAlign: 'center', fontFamily: F.mono, fontSize: 28, color: C.ink2,
        opacity: ramp(f, k0 + 20, k0 + 30)}}>eval/results/ai_layer.json · red_team_heldout</div>
    </Paper>
  );
};
