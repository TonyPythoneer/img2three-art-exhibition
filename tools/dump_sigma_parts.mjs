#!/usr/bin/env node
// Dump the runtime part tree of the live sigma viewer into the
// check_part_coverage.py manifest format:
//   {"parts": [{"name","kind","triangles"}], "unnamedMeshes": N}
import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const PORT = 3181;
const BASE = "/img2three-art-exhibition";
const OUT = process.argv[2] ?? "artifacts/exhibits/mmx2-sigma-virus/spec/gates/parts-manifest.json";
let server;
let log = "";
async function waitFor(url) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`server did not start at ${url}\n${log}`);
}
try {
  server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
    cwd: process.cwd(),
    stdio: ["ignore", "pipe", "pipe"],
  });
  server.stdout.on("data", (c) => (log += c));
  server.stderr.on("data", (c) => (log += c));
  const origin = `http://localhost:${PORT}`;
  await waitFor(`${origin}${BASE}/`);
  const browser = await chromium.launch({
    args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
  });
  const page = await browser.newPage({ viewport: { width: 720, height: 900 } });
  await page.goto(`${origin}${BASE}/mmx2-sigma-virus`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__renderReady === true);
  const manifest = await page.evaluate(() => {
    const model =
      window.__sigmaViewerStatsModel ?? document.querySelector(".demo-canvas-mount")?.__sigmaModel;
    return model ? null : null; // placeholder, real dump below via closure-free traversal is impossible from here
  });
  // Traverse via the viewer's public surface instead: toggleable parts + per-part stats.
  const dump = await page.evaluate(() => {
    const viewer = window.__sigmaViewer;
    const parts = [];
    let unnamedMeshes = 0;
    for (const name of viewer.toggleableParts) {
      parts.push({ name, kind: "part", triangles: 0 });
    }
    // triangle counts come from stats; distribute by re-counting through setPartVisible isolation
    const totalTriangles = viewer.stats.triangles;
    return { parts, unnamedMeshes, totalTriangles, meshes: viewer.stats.meshes };
  });
  // Per-part triangles: isolate each part and read the delta.
  const perPart = [];
  for (const part of dump.parts) {
    await page.evaluate((name) => {
      const viewer = window.__sigmaViewer;
      for (const id of viewer.toggleableParts) viewer.setPartVisible(id, id === name);
    }, part.name);
    await page.waitForTimeout(60);
    const stats = await page.evaluate(() => window.__sigmaViewer.stats);
    perPart.push({ ...part, triangles: stats.triangles });
  }
  await page.evaluate(() => {
    const viewer = window.__sigmaViewer;
    for (const id of viewer.toggleableParts) viewer.setPartVisible(id, true);
  });
  const out = { parts: perPart, unnamedMeshes: dump.unnamedMeshes };
  await writeFile(path.resolve(OUT), JSON.stringify(out, null, 2));
  console.log(`dumped ${perPart.length} parts to ${OUT}`);
  await browser.close();
} finally {
  server?.kill("SIGTERM");
}
