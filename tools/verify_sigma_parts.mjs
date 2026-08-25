#!/usr/bin/env node
import { spawn } from "node:child_process";
import { chromium } from "playwright";

const PORT = 3180;
const BASE = "/img2three-art-exhibition";
let server;
let log = "";
async function waitFor(url) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`server did not start at ${url}\n${log}`);
}

try {
  server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
    cwd: process.cwd(),
    stdio: ["ignore", "pipe", "pipe"],
  });
  server.stdout.on("data", (chunk) => (log += chunk));
  server.stderr.on("data", (chunk) => (log += chunk));
  const origin = `http://localhost:${PORT}`;
  await waitFor(`${origin}${BASE}/`);
  const browser = await chromium.launch({
    args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
  });
  const page = await browser.newPage({ viewport: { width: 720, height: 900 } });
  await page.goto(`${origin}${BASE}/mmx2-sigma-virus`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__renderReady === true);
  const result = await page.evaluate(() => {
    const viewer = window.__sigmaViewer;
    const initial = viewer.toggleableParts.length;
    viewer.setExplode(0.49);
    const exploded = viewer.toggleableParts.length;
    viewer.setExplode(0);
    return { initial, exploded, stats: viewer.stats, names: viewer.toggleableParts };
  });
  await browser.close();
  if (result.initial !== 16 || result.exploded !== 16)
    throw new Error(
      `expected 16 independently parameterized parts (SIGMA_PARTS): ${JSON.stringify(result)}`,
    );
  console.log(
    `PASS: ${result.initial} independently parameterized parts, ${result.stats.meshes} meshes, explode control active`,
  );
} finally {
  server?.kill("SIGTERM");
}
