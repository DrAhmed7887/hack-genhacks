// V5 capture: real screens of demo/index.html, element by element, at 3x for clean zooms.
// Usage: node video/v5/capture.mjs [outDir]   (default video/remotion/public/v5/shots)
// Writes <name>.png plus shots.json with each element's css size, so scenes can place crops exactly.
import { chromium } from '../node_modules/playwright-core/index.mjs';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const out = path.resolve(process.argv[2] || path.join(root, 'video/remotion/public/v5/shots'));
fs.mkdirSync(out, { recursive: true });
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const SCALE = 3;
const url = (q = '') => 'file://' + path.join(root, 'demo/index.html') + q;

// [name, query string, selector, optional action before the shot]
const SHOTS = [
  ['headline', '', '#headline'],
  ['season_card', '?cell=madrid/grass', '#season .card'],
  ['season', '?cell=madrid/grass', '#season'],
  ['morning_head', '', '#morning > h2'],
  ['morning_cards', '', '#morning .morning'],
  ['step_trap', '', '#morning .step:nth-child(1)'],
  ['step_cams', '', '#morning .step:nth-child(2)'],
  ['step_obs', '', '#morning .step:nth-child(3)'],
  ['console_bar', '', '#morning .console .bar'],
  ['console', '', '#morning .console'],
  ['draft_first', '', '#drafts > :first-child'],
  ['drafts_row1', '', '#drafts'],
  ['approve_btn', '', '#approve'],
  ['console_after_click', '', '#morning .console', async (p) => { await p.click('#approve'); await p.waitForTimeout(500); }],
  ['approve_after', '', '#approve', async (p) => { await p.click('#approve'); await p.waitForTimeout(300); }],
  ['safety', '', '#safety'],
  ['safety_table', '', '#safety table'],
  ['tests', '', '#tests'],
  ['tests_table', '', '#tests table'],
  ['where', '', '#where'],
];

// text phrases and row selectors whose boxes (css px, relative to the shot) are saved for callouts
const RECTS = {
  season_card: {text: ['High day', 'Trap', 'Forecast', 'trap 29/36']},
  draft_first: {text: ['your intranasal steroid spray', 'Grass pollen measured', 'Pollen levels do not diagnose anything.'], blocks: ['Pollen levels do not diagnose anything.', 'Grass pollen measured']},
  console_bar: {text: ['Nurse copilot · 111 of 200 synthetic patients, highest risk first', 'Nothing is sent from this page.']},
  console_after_click: {text: ['Approve all 111']},
  safety_table: {rows: 'tr'},
  tests_table: {rows: 'tr'},
};

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: SCALE });
const page = await ctx.newPage();
const meta = {};
for (const [name, q, sel, act] of SHOTS) {
  await page.goto(url(q), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  const el = await page.$(sel);
  if (!el) { console.log('MISSING', name, sel); continue; }
  await el.scrollIntoViewIfNeeded();
  if (act) await act(page);
  const box = await el.boundingBox();
  const spec = RECTS[name];
  const rects = spec ? await el.evaluate((root, spec) => {
    const R = root.getBoundingClientRect();
    const rel = (r) => ({x: Math.round(r.left - R.left), y: Math.round(r.top - R.top), w: Math.round(r.width), h: Math.round(r.height)});
    const out = {};
    const walk = (needle) => {
      const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      for (let n = tw.nextNode(); n; n = tw.nextNode()) {
        const i = n.textContent.indexOf(needle);
        if (i >= 0) return {node: n, i};
      }
      return null;
    };
    for (const t of spec.text || []) {
      const hit = walk(t);
      if (!hit) { out[t] = null; continue; }
      const r = document.createRange();
      r.setStart(hit.node, hit.i); r.setEnd(hit.node, hit.i + t.length);
      out[t] = rel(r.getBoundingClientRect());
    }
    for (const t of spec.blocks || []) {
      const hit = walk(t);
      out['block:' + t] = hit ? rel(hit.node.parentElement.getBoundingClientRect()) : null;
    }
    if (spec.rows) out.rows = [...root.querySelectorAll(spec.rows)].map((e) => ({...rel(e.getBoundingClientRect()), text: e.innerText.slice(0, 60)}));
    return out;
  }, spec) : undefined;
  await el.screenshot({ path: path.join(out, name + '.png') });
  meta[name] = { selector: sel, query: q, cssW: Math.round(box.width), cssH: Math.round(box.height), scale: SCALE, rects };
  console.log(name.padEnd(20), sel.padEnd(30), meta[name].cssW + 'x' + meta[name].cssH);
}
fs.writeFileSync(path.join(out, 'shots.json'), JSON.stringify(meta, null, 1));
await browser.close();
