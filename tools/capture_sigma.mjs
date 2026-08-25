#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "/img2three-art-exhibition";
const ROUTE = "mmx2-sigma-virus";
const PORT = Number(process.env.CAPTURE_PORT ?? 3179);
const ALL_VIEWS = [
  "front",
  "front-left-30",
  "front-left-60",
  "left",
  "rear-left-60",
  "rear-left-30",
  "rear",
  "rear-right-30",
  "rear-right-60",
  "right",
  "front-right-60",
  "front-right-30",
  "three-quarter",
  "top",
  "bottom",
];

function args(argv) {
  const result = {
    out: "/tmp/sigma-clean-renders",
    views: ALL_VIEWS,
    yawStep: 0,
    eachPart: false,
    viewport: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--out") result.out = argv[++i];
    else if (argv[i] === "--views") result.views = argv[++i].split(",");
    else if (argv[i] === "--yaw-sweep") result.yawStep = Number(argv[++i]);
    else if (argv[i] === "--each-part") result.eachPart = true;
    else if (argv[i] === "--silhouette") result.silhouette = true;
    else if (argv[i] === "--viewport") {
      const [w, h] = String(argv[++i]).split("x").map(Number);
      result.viewport = { width: w, height: h };
    }
  }
  return result;
}

async function waitFor(url) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`server did not start at ${url}`);
}

async function main() {
  const options = args(process.argv.slice(2));
  const out = path.isAbsolute(options.out) ? options.out : path.join(ROOT, options.out);
  await mkdir(out, { recursive: true });
  const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
    cwd: ROOT,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, FORCE_COLOR: "0" },
  });
  let log = "";
  server.stdout.on("data", (chunk) => (log += chunk));
  server.stderr.on("data", (chunk) => (log += chunk));
  const origin = `http://localhost:${PORT}`;
  let browser;
  try {
    await waitFor(`${origin}${BASE}/`).catch((error) => {
      throw new Error(`${error.message}\n${log}`);
    });
    browser = await chromium.launch({
      args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
    });
    const viewport = options.viewport ?? { width: 480, height: 690 };
    const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto(`${origin}${BASE}/${ROUTE}`, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => window.__renderReady === true, null, { timeout: 30_000 });
    if (options.silhouette) await page.evaluate(() => window.__sigmaViewer.setSilhouette(true));

    const manifest = { route: ROUTE, views: [], yaw: [], parts: [] };
    const capture = async (file) => {
      await page
        .locator("canvas")
        .first()
        .screenshot({ path: path.join(out, file) });
    };

    if (options.eachPart) {
      const parts = await page.evaluate(() => window.__sigmaViewer.toggleableParts);
      for (const part of parts) {
        await page.evaluate((keep) => {
          const viewer = window.__sigmaViewer;
          for (const id of viewer.toggleableParts) viewer.setPartVisible(id, id === keep);
          viewer.setPreset("front");
        }, part);
        await page.waitForTimeout(120);
        const file = `part-${part}.png`;
        await capture(file);
        manifest.parts.push({ part, file });
      }
      await page.evaluate(() => {
        const viewer = window.__sigmaViewer;
        for (const id of viewer.toggleableParts) viewer.setPartVisible(id, true);
      });
    }

    if (options.yawStep > 0) {
      await page.evaluate(() => window.__sigmaViewer.setPreset("front"));
      for (let degree = 0; degree <= 90; degree += options.yawStep) {
        await page.evaluate((value) => window.__sigmaViewer.setYaw(value), degree);
        await page.waitForTimeout(100);
        const file = `yaw-${String(degree).padStart(3, "0")}.png`;
        await capture(file);
        manifest.yaw.push({ degree, file });
      }
    }

    for (const view of options.views) {
      await page.evaluate((value) => window.__sigmaViewer.setPreset(value), view);
      await page.waitForTimeout(180);
      const file = `${view}.png`;
      await capture(file);
      manifest.views.push({ view, file });
    }
    if (errors.length) throw new Error(errors.join("\n"));
    await writeFile(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 2));
    console.log(
      `captured ${manifest.views.length} canonical views, ${manifest.yaw.length} yaw views, ${manifest.parts.length} parts`,
    );
  } finally {
    await browser?.close();
    server.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error.stack ?? error);
  process.exit(1);
});
