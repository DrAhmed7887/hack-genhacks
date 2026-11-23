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
  ['safety', '', '#safety'],
  ['safety_table', '', '#safety table'],
  ['tests', '', '#tests'],
  ['tests_table', '', '#tests table'],
  ['where', '', '#where'],
];

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
  await el.screenshot({ path: path.join(out, name + '.png') });
  meta[name] = { selector: sel, query: q, cssW: Math.round(box.width), cssH: Math.round(box.height), scale: SCALE };
  console.log(name.padEnd(20), sel.padEnd(30), meta[name].cssW + 'x' + meta[name].cssH);
}
fs.writeFileSync(path.join(out, 'shots.json'), JSON.stringify(meta, null, 1));
await browser.close();
