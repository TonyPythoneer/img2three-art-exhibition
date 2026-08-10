#!/usr/bin/env node
/**
 * Screenshot the recreated FF7 menu UI and diff it against the reference crop.
 *
 *   node tools/ff7-compare.mjs
 *   node tools/ff7-compare.mjs --url http://localhost:3000/img2three-art-exhibition/cloud-ultima-weapon-v2
 *
 * It drives the dev server rather than a build: the FF7 UI is plain CSS with no
 * WebGL in it, so there is nothing here that prerendering would change, and the
 * whole point of this script is a tight edit / re-shoot loop.
 *
 * `.ff7-screen` is captured on its own at --ff7-scale: 1, which is the 950x598
 * the reference crop was measured at, so the two images are directly comparable
 * without any resampling step in between.
 */

import { spawn } from "node:child_process";
import { connect } from "node:net";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PORT = 3000;
const DEFAULT_URL = `http://localhost:${PORT}/img2three-art-exhibition/cloud-ultima-weapon-v2`;

function parseArgs(argv) {
  const args = {
    url: DEFAULT_URL,
    out: "artifacts",
    reference: "artifacts/ff7-ui-reference.png",
    selector: ".ff7-screen",
    serve: true,
    timeout: 60000,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    const value = () => {
      const next = argv[i + 1];
      if (next === undefined) throw new Error(`${flag} needs a value`);
      i += 1;
      return next;
    };
    switch (flag) {
      case "--url":
        args.url = value();
        break;
      case "--out":
        args.out = value();
        break;
      case "--reference":
        args.reference = value();
        break;
      case "--selector":
        args.selector = value();
        break;
      case "--no-serve":
        args.serve = false;
        break;
      case "--timeout":
        args.timeout = Number.parseInt(value(), 10);
        break;
      default:
        throw new Error(`unknown flag ${flag}`);
    }
  }
  return args;
}

function portOpen(port) {
  return new Promise((resolve) => {
    const socket = connect({ port, host: "localhost" });
    socket.on("connect", () => (socket.destroy(), resolve(true)));
    socket.on("error", () => resolve(false));
  });
}

async function waitForPort(port, timeout) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await portOpen(port)) return;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`nothing listening on :${port} after ${timeout}ms`);
}

function run(command, commandArgs) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, commandArgs, { cwd: ROOT, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.stderr.on("data", (chunk) => (stderr += chunk));
    child.on("error", reject);
    child.on("close", (code) =>
      code === 0 ? resolve(stdout) : reject(new Error(`${command} exited ${code}\n${stderr}`)),
    );
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const outDir = path.join(ROOT, args.out);
  await mkdir(outDir, { recursive: true });

  let server = null;
  if (args.serve && !(await portOpen(PORT))) {
    server = spawn("pnpm", ["dev"], { cwd: ROOT, stdio: "ignore", detached: true });
    await waitForPort(PORT, args.timeout);
  }

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1200 } });
    await page.goto(args.url, { waitUntil: "networkidle", timeout: args.timeout });

    // The page renders the demo scaled down to fit its text column. Pin it back to
    // 1:1 and unclip the wrapper, otherwise the capture is a resampled thumbnail
    // and every pixel level comparison below it is meaningless.
    await page.addStyleTag({
      content: `.ff7-stage { --ff7-scale: 1 !important; height: 598px !important;
                             overflow: visible !important; }`,
    });

    const screen = page.locator(args.selector).first();
    await screen.waitFor({ state: "visible", timeout: args.timeout });
    // Fonts settle after layout; a capture taken before they land shows the
    // fallback face and reports a typography error that is not real. The
    // WebGL viewer shares the main thread, so fonts.ready (files fetched) is
    // not enough: the swap still has to be painted, which a blocked main
    // thread can postpone by a second or more. Wait for the face to be
    // usable, then for a run of idle frames, so the capture is not a
    // half-swapped frame.
    await page.waitForFunction(() => document.fonts.status === "loaded");
    await page.evaluate(
      () =>
        new Promise((resolve) => {
          let frames = 0;
          const tick = () => {
            frames += 1;
            if (frames >= 3) resolve();
            else requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }),
    );
    await page.waitForTimeout(250);

    // A page that composes to a fractional Y above the screen would rasterize the
    // replica off the pixel grid: every glyph's antialiasing shifts and the capture
    // clip rounds up a row, so two page states that differ only above the screen
    // would report phantom deltas. Snap the screen to the integer grid first — the
    // reference crop was captured on-grid, so this is what the comparison is for.
    await page.evaluate(() => {
      const screenEl = document.querySelector(".ff7-screen");
      if (!screenEl) return;
      const rect = screenEl.getBoundingClientRect();
      const snap = Math.round(rect.y) - rect.y;
      if (Math.abs(snap) > 0.005) {
        screenEl.style.transform = `scale(var(--ff7-scale, 1)) translateY(${snap.toFixed(4)}px)`;
      }
    });
    await page.waitForTimeout(50);

    const current = path.join(outDir, "ff7-ui-current.png");
    await screen.screenshot({ path: current, animations: "disabled" });

    const box = await screen.boundingBox();
    console.log(`captured ${path.relative(ROOT, current)} at ${box.width}x${box.height}`);

    console.log(
      await run("python3", [
        path.join(ROOT, "tools/ff7_overlay.py"),
        "--reference",
        path.join(ROOT, args.reference),
        "--current",
        current,
        "--overlay",
        path.join(outDir, "ff7-ui-overlay.png"),
        "--diff",
        path.join(outDir, "ff7-ui-diff.png"),
      ]),
    );
  } finally {
    await browser.close();
    if (server) process.kill(-server.pid, "SIGTERM");
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
