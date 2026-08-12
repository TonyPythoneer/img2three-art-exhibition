#!/usr/bin/env node
// Verify the Ultima Weapon V2 exhibit end to end: it has a card on the entry site, that card
// links to its own route, and the route mounts a live viewer whose controls all drive it.
import { spawn } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const ROOT = "/Users/tonyyang/git/personal/img2three-art-exhibition";
const BASE = "/img2three-art-exhibition";
const SLUG = "ff7-cloud-strife-ultima-weapon";
const PORT = 3178;
const origin = `http://localhost:${PORT}`;
const OUT = `${ROOT}/artifacts/ultima-v2/final`;

const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
  cwd: ROOT,
  stdio: ["ignore", "pipe", "pipe"],
});
let serverLog = "";
server.stdout.on("data", (c) => (serverLog += c));
server.stderr.on("data", (c) => (serverLog += c));

const waitForServer = async () => {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`${origin}${BASE}/`);
      if (r.ok) return;
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`dev server not ready\n${serverLog}`);
};

let chrome = null;
try {
  await mkdir(OUT, { recursive: true });
  await waitForServer();
  chrome = await chromium.launch({
    args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
  });
  const page = await chrome.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console: ${m.text()}`);
  });

  // 1. The entry site lists it. A route that nothing links to is not shipped.
  await page.goto(`${origin}${BASE}/`, { waitUntil: "load" });
  const card = page.locator(`a[href$="/${SLUG}"]`);
  await card.waitFor({ timeout: 30_000 });
  const cardTitle = await card.locator(".card-title").textContent();
  const hasCover = await card.locator("img.card-thumb").count();
  console.log(
    `entry-site card: OK — "${cardTitle?.trim()}", cover image ${hasCover ? "present" : "MISSING"}`,
  );
  // The hero fills the first viewport, so screenshot the gallery where it actually is.
  await card.scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT}/entry-site-gallery.png` });

  // 2. The card navigates to the exhibit's own route.
  await card.click();
  await page.waitForURL(`**/${SLUG}`, { timeout: 30_000 });
  await page.waitForSelector(".demo-canvas-mount canvas", { timeout: 30_000 });
  await page.waitForTimeout(3000);
  console.log(`route /${SLUG}: OK — viewer canvas mounted`);

  // The part inspector's own header count and provenance line. It used to look for a `<p>`
  // matching /個命名節點/, which the shared inspector has never rendered — so it printed
  // "(stats line not found)" every run and nobody read it. Read the elements that exist, and
  // FAIL if the count is missing, because a viewer that mounts with no parts listed is not a
  // viewer that mounted.
  const stats = await page.evaluate(() => ({
    parts: document.querySelector(".parts-count")?.textContent?.trim() ?? null,
    provenance: document.querySelector(".parts-prov")?.textContent?.trim() ?? null,
  }));
  if (!stats.parts) throw new Error("part inspector rendered no part count");
  console.log(`part inspector: ${stats.parts} parts — ${stats.provenance ?? "(no provenance)"}`);
  await page.screenshot({ path: `${OUT}/exhibit-page-v2.png` });

  // 3. Every control drives the mounted viewer. A page that mounts but whose controls throw
  //    is not shippable, and only a real click finds that.
  //
  // **This list is the panel's, and it has to be re-read off `UltimaV2Stage.vue` whenever that
  // template changes.** It used to name six FAMILY chips — 外殼 / 能量核心 / 背脊 / 護手 / 握把 /
  // 全部 — which were removed when isolation moved out of the panel and into the shared part
  // inspector, where it is per-part rather than per-family. The script did not follow, so every
  // run since then has timed out waiting for a button that no longer exists, and a red end-to-end
  // check that is red for a stale reason stops being read at all. Isolation is still covered
  // below, through the control the inspector actually renders.
  for (const [label, shot] of [
    ["參考", "preset-reference"],
    ["前", "preset-front"],
    ["側", "preset-side"],
    ["3/4", "preset-three-quarter"],
    ["中性複核", "lighting-neutral"],
    ["黑箱舞台", "lighting-blackbox"],
    ["參考外觀", "lighting-reference"],
    ["自動旋轉", "spin-on"],
    ["自動旋轉", "spin-off"],
  ]) {
    await page.getByRole("button", { name: label, exact: true }).click();
    await page.waitForTimeout(900);
    await page.screenshot({ path: `${OUT}/${shot}.png` });
    console.log(`control "${label}": OK`);
  }

  // The black-box intensity slider only exists while that mode is on, so it is driven here rather
  // than in the loop above: a control that is conditionally rendered is exactly the kind that
  // throws in one state and not the other.
  await page.getByRole("button", { name: "黑箱舞台", exact: true }).click();
  const intensity = page.locator(".panel-slider");
  await intensity.waitFor({ timeout: 10_000 });
  await intensity.fill("4.5");
  await intensity.dispatchEvent("input");
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/lighting-blackbox-intensity.png` });
  console.log('control "強度 slider": OK');

  // Isolation, through the part inspector. One part in, one part out — the round trip is the
  // check, because isolating is what swaps every other part's visibility and un-isolating is what
  // has to put them all back.
  const isolate = page.getByRole("button", { name: "隔離 crystalClampRight", exact: true });
  await isolate.waitFor({ timeout: 10_000 });
  await isolate.click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${OUT}/isolate-part.png` });
  await isolate.click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${OUT}/isolate-none.png` });
  console.log('control "隔離 / 取消隔離": OK');

  const toggle = page.getByRole("button", { name: "隱藏 leatherGrip", exact: true });
  await toggle.waitFor({ timeout: 10_000 });
  await toggle.click();
  await page.waitForTimeout(600);
  await page.getByRole("button", { name: "顯示 leatherGrip", exact: true }).click();
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/toggle-visible.png` });
  console.log('control "隱藏 / 顯示": OK');

  console.log(errors.length ? `ERRORS:\n${errors.join("\n")}` : "no page/console errors");
  process.exitCode = errors.length ? 1 : 0;
} catch (cause) {
  console.error(cause);
  process.exitCode = 1;
} finally {
  await chrome?.close();
  server.kill("SIGTERM");
}
