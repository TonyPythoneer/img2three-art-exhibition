#!/usr/bin/env node
/**
 * Structure gate for the Sigma virus head — the only gate here that scores STRUCTURE rather
 * than pixels. Every other gate reduces the model to an image, and a single fused mesh wearing
 * the right outline passes all of them.
 *
 *   node tools/verify_sigma_parts.mjs
 *
 * FAILS on: a specified part that was never built, two parts fused onto one mesh, a mesh that
 * belongs to no named part, and an explode that does not actually separate anything.
 * Its honest limit: it proves the model contains what the spec named, never that the spec named
 * enough.
 *
 * Exit 0 pass, 1 gate failure.
 */

import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "/img2three-art-exhibition";
const PORT = Number(process.env.CAPTURE_PORT ?? 3181);

/** The part table from `createSigmaVirusHead.ts` — 8 shape codes, 13 instances. */
const EXPECTED = [
  "skullShell",
  "crownPlate",
  "sidePanelL",
  "sidePanelR",
  "earPodL",
  "earPodR",
  "browRidgeL",
  "browRidgeR",
  "eyePlateL",
  "eyePlateR",
  "jawBlock",
  "chinTabL",
  "chinTabR",
];

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
  const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
    cwd: ROOT,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, FORCE_COLOR: "0" },
  });
  let log = "";
  server.stdout.on("data", (c) => (log += c));
  server.stderr.on("data", (c) => (log += c));

  let chrome = null;
  const failures = [];
  try {
    await waitForServer(`http://localhost:${PORT}${BASE}/`).catch((cause) => {
      throw new Error(`${cause.message}\n--- dev server output ---\n${log}`);
    });
    chrome = await chromium.launch({
      args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
    });
    const page = await (await chrome.newContext()).newPage();
    await page.goto(`http://localhost:${PORT}${BASE}/mmx2-sigma-virus`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForFunction(() => window.__renderReady === true, null, { timeout: 30_000 });

    const report = await page.evaluate(() => {
      const v = window.__sigmaViewer;
      const parts = v.parts.map((p) => ({
        name: p.name,
        kind: p.kind,
        module: p.module,
        triangles: p.triangles,
      }));
      return { parts, toggleable: v.toggleableParts, stats: v.stats };
    });

    const names = new Set(report.parts.map((p) => p.name));
    for (const want of EXPECTED) {
      if (!names.has(want)) failures.push(`missing part: ${want}`);
    }
    for (const got of report.parts) {
      if (got.kind === "part" && !EXPECTED.includes(got.name)) {
        failures.push(`mesh belongs to no named part in the spec table: ${got.name}`);
      }
      if (got.triangles === 0) failures.push(`part has no geometry: ${got.name}`);
    }
    if (report.toggleable.length !== EXPECTED.length) {
      failures.push(
        `toggleable count ${report.toggleable.length} != expected ${EXPECTED.length} — ` +
          `two parts are fused onto one mesh, or one part never reached the root`,
      );
    }

    // Explode has to open a gap, not translate the arrangement. Measure the model's own bounds
    // assembled vs separated: scaling about the centre must grow them.
    const grew = await page.evaluate(() => {
      const v = window.__sigmaViewer;
      const span = () => {
        const xs = v.parts.map((p) => p.object.position.length());
        return Math.max(...xs);
      };
      v.setExplode(0);
      const a = span();
      v.setExplode(1);
      const b = span();
      v.setExplode(0);
      return { assembled: a, exploded: b };
    });
    if (!(grew.exploded > grew.assembled * 1.5)) {
      failures.push(
        `explode did not separate: max part offset ${grew.assembled} -> ${grew.exploded}`,
      );
    }

    // --out keeps the record and the human line apart. Redirecting all of stdout into the record
    // instead left the trailing PASS line inside it, and gate-parts.json was not valid JSON for
    // five commits — nothing read it back, so nothing complained.
    const payload = `${JSON.stringify({ ...report, explode: grew, failures }, null, 1)}\n`;
    const outIdx = process.argv.indexOf("--out");
    if (outIdx !== -1) await writeFile(process.argv[outIdx + 1], payload);
    else process.stdout.write(payload);
  } finally {
    await chrome?.close();
    server.kill("SIGTERM");
  }

  if (failures.length) {
    process.stderr.write(`FAIL:\n  ${failures.join("\n  ")}\n`);
    process.exit(1);
  }
  process.stdout.write(`PASS: ${EXPECTED.length} parts, all named, explode separates\n`);
}

main().catch((e) => {
  process.stderr.write(`${e.stack ?? e}\n`);
  process.exit(1);
});
