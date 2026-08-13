#!/usr/bin/env node
// prompt.txt §3.4 — prove the parts-gallery mode actually exists on the exhibit route.
//
// A stage you cannot see is a stage that is not done, and the two ways this wiring has
// silently failed before are both checked here rather than eyeballed:
//   · the mode toggle is on the page and switching it remounts the viewer;
//   · the viewer exposes setExplode, without which ExhibitStage never renders the
//     explode control (`v-if="viewer?.setExplode"`) and §5.9 is untestable.
// Also loads the ?part=&view= review harness that replaced head-capture-harness.vue.
//
//   node tools/verify_cloud_gallery.mjs
//
// Exit 0 clean, 1 on any failed check, with the console errors printed.
import { spawn } from "node:child_process";
import { chromium } from "playwright";

const ROOT = new URL("..", import.meta.url).pathname.replace(/\/$/, "");
const BASE = "/img2three-art-exhibition";
const SLUG = "ff7-cloud-strife-polygon-figure";
const PORT = 3179;
const origin = `http://localhost:${PORT}`;

const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
  cwd: ROOT,
  stdio: ["ignore", "pipe", "pipe"],
});
let log = "";
server.stdout.on("data", (c) => (log += c));
server.stderr.on("data", (c) => (log += c));

const waitForServer = async () => {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(`${origin}${BASE}/`)).ok) return;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`dev server not ready\n${log}`);
};

const fails = [];
const check = (ok, label) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) fails.push(label);
};

let chrome = null;
try {
  await waitForServer();
  chrome = await chromium.launch();
  const page = await chrome.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(`${origin}${BASE}/${SLUG}#controls`, { waitUntil: "networkidle" });
  await page.waitForSelector("canvas", { timeout: 15_000 });

  const chips = await page.locator(".panel-row .chip").allTextContents();
  check(
    chips.some((t) => /Parts gallery/i.test(t)),
    `the Stage toggle offers a parts gallery (chips: ${JSON.stringify(chips)})`,
  );
  check(
    chips.some((t) => /Stage 1 parts/i.test(t)),
    "the panel states how many Stage 1 parts are built",
  );

  // Switching modes must rebuild the viewer, not just flip a label.
  await page.getByRole("button", { name: "Assembled" }).click();
  await page.waitForTimeout(400);
  await page.getByRole("button", { name: "Parts gallery" }).click();
  await page.waitForTimeout(400);
  check(await page.locator("canvas").isVisible(), "the canvas survives a mode switch");

  const explodeVisible = await page.locator("button.btn-explode").count();
  check(explodeVisible > 0, "ExhibitStage renders the explode control (setExplode is forwarded)");

  // Optional: `node tools/verify_cloud_gallery.mjs <out.png>` leaves one frame behind to
  // look at. Throwaway evidence — write it to a scratch dir, never into the repo.
  if (process.argv[2]) await page.screenshot({ path: process.argv[2] });

  // The review harness that replaced head-capture-harness.vue.
  await page.goto(`${origin}${BASE}/${SLUG}?view=front&mode=gallery`, {
    waitUntil: "networkidle",
  });
  await page.waitForTimeout(800);
  const info = await page.evaluate(() => window.__partInfo ?? null);
  check(info !== null, `?view= publishes window.__partInfo (${JSON.stringify(info)})`);
  check(info?.view === "front", "__partInfo records the requested view rather than a default");

  check(errors.length === 0, `no console errors (${errors.length})`);
  for (const e of errors) console.log(`   ${e}`);
} finally {
  await chrome?.close();
  server.kill("SIGTERM");
}

console.log(fails.length ? `\n${fails.length} check(s) failed` : "\nall checks passed");
process.exit(fails.length ? 1 : 0);
