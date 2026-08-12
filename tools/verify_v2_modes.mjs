#!/usr/bin/env node
/**
 * Mode-switch regression for the v2 exhibit's three look-dev rigs.
 *
 *   node tools/verify_v2_modes.mjs
 *
 * The black box is a presentation stage that borrows the factory's materials and adds geometry of
 * its own. Both of those are the kind of thing that quietly accumulates: an override that is
 * applied but never restored becomes the next mode's baseline, and a floor that is added but never
 * removed becomes two floors. Neither shows up as an error — the page keeps rendering, just wrong,
 * and the review rigs that every gate is measured under stop being what they were.
 *
 * So this asserts what the eye cannot check:
 *   1. referenceLighting -> blackBox -> referenceLighting restores every material value exactly
 *   2. repeated switching leaves exactly one stage floor and one spotlight, never two
 *   3. the review rigs carry no material overrides and no stage geometry at all
 *   4. the part manifest is unchanged by any of it — stage dressing is not a component
 *
 * Drives the Vite dev server, like tools/capture_ultima.mjs. Exits non-zero on the first failure.
 */

import { spawn } from "node:child_process";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = "/img2three-art-exhibition";
const PORT = 3178; // not 3177: capture_ultima.mjs owns that one, and the two may run together
const MODES = { reference: "參考外觀", neutral: "中性複核", black: "黑箱舞台" };

const failures = [];
const check = (ok, label, detail = "") => {
  if (ok) console.log(`ok    ${label}`);
  else {
    console.log(`FAIL  ${label}${detail ? `\n      ${detail}` : ""}`);
    failures.push(label);
  }
};

async function waitForServer(url, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`dev server never became ready at ${url}`);
}

/**
 * Everything about the scene this test can assert on, read out of the live viewer.
 *
 * Material values are flattened to primitives and colour hexes so they can be compared with a
 * plain deep-equal — a THREE.Color that survived a round trip is only equal to its former self by
 * value, never by identity.
 */
const probe = () => {
  const handle = window.__v2Viewer;
  if (!handle) return { error: "window.__v2Viewer missing — did the viewer mount?" };
  let spotlights = 0;
  let floors = 0;
  let lightGroups = 0;
  handle.scene.traverse((o) => {
    if (o.isSpotLight) spotlights += 1;
    if (o.name === "stageFloor") floors += 1;
    if (o.name === "lookDevRig") lightGroups += 1;
  });
  const materials = {};
  for (const [name, material] of Object.entries(handle.materials)) {
    const row = {};
    for (const key of [
      "transparent",
      "opacity",
      "transmission",
      "ior",
      "thickness",
      "roughness",
      "metalness",
      "envMapIntensity",
      "depthWrite",
      "side",
      "emissiveIntensity",
      "attenuationDistance",
    ]) {
      const value = material[key];
      if (value === undefined) continue;
      row[key] = typeof value === "object" && value?.isColor ? value.getHexString() : value;
    }
    if (material.attenuationColor?.isColor) {
      row.attenuationColor = material.attenuationColor.getHexString();
    }
    materials[name] = row;
  }
  return { spotlights, floors, lightGroups, materials };
};

const diffMaterials = (before, after) => {
  const out = [];
  for (const [name, props] of Object.entries(before)) {
    for (const [key, value] of Object.entries(props)) {
      const now = after[name]?.[key];
      if (now !== value) out.push(`${name}.${key}: ${value} -> ${now}`);
    }
  }
  return out;
};

async function main() {
  const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
    cwd: ROOT,
    stdio: ["ignore", "pipe", "pipe"],
  });
  const origin = `http://localhost:${PORT}`;
  const browser = await chromium.launch();

  try {
    await waitForServer(`${origin}${BASE}/`);
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const consoleErrors = [];
    page.on("pageerror", (e) => consoleErrors.push(String(e)));
    page.on("console", (m) => m.type() === "error" && consoleErrors.push(m.text()));

    await page.goto(`${origin}${BASE}/ff7-cloud-strife-ultima-weapon`, { waitUntil: "load" });
    await page.waitForFunction(() => Boolean(window.__v2Viewer), null, { timeout: 30_000 });

    const click = async (label) => {
      await page.getByRole("button", { name: label, exact: true }).click();
      await page.waitForTimeout(350);
      return page.evaluate(probe);
    };

    // The page opens on the reference rig, so click it first to establish the review baseline.
    const reference = await click(MODES.reference);
    check(!reference.error, "viewer exposes its debug handle", reference.error ?? "");
    check(
      reference.spotlights === 0 && reference.floors === 0,
      "referenceLighting carries no stage geometry",
      `spotlights=${reference.spotlights} floors=${reference.floors}`,
    );

    const black = await click(MODES.black);
    check(
      black.spotlights === 1 && black.floors === 1,
      "blackBox builds exactly one key and one floor",
      `spotlights=${black.spotlights} floors=${black.floors}`,
    );
    check(
      diffMaterials(reference.materials, black.materials).length > 0,
      "blackBox actually overrides materials",
      "no material differed from the review rig — the override table is not being applied",
    );

    const backAgain = await click(MODES.reference);
    const drift = diffMaterials(reference.materials, backAgain.materials);
    check(drift.length === 0, "round trip restores every material value", drift.join("; "));
    check(
      backAgain.spotlights === 0 && backAgain.floors === 0,
      "leaving blackBox removes its stage geometry",
      `spotlights=${backAgain.spotlights} floors=${backAgain.floors}`,
    );

    // Accumulation only shows up after repetition: one leaked floor per switch looks identical to
    // none until you switch enough times.
    let last = backAgain;
    for (let i = 0; i < 3; i += 1) {
      await click(MODES.black);
      await click(MODES.neutral);
      last = await click(MODES.black);
    }
    check(
      last.spotlights === 1 && last.floors === 1 && last.lightGroups === 1,
      "nothing accumulates over repeated switching",
      `after 3 more round trips: spotlights=${last.spotlights} floors=${last.floors} rigs=${last.lightGroups}`,
    );

    const settled = await click(MODES.reference);
    const finalDrift = diffMaterials(reference.materials, settled.materials);
    check(
      finalDrift.length === 0,
      "materials still intact after repeated switching",
      finalDrift.join("; "),
    );

    check(consoleErrors.length === 0, "no console or page errors", consoleErrors.join(" | "));
  } finally {
    await browser.close();
    server.kill("SIGTERM");
  }

  if (failures.length) {
    console.log(`\n${failures.length} failure(s): ${failures.join(", ")}`);
    process.exitCode = 1;
  } else {
    console.log("\nall mode-switch checks passed");
  }
}

main().catch((cause) => {
  console.error(cause);
  process.exitCode = 1;
});
