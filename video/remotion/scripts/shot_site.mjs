// Full-page screenshots of demo/index.html at laptop and phone width (QC only).
import { chromium } from "playwright-core";
import path from "node:path";
import { fileURLToPath } from "node:url";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../../..");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const out = process.argv[2];
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
for (const [name, w] of [["laptop", 1280], ["phone", 390]]) {
  const page = await browser.newPage({ viewport: { width: w, height: 900 }, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(ROOT, "demo/index.html"), { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  const sw = await page.evaluate(() => document.documentElement.scrollWidth);
  console.log(name, "scrollWidth", sw);
  await page.screenshot({ path: `${out}/site_${name}.png`, fullPage: true });
}
await browser.close();
