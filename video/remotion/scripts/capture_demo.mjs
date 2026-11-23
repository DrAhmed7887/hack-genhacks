// Real-app interaction test + stills for the PollenPlan film.
// Serves demo/ over python http.server, drives it with Chrome, fails on any console/page error.
// Output: ../public/shots/*.png (fullPage, 1920 wide, DSF 1) + boxes.json (same schema as hack-ai-for-medicine).
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..", "..");
const OUT = path.resolve(HERE, "..", "public", "shots");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 8765;
const URL = `http://127.0.0.1:${PORT}/index.html`;
fs.mkdirSync(OUT, { recursive: true });

const srv = spawn("python3", ["-m", "http.server", String(PORT), "--bind", "127.0.0.1", "--directory", path.join(ROOT, "demo")], { stdio: ["ignore", "ignore", fs.openSync("/tmp/capture_srv.log", "w")] });
const errors = [];
const failures = [];
const check = (name, ok, detail = "") => { console.log(`${ok ? "PASS" : "FAIL"} ${name} ${detail}`); if (!ok) failures.push(name); };
const boxes = {};

try {
  await new Promise(r => setTimeout(r, 1200));
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, reducedMotion: "reduce" });
  const page = await ctx.newPage();
  page.on("console", m => { if (m.type() === "error") errors.push("console: " + m.text()); });
  page.on("pageerror", e => errors.push("pageerror: " + e.message));
  page.on("response", r => { if (r.status() >= 400) errors.push("http " + r.status() + " " + r.url()); });
  page.on("requestfailed", r => errors.push("requestfailed: " + r.url()));

  const open = async () => {
    await page.goto(URL, { waitUntil: "load" });
    await page.addStyleTag({ content: "html{scrollbar-width:none}html::-webkit-scrollbar{display:none}*{caret-color:transparent}" });
    await page.evaluate(() => window.scrollTo(0, 0));
  };
  const txt = sel => page.locator(sel).innerText();
  const box = async sel => { const b = await page.locator(sel).first().boundingBox(); // page coords (scrollY=0 at capture)
    const sy = await page.evaluate(() => window.scrollY);
    return { x: Math.round(b.x), y: Math.round(b.y + sy), w: Math.round(b.width), h: Math.round(b.height) }; };
  const shoot = async (name, targets) => {
    await page.evaluate(() => window.scrollTo(0, 0));
    const t = {};
    for (const [k, sel] of Object.entries(targets)) t[k] = await box(sel);
    await page.screenshot({ path: path.join(OUT, name + ".png"), fullPage: true });
    const dims = await page.evaluate(() => ({ w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight }));
    boxes[name] = { ...dims, targets: t };
    console.log("shot", name, dims.w + "x" + dims.h);
  };

  // 1. Valencia control
  await open();
  check("valencia: drafted == 0", (await txt("#kpi-eligible")) === "0", await txt("#kpi-eligible"));
  check("valencia: trigger rule visible", await page.locator("#nurse-trigger-rule").isVisible());
  check("valencia: caveat visible", await page.locator("#nurse-caveat").isVisible());
  const scen = await page.locator("#replay-scenario-select option").allTextContents();
  check("valencia: initial scenario label", /Valencia/.test(scen[0]) && /2025-05-28/.test(scen[0]), scen[0]);
  await shoot("s2_valencia_control", { console: "#nurse-console", select: "#replay-scenario-select", kpi_drafted: "#kpi-eligible", kpi_filtered: "#kpi-filtered", trigger: "#nurse-trigger-rule", caveat: "#nurse-caveat", kpis: ".nc-kpis", nasa_panel: "#nasa-telemetry-panel" });

  // 2. Madrid grass
  await page.selectOption("#replay-scenario-select", "madrid_grass");
  check("madrid_grass: drafted == 111", (await txt("#kpi-eligible")) === "111", await txt("#kpi-eligible"));
  check("madrid_grass: blocked == 89", (await txt("#kpi-filtered")) === "89", await txt("#kpi-filtered"));
  check("madrid_grass: sent == 0", (await txt("#kpi-sent")) === "0");
  await shoot("s2_madrid_grass", { console: "#nurse-console", select: "#replay-scenario-select", kpi_drafted: "#kpi-eligible", kpi_filtered: "#kpi-filtered", kpi_sent: "#kpi-sent", trigger: "#nurse-trigger-rule", draft_table: "#nurse-draft-table", approve: "#approve-batch-btn", kpis: ".nc-kpis", nasa_panel: "#nasa-telemetry-panel" });

  // 3. Approve
  await page.click("#approve-batch-btn");
  const log = await txt("#nurse-audit-log");
  check("approve: ISO timestamp in audit log", /approved_at \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z/.test(log));
  check("approve: '0 external messages sent'", log.includes("0 external messages sent"));
  check("approve: button frozen", await page.locator("#approve-batch-btn").isDisabled());
  await shoot("s2_madrid_approved", { console: "#nurse-console", approve: "#approve-batch-btn", status: "#approve-status", audit: "#nurse-audit-log", kpi_sent: "#kpi-sent", kpis: ".nc-kpis" });

  // 4. Blocked guard (clean reload)
  await open();
  await page.selectOption("#replay-scenario-select", "madrid_grass");
  await page.click("#toggle-filtered-btn");
  const panel = await txt("#nurse-filtered-panel");
  check("guard: panel visible", await page.locator("#nurse-filtered-panel").isVisible());
  check("guard: 34 no med", /\b34 sensitised but med_on_file = none/.test(panel), panel);
  check("guard: 55 not sensitised", /\b55 not sensitised/.test(panel));
  const rows = await page.locator("#nurse-draft-table-body tr").count();
  check("guard: draft rows present", rows > 0, `rows=${rows}`);
  await shoot("s6_blocked_guard", { console: "#nurse-console", toggle: "#toggle-filtered-btn", panel: "#nurse-filtered-panel", first_row: "#nurse-draft-table-body tr:first-child", draft_table: "#nurse-draft-table", kpis: ".nc-kpis" });

  // 5. Onset + results tables, smooth scroll
  await open();
  const onsetRows = await page.locator("#onset-table-body tr").count();
  const resRows = await page.locator("#results-table-body tr").count();
  check("onset table: 28 seasons", onsetRows === 28, `rows=${onsetRows}`);
  check("results table populated", resRows > 0, `rows=${resRows}`);
  check("overall verdict present", (await txt("#overall-verdict")).trim().length > 0, (await txt("#overall-verdict")).slice(0, 80));
  await page.locator("#onset-table-body").scrollIntoViewIfNeeded();
  await page.evaluate(async () => { const el = document.getElementById("results-table-body"); el.scrollIntoView({ behavior: "smooth", block: "center" }); await new Promise(r => setTimeout(r, 900)); });
  await shoot("s4_onset_table", { onset: "#onset-table-body", results: "#results-table-body", verdict: "#overall-verdict", caption: "#threshold-caption" });

  // 6. NASA evaluation + headline metrics (V4, 23 Nov 2026)
  await open();
  check("metrics: 7,373 city-days", (await txt("#total-days")).trim() === "7373", await txt("#total-days"));
  check("metrics: P2 recall 0.416", (await txt("#p2-recall")).trim() === "0.416", await txt("#p2-recall"));
  const note = await txt("#nasa-control-note");
  check("nasa: control note says no", /Does NASA add skill\?\s*no/i.test(note), note.slice(0, 60));
  await shoot("s7_nasa_eval", { summary: "#nasa-eval-summary", note: "#nasa-control-note", days: "#total-days", recall: "#p2-recall", events: "#total-events" });

  // 7. Crisp element captures of the live NASA verdict tiles (DSF 2) for the s7n close
  const ctx2 = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  const p2 = await ctx2.newPage();
  p2.on("pageerror", e => errors.push("pageerror: " + e.message));
  await p2.goto(URL, { waitUntil: "load" });
  const cards = p2.locator("#nasa-eval-summary .ne-card");
  check("nasa tiles: CSI tile first", /0\.382 → 0\.434/.test(await cards.nth(0).innerText()));
  check("nasa tiles: control tile", /0\.486/.test(await p2.locator("#nasa-eval-summary .ne-card.bad").innerText()));
  await cards.nth(0).screenshot({ path: path.join(OUT, "s7_tile_csi.png") });
  await p2.locator("#nasa-eval-summary .ne-card.bad").screenshot({ path: path.join(OUT, "s7_tile_control.png") });
  await p2.locator("#nasa-control-note").screenshot({ path: path.join(OUT, "s7_tile_note.png") });
  // first sentence only ("Does NASA add skill? no."), cropped so it can be shown at >= 28 px
  const nb = await p2.locator("#nasa-control-note").boundingBox();
  await p2.screenshot({ path: path.join(OUT, "s7_tile_verdict.png"), clip: { x: nb.x, y: nb.y, width: 169, height: 24 } });
  await ctx2.close();

  await browser.close();
  fs.writeFileSync(path.join(OUT, "boxes.json"), JSON.stringify(boxes, null, 1));
  // Chrome auto-requests /favicon.ico (demo has no <link rel=icon>): its 404 shows as a generic console error.
  // Allow that one only if the server log proves every 404 was the favicon.
  const notFound = fs.readFileSync("/tmp/capture_srv.log", "utf8").split("\n").filter(l => /" 404 /.test(l));
  const onlyFavicon = notFound.every(l => l.includes("GET /favicon.ico"));
  check("server 404s are favicon only", onlyFavicon, `${notFound.length} x 404`);
  const real = errors.filter(e => !(onlyFavicon && /^console: Failed to load resource: .*404/.test(e)));
  check("zero console/page errors", real.length === 0, real.join(" | "));
} catch (e) {
  console.error("SCRIPT ERROR", e); failures.push("script");
} finally {
  srv.kill();
}
console.log(failures.length ? `FAILED: ${failures.join(", ")}` : "ALL PASS");
process.exit(failures.length ? 1 : 0);
