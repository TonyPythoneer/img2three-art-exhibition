#!/usr/bin/env node
/**
 * Headless per-part capture for the FF7 Cloud Strife polygon figure — prompt.txt §5.1-§5.3.
 *
 *   node tools/capture_parts.mjs --part soleL --out /tmp/soleL
 *   node tools/capture_parts.mjs --part soleL --views front,left,orbit,orbit2
 *   node tools/capture_parts.mjs --gallery --out /tmp/gallery
 *
 * Writes, into --out:
 *   <view>.png       one render per view, straight off the drawing buffer
 *   meshes.json      the built geometry, in the shape spec/gate_facets.py check consumes
 *   parts.json       the partInspector manifest, for check_part_coverage.py
 *
 * Renders are throwaway (AGENTS.md: artifacts/ keeps measurements and scripts, never
 * renders), so --out defaults under the system temp dir rather than into the repo.
 *
 * Drives the Vite dev server on the exhibit route itself: ?part=&view= is the review
 * harness (there is no separate harness page — src/pages/ is the URL surface). The page
 * sets window.__renderReady only after it has drawn a non-empty model, so a screenshot
 * cannot catch a blank canvas and be scored as a passing silhouette.
 */
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "/img2three-art-exhibition";
const SLUG = "ff7-cloud-strife-polygon-figure";
// ponytail: env override, because two capture runs sharing one port do not fail — the
// second attaches to the first one's dev server and renders the OTHER tree's model.
const PORT = Number(process.env.CAPTURE_PORT ?? 3181);
const SIZE = [700, 700];

function parseArgs(argv) {
  const args = {
    part: null,
    gallery: false,
    views: ["front", "back", "left", "right", "orbit", "orbit2"],
    out: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const [flag, value] = [argv[i], argv[i + 1]];
    if (flag === "--part") ((args.part = value), (i += 1));
    else if (flag === "--out") ((args.out = value), (i += 1));
    else if (flag === "--views")
      ((args.views = value
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean)),
        (i += 1));
    else if (flag === "--gallery") args.gallery = true;
  }
  if (!args.part && !args.gallery) throw new Error("pass --part <name> or --gallery");
  args.out ??= path.join(os.tmpdir(), `cloud-${args.part ?? "gallery"}`);
  return args;
}

async function waitForServer(url, log) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`dev server did not become ready at ${url}\n${log()}`);
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
  let context = null;
  try {
    await waitForServer(`${origin}${BASE}/`, () => serverLog);
    chrome = await chromium.launch({
      args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
    });
    context = await chrome.newContext({ deviceScaleFactor: 1 });

    let exported = false;
    for (const view of args.views) {
      const page = await context.newPage();
      await page.setViewportSize({ width: SIZE[0], height: SIZE[1] });
      const query = new URLSearchParams({ view });
      if (args.part) query.set("part", args.part);
      if (args.gallery) query.set("mode", "gallery");

      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.goto(`${origin}${BASE}/${SLUG}?${query}`, { waitUntil: "load" });
      await page
        .waitForFunction(
          () => window.__renderReady === true || typeof window.__renderError === "string",
          undefined,
          { timeout: 30_000 },
        )
        .catch(() => {});

      const harnessError = await page.evaluate(() => window.__renderError ?? null);
      if (harnessError) throw new Error(`harness failed on ${view}: ${harnessError}`);
      if (!(await page.evaluate(() => window.__renderReady === true)))
        throw new Error(
          `harness never signalled ready on ${view}; page errors: ${errors.join(" | ")}`,
        );

      if (!exported) {
        const info = await page.evaluate(() => window.__partInfo ?? null);
        const meshes = await page.evaluate(() => window.__partMeshes ?? null);
        await writeFile(path.join(outDir, "parts.json"), `${JSON.stringify(info, null, 2)}\n`);
        await writeFile(path.join(outDir, "meshes.json"), `${JSON.stringify(meshes)}\n`);
        console.log(
          `parts=${info.parts.map((p) => `${p.module}/${p.name}:${p.triangles}tri`).join(" ")} ` +
            `materials=${info.materials.join(",")}`,
        );
        exported = true;
      }

      // Read the drawing buffer rather than screenshotting the composited page: the
      // element screenshot intermittently returns an all-white frame even when the canvas
      // provably holds an image. preserveDrawingBuffer is on, so this is the same pixels.
      const dataUrl = await page.evaluate(() => {
        const canvas = document.querySelector("canvas");
        return canvas instanceof HTMLCanvasElement ? canvas.toDataURL("image/png") : null;
      });
      if (!dataUrl) throw new Error(`no canvas on ${view}`);
      const file = path.join(outDir, `${view}.png`);
      await writeFile(file, Buffer.from(dataUrl.split(",")[1], "base64"));
      console.log(`captured ${file}`);
      await page.close();
    }
  } finally {
    await context?.close();
    await chrome?.close();
    server.kill("SIGTERM");
  }
}

main().catch((cause) => {
  console.error(cause);
  process.exitCode = 1;
});
