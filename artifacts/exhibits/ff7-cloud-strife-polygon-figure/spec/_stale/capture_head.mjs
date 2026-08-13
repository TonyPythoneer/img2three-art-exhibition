#!/usr/bin/env node
/**
 * Headless capture of the Cloud Strife head (Part 1) into fixed review views.
 *
 *   node spec/capture_head.mjs --out <tmpdir>
 *
 * Drives the Vite dev server (like tools/capture_ultima.mjs) to the `head-capture-harness`
 * route, which builds the scene with createHead() and the v2 `referenceLighting` rig and renders
 * one orthographic view per page load. The five PNGs (front/left/right/back orthographic + a 3/4
 * orbit) go to a temp dir and are never committed — CLAUDE.md keeps renders out of the repo.
 *
 * The harness is a throwaway review fixture, so this script owns no port: set CAPTURE_PORT to avoid
 * colliding with another capture run sharing 3177.
 */
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "..",
  "..",
);
const BASE = "/img2three-art-exhibition";
const PORT = Number(process.env.CAPTURE_PORT ?? 3177);
const VIEWS = ["front", "left", "right", "back", "orbit"];

function parseArgs(argv) {
  const args = { out: "/tmp/ff7-head-captures", port: PORT, views: VIEWS, part: "" };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--out") {
      args.out = argv[++i];
    } else if (argv[i] === "--port") {
      args.port = Number(argv[++i]);
    } else if (argv[i] === "--part") {
      args.part = argv[++i];
    } else if (argv[i] === "--views") {
      args.views = argv[++i].split(",").map((v) => v.trim()).filter(Boolean);
    }
  }
  return args;
}

async function waitForServer(url, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // server not up yet
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`dev server did not become ready at ${url}`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const port = args.port;
  const views = args.views;
  const outDir = path.isAbsolute(args.out) ? args.out : path.join(ROOT, args.out);
  await mkdir(outDir, { recursive: true });

  const server = spawn("npx", ["vite", "--port", String(port), "--strictPort"], {
    cwd: ROOT,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, FORCE_COLOR: "0" },
  });
  let serverLog = "";
  server.stdout.on("data", (chunk) => {
    serverLog += chunk.toString();
  });
  server.stderr.on("data", (chunk) => {
    serverLog += chunk.toString();
  });

  const origin = `http://localhost:${port}`;
  let chrome = null;
  let context = null;
  let failed = false;
  const results = [];

  try {
    await waitForServer(`${origin}${BASE}/`).catch((cause) => {
      throw new Error(`${cause.message}\n--- dev server output ---\n${serverLog}`);
    });

    chrome = await chromium.launch({
      args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
    });
    context = await chrome.newContext({ deviceScaleFactor: 1 });

    for (const view of views) {
      const page = await context.newPage();
      await page.setViewportSize({ width: 720, height: 960 });
      const part = args.part ? `&part=${encodeURIComponent(args.part)}` : "";
      const url = `${origin}${BASE}/head-capture-harness?view=${view}${part}`;
      await page.goto(url, { waitUntil: "load", timeout: 30_000 });

      await page
        .waitForFunction(
          () =>
            window.__renderReady === true ||
            typeof window.__renderError === "string",
          undefined,
          { timeout: 30_000 },
        )
        .catch(() => {});

      const harnessError = await page.evaluate(() => window.__renderError ?? null);
      if (harnessError) {
        console.error(`FAIL  ${view}: harness error: ${harnessError}`);
        results.push({ view, path: null, error: harnessError });
        failed = true;
        await page.close();
        continue;
      }
      const ready = await page.evaluate(() => window.__renderReady === true);
      if (!ready) {
        console.error(`FAIL  ${view}: harness never signalled ready`);
        results.push({ view, path: null, error: "not ready" });
        failed = true;
        await page.close();
        continue;
      }

      const info = await page.evaluate(() => window.__headInfo ?? null);
      const dataUrl = await page
        .evaluate(() => {
          const canvas = document.getElementById("head-capture-canvas");
          return canvas instanceof HTMLCanvasElement
            ? canvas.toDataURL("image/png")
            : null;
        })
        .catch(() => null);
      if (!dataUrl) {
        console.error(`FAIL  ${view}: canvas produced no data URL`);
        results.push({ view, path: null, error: "no data url" });
        failed = true;
        await page.close();
        continue;
      }

      const target = path.join(outDir, `${view}.png`);
      await writeFile(target, Buffer.from(dataUrl.split(",")[1], "base64"));
      console.log(
        `captured ${view}.png  meshes=${info?.meshes} tris=${info?.triangles} ` +
          `bbox ${JSON.stringify(info?.bbox?.size)}`,
      );
      results.push({ view, path: target, error: null });
      await page.close();
    }
  } finally {
    await context?.close();
    await chrome?.close();
    server.kill("SIGTERM");
  }

  console.log("\n=== render paths ===");
  for (const r of results) {
    if (r.path) console.log(r.path);
    else console.log(`${r.view}: NOT WRITTEN (${r.error})`);
  }

  process.exitCode = failed ? 1 : 0;
}

main().catch((cause) => {
  console.error(cause);
  process.exitCode = 1;
});
