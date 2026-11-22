// Capture real demo stills for the PollenPlan film. Output: film/assets/shots/*.png
// Honest frames only: screenshots of demo/index.html as it ships, no mock UI.
import { chromium } from "playwright-core";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DEMO = "file://" + path.join(HERE, "..", "demo", "index.html");
const OUT = path.join(HERE, "film", "assets", "shots");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(DEMO);
await page.addStyleTag({ content: "html{scrollbar-width:none}html::-webkit-scrollbar{display:none}*{caret-color:transparent}" });

await page.screenshot({ path: path.join(OUT, "shot_top.png") }); // headline + verdict (frame 1)

const shots = [
  ["#headline", "shot_headline.png"],
  ["#results-table-body", "shot_ptable.png"],
  ["#onset-table-body", "shot_onset.png"],
  ["#madrid-both-below", "shot_madrid.png"],
  ["#overall-verdict", "shot_verdict.png"],
  [".metrics-grid", "shot_metrics.png"],
];
for (const [sel, file] of shots) {
  const el = await page.$(sel);
  if (!el) throw new Error("missing " + sel);
  await el.scrollIntoViewIfNeeded();
  await el.screenshot({ path: path.join(OUT, file) });
  console.log("shot", file);
}
await browser.close();
console.log("done");
