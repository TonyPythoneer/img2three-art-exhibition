#!/usr/bin/env node
/**
 * Headless capture of the Ultima Weapon review renders.
 *
 *   node tools/capture_ultima.mjs --out artifacts/ultima/blockout --detail blockout
 *   node tools/capture_ultima.mjs --out artifacts/ultima/full --detail full
 *   node tools/capture_ultima.mjs --out <dir> --views front-orthographic,exploded-three-quarter
 *   node tools/capture_ultima.mjs --out <dir> --explode-sweep     # transform-stability check
 *
 * Drives the Vite dev server rather than a build: these are review renders taken between
 * edits, and a full `vite-ssg build` per iteration would dominate the loop. The page signals
 * `window.__renderReady` on its third presented frame, so a screenshot cannot catch an empty
 * canvas, and any harness error is re-thrown here instead of being saved as a blank PNG.
 */

import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "/img2three-art-exhibition";
// ponytail: env override, because two capture runs sharing 3177 do not fail — the second one
// attaches to the first one's dev server and silently renders the OTHER working tree's model.
// No gate can catch that; a stray port is the whole fix.
const PORT = Number(process.env.CAPTURE_PORT ?? 3177);

const ALL_VIEWS = [
  "reference-matched-three-quarter",
  "front-orthographic",
  "back-orthographic",
  "left-side-thickness",
  "right-side-thickness",
  "assembled-three-quarter",
  "exploded-three-quarter",
  "isolated-outer-shell",
  "isolated-purple-core",
  "isolated-guard-assembly",
];

/** Portrait for the blade-shaped views, squarer where the guard fan or an explode spreads wide. */
const VIEW_SIZE = {
  // The v2 run names its artwork-matched view after the camera rather than the framing.
  "artwork-match": [584, 1168],
  "reference-matched-three-quarter": [584, 1168],
  "front-orthographic": [584, 1168],
  "back-orthographic": [584, 1168],
  "left-side-thickness": [584, 1168],
  "right-side-thickness": [584, 1168],
  "assembled-three-quarter": [768, 1168],
  "exploded-three-quarter": [1000, 1168],
  "isolated-outer-shell": [584, 1168],
  "isolated-purple-core": [584, 1168],
  "isolated-guard-assembly": [900, 700],
  // v2 correction-pass views.
  "rear-three-quarter": [768, 1168],
  "closeup-crystal-clamp": [760, 760],
  "closeup-clamp-bases": [760, 760],
  "closeup-driver-joints": [900, 700],
  "closeup-connectors": [1000, 700],
  "closeup-spinner-ends": [760, 760],
  "closeup-grip-pommel": [700, 760],
  "material-transmission": [760, 1000],
};

function parseArgs(argv) {
  const args = {
    out: "artifacts/ultima",
    detail: "full",
    mode: "referenceLighting",
    views: ALL_VIEWS,
    explodeSweep: false,
    route: "ultima-harness",
  };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    const value = argv[i + 1];
    if (flag === "--route") {
      args.route = value;
      i += 1;
    } else if (flag === "--out") {
      args.out = value;
      i += 1;
    } else if (flag === "--detail") {
      args.detail = value;
      i += 1;
    } else if (flag === "--mode") {
      args.mode = value;
      i += 1;
    } else if (flag === "--views") {
      args.views = value
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
      i += 1;
    } else if (flag === "--explode-sweep") {
      args.explodeSweep = true;
    } else if (flag === "--flat") {
      args.flat = true;
    } else if (flag === "--hide") {
      args.hide = value;
      i += 1;
    } else if (flag === "--suffix") {
      args.suffix = value;
      i += 1;
    }
    // Arbitrary harness query params, e.g. --extra yaw=24,roll=18.13 — used by the v2 run's
    // camera solve, which sweeps yaw/pitch/roll instead of editing a constant per trial.
    else if (flag === "--extra") {
      args.extra = value;
      i += 1;
    }
    // One shot per value, e.g. --sweep yaw=14;18;22 — the camera solve, in one server run.
    else if (flag === "--sweep") {
      args.sweep = value;
      i += 1;
    }
  }
  return args;
}

