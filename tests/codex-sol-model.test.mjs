import test from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";

const factoryUrl = new URL(
  "../src/exhibits/cloud-ultima-weapon-codex-sol/createCodexSolUltimaWeaponModel.ts",
  import.meta.url,
);

test("Codex Sol owns an independent named model hierarchy", async () => {
  assert.ok(existsSync(factoryUrl), "Codex Sol factory must exist");
  const source = readFileSync(factoryUrl, "utf8");
  assert.doesNotMatch(source, /cloud-ultima-weapon(?:-fable)?\//);

  const { createCodexSolUltimaWeaponModel } = await import(factoryUrl.href);
  const model = createCodexSolUltimaWeaponModel();

  assert.equal(model.name, "codexSolUltimaWeapon");
  assert.equal(model.userData.provenance, "codex-sol-5.6-xhigh");
  for (const name of [
    "outerShell",
    "purpleCore",
    "magentaSpine",
    "guardAssembly",
    "handleAssembly",
  ]) {
    assert.ok(model.getObjectByName(name), `missing ${name}`);
  }
});

test("explode moves parts and restores their authored transforms", async () => {
  assert.ok(existsSync(factoryUrl), "Codex Sol factory must exist");
  const { createCodexSolUltimaWeaponModel } = await import(factoryUrl.href);
  const model = createCodexSolUltimaWeaponModel();
  const runtime = model.userData.sculptRuntime;
  const before = new Map(runtime.parts.map((part) => [part.id, part.object.position.clone()]));

  runtime.setExplode(1);
  assert.ok(
    runtime.parts.some((part) => part.object.position.distanceTo(before.get(part.id)) > 1e-9),
  );

  runtime.setExplode(0);
  assert.ok(
    runtime.parts.every((part) => part.object.position.distanceTo(part.homePosition) < 1e-9),
  );
});
