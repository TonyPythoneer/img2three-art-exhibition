#!/usr/bin/env node
/** Exploded parts must stay above the black box floor. */
import { spawn } from "node:child_process";
import process from "node:process";
import { chromium } from "playwright";

const ROOT = "/Users/tonyyang/git/personal/img2three-art-exhibition";
const BASE = "/img2three-art-exhibition";
const PORT = 3179;

const waitForServer = async (url) => {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {}
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error("dev server never came up");
};

/** Lowest world-space Y of the model, and the floor's Y, read without a THREE import. */
const probe = () => {
  const scene = window.__v2Viewer?.scene;
  if (!scene) return { error: "no __v2Viewer" };
  let floorY = null;
  let lowest = Infinity;
  const model = scene.children.find((c) => c.userData?.sculptRuntime);
  scene.updateMatrixWorld(true);
  scene.traverse((o) => {
    if (o.name === "stageFloor") floorY = o.matrixWorld.elements[13];
  });
  model?.traverse((o) => {
    if (!o.isMesh || !o.visible) return;
    o.geometry.computeBoundingBox();
    const b = o.geometry.boundingBox;
    const e = o.matrixWorld.elements;
    for (const x of [b.min.x, b.max.x])
      for (const y of [b.min.y, b.max.y])
        for (const z of [b.min.z, b.max.z]) {
          const wy = e[1] * x + e[5] * y + e[9] * z + e[13];
          if (wy < lowest) lowest = wy;
        }
  });
  return { floorY, lowest, lift: model?.position.y ?? null };
};

const server = spawn("npx", ["vite", "--port", String(PORT), "--strictPort"], {
  cwd: ROOT,
  stdio: ["ignore", "pipe", "pipe"],
});
const origin = `http://localhost:${PORT}`;
const browser = await chromium.launch();
let failed = false;

try {
  await waitForServer(`${origin}${BASE}/`);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(`${origin}${BASE}/ff7-cloud-ultima-weapon`, { waitUntil: "load" });
  await page.waitForFunction(() => Boolean(window.__v2Viewer), null, { timeout: 30_000 });

  await page.getByRole("button", { name: "Controls", exact: true }).click();
  await page.getByRole("button", { name: "Black Box Stage", exact: true }).click();
  await page.waitForTimeout(400);
  const rest = await page.evaluate(probe);

  await page.getByRole("button", { name: /Explode parts/ }).click();
  await page.waitForTimeout(2400);
  const blown = await page.evaluate(probe);

  await page.getByRole("button", { name: /Assemble/ }).click();
  await page.waitForTimeout(2400);
  const back = await page.evaluate(probe);

  console.log("rest  ", rest);
  console.log("blown ", blown);
  console.log("back  ", back);

  const ok = (label, cond) => {
    console.log(`${cond ? "ok   " : "FAIL "} ${label}`);
    if (!cond) failed = true;
  };
  ok("floor exists in black box", rest.floorY !== null);
  ok("at rest the model clears the floor", rest.lowest > rest.floorY);
  ok("at rest there is no lift", Math.abs(rest.lift) < 1e-6);
  ok("exploded parts stay above the floor", blown.lowest > blown.floorY);
  ok("exploding did lift the model", blown.lift > 0);
  ok("assembling drops the lift back", Math.abs(back.lift) < 1e-6);
} finally {
  await browser.close();
  server.kill("SIGTERM");
}
process.exitCode = failed ? 1 : 0;