async function waitForServer(url, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // server not up yet
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
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
  server.stdout.on("data", (chunk) => {
    serverLog += chunk.toString();
  });
  server.stderr.on("data", (chunk) => {
    serverLog += chunk.toString();
  });

  const origin = `http://localhost:${PORT}`;
  const browser = null;
  let context = null;
  let chrome = null;
  // `purpose` and `gate` are stamped so a directory of renders can never be mistaken for the kind
  // it is not. The black box is a presentation stage lit to look good in a dark room; measuring it
  // against a white-background 1997 artwork would produce a permanently red score that means
  // nothing. Nothing enforces this — run_gates.sh simply never reads the blackbox directory — so
  // the manifest is where the intent is written down for whoever finds the folder later.
  const presentation = args.mode === "blackBox";
  const manifest = {
    detail: args.detail,
    mode: args.mode,
    purpose: presentation ? "presentation" : "review",
    gate: presentation ? "none" : "tier1",
    renders: [],
  };

  try {
    await waitForServer(`${origin}${BASE}/`).catch((cause) => {
      throw new Error(`${cause.message}\n--- dev server output ---\n${serverLog}`);
    });

    chrome = await chromium.launch({
      args: ["--use-gl=angle", "--use-angle=default", "--enable-unsafe-swiftshader"],
    });
    context = await chrome.newContext({ deviceScaleFactor: 1 });

    const sweepKey = args.sweep?.split("=")[0]?.trim();
    const sweepValues = args.sweep?.split("=").slice(1).join("=").split(";").filter(Boolean) ?? [];

    const shots = sweepKey
      ? args.views.flatMap((view) =>
          sweepValues.map((v) => ({
            view,
            explode: null,
            param: [sweepKey, v],
            file: `${view}-${sweepKey}${v}.png`,
          })),
        )
      : args.explodeSweep
        ? // Sweep explode up and back down through the same camera. If setExplode accumulated
          // error, the 1.0-down frame would not match the 1.0-up frame and the final 0.0 frame
          // would not match the assembled render.
          [0, 0.5, 1, 0.5, 0].map((amount, index) => ({
            view: "exploded-three-quarter",
            explode: amount,
            file: `explode-sweep-${index}-${amount}.png`,
          }))
        : args.views.map((view) => ({
            view,
            explode: null,
            file: `${view}${args.suffix ?? ""}.png`,
          }));

    for (const shot of shots) {
      const [width, height] = VIEW_SIZE[shot.view] ?? [584, 1168];
      const page = await context.newPage();
      await page.setViewportSize({ width, height });
      const query = new URLSearchParams({
        view: shot.view,
        mode: args.mode,
        detail: args.detail,
        w: String(width),
        h: String(height),
      });
      if (shot.explode !== null) query.set("explode", String(shot.explode));
      if (args.flat) query.set("flat", "1");
      if (args.hide) query.set("hide", args.hide);
      for (const pair of (args.extra ?? "").split(",").filter(Boolean)) {
        const [key, ...rest] = pair.split("=");
        query.set(key.trim(), rest.join("="));
      }
      if (shot.param) query.set(shot.param[0], shot.param[1]);

      const errors = [];
      page.on("pageerror", (err) => errors.push(err.message));
      await page.goto(`${origin}${BASE}/${args.route}?${query}`, { waitUntil: "load" });

      await page
        .waitForFunction(
          () => window.__renderReady === true || typeof window.__renderError === "string",
          undefined,
          { timeout: 30_000 },
        )
        .catch(() => {
          /* fall through to the explicit error read below */
        });

      const harnessError = await page.evaluate(() => window.__renderError ?? null);
      if (harnessError) throw new Error(`harness failed on ${shot.view}: ${harnessError}`);
      const ready = await page.evaluate(() => window.__renderReady === true);
      if (!ready)
        throw new Error(
          `harness never signalled ready on ${shot.view}; page errors: ${errors.join(" | ")}`,
        );

      const info = await page.evaluate(() => window.__renderHarness ?? {});
      if (!manifest.parts) {
        manifest.parts = await page.evaluate(() => window.__partManifest ?? null);
        if (manifest.parts) {
          await writeFile(
            path.join(outDir, "parts.json"),
            `${JSON.stringify(manifest.parts, null, 2)}\n`,
          );
        }
      }
      // The compositor intermittently hands back an all-white frame even after __renderReady.
      // Sample the live canvas and wait for real content before screenshotting, otherwise a
      // blank PNG lands in the evidence set looking like a captured render.
      const painted = await page
        .waitForFunction(
          () => {
            const canvas = document.querySelector("#ultima-harness-canvas");
            if (!(canvas instanceof HTMLCanvasElement)) return false;
            const probe = document.createElement("canvas");
            probe.width = 64;
            probe.height = 128;
            const ctx = probe.getContext("2d");
            if (!ctx) return false;
            ctx.drawImage(canvas, 0, 0, probe.width, probe.height);
            const { data } = ctx.getImageData(0, 0, probe.width, probe.height);
            let painted = 0;
            for (let i = 0; i < data.length; i += 4) {
              if (data[i + 3] > 24 && Math.min(data[i], data[i + 1], data[i + 2]) < 244)
                painted += 1;
            }
            return painted > 40;
          },
          undefined,
          { timeout: 15_000 },
        )
        .then(() => true)
        .catch(() => false);
      if (!painted) throw new Error(`canvas stayed blank on ${shot.view}`);

      const target = path.join(outDir, shot.file);
      // Read the drawing buffer directly instead of screenshotting the composited page. The
      // element screenshot intermittently returns an all-white frame (and loses the page
      // context outright on the wider views) even when the canvas provably holds an image;
      // `preserveDrawingBuffer` is on, so toDataURL is the same pixels without the compositor.
      const dataUrl = await page
        .evaluate(() => {
          const canvas = document.querySelector("#ultima-harness-canvas");
          return canvas instanceof HTMLCanvasElement ? canvas.toDataURL("image/png") : null;
        })
        .catch(() => null);
      if (dataUrl) {
        await writeFile(target, Buffer.from(dataUrl.split(",")[1], "base64"));
      } else {
        await page
          .locator("#ultima-harness-canvas")
          .screenshot({ path: target })
          .catch(() => page.screenshot({ path: target, clip: { x: 0, y: 0, width, height } }));
      }
      manifest.renders.push({ ...shot, file: shot.file, width, height, info });
      console.log(
        `captured ${shot.file}  parts=${info.namedParts} meshes=${info.meshCount} tris=${info.triangles}`,
      );
      await page.close();
    }

    await writeFile(path.join(outDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  } finally {
    await context?.close();
    await chrome?.close();
    await browser?.close();
    server.kill("SIGTERM");
  }
}

main().catch((cause) => {
  console.error(cause);
  process.exitCode = 1;
});
