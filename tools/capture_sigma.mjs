#!/usr/bin/env node
/**
 * Headless capture of the MMX2 Sigma virus head, straight off the real exhibit route.
 *
 *   node tools/capture_sigma.mjs --out /tmp/sigma-renders
 *   node tools/capture_sigma.mjs --out <dir> --views front,side
 *
 * Drives the exhibit page rather than a harness route, because a harness route is a second
 * `.vue` in `src/pages/` and therefore a second URL nobody wants. The page signals
 * `window.__renderReady` on its third presented frame, so a screenshot cannot catch an empty
 * canvas, and a page error is re-thrown here instead of being saved as a blank PNG.
 *
 * The renders themselves are NOT tracked — regenerate them from this script.
 */

import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "/img2three-art-exhibition";
const ROUTE = "mmx2-sigma-virus";
// ponytail: env override, because two capture runs sharing one port do not fail — the second
// attaches to the first one's dev server and silently renders the OTHER tree's model.
const PORT = Number(process.env.CAPTURE_PORT ?? 3179);

const ALL_VIEWS = ["front", "three-quarter", "side", "top"];
const SIZE = [720, 900];

function parseArgs(argv) {
  const args = { out: "/tmp/sigma-renders", views: ALL_VIEWS, explode: null, yawStep: 0 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--out") args.out = argv[(i += 1)];
    else if (argv[i] === "--views") args.views = argv[(i += 1)].split(",").map((v) => v.trim());
    else if (argv[i] === "--explode") args.explode = Number(argv[(i += 1)]);
    // Yaw sweep for the depth gate: 0..90 degrees in this step, from the front camera.
    else if (argv[i] === "--yaw-sweep") args.yawStep = Number(argv[(i += 1)]);
  }
  return args;
}

async function waitForServer(url, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`dev server did not become ready at ${url}`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const outDir = path.isAbsolute(args.out) ? args.out : path.join(ROOT, args.out);
  await mkdir(outDir, { recursive: true });

  const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
    cwd: ROOT,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, FORCE_COLOR: "0" },
  });
  let serverLog = "";
  server.stdout.on("data", (c) => (serverLog += c));
  server.stderr.on("data", (c) => (serverLog += c));

  const origin = `http://localhost:${PORT}`;
  let chrome = null;
  const manifest = { route: ROUTE, size: SIZE, renders: [] };

  try {
    await waitForServer(`${origin}${BASE}/`).catch((cause) => {
      throw new Error(`${cause.message}\n--- dev server output ---\n${serverLog}`);
    });

    chrome = await chromium.launch({
      args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
    });
    const context = await chrome.newContext({ deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));

    await page.setViewportSize({ width: SIZE[0], height: SIZE[1] });
    await page.goto(`${origin}${BASE}/${ROUTE}`, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => window.__renderReady === true, null, { timeout: 30_000 });

    if (args.yawStep > 0) {
      // The front camera stays fixed and the HEAD turns, which is what makes the width sweep
      // comparable to the reference's: those 87 frames are one mesh yawing in front of a fixed
      // camera too. Orbiting the camera instead would add perspective the reference does not have.
      await page.evaluate(() => window.__sigmaViewer.setPreset("front"));
      await page.waitForTimeout(600);
      for (let deg = 0; deg <= 90; deg += args.yawStep) {
        await page.evaluate((d) => window.__sigmaViewer.setYaw(d), deg);
        await page.waitForTimeout(120);
        const file = `yaw-${String(deg).padStart(3, "0")}.png`;
        await page
          .locator("canvas")
          .first()
          .screenshot({ path: path.join(outDir, file) });
        manifest.renders.push({ yaw: deg, file });
        process.stdout.write(`captured ${file}\n`);
      }
      await page.evaluate(() => window.__sigmaViewer.setYaw(0));
    }

    for (const view of args.views) {
      await page.evaluate(
        ([v, explode]) => {
          window.__sigmaViewer.setPreset(v);
          if (explode !== null) window.__sigmaViewer.setExplode(explode);
        },
        [view, args.explode],
      );
      // The orbit controls are damped, so the preset eases in over a few frames.
      await page.waitForTimeout(500);
      const canvas = page.locator("canvas").first();
      const file = `${view}${args.explode ? `-explode${args.explode}` : ""}.png`;
      await canvas.screenshot({ path: path.join(outDir, file) });
      manifest.renders.push({ view, file });
      process.stdout.write(`captured ${file}\n`);
    }

    if (errors.length) throw new Error(`page errors:\n${errors.join("\n")}`);
    await writeFile(path.join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2));
  } finally {
    await chrome?.close();
    server.kill("SIGTERM");
  }
}

main().catch((e) => {
  process.stderr.write(`${e.stack ?? e}\n`);
  process.exit(1);
});
