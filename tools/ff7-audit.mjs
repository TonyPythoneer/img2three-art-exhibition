#!/usr/bin/env node
/**
 * Programmatic audit of the FF7 page skin. Everything in here is checkable without looking
 * at the result — it is the half of the verification a model with no image input can own.
 *
 *   node tools/ff7-audit.mjs
 *   node tools/ff7-audit.mjs --json          # machine-readable only, no prose
 *
 * Exits 0 when every check passes, 1 otherwise, and prints one line per check either way.
 * It also writes artifacts/ff7-page-<width>.png at each breakpoint — the script never looks
 * at those; they exist so a human can, which is the part this file deliberately does not
 * claim to cover.
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
const BASE = `http://localhost:${PORT}/img2three-art-exhibition`;
const SKINNED = "/ff7-cloud-strife-ultima-weapon";
const UNSKINNED = ["/", "/balamb-garden"];
const WIDTHS = [1400, 1024, 700, 480, 375];

/** The old gallery palette. Any of these surviving on the skinned page is a miss. */
const BANNED = {
  "ground #0b0f16": "11, 15, 22",
  "panel #121826": "18, 24, 38",
  "line #223049": "34, 48, 73",
  "accent #7fd4ff": "127, 212, 255",
};

const results = [];
const check = (name, ok, detail) => results.push({ name, ok: Boolean(ok), detail });

function portOpen(port) {
  return new Promise((resolve) => {
    const socket = connect({ port, host: "localhost" });
    socket.on("connect", () => (socket.destroy(), resolve(true)));
    socket.on("error", () => resolve(false));
  });
}

async function waitForPort(port, timeout = 90000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await portOpen(port)) return true;
    await new Promise((r) => setTimeout(r, 250));
  }
  return false;
}

/**
 * Walks every element outside `.ff7-screen` and reports the ones still painting the old
 * palette, still rounded, or still blurring. Runs in the page: pulling several hundred
 * computed styles across the CDP boundary one at a time is far slower than one round trip.
 */
const sweep = (banned) => {
  const bad = { palette: [], radius: [], blur: [] };
  const label = (el) =>
    `${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}` +
    `${typeof el.className === "string" && el.className ? "." + el.className.trim().split(/\s+/).slice(0, 3).join(".") : ""}`;
  for (const el of document.querySelectorAll("*")) {
    if (el.closest(".ff7-screen")) continue;
    const s = getComputedStyle(el);
    const paint = [
      s.color,
      s.backgroundColor,
      s.backgroundImage,
      s.borderTopColor,
      s.borderRightColor,
      s.borderBottomColor,
      s.borderLeftColor,
      s.outlineColor,
      s.boxShadow,
    ].join(" ");
    for (const [name, rgb] of Object.entries(banned)) {
      // A transparent border still reports its colour, so a 0-width border is not a hit.
      if (paint.includes(rgb)) bad.palette.push(`${label(el)} :: ${name}`);
    }
    for (const corner of [
      s.borderTopLeftRadius,
      s.borderTopRightRadius,
      s.borderBottomRightRadius,
      s.borderBottomLeftRadius,
    ]) {
      if (corner && corner !== "0px" && !bad.radius.includes(label(el))) bad.radius.push(label(el));
    }
    if (s.backdropFilter && s.backdropFilter !== "none") bad.blur.push(label(el));
  }
  for (const key of Object.keys(bad)) bad[key] = [...new Set(bad[key])].slice(0, 12);
  return bad;
};

async function main() {
  const json = process.argv.includes("--json");
  await mkdir(path.join(ROOT, "artifacts"), { recursive: true });

  let server = null;
  if (!(await portOpen(PORT))) {
    server = spawn("pnpm", ["dev"], { cwd: ROOT, stdio: "ignore", detached: true });
    if (!(await waitForPort(PORT))) throw new Error(`dev server never came up on :${PORT}`);
  }

  const browser = await chromium.launch();
  try {
    for (const width of WIDTHS) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } });
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
      await page.goto(`${BASE}${SKINNED}`, { waitUntil: "networkidle" });
      await page.evaluate(() => document.fonts.ready);

      const overflow = await page.evaluate(() => ({
        scroll: document.documentElement.scrollWidth,
        client: document.documentElement.clientWidth,
      }));
      check(
        `no horizontal overflow @${width}`,
        overflow.scroll <= overflow.client + 1,
        `scrollWidth ${overflow.scroll} vs clientWidth ${overflow.client}`,
      );

      const bad = await page.evaluate(sweep, BANNED);
      check(`old palette gone @${width}`, bad.palette.length === 0, bad.palette.join(" | "));
      check(`no border-radius @${width}`, bad.radius.length === 0, bad.radius.join(" | "));
      check(`no backdrop-filter @${width}`, bad.blur.length === 0, bad.blur.join(" | "));
      check(`no console errors @${width}`, errors.length === 0, errors.slice(0, 3).join(" | "));

      if (width === 1400) {
        const dashboard = await page.locator(".ff7-command-center").count();
        check("dashboard present", dashboard > 0, `${dashboard} .ff7-command-center found`);

        const viewer = await page.locator(".ff7-viewer-shell").boundingBox();
        const viewport = page.viewportSize();
        check(
          "viewer is hero at 1400",
          viewer && viewer.width > viewport.width * 0.4,
          viewer ? `${viewer.width}px wide` : "no .ff7-viewer-shell",
        );

        const commandPanel = await page.locator(".ff7-command-panel").count();
        check(
          "command panel present",
          commandPanel > 0,
          `${commandPanel} .ff7-command-panel found`,
        );

        const sprite = await page.request.get(`${BASE}/assets/ff7-hand-cursor.png`);
        check("hand cursor asset serves", sprite.status() === 200, `HTTP ${sprite.status()}`);
      }

      await page.screenshot({
        path: path.join(ROOT, `artifacts/ff7-page-${width}.png`),
        fullPage: true,
        animations: "disabled",
      });
      await page.close();
    }

    // The skin must not have leaked. `.chip` in particular is shared with the other exhibit.
    for (const route of UNSKINNED) {
      const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
      await page.goto(`${BASE}${route}`, { waitUntil: "networkidle" });
      const leaked = await page.evaluate(() => ({
        skin: Boolean(document.querySelector(".ff7-page")),
        htmlBg: getComputedStyle(document.documentElement).backgroundColor,
      }));
      check(
        `${route} unskinned`,
        !leaked.skin && leaked.htmlBg === "rgb(11, 15, 22)",
        `ff7-page=${leaked.skin} htmlBackground=${leaked.htmlBg}`,
      );
      await page.close();
    }
  } finally {
    await browser.close();
    if (server) process.kill(-server.pid, "SIGTERM");
  }

  const failed = results.filter((r) => !r.ok);
  if (json) {
    console.log(JSON.stringify({ passed: results.length - failed.length, results }, null, 2));
  } else {
    for (const r of results) {
      console.log(
        `${r.ok ? "PASS" : "FAIL"}  ${r.name}${r.detail && !r.ok ? `  -> ${r.detail}` : ""}`,
      );
    }
    console.log(`\n${results.length - failed.length}/${results.length} passed`);
    console.log("screenshots for a human: artifacts/ff7-page-<width>.png");
  }
  process.exit(failed.length ? 1 : 0);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
